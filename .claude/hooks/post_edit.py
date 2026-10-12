#!/usr/bin/env python3
"""Hook PostToolUse (Edit|Write) du projet MadaSource.

1. Fichier Python modifié : si Ruff est installé (backend/.venv, .venv ou
   PATH), lance `ruff format` puis `ruff check` (sans --fix) sur ce seul
   fichier. Les erreurs de lint sont renvoyées à Claude pour correction.
   Si Ruff est absent, ne fait rien. Aucun test n'est lancé ici : la suite
   complète passe par le skill pytest-workflow.
2. Fichier critique modifié (Docker, CI, dépendances, migrations, sécurité,
   configuration Claude) : ajoute un rappel de relecture par l'agent adapté.

Désactivation : retirer son entrée dans .claude/settings.json, ou
"disableAllHooks": true dans .claude/settings.local.json (personnel).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PREFIX = "[MadaSource post-edit]"
MAX_OUTPUT = 3000

REMINDERS = [
    (re.compile(r"(^|/)((docker-)?compose[\w.-]*\.ya?ml|Dockerfile[\w.-]*|\.dockerignore)$"),
     "fichier Docker modifié : vérification par l'agent devops-engineer (skill docker-ci)."),
    (re.compile(r"^\.github/workflows/"), "workflow CI modifié : vérification par l'agent devops-engineer."),
    (re.compile(r"(^|/)(pyproject\.toml|uv\.lock|\.python-version)$"),
     "dépendances ou version Python modifiées : justifier la dépendance, vérifier la cohérence des versions (skill docker-ci)."),
    (re.compile(r"(^|/)\.env\.example$"), "`.env.example` modifié : valeurs factices uniquement, documenter chaque variable."),
    (re.compile(r"^backend/alembic/|(^|/)alembic\.ini$|^backend/app/.*models\.py$"),
     "modèle ou migration modifié : relecture par l'agent database-reviewer (skill database-migrations)."),
    (re.compile(r"^backend/app/(core/(security|config)|modules/(auth|access_control|audit)/)"),
     "code de sécurité modifié : audit par l'agent security-auditor."),
    (re.compile(r"^(CLAUDE\.md|\.claude/(agents|skills|rules)/)"),
     "configuration Claude Code modifiée : mettre à jour docs/backend/claude-code-setup.md."),
]


def find_ruff(project: Path) -> str | None:
    for candidate in (project / "backend/.venv/bin/ruff", project / ".venv/bin/ruff"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return shutil.which("ruff")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=25)


def main() -> None:
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input") or {}
    raw_path = tool_input.get("file_path")
    if not raw_path:
        return

    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    path = Path(raw_path)
    if not path.is_absolute():
        path = project / path
    path = path.resolve()
    try:
        rel = path.relative_to(project).as_posix()
    except ValueError:
        return

    notes = [msg for pattern, msg in REMINDERS if pattern.search(rel)]
    lint_report = ""

    if path.suffix == ".py" and path.is_file() and "/.venv/" not in f"/{rel}":
        ruff = find_ruff(project)
        if ruff:
            run([ruff, "format", "--quiet", str(path)], project)
            check = run([ruff, "check", "--quiet", "--output-format=concise", str(path)], project)
            if check.returncode != 0:
                lint_report = (check.stdout + check.stderr).strip()[:MAX_OUTPUT]

    output: dict = {}
    if lint_report:
        output["decision"] = "block"
        output["reason"] = f"{PREFIX} Ruff signale des problèmes dans {rel} (fichier déjà formaté) :\n{lint_report}"
    if notes:
        output["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": f"{PREFIX} " + " ".join(notes),
        }
    if output:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # non bloquant : signalé sur stderr
        print(f"{PREFIX} erreur interne du hook : {exc}", file=sys.stderr)
        sys.exit(1)
