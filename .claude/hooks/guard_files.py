#!/usr/bin/env python3
"""Hook PreToolUse (Edit|Write|NotebookEdit) du projet MadaSource.

- Refuse (deny) l'écriture de fichiers de secrets par Claude : vrais .env,
  clés privées, certificats, dossier secrets/.
- Demande confirmation (ask) avant de modifier un fichier critique :
  configuration Claude Code et hooks, workflows CI, roadmap et planning,
  révision Alembic déjà existante.
- Laisse passer tout le reste, sans rien afficher.

Ce script ne modifie rien. Désactivation : retirer son entrée dans
.claude/settings.json, ou "disableAllHooks": true dans
.claude/settings.local.json (personnel).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PREFIX = "[MadaSource guard]"

ENV_FILE = re.compile(r"^\.env(\.[\w.-]+)?$")
ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist")
SECRET_FILE = re.compile(r"^(id_(rsa|ed25519|ecdsa|dsa)(\.pub)?|.*\.(pem|key|p12|pfx|jks|keystore))$")

ASK_EXACT = {
    ".claude/settings.json": "configuration partagée de Claude Code (permissions et hooks).",
    ".claude/settings.local.json": "configuration personnelle de Claude Code.",
    "roadmap.md": "roadmap métier : modification soumise à validation.",
    "roadmap_backend_fastapi.md": "roadmap backend : modification soumise à validation.",
    "planning.md": "planning client : modification soumise à validation.",
}
ASK_PREFIX = {
    ".claude/hooks/": "script de hook de sécurité.",
    ".github/workflows/": "workflow CI.",
}
MIGRATIONS_DIR = "backend/alembic/versions/"


def decide(decision: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"{PREFIX} {reason}",
        }
    }, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input") or {}
    raw_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not raw_path:
        return

    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    path = Path(raw_path)
    if not path.is_absolute():
        path = project / path
    path = path.resolve()
    name = path.name

    if (ENV_FILE.match(name) and not name.endswith(ENV_TEMPLATE_SUFFIXES)) or SECRET_FILE.match(name) \
            or "secrets" in path.parts:
        decide("deny", f"« {name} » peut contenir des secrets : Claude ne l'écrit pas. "
                       "Modifiez-le vous-même ; seul .env.example est géré par Claude.")

    try:
        rel = path.relative_to(project).as_posix()
    except ValueError:
        return  # hors du projet : laissé aux règles de permission normales

    if rel in ASK_EXACT:
        decide("ask", f"fichier critique : {ASK_EXACT[rel]}")
    for prefix, reason in ASK_PREFIX.items():
        if rel.startswith(prefix):
            decide("ask", f"fichier critique : {reason}")
    if rel.startswith(MIGRATIONS_DIR) and rel.endswith(".py") and path.exists():
        decide("ask", "modification d'une révision Alembic existante. Si elle est déjà appliquée "
                      "ou partagée, créer une nouvelle révision plutôt que l'éditer.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # échec ouvert, signalé sur stderr
        print(f"{PREFIX} erreur interne du hook : {exc}", file=sys.stderr)
        sys.exit(1)
