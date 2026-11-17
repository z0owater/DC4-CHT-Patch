import struct, zlib
MAGIC = b'XP3\r\n \n\x1a\x8b\x67\x01'

def read_index(d):
    assert d[:11] == MAGIC, 'not xp3'
    off = struct.unpack_from('<Q', d, 11)[0]
    if off == 0x17:                       # krkr2.3+ header with cushion
        off = struct.unpack_from('<Q', d, 0x20)[0]  # actual index offset after minor-version chunk
    flag = d[off]
    if flag & 0x07 == 1:
        csize, osize = struct.unpack_from('<QQ', d, off + 1)
        idx = zlib.decompress(d[off + 17: off + 17 + csize]); assert len(idx) == osize
    else:
        size = struct.unpack_from('<Q', d, off + 1)[0]; idx = d[off + 9: off + 9 + size]
    return off, flag, idx

def chunks(b):
    p = 0
    while p + 12 <= len(b):
        tag = b[p:p+4]; size = struct.unpack_from('<Q', b, p + 4)[0]
        yield tag, b[p+12:p+12+size]; p += 12 + size

def entries(d):
    _, _, idx = read_index(d)
    out = []
    for tag, body in chunks(idx):
        e = {'tag': tag}
        if tag == b'File':
            for t2, b2 in chunks(body):
                if t2 == b'info':
                    fl, osz, psz, nl = struct.unpack_from('<IQQH', b2, 0)
                    e.update(flags=fl, osize=osz, psize=psz, name=b2[22:22+nl*2].decode('utf-16le'))
                elif t2 == b'segm':
                    e['segs'] = [struct.unpack_from('<IQQQ', b2, i) for i in range(0, len(b2), 28)]
                elif t2 == b'adlr':
                    e['adler'] = struct.unpack_from('<I', b2, 0)[0]
                else:
                    e.setdefault('extra', []).append((t2, b2))
        else:
            e['body'] = body
        out.append(e)
    return out

def read_file(d, e):
    parts = []
    for fl, off, osz, psz in e['segs']:
        raw = d[off: off + psz]
        parts.append(zlib.decompress(raw) if fl & 7 == 1 else raw)
    return b''.join(parts)

def keystream(runs, n):
    ks = bytearray(n)
    for k, (start, val) in enumerate(runs):
        end = runs[k + 1][0] if k + 1 < len(runs) else n
        if start >= n: break
        ks[start:min(end, n)] = bytes([val]) * (min(end, n) - start)
    return bytes(ks)

def write_xp3(path, items):
    """items: list of dicts {name, flags, adler, raw_segment(bytes, already final) or data(final bytes to compress)}"""
    out = bytearray(MAGIC + b'\0' * 8)
    idx = bytearray()
    for it in items:
        if 'raw_segment' in it:
            seg, osize, sflag = it['raw_segment'], it['osize'], it['seg_flag']
        else:
            seg, osize, sflag = zlib.compress(it['data'], 9), len(it['data']), 1
        off = len(out); out += seg
        name = it['name'].encode('utf-16le')
        info = struct.pack('<IQQH', it['flags'], osize, len(seg), len(it['name'])) + name
        segm = struct.pack('<IQQQ', sflag, off, osize, len(seg))
        adlr = struct.pack('<I', it['adler'])
        body = (b'info' + struct.pack('<Q', len(info)) + info +
                b'segm' + struct.pack('<Q', len(segm)) + segm +
                b'adlr' + struct.pack('<Q', len(adlr)) + adlr)
        idx += b'File' + struct.pack('<Q', len(body)) + body
    ioff = len(out)
    out += b'\x00' + struct.pack('<Q', len(idx)) + idx
    struct.pack_into('<Q', out, 11, ioff)
    with open(path, 'wb') as f: f.write(out)
