"""
Pre-game lobby: waits for the configured number of human clients, assigns each
to a team in connection order, and fires GAME_START.
"""

import asyncio
import json
import struct

import msgpack


async def wait_for_humans(host: str, port: int, scene_path: str,
                          human_teams: list[str]):
    """
    Start a TCP server and wait for `len(human_teams)` clients.

    Connection order maps to `human_teams` order: the first connection becomes
    `human_teams[0]`, the second `human_teams[1]`, and so on. Once all human
    seats are filled, GAME_START is sent to every client.

    Returns a list of (reader, writer, team) tuples in connection order.
    If `human_teams` is empty (e.g. all-AI match), returns immediately.
    """
    if not human_teams:
        return []

    players: list[tuple[asyncio.StreamReader, asyncio.StreamWriter, str]] = []
    ready = asyncio.Event()

    with open(scene_path) as f:
        scene_data = json.load(f)
    scene_json = json.dumps(scene_data).encode()

    async def _handle(reader, writer):
        idx = len(players)
        if idx >= len(human_teams):
            writer.close()
            return
        team = human_teams[idx]
        players.append((reader, writer, team))
        print(f"[lobby] Player {idx + 1}/{len(human_teams)} connected → team={team}")
        if len(players) == len(human_teams):
            ready.set()

    server = await asyncio.start_server(_handle, host, port)
    addr = server.sockets[0].getsockname()
    print(f"[lobby] Listening on {addr[0]}:{addr[1]} — "
          f"waiting for {len(human_teams)} player(s)…")

    await ready.wait()
    server.close()  # stop accepting new connections; existing ones stay open

    # Send GAME_START to every human simultaneously
    start_tasks = []
    for reader, writer, team in players:
        msg = msgpack.packb({
            "type":        "GAME_START",
            "player_team": team,
            "scene_json":  scene_json,
        }, use_bin_type=True)
        framed = struct.pack(">I", len(msg)) + msg
        writer.write(framed)
        start_tasks.append(writer.drain())
    await asyncio.gather(*start_tasks)

    print(f"[lobby] GAME_START sent to {len(players)} player(s).")
    return players
