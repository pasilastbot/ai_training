#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Factory Rehearsal Demo (Claude + Codex) ==="
echo "Folder: $SCRIPT_DIR"

if command -v uv >/dev/null 2>&1; then
  PYTHON_CMD=(uv run python)
  echo "[info] Using Python runner: uv run python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=(python3)
  echo "[info] Using Python runner: python3"
else
  echo "[error] Neither uv nor python3 found"
  exit 1
fi

echo
echo "0) Runtime info"
"${PYTHON_CMD[@]}" - <<'PY'
import platform
import sys
print(f"[info] python: {sys.version.split()[0]}")
if sys.version_info < (3, 10):
    print("[warn] Python < 3.10 detected. Some backends in this repo need newer Python.")
print(f"[info] platform: {platform.platform()}")
PY

echo
echo "1) Syntax check"
"${PYTHON_CMD[@]}" -m py_compile \
  backend_runner.py \
  01_minimal_factory.py \
  02_factory_catalog.py \
  03_resumable_factory.py \
  04_spec_loop_factory.py
echo "[ok] Python syntax is valid"

echo
echo "2) Dependency check"
claude_sdk_ok=0
set +e
"${PYTHON_CMD[@]}" - <<'PY'
try:
    import claude_agent_sdk  # noqa: F401
    print("[ok] claude-agent-sdk is installed")
except Exception:
    print("[warn] claude-agent-sdk not installed")
    print("       Install with: pip install -r requirements.txt")
    raise SystemExit(1)
PY
if [[ "$?" -eq 0 ]]; then
  claude_sdk_ok=1
fi
set -e

if command -v codex >/dev/null 2>&1; then
  echo "[ok] codex binary found"
  codex --version || true
else
  echo "[warn] codex binary not found (Codex backend will be skipped)"
fi

if command -v opencode >/dev/null 2>&1; then
  echo "[ok] opencode binary found"
  opencode --version || true
else
  echo "[warn] opencode binary not found (OpenCode backend will be skipped)"
fi

echo
echo "3) Runtime demo"
have_attempts=0
failed_runs=0

if [[ "$claude_sdk_ok" -eq 1 ]]; then
  echo "[info] Attempting Claude backend demo"
  have_attempts=1
  set +e
  "${PYTHON_CMD[@]}" 01_minimal_factory.py --backend claude "Give a short definition of software factory pattern."
  status_one=$?
  "${PYTHON_CMD[@]}" 02_factory_catalog.py planner --backend claude "Create a 3-step plan to build a custom factory."
  status_two=$?
  set -e
  if [[ "$status_one" -ne 0 || "$status_two" -ne 0 ]]; then
    failed_runs=1
    echo "[warn] Claude backend demo failed."
    echo "       If you rely on API auth, set ANTHROPIC_API_KEY."
    echo "       If you rely on CLI/subscription auth, verify local Claude auth/session."
  fi
else
  echo "[warn] Skipping Claude backend demo (claude-agent-sdk not installed)"
fi

if command -v codex >/dev/null 2>&1; then
  echo "[info] Attempting Codex backend demo"
  have_attempts=1
  set +e
  timeout 45s "${PYTHON_CMD[@]}" 01_minimal_factory.py --backend codex "Give a short definition of software factory pattern."
  status_three=$?
  timeout 45s "${PYTHON_CMD[@]}" 02_factory_catalog.py planner --backend codex "Create a 3-step plan to build a custom factory."
  status_four=$?
  set -e
  if [[ "$status_three" -ne 0 || "$status_four" -ne 0 ]]; then
    failed_runs=1
    echo "[warn] Codex backend demo failed."
    if [[ "$status_three" -eq 124 || "$status_four" -eq 124 ]]; then
      echo "       Codex call timed out (possible interactive auth prompt)."
    fi
    echo "       Ensure codex auth is active (or set OPENAI_API_KEY if needed)."
  fi
else
  echo "[warn] Skipping Codex backend demo (codex binary not found)"
fi

if command -v opencode >/dev/null 2>&1; then
  echo "[info] Attempting OpenCode backend demo"
  have_attempts=1
  set +e
  timeout 45s "${PYTHON_CMD[@]}" 01_minimal_factory.py --backend opencode "Give a short definition of software factory pattern."
  status_five=$?
  set -e
  if [[ "$status_five" -ne 0 ]]; then
    failed_runs=1
    echo "[warn] OpenCode backend demo failed."
    if [[ "$status_five" -eq 124 ]]; then
      echo "       OpenCode call timed out (possible interactive auth prompt)."
    fi
    echo "       Ensure opencode auth is active and the selected model is available."
  fi
else
  echo "[warn] Skipping OpenCode backend demo (opencode binary not found)"
fi

if [[ "$have_attempts" -eq 0 ]]; then
  echo "[warn] No backends were attempted."
  exit 0
fi

if [[ "$failed_runs" -ne 0 ]]; then
  echo
  echo "[warn] One or more live demo runs failed."
  exit 1
fi

echo
echo "[ok] Live demo runs completed"
