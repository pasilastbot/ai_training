import argparse
from pathlib import Path

from backend_runner import BackendRunOptions, get_default_cwd, run_sync


def session_file_for(backend: str) -> Path:
    return Path(f'.factory-session-id-{backend}')


def load_session_id(backend: str) -> str | None:
    session_file = session_file_for(backend)
    if not session_file.exists():
        return None
    text = session_file.read_text(encoding='utf-8').strip()
    return text or None


def save_session_id(backend: str, session_id: str) -> None:
    session_file_for(backend).write_text(session_id, encoding='utf-8')


def run(task: str, resume: bool, backend: str) -> None:
    resume_id = load_session_id(backend) if resume else None

    result = run_sync(
        BackendRunOptions(
            backend=backend,  # type: ignore[arg-type]
            prompt=f'You are a resumable software factory.\n\nTask:\n{task}',
            cwd=get_default_cwd(),
            allowed_tools=['Read', 'Glob', 'Grep', 'Edit', 'Bash'],
            permission_mode='acceptEdits',
            max_turns=20,
            resume_session_id=resume_id,
        )
    )

    if result.session_id:
        save_session_id(backend, result.session_id)
        print(f'[info] session saved ({backend}): {result.session_id}')

    print('\n=== RESULT ===\n')
    if result.ok:
        print(result.text)
    else:
        print(f'Factory stopped: {result.stop_reason}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['start', 'resume'])
    parser.add_argument('task', nargs='+')
    parser.add_argument('--backend', choices=['claude', 'codex', 'opencode'], default='claude')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode = args.mode.strip().lower()
    if mode not in {'start', 'resume'}:
        raise SystemExit('First argument must be "start" or "resume".')
    task = ' '.join(args.task).strip()
    run(task, resume=mode == 'resume', backend=args.backend)


if __name__ == '__main__':
    main()
