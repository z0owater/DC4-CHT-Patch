"""Rules for converting D.C.4 Sweet Harmony (KAG .scn / PSB) Simplified text to Traditional, in place."""
import re, collections
from psb import PSB, S, walk

KANA = re.compile('[ぁ-ゖゝ-ゟァ-ヺヽ-ヿ]')
WS = '\n　 '

def protected(sc):
    keep = set()
    for i, c in enumerate(sc):
        if c == '栖': keep.add(i)
        elif c == '里' and i > 0 and sc[i-1] in '有琴': keep.add(i)
        elif c == '叶':
            j = i + 1
            while j < len(sc) and sc[j] in WS: j += 1
            if j < len(sc) and sc[j] == '方': keep.add(i)
    return keep

def kind(path):
    """'disp' = shown text, 'speaker' = speaker key (also used as layer name), 'arg' = plain lines argument, None = identifier."""
    n = len(path)
    if n >= 3 and path[0] == 'scenes':
        if path[2] == 'texts':
            if n == 5 and path[4] == 0: return 'speaker'
            if n == 7 and path[4] == 1 and path[6] in (0, 1): return 'disp'
        if path[2] == 'selects' and n == 5 and path[4] == 'text': return 'disp'
        if path[-1] == 'text' and n >= 4 and path[-3] == 'comumode': return 'disp'
        if path[2] == 'lines' and n == 5: return 'arg'
    return None

def plan(psb, cc):
    """-> {string index: new string} for strings safe to convert."""
    uses = collections.defaultdict(set)
    for path, v in walk(psb.root()):
        if isinstance(v, S): uses[v.i].add(kind(path))
    out = {}
    for i, ks in uses.items():
        if None in ks: continue                      # used as an identifier somewhere -> leave
        if ks <= {'arg'}: continue                   # only plain command args (Japanese labels etc.) -> leave
        s = psb.string(i)
        if KANA.search(s): continue                  # untranslated Japanese
        t = cc.convert(s)
        if len(t) != len(s): t = ''.join(cc.convert(c) for c in s)
        keep = protected(s)
        t = ''.join(s[k] if k in keep else c for k, c in enumerate(t))
        t = ''.join(a if len(a.encode()) != len(b.encode()) else b for a, b in zip(s, t))  # same UTF-8 width only
        if t != s: out[i] = t
    return out

def apply(raw, psb, changes):
    buf = bytearray(raw)
    for i, t in changes.items():
        s, e = psb.string_span(i)
        nb = t.encode('utf-8'); assert len(nb) == e - s
        buf[s:e] = nb
    return bytes(buf)
