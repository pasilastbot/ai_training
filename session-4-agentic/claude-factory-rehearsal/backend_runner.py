from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

Backend = Literal['claude', 'codex', 'opencode']


@dataclass
class BackendRunOptions:
    backend: Backend
    prompt: str
    cwd: Path
    allowed_tools: list[str]
    permission_mode: str
    max_turns: int
    resume_session_id: str | None = None
    model: str | None = None
    timeout_seconds: int = 180


@dataclass
class BackendRunResult:
    ok: bool
    text: str
    stop_reason: str
    session_id: str | None


async def _run_claude(options: BackendRunOptions) -> BackendRunResult:
    logger.info(
        'Running claude backend (cwd=%s, model=%s, resume=%s)',
        options.cwd,
        options.model,
        options.resume_session_id,
    )
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, SystemMessage, query

    last_session_id: str | None = options.resume_session_id
    final_result: BackendRunResult | None = None
    try:
        async for message in query(
            prompt=options.prompt,
            options=ClaudeAgentOptions(
                allowed_tools=options.allowed_tools,
                permission_mode=options.permission_mode,
                max_turns=options.max_turns,
                setting_sources=['project'],
                resume=options.resume_session_id,
                model=options.model,
            ),
        ):
            if isinstance(message, SystemMessage) and getattr(message, 'subtype', None) == 'init':
                maybe_id = getattr(message, 'session_id', None)
                if maybe_id:
                    last_session_id = str(maybe_id)

            if isinstance(message, ResultMessage):
                if message.session_id:
                    last_session_id = str(message.session_id)
                if message.subtype == 'success':
                    final_result = BackendRunResult(
                        ok=True,
                        text=message.result or '',
                        stop_reason=message.subtype,
                        session_id=last_session_id,
                    )
                else:
                    final_result = BackendRunResult(
                        ok=False,
                        text='',
                        stop_reason=message.subtype,
                        session_id=last_session_id,
                    )
    except Exception as e:
        logger.error('Claude backend error: %s', e)
        if 'limit' in str(e).lower() or 'subscription' in str(e).lower():
            return BackendRunResult(
                ok=False,
                text='',
                stop_reason='claude_api_limit',
                session_id=last_session_id,
            )
        return BackendRunResult(
            ok=False,
            text='',
            stop_reason=f'claude_error: {e}',
            session_id=last_session_id,
        )

    if final_result is not None:
        return final_result

    return BackendRunResult(
        ok=False,
        text='',
        stop_reason='no_result_message',
        session_id=last_session_id,
    )


async def _run_codex(options: BackendRunOptions) -> BackendRunResult:
    logger.info(
        'Running codex backend (cwd=%s, model=%s, resume=%s)',
        options.cwd,
        options.model,
        options.resume_session_id,
    )
    cmd = ['codex', 'exec', '--json']
    if options.model:
        cmd.extend(['--model', options.model])
    if options.permission_mode == 'acceptEdits':
        cmd.append('--full-auto')
    elif options.permission_mode in ('default', 'plan'):
        cmd.extend(['-s', 'read-only'])
    if options.resume_session_id:
        cmd.extend(['resume', options.resume_session_id, options.prompt])
    else:
        cmd.append(options.prompt)

    logger.debug('Codex command prepared: %s', cmd)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(options.cwd),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=options.timeout_seconds
        )
    except asyncio.TimeoutError:
        logger.error('Codex backend timed out after %ds (cwd=%s)', options.timeout_seconds, options.cwd)
        try:
            process.kill()
        except ProcessLookupError:
            pass
        try:
            await process.wait()
        except Exception:
            pass
        return BackendRunResult(
            ok=False,
            text='',
            stop_reason=f'codex_error: timeout after {options.timeout_seconds}s',
            session_id=None,
        )
    stdout_text = stdout_bytes.decode('utf-8', errors='replace').strip()
    stderr_text = stderr_bytes.decode('utf-8', errors='replace').strip()

    if process.returncode != 0:
        details = stderr_text or stdout_text or f'codex exit code {process.returncode}'
        logger.error(
            'Codex backend failed (code=%s, details=%s)',
            process.returncode,
            details,
        )
        return BackendRunResult(
            ok=False,
            text='',
            stop_reason=f'codex_error: {details}',
            session_id=None,
        )

    session_id: str | None = None
    result_text = ''
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if data.get('type') == 'thread.started':
            maybe_id = data.get('thread_id')
            if isinstance(maybe_id, str) and maybe_id:
                session_id = maybe_id

        if data.get('type') == 'item.completed':
            item = data.get('item')
            if isinstance(item, dict) and item.get('type') == 'agent_message':
                text = item.get('text')
                if isinstance(text, str) and text.strip():
                    result_text = text

    if not result_text:
        logger.warning(
            'Codex backend returned no parsed agent message; using raw stdout'
        )
        result_text = stdout_text

    logger.info(
        'Codex backend completed (session_id=%s, text_len=%d)',
        session_id,
        len(result_text),
    )

    return BackendRunResult(
        ok=True,
        text=result_text,
        stop_reason='success',
        session_id=session_id,
    )


async def _run_opencode(options: BackendRunOptions) -> BackendRunResult:
    logger.info(
        'Running opencode backend (cwd=%s, model=%s, resume=%s)',
        options.cwd,
        options.model,
        options.resume_session_id,
    )
    cmd = ['opencode', 'run', '--format', 'json']
    if options.model:
        cmd.extend(['--model', options.model])
    if options.resume_session_id:
        cmd.extend(['--session', options.resume_session_id])
    cmd.append(options.prompt)

    logger.debug('Opencode command prepared: %s', cmd)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(options.cwd),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=options.timeout_seconds
        )
    except asyncio.TimeoutError:
        logger.error('Opencode backend timed out after %ds (cwd=%s)', options.timeout_seconds, options.cwd)
        try:
            process.kill()
        except ProcessLookupError:
            pass
        try:
            await process.wait()
        except Exception:
            pass
        return BackendRunResult(
            ok=False,
            text='',
            stop_reason=f'opencode_error: timeout after {options.timeout_seconds}s',
            session_id=None,
        )
    stdout_text = stdout_bytes.decode('utf-8', errors='replace').strip()
    stderr_text = stderr_bytes.decode('utf-8', errors='replace').strip()

    if process.returncode != 0:
        details = stderr_text or stdout_text or f'opencode exit code {process.returncode}'
        logger.error(
            'Opencode backend failed (code=%s, details=%s)',
            process.returncode,
            details,
        )
        return BackendRunResult(
            ok=False,
            text='',
            stop_reason=f'opencode_error: {details}',
            session_id=None,
        )

    session_id: str | None = None
    result_text = ''
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not session_id:
            maybe_session = data.get('sessionID') or data.get('sessionId')
            if isinstance(maybe_session, str) and maybe_session:
                session_id = maybe_session

        message = data.get('message') or data.get('text')
        if isinstance(message, str) and message.strip():
            result_text = message

        part = data.get('part')
        if isinstance(part, dict):
            part_text = part.get('text')
            if isinstance(part_text, str) and part_text.strip():
                result_text = part_text

    if not result_text:
        logger.warning(
            'Opencode backend returned no parsed message; using raw stdout'
        )
        result_text = stdout_text

    logger.info(
        'Opencode backend completed (session_id=%s, text_len=%d)',
        session_id,
        len(result_text),
    )

    return BackendRunResult(
        ok=True,
        text=result_text,
        stop_reason='success',
        session_id=session_id,
    )


async def run_backend(options: BackendRunOptions) -> BackendRunResult:
    prompt_preview = options.prompt[:500] + '...' if len(options.prompt) > 500 else options.prompt
    print(f'\n=== PROMPT TO {options.backend.upper()} ===')
    print(prompt_preview)
    print('=== END PROMPT ===\n')
    if options.backend == 'claude':
        return await _run_claude(options)
    if options.backend == 'codex':
        return await _run_codex(options)
    return await _run_opencode(options)


def get_default_cwd() -> Path:
    return Path(__file__).resolve().parents[2]


def run_sync(options: BackendRunOptions) -> BackendRunResult:
    return asyncio.run(run_backend(options))
