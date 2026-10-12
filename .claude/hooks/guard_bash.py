#!/usr/bin/env python3
"""Hook PreToolUse (Bash) du projet MadaSource.

Lit l'événement JSON de Claude Code sur stdin, puis :
- refuse (deny) les commandes que Claude ne doit jamais lancer dans ce projet ;
- demande confirmation (ask) pour les commandes destructrices ou sortantes ;
- laisse passer tout le reste, sans rien afficher.

Ce script ne modifie rien. En cas d'erreur interne, il échoue « ouvert »
(code 1, non bloquant) : les règles `permissions` de settings.json restent
la première ligne de défense.

Désactivation : retirer son entrée dans .claude/settings.json, ou mettre
"disableAllHooks": true dans .claude/settings.local.json (personnel).
"""

from __future__ import annotations

import json
import re
import shlex
import sys

PREFIX = "[MadaSource guard]"

# Vrais fichiers d'environnement (secrets). Les modèles versionnés restent lisibles.
ENV_FILE = re.compile(r"^\.env(\.[\w.-]+)?$")
ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist")
READERS = {
    "cat", "tac", "nl", "less", "more", "head", "tail", "bat", "batcat",
    "grep", "egrep", "rg", "ag", "awk", "gawk", "sed", "cut", "sort", "uniq",
    "strings", "xxd", "od", "hexdump", "base64", "diff", "jq", "yq",
    "cp", "mv", "scp", "rsync", "source", ".", "vi", "vim", "nano", "emacs",
}
DANGEROUS_RM_TARGETS = {"/", "/*", "~", "~/", "$HOME", "${HOME}", "*", ".", "./", "..", "../"}

DENY = [
    (re.compile(r"(^|[\s;&|(])sudo\s"), "sudo est interdit à Claude dans ce projet."),
    (re.compile(r"\bdocker\s+(system|volume|image|container|builder|network)\s+prune\b"),
     "un prune Docker supprime des données ou des images."),
    (re.compile(r"\bmkfs(\.\w+)?\b|\bdd\s[^;&|]*\bof=/dev/"), "écriture disque brute."),
    (re.compile(r"\bchmod\s+(-\S+\s+)*(0?777|a\+rwx|ugo\+rwx)\b"), "permissions 777."),
    (re.compile(r"\balembic\s+downgrade\s+base\b"), "`alembic downgrade base` détruit tout le schéma."),
]
DENY_SQL = re.compile(r"(?i)\bdrop\s+(database|schema)\b")

ASK = [
    (re.compile(r"\bdocker[\s-]+compose\b[^;&|]*\bdown\b[^;&|]*\s(-v|--volumes)\b"),
     "`docker compose down -v` supprime les volumes (données PostgreSQL)."),
    (re.compile(r"\bdocker\s+volume\s+rm\b|\bdocker\s+rm\b[^;&|]*\s-[a-zA-Z]*v"), "suppression de volume Docker."),
    (re.compile(r"\bgit\s+reset\s+[^;&|]*--hard\b"), "`git reset --hard` efface les modifications locales."),
    (re.compile(r"\bgit\s+clean\b[^;&|]*\s-[a-zA-Z]*f"), "`git clean -f` supprime les fichiers non suivis."),
    (re.compile(r"\bgit\s+push\b[^;&|]*\s(--force(-with-lease)?\b|-[a-zA-Z]*f\b)"), "push forcé."),
    (re.compile(r"\bgit\s+(checkout|restore)\b[^;&|]*\s\.(\s|$)"), "abandon de toutes les modifications locales."),
    (re.compile(r"\bgit\s+branch\s+[^;&|]*-D\b"), "suppression forcée de branche."),
    (re.compile(r"\bgit\s+stash\s+(drop|clear)\b"), "suppression de stash."),
    (re.compile(r"\balembic\s+downgrade\b"), "downgrade de migration Alembic."),
    (re.compile(r"\bdropdb\b"), "suppression de base PostgreSQL."),
    (re.compile(r"\b(kubectl|helm|flyctl|heroku|ansible-playbook)\b|\bterraform\s+(apply|destroy)\b|\bfly\s+deploy\b|\bvercel\b"),
     "commande de déploiement : jamais sans demande explicite."),
    (re.compile(r"(^|[\s;&|])(ssh|scp)\s"), "connexion à une machine distante."),
    (re.compile(r"\bdocker\s+push\b|\buv\s+publish\b|\btwine\s+upload\b|\bnpm\s+publish\b|\bgh\s+release\s+create\b"),
     "publication vers un service externe."),
    (re.compile(r"\b(curl|wget)\b[^;&]*\|\s*(ba|z|fi)?sh\b"), "exécution d'un script téléchargé."),
]
ASK_SQL = re.compile(r"(?i)\b(drop\s+table|truncate|delete\s+from|alter\s+table\s+\S+\s+drop)\b")
SQL_CLIENT = re.compile(r"\b(psql|pgcli)\b")


def decide(decision: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"{PREFIX} {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def is_real_env_file(token: str) -> bool:
    name = token.strip("'\"").rstrip("/").rsplit("/", 1)[-1]
    if name.startswith("<"):
        name = name[1:]
    return bool(ENV_FILE.match(name)) and not name.endswith(ENV_TEMPLATE_SUFFIXES)


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def program_of(tokens: list[str]) -> tuple[str, list[str]]:
    """Retourne le programme (sans chemin) et ses arguments, en sautant VAR=val."""
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    if i >= len(tokens):
        return "", []
    return tokens[i].rsplit("/", 1)[-1], tokens[i + 1:]


def check_segment(segment: str) -> tuple[str, str] | None:
    tokens = tokenize(segment)
    prog, args = program_of(tokens)

    # Lecture ou copie d'un vrai .env (y compris par redirection « < .env »).
    for idx, tok in enumerate(tokens):
        if is_real_env_file(tok) and (prog in READERS or (idx > 0 and tokens[idx - 1] == "<") or tok.startswith("<")):
            return "deny", "lecture ou copie d'un vrai fichier .env (secrets). Seul .env.example est lisible."

    if prog == "rm":
        flags = [a for a in args if a.startswith("-") and a != "--"]
        targets = [a for a in args if not a.startswith("-")]
        recursive = "--recursive" in flags or any("r" in f.lower() for f in flags if not f.startswith("--"))
        force = "--force" in flags or any("f" in f for f in flags if not f.startswith("--"))
        if recursive and any(t in DANGEROUS_RM_TARGETS or re.fullmatch(r"/home/[^/]+/?", t) for t in targets):
            return "deny", "suppression récursive de la racine, du répertoire personnel, du dossier courant ou d'un joker."
        if recursive or force:
            return "ask", f"suppression de fichiers ({' '.join(['rm', *args])[:120]})."
    return None


def main() -> None:
    event = json.load(sys.stdin)
    if event.get("tool_name") != "Bash":
        return
    command = (event.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        return

    for pattern, reason in DENY:
        if pattern.search(command):
            decide("deny", reason)
    if SQL_CLIENT.search(command) and DENY_SQL.search(command):
        decide("deny", "suppression de base ou de schéma PostgreSQL.")

    pending_ask: str | None = None
    for segment in re.split(r"\|\||&&|[;|&\n]", command):
        if not segment.strip():
            continue
        result = check_segment(segment)
        if result and result[0] == "deny":
            decide("deny", result[1])
        if result and pending_ask is None:
            pending_ask = result[1]

    if pending_ask:
        decide("ask", pending_ask)
    for pattern, reason in ASK:
        if pattern.search(command):
            decide("ask", reason)
    if SQL_CLIENT.search(command) and ASK_SQL.search(command):
        decide("ask", "commande SQL destructrice (DROP TABLE, TRUNCATE, DELETE, ALTER … DROP).")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # échec ouvert, signalé sur stderr
        print(f"{PREFIX} erreur interne du hook : {exc}", file=sys.stderr)
        sys.exit(1)
