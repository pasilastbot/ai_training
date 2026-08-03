#!/usr/bin/env bash
# Start all Session 3 agents: FastAPI (8001–8005) then Flask UIs (5001–5005).
# Run from repo: ./agents/start-all.sh
# Loads env files before spawning (same idea as agent_env.py): parent repo, then session folder.
# Prerequisites: python3.12+ .venv (see below); GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY in .env

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
LOG="${TMPDIR:-/tmp}/session3-agents"
mkdir -p "$LOG"

load_env_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  set -a
  # shellcheck disable=SC1090
  . "$f"
  set +a
}

# Broad → narrow so session-specific .env wins over repo root
load_env_file "${ROOT}/../.env"
load_env_file "${ROOT}/.env"
load_env_file "${ROOT}/../.env.local"
load_env_file "${ROOT}/.env.local"

if [[ ! -x "$PY" ]]; then
  echo "Missing interpreter: $PY"
  echo "Create venv (Python 3.12+ recommended): cd \"$ROOT\" && /opt/homebrew/bin/python3.12 -m venv .venv && . .venv/bin/activate && pip install -U pip && for f in agents/*/requirements.txt; do pip install -r \"\$f\"; done"
  exit 1
fi

start_api() {
  local dir="$1" tag="$2"
  (cd "${ROOT}/agents/${dir}" && nohup "$PY" api/main.py >>"${LOG}/${tag}-api.log" 2>&1 &)
}

start_ui() {
  local dir="$1" tag="$2"
  (cd "${ROOT}/agents/${dir}" && nohup "$PY" ui/app.py >>"${LOG}/${tag}-ui.log" 2>&1 &)
}

start_api prospecting-agent prospecting
start_api lunch-selection-agent lunch
start_api tes-agent tes
start_api holiday-planner holiday
start_api weather-forecast-agent weather

sleep 4

start_ui prospecting-agent prospecting
start_ui lunch-selection-agent lunch
start_ui tes-agent tes
start_ui holiday-planner holiday
start_ui weather-forecast-agent weather

echo "Session 3 agents started. Logs: ${LOG}"
echo "UIs: http://localhost:5001 http://localhost:5002 http://localhost:5003 http://localhost:5004 http://localhost:5005"

if [[ "$(uname -s)" == "Darwin" ]]; then
  for u in http://localhost:5001 http://localhost:5002 http://localhost:5003 http://localhost:5004 http://localhost:5005; do
    open "$u"
  done
fi
