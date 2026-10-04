#!/usr/bin/env python3
"""Minimal PFH5 .pack reader/writer for Total War: WARHAMMER III.

Read side: enough to list and extract entries from the retail packs.
Write side: builds a simple Mod/Movie pack with uncompressed entries.

PFH5 header (28 bytes):
    0x00  magic   b"PFH5"
    0x04  u32     type-and-flags (low nibble: 0=boot 1=release 2=patch 3=mod 4=movie)
    0x08  u32     dependency pack count
    0x0C  u32     dependency index size (bytes)
    0x10  u32     file count
    0x14  u32     file index size (bytes)
    0x18  u32     timestamp
File index entry: u32 size, [u32 timestamp if flag 0x40], u8 is_compressed,
NUL-terminated path (backslash separators). Data follows, concatenated in
index order.
"""
from __future__ import annotations

import struct
import sys
from dataclasses import dataclass

FLAG_EXTENDED_HEADER = 0x100
FLAG_INDEX_TIMESTAMPS = 0x40
FLAG_ENCRYPTED_INDEX = 0x80

TYPE_MOD = 3
TYPE_MOVIE = 4


@dataclass
class Entry:
    path: str  # backslash-separated internal path, as stored
    size: int
    offset: int  # absolute offset of the data in the pack file
    is_compressed: int


class PackFile:
    def __init__(self, path: str):
        self.path = path
        self.entries: dict[str, Entry] = {}
        self._parse()

    def _parse(self) -> None:
        with open(self.path, "rb") as f:
            head = f.read(28)
            if head[:4] != b"PFH5":
                raise ValueError(f"{self.path}: not PFH5 (got {head[:4]!r})")
            tf, dep_count, dep_size, file_count, index_size, _ts = struct.unpack(
                "<6I", head[4:28]
            )
            self.type_flags = tf
            if tf & FLAG_ENCRYPTED_INDEX:
                raise ValueError(f"{self.path}: encrypted index unsupported")
            has_entry_ts = bool(tf & FLAG_INDEX_TIMESTAMPS)
            f.seek(dep_size, 1)  # skip dependency list
            index = f.read(index_size)
            data_start = 28 + dep_size + index_size

            pos = 0
            offset = data_start
            for _ in range(file_count):
                (size,) = struct.unpack_from("<I", index, pos)
                pos += 4
                if has_entry_ts:
                    pos += 4
                is_compressed = index[pos]
                pos += 1
                end = index.index(b"\x00", pos)
                path = index[pos:end].decode("latin-1")
                pos = end + 1
                self.entries[path] = Entry(path, size, offset, is_compressed)
                offset += size
            self._data_end = offset

    def sanity_check(self) -> None:
        import os

        actual = os.path.getsize(self.path)
        if self._data_end != actual:
            raise ValueError(
                f"{self.path}: parsed data end {self._data_end} != file size {actual}"
            )

    def read(self, path: str) -> bytes:
        e = self.entries[path]
        if e.is_compressed:
            raise ValueError(f"{path}: compressed entries not supported here")
        with open(self.path, "rb") as f:
            f.seek(e.offset)
            return f.read(e.size)


def write_pack(out_path: str, files: dict[str, bytes], pack_type: int = TYPE_MOD) -> None:
    """files: {internal_path_with_backslashes: data}. Entries stored uncompressed."""
    index = bytearray()
    blobs = []
    for path in sorted(files):
        data = files[path]
        index += struct.pack("<I", len(data))
        index += b"\x00"  # is_compressed = 0
        index += path.encode("latin-1") + b"\x00"
        blobs.append(data)
    header = b"PFH5" + struct.pack(
        "<6I", pack_type, 0, 0, len(files), len(index), 0
    )
    with open(out_path, "wb") as f:
        f.write(header)
        f.write(index)
        for b in blobs:
            f.write(b)


if __name__ == "__main__":
    cmd = sys.argv[1]
    pack = PackFile(sys.argv[2])
    pack.sanity_check()
    if cmd == "list":
        pat = sys.argv[3].lower() if len(sys.argv) > 3 else None
        n = 0
        for p, e in pack.entries.items():
            if pat is None or pat in p.lower():
                print(f"{e.size:>12}  c={e.is_compressed}  {p}")
                n += 1
        print(f"-- {n} entries (of {len(pack.entries)}) "
              f"type_flags=0x{pack.type_flags:x}", file=sys.stderr)
    elif cmd == "cat":
        sys.stdout.buffer.write(pack.read(sys.argv[3]))
