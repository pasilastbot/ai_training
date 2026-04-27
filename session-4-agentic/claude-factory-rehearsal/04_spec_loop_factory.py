from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend_runner import Backend, BackendRunOptions, get_default_cwd, run_sync


@dataclass
class CheckResult:
    name: str
    command: str
    passed: bool
    exit_code: int
    output: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Spec-driven loop: implement -> test -> review until done'
    )
    parser.add_argument('--spec', required=True, help='Path to JSON spec file')
    parser.add_argument(
        '--backend', choices=['claude', 'codex', 'opencode'], default='claude'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=None,
        help='Override spec max_iterations',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=180,
        help='Agent timeout in seconds (default: 180)',
    )
    return parser.parse_args()


def load_spec(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'goal' not in data:
        raise SystemExit('Spec must include "goal".')
    if 'checks' not in data or not isinstance(data['checks'], list) or not data['checks']:
        raise SystemExit('Spec must include non-empty "checks" list.')
    return data


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


def run_check(check: dict[str, Any], cwd: Path, python_cmd: str) -> CheckResult:
    name = str(check.get('name', 'check'))
    raw_command = str(check.get('command', '')).strip()
    if not raw_command:
        return CheckResult(
            name=name,
            command='',
            passed=False,
            exit_code=1,
            output='Missing command in spec check',
        )

    timeout_seconds = int(check.get('timeout_seconds', 300))
    command = raw_command.replace('{python}', python_cmd)
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


def build_implement_prompt(
    spec: dict[str, Any],
    iteration: int,
    max_iterations: int,
    failed_checks: list[CheckResult],
) -> str:
    checks_text = 'No previous check failures.'
    if failed_checks:
        lines = []
        for result in failed_checks:
            lines.append(
                f'- {result.name} failed (exit {result.exit_code})\n'
                f'  command: {result.command}\n'
                f'  output:\n{result.output[:2000]}'
            )
        checks_text = '\n'.join(lines)

    instructions = spec.get(
        'implement_instructions',
        (
            'Implement the requested changes, then stop. '
            'Do not claim success unless checks can pass.'
        ),
    )
    return (
        f"You are a software factory in iteration {iteration}/{max_iterations}.\n\n"
        f"Goal:\n{spec['goal']}\n\n"
        f"Implementation instructions:\n{instructions}\n\n"
        f"Current known failures:\n{checks_text}\n"
    )


def build_review_prompt(spec: dict[str, Any], check_results: list[CheckResult]) -> str:
    lines = []
    for result in check_results:
        status = 'PASS' if result.passed else 'FAIL'
        lines.append(f'- {result.name}: {status}')

    review_instructions = spec.get(
        'review_instructions',
        (
            'Review whether this task is complete based on goal and checks. '
            'Return exactly one marker: FINAL_STATUS: APPROVED or FINAL_STATUS: CHANGES_REQUIRED.'
        ),
    )
    return (
        f"Goal:\n{spec['goal']}\n\n"
        f"Check summary:\n{chr(10).join(lines)}\n\n"
        f"{review_instructions}"
    )


def is_review_approved(text: str) -> bool:
    normalized = text.upper()
    return 'FINAL_STATUS: APPROVED' in normalized


def run_loop(spec: dict[str, Any], backend: Backend, max_iterations: int, spec_dir: Path, timeout: int) -> int:
    cwd = spec_dir
    python_cmd = resolve_python_cmd()
    allowed_tools = list(
        spec.get('allowed_tools', ['Read', 'Glob', 'Grep', 'Edit', 'Bash'])
    )
    permission_mode = str(spec.get('permission_mode', 'acceptEdits'))
    agent_max_turns = int(spec.get('agent_max_turns', 20))
    model = spec.get('model')
    agent_timeout = int(spec.get('agent_timeout_seconds', timeout))
    session_id: str | None = None

    failed_checks: list[CheckResult] = []
    for iteration in range(1, max_iterations + 1):
        print(f'\n=== LOOP ITERATION {iteration}/{max_iterations} ===')

        implement_prompt = build_implement_prompt(
            spec=spec,
            iteration=iteration,
            max_iterations=max_iterations,
            failed_checks=failed_checks,
        )
        implement_result = run_sync(
            BackendRunOptions(
                backend=backend,
                prompt=implement_prompt,
                cwd=cwd,
                allowed_tools=allowed_tools,
                permission_mode=permission_mode,
                max_turns=agent_max_turns,
                resume_session_id=session_id,
                model=model,
                timeout_seconds=agent_timeout,
            )
        )
        if not implement_result.ok:
            print(f'[error] Implement phase failed: {implement_result.stop_reason}')
            return 1
        session_id = implement_result.session_id or session_id
        print('[ok] Implement phase completed')

        check_results: list[CheckResult] = []
        any_failed = False
        for check in spec['checks']:
            result = run_check(check=check, cwd=cwd, python_cmd=python_cmd)
            check_results.append(result)
            status = 'PASS' if result.passed else 'FAIL'
            print(f'[{status}] {result.name} :: {result.command}')
            if not result.passed:
                any_failed = True
                print(result.output[:600])

        if any_failed:
            failed_checks = [r for r in check_results if not r.passed]
            print('[info] Checks failed, continuing loop.')
            continue

        review_prompt = build_review_prompt(spec=spec, check_results=check_results)
        review_result = run_sync(
            BackendRunOptions(
                backend=backend,
                prompt=review_prompt,
                cwd=cwd,
                allowed_tools=['Read', 'Glob', 'Grep'],
                permission_mode='default',
                max_turns=max(10, agent_max_turns // 2),
                resume_session_id=session_id,
                model=model,
                timeout_seconds=agent_timeout,
            )
        )
        if not review_result.ok:
            print(f'[warn] Review phase failed: {review_result.stop_reason}')
            return 1

        review_text = review_result.text or ''
        print('\n--- REVIEW OUTPUT ---\n')
        print(review_text[:1200])
        if is_review_approved(review_text):
            print('\n[ok] Factory loop completed successfully.')
            return 0

        print('[info] Review requested changes, continuing loop.')
        failed_checks = []

    print('\n[warn] Reached max iterations without completion.')
    return 1


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    spec = load_spec(spec_path)
    max_iterations = (
        args.max_iterations
        if args.max_iterations is not None
        else int(spec.get('max_iterations', 5))
    )
    exit_code = run_loop(
        spec=spec,
        backend=args.backend,
        max_iterations=max_iterations,
        spec_dir=spec_path.parent,
        timeout=args.timeout,
    )
    raise SystemExit(exit_code)


if __name__ == '__main__':
    main()
