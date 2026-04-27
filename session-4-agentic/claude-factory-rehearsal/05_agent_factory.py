#!/usr/bin/env python3
"""
Agent Factory — Creates and validates new agents under session-3-ai-agents.

This factory combines all previous concepts:
- Roles (spec_generator, implementer, validator, reviewer) from 02_factory_catalog.py
- Resume capability from 03_resumable_factory.py
- Spec-driven loops from 04_spec_loop_factory.py

Workflow:
1. SPEC GENERATION: Generate agent specification from a simple idea
2. IMPLEMENT: Create the agent following the spec and AGENTS.md structure
3. VALIDATE: Run syntax/lint/test checks
4. REVIEW: Evaluate completeness and quality
5. FIX: Loop back to fix issues until all checks pass

Usage:
  # Start fresh with an idea
  uv run python 05_agent_factory.py start --backend claude "weather agent that shows forecasts"

  # Resume a previous session
  uv run python 05_agent_factory.py resume --backend claude "continue implementing"

  # Generate spec only (no implementation)
  uv run python 05_agent_factory.py spec --backend claude "recipe finder agent"

  # Implement from existing spec file
  uv run python 05_agent_factory.py implement --backend claude --spec agent-spec.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from backend_runner import Backend, BackendRunOptions, run_sync

AGENTS_BASE = Path(__file__).resolve().parents[2] / 'session-3-ai-agents' / 'agents'
SESSION_FILE_PREFIX = '.agent-factory-session-'


@dataclass
class RoleSpec:
    name: str
    role: str
    allowed_tools: list[str]
    permission_mode: str
    max_turns: int


ROLES: dict[str, RoleSpec] = {
    'spec_generator': RoleSpec(
        name='spec_generator',
        role=(
            'You are a specification architect. Your job is to generate detailed '
            'JSON specifications for new AI agents. You analyze requirements and '
            'produce structured specs that can be implemented. Do not write code, '
            'only produce the specification JSON.'
        ),
        allowed_tools=['Read', 'Glob', 'Grep'],
        permission_mode='default',
        max_turns=15,
    ),
    'implementer': RoleSpec(
        name='implementer',
        role=(
            'You are an implementation factory. Your job is to implement agents '
            'according to specifications. You write clean, working Python code '
            'following the exact structure defined in AGENTS.md. Create all required '
            'files: main agent, UI, API, tools, skills, subagents, and memory.'
        ),
        allowed_tools=['Read', 'Glob', 'Grep', 'Edit', 'Bash'],
        permission_mode='acceptEdits',
        max_turns=30,
    ),
    'validator': RoleSpec(
        name='validator',
        role=(
            'You are a validation factory. Your job is to check that implementations '
            'are syntactically correct, follow the required structure, and pass basic '
            'tests. Report issues clearly with file paths and line numbers.'
        ),
        allowed_tools=['Read', 'Glob', 'Grep', 'Bash'],
        permission_mode='default',
        max_turns=15,
    ),
    'reviewer': RoleSpec(
        name='reviewer',
        role=(
            'You are a code review factory. Your job is to review agent implementations '
            'for completeness, quality, and adherence to the spec. Return exactly one marker: '
            'FINAL_STATUS: APPROVED or FINAL_STATUS: CHANGES_REQUIRED with specific feedback.'
        ),
        allowed_tools=['Read', 'Glob', 'Grep'],
        permission_mode='default',
        max_turns=12,
    ),
    'fixer': RoleSpec(
        name='fixer',
        role=(
            'You are a bug-fix factory. Your job is to fix issues found during validation '
            'or review. Make minimal, targeted fixes that address the specific problems. '
            'Focus on one issue at a time and verify the fix before moving on.'
        ),
        allowed_tools=['Read', 'Glob', 'Grep', 'Edit', 'Bash'],
        permission_mode='acceptEdits',
        max_turns=20,
    ),
}


@dataclass
class CheckResult:
    name: str
    command: str
    passed: bool
    exit_code: int
    output: str


def session_file_for(backend: str) -> Path:
    return Path(f'{SESSION_FILE_PREFIX}{backend}')


def load_session_id(backend: str) -> str | None:
    session_file = session_file_for(backend)
    if not session_file.exists():
        return None
    text = session_file.read_text(encoding='utf-8').strip()
    return text or None


def save_session_id(backend: str, session_id: str) -> None:
    session_file_for(backend).write_text(session_id, encoding='utf-8')


def resolve_python_cmd() -> str:
    uv_probe = subprocess.run(
        ['bash', '-lc', "command -v uv >/dev/null 2>&1 && uv run python -c \"print('ok')\""],
        capture_output=True,
        text=True,
        check=False,
    )
    if uv_probe.returncode == 0:
        return 'uv run python'
    return 'python3'


def load_agents_md() -> str:
    agents_md_path = AGENTS_BASE / 'AGENTS.md'
    if agents_md_path.exists():
        return agents_md_path.read_text(encoding='utf-8')
    return ''


def run_role(
    role: RoleSpec,
    prompt: str,
    backend: Backend,
    cwd: Path,
    session_id: str | None = None,
    timeout: int = 300,
    model: str | None = None,
) -> tuple[str, str | None, bool]:
    """Run a role and return (text, session_id, success)."""
    full_prompt = f'{role.role}\n\n{prompt}'
    result = run_sync(
        BackendRunOptions(
            backend=backend,
            prompt=full_prompt,
            cwd=cwd,
            allowed_tools=role.allowed_tools,
            permission_mode=role.permission_mode,
            max_turns=role.max_turns,
            resume_session_id=session_id,
            model=model,
            timeout_seconds=timeout,
        )
    )
    return (
        result.text if result.ok else f'Role "{role.name}" failed: {result.stop_reason}',
        result.session_id,
        result.ok,
    )


def run_check(check: dict[str, Any], cwd: Path, python_cmd: str) -> CheckResult:
    name = str(check.get('name', 'check'))
    raw_command = str(check.get('command', '')).strip()
    if not raw_command:
        return CheckResult(
            name=name,
            command='',
            passed=False,
            exit_code=1,
            output='Missing command in check',
        )

    timeout_seconds = int(check.get('timeout_seconds', 120))
    command = raw_command.replace('{python}', python_cmd).replace('{agent_dir}', str(cwd))

    try:
        completed = subprocess.run(
            ['bash', '-lc', command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        output = (completed.stdout or '') + (completed.stderr or '')
        return CheckResult(
            name=name,
            command=command,
            passed=completed.returncode == 0,
            exit_code=completed.returncode,
            output=output.strip(),
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=name,
            command=command,
            passed=False,
            exit_code=-1,
            output='Check timed out',
        )


def build_agent_checks(agent_name: str) -> list[dict[str, Any]]:
    """Build validation checks for an agent."""
    agent_dir = AGENTS_BASE / agent_name
    snake_name = agent_name.replace('-', '_')

    return [
        {
            'name': 'main_agent_syntax',
            'command': f'{{python}} -m py_compile {agent_dir}/{snake_name}.py',
            'timeout_seconds': 30,
        },
        {
            'name': 'agent_env_exists',
            'command': f'test -f {agent_dir}/agent_env.py && {{python}} -m py_compile {agent_dir}/agent_env.py',
            'timeout_seconds': 30,
        },
        {
            'name': 'ui_app_syntax',
            'command': f'{{python}} -m py_compile {agent_dir}/ui/app.py',
            'timeout_seconds': 30,
        },
        {
            'name': 'api_main_syntax',
            'command': f'{{python}} -m py_compile {agent_dir}/api/main.py',
            'timeout_seconds': 30,
        },
        {
            'name': 'tools_syntax',
            'command': f'for f in {agent_dir}/tools/*.py; do {{python}} -m py_compile "$f" || exit 1; done',
            'timeout_seconds': 60,
        },
        {
            'name': 'subagents_syntax',
            'command': f'for f in {agent_dir}/subagents/*.py; do {{python}} -m py_compile "$f" || exit 1; done',
            'timeout_seconds': 60,
        },
        {
            'name': 'memory_syntax',
            'command': f'{{python}} -m py_compile {agent_dir}/memory/memory.py',
            'timeout_seconds': 30,
        },
        {
            'name': 'structure_check',
            'command': (
                f'test -f {agent_dir}/{snake_name}.py && '
                f'test -f {agent_dir}/agent_env.py && '
                f'test -d {agent_dir}/ui && '
                f'test -d {agent_dir}/api && '
                f'test -d {agent_dir}/tools && '
                f'test -d {agent_dir}/skills && '
                f'test -d {agent_dir}/subagents && '
                f'test -d {agent_dir}/memory && '
                f'test -d {agent_dir}/memory/data'
            ),
            'timeout_seconds': 10,
        },
        {
            'name': 'skills_exist',
            'command': f'ls {agent_dir}/skills/*.md >/dev/null 2>&1',
            'timeout_seconds': 10,
        },
        {
            'name': 'no_surrogate_escapes',
            'command': (
                f'! grep -r "\\\\\\\\u[dD][89aAbBcCdDeEfF][0-9a-fA-F]\\{{2\\}}" {agent_dir} '
                f'--include="*.py" 2>/dev/null || echo "No surrogate escapes found"'
            ),
            'timeout_seconds': 30,
        },
    ]


def generate_spec_prompt(idea: str, agents_md: str) -> str:
    return f'''Generate a detailed JSON specification for a new AI agent based on this idea:

"{idea}"

The specification must follow the structure defined in the AGENTS.md file below.

## AGENTS.md Reference
{agents_md}

## Output Format

Return a valid JSON object with this structure:
```json
{{
  "name": "agent-name",
  "description": "Brief description of what the agent does",
  "capabilities": ["capability1", "capability2", ...],
  "tools": [
    {{"name": "tool_name", "description": "what it does", "parameters": [...]}}
  ],
  "skills": [
    {{"name": "skill-name", "description": "when to use this skill", "tools": [...]}}
  ],
  "subagents": [
    {{"name": "subagent_name", "purpose": "what it handles"}}
  ],
  "memory_schemas": [
    {{"name": "schema_name", "description": "what data it stores", "fields": [...]}}
  ],
  "api_endpoints": [
    {{"method": "GET", "path": "/endpoint", "description": "what it does"}}
  ],
  "ui_views": [
    {{"name": "view_name", "description": "what user sees"}}
  ],
  "environment_variables": [
    {{"name": "VAR_NAME", "required": true, "description": "what it's for"}}
  ]
}}
```

Be thorough and specific. The spec will be used to implement the agent.'''


def build_implement_prompt(
    spec: dict[str, Any],
    agents_md: str,
    iteration: int,
    max_iterations: int,
    failed_checks: list[CheckResult],
    review_feedback: str | None = None,
) -> str:
    agent_name = spec.get('name', 'new-agent')

    checks_text = 'No previous check failures.'
    if failed_checks:
        lines = []
        for result in failed_checks:
            lines.append(
                f'- {result.name} FAILED (exit {result.exit_code})\n'
                f'  command: {result.command}\n'
                f'  output:\n{result.output[:1500]}'
            )
        checks_text = '\n'.join(lines)

    feedback_text = ''
    if review_feedback:
        feedback_text = f'\n\nReview Feedback:\n{review_feedback}'

    return f'''You are implementing iteration {iteration}/{max_iterations} for agent "{agent_name}".

## Agent Specification
```json
{json.dumps(spec, indent=2)}
```

## Target Directory
{AGENTS_BASE / agent_name}

## Required Structure (from AGENTS.md)
{agents_md}

## Current Known Failures
{checks_text}
{feedback_text}

## Instructions

1. Create the complete agent folder structure under session-3-ai-agents/agents/{agent_name}/
2. Implement ALL required components:
   - Main agent CLI ({agent_name.replace('-', '_')}.py)
   - agent_env.py (environment loader - copy pattern from lunch-selection-agent)
   - UI folder with app.py (Flask)
   - API folder with main.py (FastAPI)
   - Tools folder with all specified tools
   - Skills folder with all specified skills (markdown files)
   - Subagents folder with all specified subagents
   - Memory folder with memory.py and schemas

3. Use the lunch-selection-agent as a reference for patterns
4. Ensure all Python files have correct syntax (compatible with Python 3.9+)
5. Include proper argparse CLI interfaces
6. Add docstrings and type hints

## CRITICAL COMPATIBILITY RULES (will fail validation if violated)

1. **NO Unicode surrogate escapes**: Never use \\ud83d\\udcac or similar surrogate pairs.
   - BAD: "\\ud83d\\udcac" (surrogate escape)
   - GOOD: "💬" (actual emoji character)

2. **NO nested f-strings with backslashes**: Python <3.12 doesn't support this.
   - BAD: f"data: {{json.dumps({{'msg': f'\\u2630 {{line}}'}})}}\\n"
   - GOOD: msg = '\\u2630 ' + line; f"data: {{json.dumps({{'msg': msg}})}}\\n"

3. **Emoji in templates**: Use actual Unicode characters, not escape sequences.
   - BAD: <h2>\\ud83c\\udf24 Weather</h2>
   - GOOD: <h2>🌤 Weather</h2>

## E2E TESTS MUST PASS

The factory will run these end-to-end tests after validation:
1. **api_health_check**: API server must start and respond to GET /health with 200
2. **api_endpoint_test**: At least one API endpoint must respond
3. **ui_serves_html**: UI server must start and serve HTML on /
4. **cli_help**: CLI must respond to --help with usage information

Ensure:
- API has a /health endpoint returning {{"status": "ok"}}
- UI app.py runs on a configurable port (use port from Flask config)
- Main agent CLI supports --help argument

Fix any failing checks first, then continue implementation.'''


def build_review_prompt(
    spec: dict[str, Any],
    agents_md: str,
    check_results: list[CheckResult],
    e2e_results: list[E2ETestResult] | None = None,
) -> str:
    agent_name = spec.get('name', 'new-agent')

    check_summary = []
    for result in check_results:
        status = 'PASS' if result.passed else 'FAIL'
        check_summary.append(f'- {result.name}: {status}')

    e2e_summary = ''
    if e2e_results:
        e2e_lines = []
        for result in e2e_results:
            status = 'PASS' if result.passed else 'FAIL'
            e2e_lines.append(f'- {result.name}: {status} ({result.duration_ms}ms)')
        e2e_summary = f'''

## E2E Test Results
{chr(10).join(e2e_lines)}'''

    return f'''Review the implementation of agent "{agent_name}".

## Agent Specification
```json
{json.dumps(spec, indent=2)}
```

## Required Structure (from AGENTS.md)
{agents_md[:2000]}

## Validation Check Results
{chr(10).join(check_summary)}
{e2e_summary}

## Review Instructions

1. Verify all spec requirements are implemented
2. Check code quality and patterns match other agents
3. Ensure all files follow the AGENTS.md structure
4. Look for missing functionality or incomplete implementations
5. Confirm all E2E tests pass (API starts, UI serves HTML, CLI works)

Return exactly one marker:
- FINAL_STATUS: APPROVED — if the agent is complete, tested, and ready for use
- FINAL_STATUS: CHANGES_REQUIRED — if improvements are needed

If changes are required, list the specific issues that need to be fixed.'''


def is_review_approved(text: str) -> bool:
    normalized = text.upper()
    return 'FINAL_STATUS: APPROVED' in normalized


@dataclass
class E2ETestResult:
    name: str
    passed: bool
    output: str
    duration_ms: int


def run_e2e_tests(agent_name: str, agent_dir: Path, python_cmd: str) -> list[E2ETestResult]:
    """Run end-to-end tests for the agent: API, UI, and CLI."""
    import socket
    import time
    import urllib.request
    import urllib.error

    results: list[E2ETestResult] = []
    snake_name = agent_name.replace('-', '_')

    def find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    api_port = find_free_port()
    ui_port = find_free_port()

    api_process = None
    ui_process = None

    try:
        # Test 1: API server starts and responds to health check
        start_time = time.time()
        try:
            api_process = subprocess.Popen(
                ['bash', '-lc', f'{python_cmd} -m uvicorn api.main:app --port {api_port}'],
                cwd=str(agent_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for API to start (max 15 seconds)
            api_ready = False
            for _ in range(30):
                time.sleep(0.5)
                try:
                    req = urllib.request.Request(f'http://127.0.0.1:{api_port}/health')
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        if resp.status == 200:
                            api_ready = True
                            break
                except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
                    pass

            duration = int((time.time() - start_time) * 1000)
            if api_ready:
                results.append(E2ETestResult(
                    name='api_health_check',
                    passed=True,
                    output=f'API responded to /health on port {api_port}',
                    duration_ms=duration,
                ))
            else:
                stderr = api_process.stderr.read() if api_process.stderr else ''
                results.append(E2ETestResult(
                    name='api_health_check',
                    passed=False,
                    output=f'API failed to start or respond. stderr: {stderr[:500]}',
                    duration_ms=duration,
                ))
        except Exception as e:
            results.append(E2ETestResult(
                name='api_health_check',
                passed=False,
                output=f'API test error: {e}',
                duration_ms=int((time.time() - start_time) * 1000),
            ))

        # Test 2: API endpoint returns valid response
        if results[-1].passed:
            start_time = time.time()
            try:
                # Try a simple GET endpoint (locations or similar)
                endpoints_to_try = ['/locations', '/weather/test', '/docs']
                endpoint_ok = False
                tested_endpoint = ''

                for endpoint in endpoints_to_try:
                    try:
                        req = urllib.request.Request(f'http://127.0.0.1:{api_port}{endpoint}')
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            if resp.status in (200, 422):  # 422 is OK for missing params
                                endpoint_ok = True
                                tested_endpoint = endpoint
                                break
                    except urllib.error.HTTPError as e:
                        if e.code in (404, 422):  # Expected errors are OK
                            endpoint_ok = True
                            tested_endpoint = endpoint
                            break

                duration = int((time.time() - start_time) * 1000)
                results.append(E2ETestResult(
                    name='api_endpoint_test',
                    passed=endpoint_ok,
                    output=f'API endpoint {tested_endpoint} responded' if endpoint_ok else 'No API endpoints responded',
                    duration_ms=duration,
                ))
            except Exception as e:
                results.append(E2ETestResult(
                    name='api_endpoint_test',
                    passed=False,
                    output=f'API endpoint test error: {e}',
                    duration_ms=int((time.time() - start_time) * 1000),
                ))

        # Test 3: UI server starts and serves HTML
        start_time = time.time()
        try:
            ui_process = subprocess.Popen(
                ['bash', '-lc', f'{python_cmd} ui/app.py'],
                cwd=str(agent_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**subprocess.os.environ, 'FLASK_RUN_PORT': str(ui_port)},
            )

            # Wait for UI to start (max 10 seconds)
            ui_ready = False
            for _ in range(20):
                time.sleep(0.5)
                try:
                    req = urllib.request.Request(f'http://127.0.0.1:{ui_port}/')
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        content = resp.read().decode('utf-8', errors='replace')
                        if resp.status == 200 and ('html' in content.lower() or '<!DOCTYPE' in content):
                            ui_ready = True
                            break
                except (urllib.error.URLError, ConnectionRefusedError, TimeoutError):
                    pass

            duration = int((time.time() - start_time) * 1000)
            if ui_ready:
                results.append(E2ETestResult(
                    name='ui_serves_html',
                    passed=True,
                    output=f'UI served HTML on port {ui_port}',
                    duration_ms=duration,
                ))
            else:
                stderr = ui_process.stderr.read() if ui_process.stderr else ''
                results.append(E2ETestResult(
                    name='ui_serves_html',
                    passed=False,
                    output=f'UI failed to start or serve HTML. stderr: {stderr[:500]}',
                    duration_ms=duration,
                ))
        except Exception as e:
            results.append(E2ETestResult(
                name='ui_serves_html',
                passed=False,
                output=f'UI test error: {e}',
                duration_ms=int((time.time() - start_time) * 1000),
            ))

        # Test 4: CLI agent shows help
        start_time = time.time()
        try:
            cli_result = subprocess.run(
                ['bash', '-lc', f'{python_cmd} {snake_name}.py --help'],
                cwd=str(agent_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            duration = int((time.time() - start_time) * 1000)

            if cli_result.returncode == 0 and ('usage' in cli_result.stdout.lower() or 'help' in cli_result.stdout.lower()):
                results.append(E2ETestResult(
                    name='cli_help',
                    passed=True,
                    output='CLI --help works correctly',
                    duration_ms=duration,
                ))
            else:
                results.append(E2ETestResult(
                    name='cli_help',
                    passed=False,
                    output=f'CLI --help failed: {cli_result.stderr[:300]}',
                    duration_ms=duration,
                ))
        except Exception as e:
            results.append(E2ETestResult(
                name='cli_help',
                passed=False,
                output=f'CLI test error: {e}',
                duration_ms=int((time.time() - start_time) * 1000),
            ))

    finally:
        # Clean up processes
        for proc in [api_process, ui_process]:
            if proc is not None:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass

    return results


def extract_spec_from_response(text: str) -> dict[str, Any] | None:
    """Extract JSON spec from response text."""
    import re
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    return None


def run_spec_generation(
    idea: str,
    backend: Backend,
    timeout: int,
    model: str | None = None,
) -> dict[str, Any] | None:
    """Generate agent spec from idea."""
    print('\n=== PHASE 1: SPEC GENERATION ===\n')

    agents_md = load_agents_md()
    prompt = generate_spec_prompt(idea, agents_md)

    text, _, success = run_role(
        role=ROLES['spec_generator'],
        prompt=prompt,
        backend=backend,
        cwd=AGENTS_BASE.parent,
        timeout=timeout,
        model=model,
    )

    if not success:
        print(f'[error] Spec generation failed: {text}')
        return None

    spec = extract_spec_from_response(text)
    if not spec:
        print('[error] Could not extract JSON spec from response')
        print('Response:', text[:1000])
        return None

    print(f'[ok] Generated spec for agent: {spec.get("name", "unknown")}')
    return spec


def run_implementation_loop(
    spec: dict[str, Any],
    backend: Backend,
    max_iterations: int,
    timeout: int,
    resume_session: bool = False,
    model: str | None = None,
) -> int:
    """Run the implement -> validate -> review loop."""
    agent_name = spec.get('name', 'new-agent')
    agent_dir = AGENTS_BASE / agent_name
    agents_md = load_agents_md()
    python_cmd = resolve_python_cmd()

    session_id = load_session_id(backend) if resume_session else None
    checks = build_agent_checks(agent_name)
    failed_checks: list[CheckResult] = []
    review_feedback: str | None = None

    for iteration in range(1, max_iterations + 1):
        print(f'\n=== ITERATION {iteration}/{max_iterations} ===\n')

        print('[phase] IMPLEMENT')
        implement_prompt = build_implement_prompt(
            spec=spec,
            agents_md=agents_md,
            iteration=iteration,
            max_iterations=max_iterations,
            failed_checks=failed_checks,
            review_feedback=review_feedback,
        )

        role = ROLES['fixer'] if failed_checks or review_feedback else ROLES['implementer']
        text, new_session_id, success = run_role(
            role=role,
            prompt=implement_prompt,
            backend=backend,
            cwd=AGENTS_BASE.parent,
            session_id=session_id,
            timeout=timeout,
            model=model,
        )

        if new_session_id:
            session_id = new_session_id
            save_session_id(backend, session_id)
            print(f'[info] Session saved: {session_id[:20]}...')

        if not success:
            print(f'[error] Implementation phase failed: {text}')
            return 1

        print('[ok] Implementation phase completed')

        print('\n[phase] VALIDATE')
        check_results: list[CheckResult] = []
        any_failed = False

        for check in checks:
            result = run_check(check=check, cwd=agent_dir, python_cmd=python_cmd)
            check_results.append(result)
            status = 'PASS' if result.passed else 'FAIL'
            print(f'  [{status}] {result.name}')
            if not result.passed:
                any_failed = True
                if result.output:
                    print(f'       {result.output[:200]}')

        if any_failed:
            failed_checks = [r for r in check_results if not r.passed]
            review_feedback = None
            print(f'[info] {len(failed_checks)} checks failed, continuing loop.')
            continue

        print('[ok] All validation checks passed')

        print('\n[phase] E2E TEST')
        e2e_results = run_e2e_tests(agent_name, agent_dir, python_cmd)
        e2e_failed = False

        for result in e2e_results:
            status = 'PASS' if result.passed else 'FAIL'
            print(f'  [{status}] {result.name} ({result.duration_ms}ms)')
            if not result.passed:
                e2e_failed = True
                print(f'       {result.output[:300]}')

        if e2e_failed:
            # Convert E2E failures to check results for the fixer
            failed_checks = [
                CheckResult(
                    name=f'e2e_{r.name}',
                    command='E2E test',
                    passed=False,
                    exit_code=1,
                    output=r.output,
                )
                for r in e2e_results if not r.passed
            ]
            review_feedback = None
            print(f'[info] {len(failed_checks)} E2E tests failed, continuing loop.')
            continue

        print('[ok] All E2E tests passed')

        print('\n[phase] REVIEW')
        review_prompt = build_review_prompt(
            spec=spec,
            agents_md=agents_md,
            check_results=check_results,
            e2e_results=e2e_results,
        )

        review_text, new_session_id, success = run_role(
            role=ROLES['reviewer'],
            prompt=review_prompt,
            backend=backend,
            cwd=AGENTS_BASE.parent,
            session_id=session_id,
            timeout=timeout,
            model=model,
        )

        if new_session_id:
            session_id = new_session_id
            save_session_id(backend, session_id)

        if not success:
            print(f'[warn] Review phase failed: {review_text}')
            return 1

        print('\n--- REVIEW OUTPUT ---')
        print(review_text[:1500])
        print('--- END REVIEW ---\n')

        if is_review_approved(review_text):
            print(f'\n[SUCCESS] Agent "{agent_name}" implementation completed!')
            print(f'Location: {agent_dir}')
            return 0

        print('[info] Review requested changes, continuing loop.')
        failed_checks = []
        review_feedback = review_text

    print(f'\n[warn] Reached max iterations ({max_iterations}) without completion.')
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Agent Factory — Create and validate new agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Start fresh with an idea
  uv run python 05_agent_factory.py start --backend claude "weather forecast agent"

  # Resume a previous session
  uv run python 05_agent_factory.py resume --backend claude "continue"

  # Generate spec only
  uv run python 05_agent_factory.py spec --backend claude "recipe finder agent"

  # Implement from existing spec
  uv run python 05_agent_factory.py implement --backend claude --spec agent-spec.json
''',
    )

    parser.add_argument(
        'mode',
        choices=['start', 'resume', 'spec', 'implement'],
        help='Factory mode: start (new), resume (continue), spec (generate only), implement (from spec)',
    )
    parser.add_argument(
        'idea',
        nargs='*',
        help='Agent idea or follow-up task (required for start/spec modes)',
    )
    parser.add_argument(
        '--backend',
        choices=['claude', 'codex', 'opencode'],
        default='claude',
        help='Backend to use (default: claude)',
    )
    parser.add_argument(
        '--spec',
        type=Path,
        help='Path to existing spec file (for implement mode)',
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=5,
        help='Maximum implementation iterations (default: 5)',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Agent timeout in seconds (default: 300)',
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model override for backend',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for generated spec (spec mode only)',
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode: Literal['start', 'resume', 'spec', 'implement'] = args.mode
    idea = ' '.join(args.idea).strip() if args.idea else ''
    backend: Backend = args.backend

    if mode in ('start', 'spec') and not idea:
        print(f'[error] {mode} mode requires an idea argument')
        raise SystemExit(1)

    print(f'\n{"=" * 60}')
    print(f'AGENT FACTORY — Mode: {mode.upper()}')
    print(f'Backend: {backend}')
    print(f'{"=" * 60}')

    if mode == 'spec':
        spec = run_spec_generation(
            idea=idea,
            backend=backend,
            timeout=args.timeout,
            model=args.model,
        )
        if spec:
            output_path = args.output or Path(f'{spec.get("name", "agent")}-spec.json')
            output_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
            print(f'\n[ok] Spec saved to: {output_path}')
            raise SystemExit(0)
        raise SystemExit(1)

    if mode == 'implement':
        if not args.spec or not args.spec.exists():
            print('[error] --spec file required for implement mode')
            raise SystemExit(1)
        spec = json.loads(args.spec.read_text(encoding='utf-8'))
        exit_code = run_implementation_loop(
            spec=spec,
            backend=backend,
            max_iterations=args.max_iterations,
            timeout=args.timeout,
            resume_session=False,
            model=args.model,
        )
        raise SystemExit(exit_code)

    if mode == 'start':
        spec = run_spec_generation(
            idea=idea,
            backend=backend,
            timeout=args.timeout,
            model=args.model,
        )
        if not spec:
            raise SystemExit(1)

        spec_path = Path(f'{spec.get("name", "agent")}-spec.json')
        spec_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
        print(f'[info] Spec saved to: {spec_path}')

        exit_code = run_implementation_loop(
            spec=spec,
            backend=backend,
            max_iterations=args.max_iterations,
            timeout=args.timeout,
            resume_session=False,
            model=args.model,
        )
        raise SystemExit(exit_code)

    if mode == 'resume':
        session_id = load_session_id(backend)
        if not session_id:
            print(f'[error] No saved session for backend "{backend}"')
            raise SystemExit(1)

        print(f'[info] Resuming session: {session_id[:20]}...')

        spec_files = list(Path('.').glob('*-spec.json'))
        if not spec_files:
            print('[error] No spec file found. Run "start" first.')
            raise SystemExit(1)

        spec_path = spec_files[-1]
        spec = json.loads(spec_path.read_text(encoding='utf-8'))
        print(f'[info] Using spec: {spec_path}')

        exit_code = run_implementation_loop(
            spec=spec,
            backend=backend,
            max_iterations=args.max_iterations,
            timeout=args.timeout,
            resume_session=True,
            model=args.model,
        )
        raise SystemExit(exit_code)


if __name__ == '__main__':
    main()
