"""Building index entries from SKILL.md bytes, and the stored copies of skills."""
from __future__ import annotations

import shutil
import zipfile
import zlib
from pathlib import Path
from typing import Tuple, Union

from sklcli.errors import NoInterfaceError, SklError
from sklcli.models import Entry, Source
from sklcli.parsing.interface import parse_interface
from sklcli.parsing.skillmd import extract_block, frontmatter_name
from sklcli.store.paths import MAX_SKILL_BYTES, NAME_RE, skill_folder


def entry_from_bytes(data: bytes, fallback_name: str, source: Source,
                     source_path: Union[str, Path]) -> Entry:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise SklError("not valid UTF-8")
    block = extract_block(text)
    if block is None:
        raise NoInterfaceError("no command interface block")
    interface = parse_interface(block)
    name = frontmatter_name(text)
    if not name:
        usage = (interface or {}).get("usage_line") or ""
        first = usage.split()[0].lstrip("/") if usage.split() else ""
        name = first or fallback_name
    if not NAME_RE.fullmatch(name or ""):
        raise SklError("unsafe skill name '%s'" % name)
    return Entry(name=name, source=source.value, source_path=str(source_path),
                 usage_block=block, interface=interface)


def make_entry(skill_md_path: Union[str, Path], source: Source) -> Entry:
    path = Path(skill_md_path)
    try:
        data = path.read_bytes()
    except OSError as e:
        raise SklError("cannot read: %s" % (e.strerror or e))
    return entry_from_bytes(data, path.parent.name, source, path)


def write_store(name: str, data: bytes) -> None:
    folder = skill_folder(name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_bytes(data)


def drop_store(name: str) -> None:
    shutil.rmtree(str(skill_folder(name)), ignore_errors=True)


def read_skill_source(p: Path) -> Tuple[bytes, str]:
    """Return (bytes, fallback_name) for a SKILL.md, a folder, or a zip."""
    if p.is_dir():
        f = p / "SKILL.md"
        if not f.is_file():
            raise SklError("no SKILL.md in %s" % p)
        return f.read_bytes(), p.resolve().name
    if not p.exists():
        raise SklError("no such file: %s" % p)
    if p.suffix.lower() in (".skill", ".zip"):
        return _read_zip(p)
    return p.read_bytes(), p.resolve().parent.name


def _read_zip(p: Path) -> Tuple[bytes, str]:
    try:
        zf = zipfile.ZipFile(str(p))
    except zipfile.BadZipFile:
        raise SklError("not a valid zip file: %s" % p)
    with zf:
        try:
            names = zf.namelist()
            member = None
            if "SKILL.md" in names:
                member = "SKILL.md"
            else:
                for n in names:
                    parts = n.split("/")
                    if len(parts) == 2 and parts[1] == "SKILL.md" and parts[0] not in ("", ".", ".."):
                        member = n
                        break
            if member is None:
                raise SklError("no SKILL.md in %s" % p)
            if zf.getinfo(member).file_size > MAX_SKILL_BYTES:
                raise SklError("SKILL.md in %s is too large" % p)
            fallback = member.split("/")[0] if "/" in member else p.stem
            return zf.read(member), fallback
        except (zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError, EOFError) as e:
            raise SklError("cannot read %s: %s" % (p, e))
