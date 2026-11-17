"""Minimal PSB (emote) reader for KAG .scn files: tree with string *indexes* so text can be patched in place."""
import struct

class S:   # string reference
    __slots__ = ('i',)
    def __init__(self, i): self.i = i
    def __repr__(self): return 'S(%d)' % self.i

def _uint(b, p, n): return int.from_bytes(b[p:p+n], 'little'), p + n

def read_array(b, p):
    t = b[p]; p += 1
    assert 0x0D <= t <= 0x14, ('bad array type', hex(t), p)
    cnt, p = _uint(b, p, t - 0x0C)
    es = b[p] - 0x0C; p += 1
    vals = [int.from_bytes(b[p+i*es:p+(i+1)*es], 'little') for i in range(cnt)]
    return vals, p + cnt * es

class PSB:
    def __init__(self, b):
        assert b[:4] == b'PSB\x00', 'not PSB'
        self.b = b
        self.ver, self.enc = struct.unpack_from('<HH', b, 4)
        (self.hdr_len, self.o_names, self.o_strings, self.o_strdata, self.o_chunk_off,
         self.o_chunk_len, self.o_chunk_data, self.o_root) = struct.unpack_from('<8I', b, 8)
        charset, p = read_array(b, self.o_names)
        ndata, p = read_array(b, p)
        nidx, p = read_array(b, p)
        self.names = []
        for a in nidx:
            bb = ndata[a]; out = []
            while bb != 0:
                c = ndata[bb]; d = charset[c]; out.append(chr(bb - d)); bb = c
            self.names.append(''.join(reversed(out)))
        self.str_offsets, _ = read_array(b, self.o_strings)

    def string_span(self, i):
        s = self.o_strdata + self.str_offsets[i]
        e = self.b.index(b'\x00', s)
        return s, e

    def string(self, i):
        s, e = self.string_span(i); return self.b[s:e].decode('utf-8')

    def value(self, p):
        b = self.b; t = b[p]
        if t == 0x01: return None
        if t == 0x02: return False
        if t == 0x03: return True
        if t == 0x04: return 0
        if 0x05 <= t <= 0x0C:
            n = t - 0x04; return int.from_bytes(b[p+1:p+1+n], 'little', signed=True)
        if 0x0D <= t <= 0x14: return read_array(b, p)[0]
        if 0x15 <= t <= 0x18: return S(int.from_bytes(b[p+1:p+1+(t-0x14)], 'little'))
        if 0x19 <= t <= 0x1C: return ('res', int.from_bytes(b[p+1:p+1+(t-0x18)], 'little'))
        if t == 0x1D: return 0.0
        if t == 0x1E: return struct.unpack_from('<f', b, p+1)[0]
        if t == 0x1F: return struct.unpack_from('<d', b, p+1)[0]
        if t == 0x20:
            offs, q = read_array(b, p + 1)
            return [self.value(q + o) for o in offs]
        if t == 0x21:
            keys, q = read_array(b, p + 1)
            offs, q = read_array(b, q)
            return {self.names[k]: self.value(q + o) for k, o in zip(keys, offs)}
        if 0x22 <= t <= 0x25: return ('xres', int.from_bytes(b[p+1:p+1+(t-0x21)], 'little'))
        raise ValueError('unknown type %02X at %X' % (t, p))

    def root(self): return self.value(self.o_root)

def walk(v, path=()):
    if isinstance(v, dict):
        for k, x in v.items(): yield from walk(x, path + (k,))
    elif isinstance(v, list):
        for i, x in enumerate(v): yield from walk(x, path + (i,))
    else:
        yield path, v
