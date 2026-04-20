import argparse
from dataclasses import dataclass

from backend_runner import BackendRunOptions, get_default_cwd, run_sync


@dataclass
class FactorySpec:
    name: str
    role: str
    allowed_tools: list[str]
    max_turns: int = 20
    permission_mode: str = 'acceptEdits'


FACTORIES: dict[str, FactorySpec] = {
    'analyzer': FactorySpec(
        name='analyzer',
        role='You are an analysis factory. Only inspect and explain. Do not change files.',
        allowed_tools=['Read', 'Glob', 'Grep', 'WebSearch', 'WebFetch'],
        permission_mode='default',
        max_turns=12,
    ),
    'fixer': FactorySpec(
        name='fixer',
        role='You are a bug-fix factory. Make minimal safe edits and validate.',
        allowed_tools=['Read', 'Glob', 'Grep', 'Edit', 'Bash'],
        permission_mode='acceptEdits',
        max_turns=20,
    ),
    'planner': FactorySpec(
        name='planner',
        role='You are a planning factory. Produce actionable implementation plans only.',
        allowed_tools=['Read', 'Glob', 'Grep'],
        permission_mode='plan',
        max_turns=10,
    ),
}


def run_factory(spec: FactorySpec, task: str, backend: str) -> str:
    prompt = f'{spec.role}\n\nTask:\n{task}'
    result = run_sync(
        BackendRunOptions(
            backend=backend,  # type: ignore[arg-type]
            prompt=prompt,
            cwd=get_default_cwd(),
            allowed_tools=spec.allowed_tools,
            permission_mode=spec.permission_mode,
            max_turns=spec.max_turns,
        )
    )
    if result.ok:
        return result.text
    return f'Factory "{spec.name}" stopped: {result.stop_reason}'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('factory')
    parser.add_argument('task', nargs='+')
    parser.add_argument('--backend', choices=['claude', 'codex', 'opencode'], default='claude')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    factory_name = args.factory.strip().lower()
    task = ' '.join(args.task).strip()
    if factory_name not in FACTORIES:
        available = ', '.join(sorted(FACTORIES))
        raise SystemExit(f'Unknown factory "{factory_name}". Available factories: {available}')

    result = run_factory(FACTORIES[factory_name], task, backend=args.backend)
    print(f'\n=== FACTORY: {factory_name} ===\n')
    print(result)


if __name__ == '__main__':
    main()
