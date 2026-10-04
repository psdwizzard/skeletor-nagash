#!/usr/bin/env python3
"""Find all .wem IDs owned by a VO actor in TWW3 Wwise soundbanks (bank v136).

Walks every .bnk inside audio_en_bnk.pack, parses HIRC, finds Dialogue_Event
(type 15) decision trees, collects the leaves reached through a node keyed with
the actor's FNV-1 hash, then resolves leaf audio nodes through containers down
to Sound objects (type 2), whose sourceID is the .wem filename.

Container child discovery is heuristic: we look for a [u32 N][N x u32 id]
children-list pattern where every id is a known HIRC object, and only recurse
into sound/container types — never busses, actions, events, or music objects.
Run with --diag to cross-check two actors for contamination overlap.
"""
from __future__ import annotations

import json
import struct
import sys
from collections import defaultdict

sys.path.insert(0, __import__("os").path.dirname(__file__))
from packfile import PackFile  # noqa: E402

SOUND = 2
CONTAINER_TYPES = {5, 6, 7, 9}  # RanSeq, Switch, ActorMixer, Layer
FOLLOW_TYPES = CONTAINER_TYPES | {SOUND}
DIALOGUE_EVENT = 15


def fnv1_32(s: str) -> int:
    h = 2166136261
    for b in s.lower().encode():
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= b
    return h


def parse_bank(data: bytes):
    """Yield (hirc_type, obj_id, payload) for every HIRC item. payload excludes id."""
    pos = 0
    while pos + 8 <= len(data):
        tag = data[pos:pos + 4]
        (size,) = struct.unpack_from("<I", data, pos + 4)
        body = data[pos + 8:pos + 8 + size]
        if tag == b"HIRC":
            (count,) = struct.unpack_from("<I", body, 0)
            p = 4
            for _ in range(count):
                htype = body[p]
                (hsize,) = struct.unpack_from("<I", body, p + 1)
                (oid,) = struct.unpack_from("<I", body, p + 5)
                payload = body[p + 9:p + 5 + hsize]
                yield htype, oid, payload
                p += 5 + hsize
        pos += 8 + size


def dialogue_event_leaves(payload: bytes, actor_hash: int):
    """Return audioNodeIds of all leaves under any tree node keyed actor_hash."""
    p = 0
    p += 1  # uProbability
    (depth,) = struct.unpack_from("<I", payload, p)
    p += 4
    p += depth * 4  # argument group ids
    p += depth * 1  # argument group types
    (tree_size,) = struct.unpack_from("<I", payload, p)
    p += 4
    p += 1  # uMode
    tree = payload[p:p + tree_size]
    n_nodes = tree_size // 12

    def node(i):
        key, val, _w, _pr = struct.unpack_from("<IIHH", tree, i * 12)
        return key, val

    leaves = []

    def walk(i, d, under_actor):
        key, val = node(i)
        hit = under_actor or key == actor_hash
        if d >= 1 and _is_leaf(val, d):
            if hit and val:
                leaves.append(val)
            return
        idx, count = val & 0xFFFF, val >> 16
        for c in range(idx, min(idx + count, n_nodes)):
            walk(c, d + 1, hit)

    def _is_leaf(val, d):
        if d >= tree_depth:
            return True
        idx, count = val & 0xFFFF, val >> 16
        return not (0 < count <= n_nodes and 0 < idx < n_nodes and idx + count <= n_nodes)

    tree_depth = depth
    if n_nodes:
        # root node children (depth 0 node is the argument-0 dispatcher)
        key, val = node(0)
        if _is_leaf(val, 0):
            if key == actor_hash and val:
                leaves.append(val)
        else:
            idx, count = val & 0xFFFF, val >> 16
            for c in range(idx, min(idx + count, n_nodes)):
                walk(c, 1, key == actor_hash)
    return leaves


def children_lists(payload: bytes, known_ids):
    """Heuristic: find [u32 N][N x u32] runs where all N ids are known objects."""
    found = set()
    for off in range(0, max(0, len(payload) - 8)):
        (n,) = struct.unpack_from("<I", payload, off)
        if not (0 < n <= 4096) or off + 4 + 4 * n > len(payload):
            continue
        ids = struct.unpack_from(f"<{n}I", payload, off + 4)
        if all(i in known_ids for i in ids):
            found.update(ids)
    return found


def resolve_to_wems(start_id, objects, visited=None):
    """Follow containers down to Sound objects; return their sourceIDs."""
    if visited is None:
        visited = set()
    if start_id in visited or start_id not in objects:
        return set()
    visited.add(start_id)
    htype, payload = objects[start_id]
    if htype == SOUND:
        # after id: u32 pluginID, u8 streamType, u32 sourceID
        (source_id,) = struct.unpack_from("<I", payload, 5)
        return {source_id}
    wems = set()
    if htype in CONTAINER_TYPES:
        for child in children_lists(payload, objects.keys()):
            if objects.get(child, (None,))[0] in FOLLOW_TYPES:
                wems |= resolve_to_wems(child, objects, visited)
    return wems


def collect_actor(bnk_pack_path: str, actor_key: str):
    actor_hash = fnv1_32(actor_key)
    pack = PackFile(bnk_pack_path)
    # pass 1: global object map across every bank (leaves can reference
    # objects living in a different bank, e.g. the split-hash banks)
    objects = {}
    bank_events = {}  # bank path -> [(event_id, payload)]
    for path in pack.entries:
        if not path.endswith(".bnk"):
            continue
        devents = []
        for htype, oid, payload in parse_bank(pack.read(path)):
            objects[oid] = (htype, payload)
            if htype == DIALOGUE_EVENT:
                devents.append((oid, payload))
        if devents:
            bank_events[path] = devents

    # pass 2: walk dialogue events, resolve leaves against the global map
    results = []
    unresolved = []
    for path, devents in bank_events.items():
        bank_wems = {}
        for oid, payload in devents:
            leaves = dialogue_event_leaves(payload, actor_hash)
            if not leaves:
                continue
            wems = set()
            for leaf in set(leaves):
                got = resolve_to_wems(leaf, objects)
                if not got:
                    unresolved.append((path.split("\\")[-1], oid, leaf))
                wems |= got
            if wems:
                bank_wems[oid] = sorted(wems)
        if bank_wems:
            results.append({
                "bank": path.split("\\")[-1],
                "events": {str(k): v for k, v in bank_wems.items()},
            })
    return actor_hash, results, unresolved


def main():
    bnk_pack = sys.argv[1]
    actor_key = sys.argv[2]
    actor_hash, results, unresolved = collect_actor(bnk_pack, actor_key)
    all_wems = sorted({w for r in results for v in r["events"].values() for w in v})
    out = {
        "actor_key": actor_key,
        "actor_hash": actor_hash,
        "banks": results,
        "wem_ids": all_wems,
    }
    json.dump(out, sys.stdout, indent=1)
    per_bank = {r["bank"]: sum(len(v) for v in r["events"].values()) for r in results}
    print(f"\nactor_hash={actor_hash}  banks={len(results)}  "
          f"unique_wems={len(all_wems)}  per-bank wem refs: {per_bank}",
          file=sys.stderr)
    if unresolved:
        print(f"UNRESOLVED leaves ({len(unresolved)}): {unresolved[:10]}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
