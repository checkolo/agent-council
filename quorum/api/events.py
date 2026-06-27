from __future__ import annotations

import asyncio
from typing import Any

_subscribers: dict[str, list[asyncio.Queue]] = {}


def subscribe(run_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(run_id, []).append(q)
    return q


def unsubscribe(run_id: str, q: asyncio.Queue) -> None:
    subs = _subscribers.get(run_id, [])
    if q in subs:
        subs.remove(q)


def publish(run_id: str, event_type: str, payload: dict) -> None:
    event = {"type": event_type, "data": payload}
    for q in _subscribers.get(run_id, []):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


def make_event_callback(run_id: str):
    def callback(event_type: str, payload: dict) -> None:
        publish(run_id, event_type, payload)
    return callback


async def replay_events_from_storage(
    storage,
    run_id: str,
    after_id: int = 0,
) -> list[dict[str, Any]]:
    return storage.get_events(run_id, after_id)
