"""Install the Simplified Chinese patch by acies from the file the player downloaded.

Nothing of the patch is shipped here. The player downloads it from acies's page and
picks it: the .zip itself, the extracted folder, or any file inside that folder.
inspect() finds the patch inside it and tells which game it is for; install() copies
it into the game folder, exactly as the patch's own instructions say (copy everything
over the game folder).
"""
import ctypes
import os
import shutil
import zipfile

from common import say, rd, wr

PAGES = {'ph': 'https://2dfan.com/downloads/47006', 'sh': 'https://2dfan.com/downloads/47045'}
KIND_OF_EXE = {'DC4PHDL.exe': 'ph', 'DC4_SH.exe': 'sh'}
GAME_NAME = {'ph': 'D.C.4 Plus Harmony', 'sh': 'D.C.4 Sweet Harmony'}
GAME_EXES = ('dc4phdl.exe', 'dc4_sh.exe')
ARCHIVES = ('.7z', '.rar', '.001')


class NotAPatch(RuntimeError):
    pass


class NeedsExtract(RuntimeError):
    pass


def _kind(rel):
    """rel: lower-case posix paths relative to a candidate patch root."""
    if 'winmm.dll' not in rel or 'fonthook.ini' not in rel:
        return None
    if any(n in rel for n in GAME_EXES):
        return None                       # that's a game folder, not a patch
    if '_work/carrier_map.json' in rel and any(n.startswith('advdata/mes/') and n.endswith('.mes') for n in rel):
        return 'ph'
    if 'patch.xp3' in rel:
        return 'sh'
    return None


def _find_root(names):
    """names: posix paths. -> (root prefix ending in '/' or '', kind) or (None, None)."""
    roots = sorted({n[:-len('winmm.dll')] for n in names if n.lower().endswith('winmm.dll')
                    and (len(n) == 9 or n[-10] == '/')}, key=len)
    for r in roots:
        rel = {n[len(r):].lower() for n in names if n.startswith(r)}
        k = _kind(rel)
        if k:
            return r, k
    return None, None


def _zip_name(info):
    """Chinese zips often store GBK names without the UTF-8 flag; Python reads those as cp437."""
    n = info.filename
    if not info.flag_bits & 0x800:
        try:
            n = n.encode('cp437').decode('gbk')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return n.replace('\\', '/')


def _folder_names(folder, limit=20000):
    out = []
    for dp, dns, fns in os.walk(folder):
        depth = os.path.relpath(dp, folder).count(os.sep)
        if depth >= 4:
            dns[:] = []
        for f in fns:
            out.append(os.path.relpath(os.path.join(dp, f), folder).replace(os.sep, '/'))
            if len(out) > limit:
                return out
    return out


def inspect(path, climb=True):
    """-> dict(path, kind, root, zip) for the patch found in `path`; raises NotAPatch / NeedsExtract.
    climb=True also tries up to two parent folders (the player picked a file deep inside)."""
    path = os.path.abspath(path)
    if os.path.isfile(path) and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names = [_zip_name(i) for i in z.infolist() if not i.is_dir()]
        root, kind = _find_root(names)
        if kind:
            return dict(path=path, kind=kind, root=root, zip=True)
        raise NotAPatch(path)
    if os.path.isfile(path) and path.lower().endswith(ARCHIVES):
        raise NeedsExtract(path)
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    for _ in range(3 if climb else 1):    # the folder itself, then up to two levels up
        root, kind = _find_root(_folder_names(folder))
        if kind:
            return dict(path=folder, kind=kind, root=root, zip=False)
        if any(os.path.isfile(os.path.join(folder, e)) for e in ('DC4PHDL.exe', 'DC4_SH.exe')):
            break                         # reached a game folder - don't search above it
        parent = os.path.dirname(folder)
        if parent == folder:
            break
        folder = parent
    raise NotAPatch(path)


def _safe(rel):
    rel = rel.replace('\\', '/')
    parts = [p for p in rel.split('/') if p not in ('', '.')]
    if not parts or '..' in parts or ':' in parts[0]:
        return None
    return os.path.join(*parts)


def install(src, store):
    """Copy the patch found by inspect() into the current folder (the game folder)."""
    say('[0/5] Installing the Simplified Chinese patch by acies from %s' % os.path.basename(src['path']))
    if src['kind'] == 'sh':
        for n in ('GameFont.otf', 'GameFont.ttf'):        # keep only the patch's own font
            if os.path.exists(n):
                os.remove(n)
    root, n = src['root'], 0
    if src['zip']:
        with zipfile.ZipFile(src['path']) as z:
            for info in z.infolist():
                name = _zip_name(info)
                if info.is_dir() or not name.startswith(root):
                    continue
                rel = _safe(name[len(root):])
                if rel:
                    wr(rel, z.read(info))
                    n += 1
    else:
        base = os.path.join(src['path'], *[p for p in root.split('/') if p])
        for rel in _folder_names(base, limit=10 ** 6):
            dst = _safe(rel)
            if dst:
                wr(dst, rd(os.path.join(base, rel)))
                n += 1
    say('      %d files copied' % n)
    # A freshly installed Simplified patch replaces the backup made from an older one.
    scb = os.path.join(store, 'SC_backup')
    if os.path.isdir(scb):
        prev = scb + '.prev'
        shutil.rmtree(prev, ignore_errors=True)
        os.rename(scb, prev)
        say('      previous Simplified backup kept as %s' % prev)


def downloads_dir():
    try:
        from ctypes import wintypes
        guid = (ctypes.c_ubyte * 16)(*bytes.fromhex('904fa6374ec53e4c9b5d3d29148edd64'))   # FOLDERID_Downloads
        p = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(p)) == 0:
            d = p.value
            ctypes.windll.ole32.CoTaskMemFree(p)
            if d and os.path.isdir(d):
                return d
    except Exception:
        pass
    d = os.path.join(os.path.expanduser('~'), 'Downloads')
    return d if os.path.isdir(d) else None


def find_in_downloads(kind):
    """Newest download in Downloads (or one folder below) that holds the acies patch for `kind`."""
    base = downloads_dir()
    if not base:
        return None
    cands = []
    for e in os.scandir(base):
        try:
            if e.is_file() and e.name.lower().endswith('.zip') and e.stat().st_size < 3 * 2 ** 30:
                cands.append(e.path)
            elif e.is_dir():
                cands.append(e.path)
                for c in os.scandir(e.path):
                    if c.is_dir() or (c.is_file() and c.name.lower().endswith('.zip')):
                        cands.append(c.path)
        except OSError:
            continue
    cands.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)

    def patch_dirs(p):
        """p itself or its sub-folders that hold winmm.dll and are not a game folder."""
        out = []
        for d in [p] + [os.path.join(p, c) for c in os.listdir(p)]:
            if (os.path.isdir(d) and os.path.isfile(os.path.join(d, 'winmm.dll'))
                    and not any(os.path.isfile(os.path.join(d, e)) for e in ('DC4PHDL.exe', 'DC4_SH.exe'))):
                out.append(d)
        return out

    seen = set()
    for p in cands:
        try:
            targets = patch_dirs(p) if os.path.isdir(p) else [p]
            for t in targets:
                if t in seen:
                    continue
                seen.add(t)
                src = inspect(t, climb=False)
                if src['kind'] == kind:
                    return src
        except (RuntimeError, OSError, zipfile.BadZipFile):
            continue
    return None
