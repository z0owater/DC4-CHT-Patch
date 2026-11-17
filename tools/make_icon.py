"""Draws the launcher icon (a five-petal sakura) -> assets/icon.png + assets/icon.ico.

Pure standard library: the flower is computed per pixel with 4x4 supersampling.
Run:  python tools/make_icon.py
"""
import math
import os
import struct
import zlib

PETAL_TIP = (255, 228, 238)
PETAL_BASE = (240, 120, 164)
CENTER = (214, 72, 120)
STAMEN = (255, 214, 102)


def petal_hit(u, v, R):
    """u: distance along the petal axis from the flower centre, v: sideways offset."""
    if u <= 0 or u >= R:
        return False
    t = u / R
    half = R * 0.36 * math.sin(math.pi * min(1.0, t * 1.08)) ** 0.75 + R * 0.04
    if abs(v) > half:
        return False
    notch = 0.84                                   # the little V cut at the petal tip
    if t > notch and abs(v) < (t - notch) * R * 0.95:
        return False
    return True


def sample(x, y, size):
    c = size / 2
    R = size * 0.49
    dx, dy = x - c, y - c
    r = math.hypot(dx, dy)
    if r < size * 0.085:
        return STAMEN + (255,)
    if r < size * 0.15:
        return CENTER + (255,)
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        u = dx * math.cos(a) + dy * math.sin(a)
        v = -dx * math.sin(a) + dy * math.cos(a)
        if petal_hit(u, v, R):
            t = min(1.0, u / R)
            col = tuple(round(PETAL_BASE[i] + (PETAL_TIP[i] - PETAL_BASE[i]) * t ** 0.8) for i in range(3))
            # thin vein along the middle of each petal
            if abs(v) < size * 0.012 and 0.18 < t < 0.62:
                col = tuple(round(ch * 0.9) for ch in col)
            return col + (255,)
    return (0, 0, 0, 0)


def render(size, ss=4):
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            acc = [0, 0, 0, 0]
            for j in range(ss):
                for i in range(ss):
                    p = sample(x + (i + 0.5) / ss, y + (j + 0.5) / ss, size)
                    a = p[3]
                    acc[0] += p[0] * a; acc[1] += p[1] * a; acc[2] += p[2] * a; acc[3] += a
            n = ss * ss
            a = acc[3] / n
            if a:
                row += bytes((round(acc[0] / acc[3]), round(acc[1] / acc[3]), round(acc[2] / acc[3]), round(a)))
            else:
                row += b'\0\0\0\0'
        rows.append(bytes(row))
    return rows


def png(rows, size):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    raw = b''.join(b'\0' + r for r in rows)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def ico(images):
    """images: list of (size, png bytes) - PNG-compressed icon entries (Windows Vista+)."""
    head = struct.pack('<HHH', 0, 1, len(images))
    off = 6 + 16 * len(images)
    dirs, blobs = b'', b''
    for size, data in images:
        dirs += struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(data), off + len(blobs))
        blobs += data
    return head + dirs + blobs


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
    os.makedirs(out, exist_ok=True)
    images = []
    for s in (16, 24, 32, 48, 64, 128, 256):
        images.append((s, png(render(s), s)))
    with open(os.path.join(out, 'icon.ico'), 'wb') as f:
        f.write(ico(images))
    with open(os.path.join(out, 'icon.png'), 'wb') as f:
        f.write(dict(images)[256])
    print('wrote assets/icon.ico and assets/icon.png')


if __name__ == '__main__':
    main()
