import argparse
from dataclasses import dataclass

from backend_runner import BackendRunOptions, get_default_cwd, run_sync


@dataclass
class FactorySpec:
    name: str
    prompt_template: str
    allowed_tools: list[str]
    max_turns: int = 20
    permission_mode: str = 'acceptEdits'


class Factory:
    def __init__(self, spec: FactorySpec, backend: str) -> None:
        self.spec = spec
        self.backend = backend

    def run(self, task: str) -> str:
        prompt = self.spec.prompt_template.format(task=task)
        result = run_sync(
            BackendRunOptions(
                backend=self.backend,  # type: ignore[arg-type]
                prompt=prompt,
                cwd=get_default_cwd(),
                allowed_tools=self.spec.allowed_tools,
                max_turns=self.spec.max_turns,
                permission_mode=self.spec.permission_mode,
            )
        )
        if result.ok:
            return result.text
        return f'Factory stopped: {result.stop_reason}'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('task', nargs='*')
    parser.add_argument('--backend', choices=['claude', 'codex', 'opencode'], default='claude')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task = ' '.join(args.task).strip() or 'List the top 3 improvement ideas for this repository.'

    factory = Factory(
        FactorySpec(
            name='minimal-factory',
            prompt_template='You are a simple software factory. Complete this task: {task}',
            allowed_tools=['Read', 'Glob', 'Grep', 'Edit', 'Bash'],
            max_turns=15,
        ),
        backend=args.backend,
    )

    result = factory.run(task)
    print('\n=== FACTORY RESULT ===\n')
    print(result)


if __name__ == '__main__':
    main()
