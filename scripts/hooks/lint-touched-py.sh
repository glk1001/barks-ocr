#!/usr/bin/env bash
#
# lint-touched-py.sh -- PostToolUse hook: ruff + ty on the .py file just edited.
#
# Wired up in .claude/settings.json under PostToolUse / "Edit|Write". Reads the
# hook payload on stdin, and for a Python file inside this repo runs, in order:
#
#   uv run ruff check --fix <file>    fix what is auto-fixable
#   uv run ruff format <file>         apply the 100-column format
#   uv run ty check <file>            report what neither can fix
#
# NON-BLOCKING by design. ruff's two passes repair the file silently; anything
# still wrong is handed back as `additionalContext` so it reaches the model
# without failing the edit. A mid-refactor file is routinely un-type-checkable
# for a few edits, and a blocking gate there would stop honest work.
#
# Exits 0 always. A missing uv, a file outside the repo, or a non-.py path is a
# no-op, so the hook cannot break an editing session.
#
# Test it without an edit:
#   echo '{"tool_input":{"file_path":"src/barks_ocr/tools/vision_status.py"}}' \
#       | bash scripts/hooks/lint-touched-py.sh

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

payload=$(cat)
file=$(printf '%s' "$payload" | jq -r '.tool_response.filePath // .tool_input.file_path // empty' 2>/dev/null)

[[ -n "$file" && "$file" == *.py ]] || exit 0

# Relative paths in the payload are relative to the project dir.
[[ "$file" = /* ]] || file="$REPO_DIR/$file"
[[ -f "$file" ]] || exit 0

# Only lint files belonging to this repo -- a session can touch several.
[[ "$file" == "$REPO_DIR"/* ]] || exit 0

command -v uv >/dev/null 2>&1 || exit 0

# uv resolves the project from the cwd, so run from the repo root regardless of
# where the hook was invoked.
cd "$REPO_DIR" || exit 0

out=$( (uv run ruff check --fix "$file" && uv run ruff format "$file" && uv run ty check "$file") 2>&1 )
status=$?
((status == 0)) && exit 0

# Feed the failure back as context rather than blocking the edit.
jq -n --arg ctx "ruff/ty on ${file#"$REPO_DIR"/}:
$out" '{
    hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext: $ctx
    }
}'
exit 0
