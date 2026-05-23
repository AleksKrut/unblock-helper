"""Проверка доступности YouTube и Discord."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

DEFAULT_TARGETS = [
    ("YouTube", "https://www.youtube.com"),
    ("Discord", "https://discord.com"),
    ("Discord API", "https://discord.com/api/v10/gateway"),
]


@dataclass
class CheckResult:
    name: str
    url: str
    ok: bool
    status: int | None
    error: str | None
    elapsed_ms: float


async def _probe(
    client: httpx.AsyncClient,
    name: str,
    url: str,
) -> CheckResult:
    import time

    start = time.perf_counter()
    try:
        r = await client.get(url, follow_redirects=True)
        elapsed = (time.perf_counter() - start) * 1000
        ok = r.status_code < 500
        return CheckResult(name, url, ok, r.status_code, None, elapsed)
    except Exception as exc:  # noqa: BLE001 — показываем пользователю
        elapsed = (time.perf_counter() - start) * 1000
        return CheckResult(name, url, False, None, str(exc), elapsed)


async def run_checks(
    targets: list[tuple[str, str]] | None = None,
    timeout: float = 15.0,
) -> list[CheckResult]:
    targets = targets or DEFAULT_TARGETS
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        return list(await asyncio.gather(*[_probe(client, n, u) for n, u in targets]))


def all_ok(results: list[CheckResult]) -> bool:
    return bool(results) and all(r.ok for r in results)


def format_results(results: list[CheckResult], via: str) -> str:
    lines = [f"Проверка ({via}):", ""]
    for r in results:
        if r.ok:
            lines.append(f"  [OK]   {r.name}: HTTP {r.status} ({r.elapsed_ms:.0f} ms)")
        else:
            detail = f"HTTP {r.status}" if r.status else r.error
            lines.append(f"  [FAIL] {r.name}: {detail}")
    ok_count = sum(1 for r in results if r.ok)
    lines.append("")
    lines.append(f"Итого: {ok_count}/{len(results)} доступны")
    return "\n".join(lines)
