"""Shared helpers: console output, files, Windows fonts, FontHook.ini editing, sharp window."""
import hashlib
import os
import sys

DEFAULT_SIZE = 28          # text size in pixels (both games)
SIZE_MIN, SIZE_MAX = 16, 31


_sink = None      # the launcher sets this to receive progress lines instead of the console


def set_output(fn):
    global _sink
    _sink = fn


def say(*a):
    if _sink is not None:
        _sink(' '.join(str(x) for x in a))
    else:
        print(*a, flush=True)


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def wr(p, b):
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b)


def font_dirs():
    yield os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
    la = os.environ.get('LOCALAPPDATA')
    if la:
        yield os.path.join(la, 'Microsoft', 'Windows', 'Fonts')


def find_font(*names):
    for n in names:
        for d in font_dirs():
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


# ---------------------------------------------------------------- FontHook.ini
def _key(line):
    return line.split('=', 1)[0].strip() if '=' in line else None


def ini_read(p):
    """-> (has_utf8_bom, non-empty lines). Missing file -> (False, [])."""
    if not os.path.exists(p):
        return False, []
    raw = rd(p)
    text = raw.decode('utf-8-sig', 'replace').replace('\r\n', '\n')
    return raw.startswith(b'\xef\xbb\xbf'), [ln for ln in text.split('\n') if ln.strip()]


def ini_get(lines, key):
    for ln in lines:
        if _key(ln) == key:
            return ln.split('=', 1)[1].strip()
    return None


def ini_set(lines, head=(), tail=()):
    """Put (key, value) pairs inside [FontHook]: `head` right after the section header,
    `tail` at the end of the section. Any older copies of those keys are removed."""
    keys = {k for k, _ in head} | {k for k, _ in tail}
    out = [ln for ln in lines if _key(ln) not in keys]
    stripped = [ln.strip() for ln in out]
    if '[FontHook]' not in stripped:
        out.insert(0, '[FontHook]')
        stripped.insert(0, '[FontHook]')
    start = stripped.index('[FontHook]')
    out[start + 1:start + 1] = ['%s=%s' % kv for kv in head]
    end = start + 1
    while end < len(out) and not out[end].strip().startswith('['):
        end += 1
    out[end:end] = ['%s=%s' % kv for kv in tail]
    return out


def ini_write(p, lines, bom):
    wr(p, (b'\xef\xbb\xbf' if bom else b'') + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))


def ini_update(p, head=(), tail=()):
    """Edit one FontHook.ini in place, keeping its encoding (UTF-8, with or without BOM)."""
    bom, lines = ini_read(p)
    ini_write(p, ini_set(lines, head, tail), bom)


# ---------------------------------------------------------------- sharp window (optional)
# Same per-user flag Windows writes for Properties > Compatibility > Change high DPI settings >
# "Override high DPI scaling behavior: Application". Only affects that exact exe path.
LAYERS_KEY = r'Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
DPI_FLAGS = {'HIGHDPIAWARE', 'DPIUNAWARE', 'GDIDPISCALING'}


def display_scale():
    try:
        import ctypes
        u, g = ctypes.windll.user32, ctypes.windll.gdi32
        try:
            u.SetProcessDPIAware()
        except Exception:
            pass
        hdc = u.GetDC(0)
        dpi = g.GetDeviceCaps(hdc, 88)
        u.ReleaseDC(0, hdc)
        return round(dpi * 100 / 96) if dpi else None
    except Exception:
        return None


def merge_flags(old):
    toks = (old or '').split()
    if toks and toks[0] == '~':
        toks.pop(0)
    toks = [t for t in toks if t.upper() not in DPI_FLAGS] + ['HIGHDPIAWARE']
    return '~ ' + ' '.join(toks)


def sharp_window_is_on(exe_path):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, LAYERS_KEY) as k:
            return 'HIGHDPIAWARE' in winreg.QueryValueEx(k, exe_path)[0].upper().split()
    except Exception:
        return False


def set_sharp_window(exe_path):
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, LAYERS_KEY, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as k:
        try:
            old = winreg.QueryValueEx(k, exe_path)[0]
        except FileNotFoundError:
            old = ''
        new = merge_flags(old)
        winreg.SetValueEx(k, exe_path, 0, winreg.REG_SZ, new)
    return old, new


def clear_sharp_window(exe_path):
    """Undo set_sharp_window (keeps any other compatibility flags the user set)."""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, LAYERS_KEY, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as k:
            old = winreg.QueryValueEx(k, exe_path)[0]
            toks = [t for t in old.split() if t != '~' and t.upper() != 'HIGHDPIAWARE']
            if toks:
                winreg.SetValueEx(k, exe_path, 0, winreg.REG_SZ, '~ ' + ' '.join(toks))
            else:
                winreg.DeleteValue(k, exe_path)
    except FileNotFoundError:
        pass


def ask(prompt, default=''):
    """input() that never crashes when there is no console input (returns the default)."""
    if '--yes' in sys.argv:
        return default
    try:
        return input(prompt).strip() or default
    except EOFError:
        return default
