"""Game font for D.C.4 Sweet Harmony CHT (KiriKiri, GDI glyph rendering).

build_font_sh(src_ttc, fallback_ttc, ref_font, used_chars, out_path, family, scale)

- base: Microsoft JhengHei Bold (TW glyph forms)
- glyphs can be scaled by `scale` inside unchanged advance widths. DC4-CHT-Patch uses 1.0
  (natural size) and sets the text size with FontHook instead, which scales the advance
  widths too, so the gaps between letters stay correct
- vertical metrics / codepage / weight copied from the patch's own font (ref_font) so the
  engine places text exactly where it did before
- chars missing from the base (♪ ◯ ...) copied from the fallback font
- …… and —— made full-width so they join up; symbols that are full-width in ref_font but
  narrow in the base are centred in a full cell
- hinting dropped (it no longer matches the scaled outlines); grayscale smoothing at all sizes
"""
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen


def build_font_sh(src, fallback, ref_path, used, out, family='DC4TC', scale=1.05, log=print):
    f = TTFont(src, fontNumber=0)
    ref = TTFont(ref_path, lazy=True)
    EM = f['head'].unitsPerEm
    rk = EM / ref['head'].unitsPerEm
    ro, rh = ref['OS/2'], ref['hhea']
    TYPO_A, TYPO_D = round(ro.sTypoAscender * rk), round(ro.sTypoDescender * rk)
    MID = (TYPO_A + TYPO_D) / 2                   # centre of the ideographic em box
    glyf, hmtx = f['glyf'], f['hmtx']
    vmtx = f['vmtx'] if 'vmtx' in f else None
    cmap = f.getBestCmap()
    order = f.getGlyphOrder()

    # ---- 1. drop hinting, scale every outline about (advance/2, MID)
    empty = ttProgram.Program(); empty.fromBytecode(b'')
    for t in ('fpgm', 'prep', 'cvt ', 'hdmx', 'LTSH', 'VDMX', 'MERG', 'DSIG', 'kern'):
        if t in f: del f[t]
    s = scale
    composites = []
    for gname in order:
        g = glyf[gname]
        if g.isComposite():
            composites.append(gname); continue
        if g.numberOfContours > 0:
            cx = hmtx[gname][0] / 2
            coords = g.coordinates
            for i in range(len(coords)):
                x, y = coords[i]
                coords[i] = (round(cx + (x - cx) * s), round(MID + (y - MID) * s))
            g.program = empty
            g.recalcBounds(glyf)
    for gname in composites:
        g = glyf[gname]
        cx = hmtx[gname][0] / 2
        for c in g.components:
            cc = hmtx[c.glyphName][0] / 2
            c.x = round(c.x * s + (1 - s) * (cx - cc))
            c.y = round(c.y * s)
        if hasattr(g, 'program'): g.program = empty
    for gname in order:
        g = glyf[gname]
        if g.numberOfContours != 0 or g.isComposite():
            g.recalcBounds(glyf)
            hmtx.metrics[gname] = (hmtx[gname][0], getattr(g, 'xMin', 0))
    gasp = newTable('gasp'); gasp.version = 1; gasp.gaspRange = {0xFFFF: 0x000A}; f['gasp'] = gasp

    def add(name, g, adv):
        g.recalcBounds(glyf)
        order.append(name); glyf.glyphs[name] = g
        if hasattr(glyf, 'glyphOrder'): glyf.glyphOrder = order
        hmtx.metrics[name] = (adv, getattr(g, 'xMin', 0) if g.numberOfContours else 0)
        if vmtx is not None:
            top = getattr(g, 'yMax', TYPO_A) if g.numberOfContours else TYPO_A
            vmtx.metrics[name] = (EM, max(0, TYPO_A - top))
        return name

    def outline(gs, gname, dx=0, dy=0, sc=1.0, about=None):
        rec = DecomposingRecordingPen(gs); gs[gname].draw(rec)
        pen = TTGlyphPen(None)
        if about:   # scale about a point, then shift
            ax, ay = about
            m = (sc, 0, 0, sc, ax - ax * sc + dx, ay - ay * sc + dy)
        else:
            m = (sc, 0, 0, sc, dx, dy)
        rec.replay(TransformPen(pen, m))
        return pen.glyph()

    gs = f.getGlyphSet()
    override = {}

    # ---- 2. full-width dash (one bar across the cell)
    d = glyf[cmap[0x2014]]; d.recalcBounds(glyf); th = d.yMax - d.yMin
    pen = TTGlyphPen(None); y0, y1 = round(MID - th / 2), round(MID + th / 2)
    pen.moveTo((0, y0)); pen.lineTo((0, y1)); pen.lineTo((EM, y1)); pen.lineTo((EM, y0)); pen.closePath()
    override[0x2014] = override[0x2015] = add('dc4.dash.fw', pen.glyph(), EM)

    # ---- 3. full-width ellipsis: 3 dots spread over the cell, vertically centred
    e = glyf[cmap[0x2026]]; e.recalcBounds(glyf)
    coords, ends, _ = e.getCoordinates(glyf)
    starts = [0] + [x + 1 for x in ends[:-1]]
    n = len(ends)
    # copy the glyph and move each contour (dot) to its slot
    g2 = Glyph_copy(e)
    c2 = g2.coordinates
    for k, (a, b) in enumerate(zip(starts, ends)):
        xs = [coords[i][0] for i in range(a, b + 1)]
        dx = EM * (2 * k + 1) / (2 * n) - (min(xs) + max(xs)) / 2
        dy = MID - (e.yMin + e.yMax) / 2
        for i in range(a, b + 1):
            c2[i] = (round(coords[i][0] + dx), round(coords[i][1] + dy))
    override[0x2026] = add('dc4.ellipsis.fw', g2, EM)

    # ---- 4. chars the base lacks -> from fallback font, scaled to EM and by `scale`, centred
    fb = TTFont(fallback, fontNumber=0); fcm = fb.getBestCmap(); fgs = fb.getGlyphSet()
    fk = EM / fb['head'].unitsPerEm
    for ch in used:
        cp = ord(ch)
        if cp < 0x20 or cp in cmap or cp in override or cp not in fcm: continue
        adv = fb['hmtx'][fcm[cp]][0] * fk
        full = adv > EM * 0.6
        g = outline_xform(fgs, fcm[cp], fk, s, adv / 2, MID, (EM - adv) / 2 if full else 0)
        override[cp] = add('dc4.fb.%04X' % cp, g, EM if full else round(adv))
        log('   added %s from fallback font' % ch)

    # ---- 5. symbols full-width in the reference font but narrow here -> centred copy
    rcm = ref.getBestCmap(); rhm = ref['hmtx']
    for ch in used:
        cp = ord(ch)
        if cp < 0x80 or cp in override or cp not in cmap or cp not in rcm: continue
        if 0x3400 <= cp <= 0x9FFF: continue
        if rhm[rcm[cp]][0] == ref['head'].unitsPerEm and hmtx[cmap[cp]][0] != EM:
            adv = hmtx[cmap[cp]][0]
            override[cp] = add('dc4.fw.%04X' % cp, outline(gs, cmap[cp], dx=round((EM - adv) / 2)), EM)

    for t in f['cmap'].tables:
        if t.isUnicode():
            for cp, gname in override.items():
                if cp <= 0xFFFF or t.format in (12, 13): t.cmap[cp] = gname

    f.setGlyphOrder(order); f['maxp'].numGlyphs = len(order)
    if hasattr(f['post'], 'extraNames'): f['post'].formatType = 3.0

    # ---- 6. metrics / flags copied from the reference font
    hh, os2 = f['hhea'], f['OS/2']
    hh.ascent, hh.descent, hh.lineGap = round(rh.ascent * rk), round(rh.descent * rk), 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = TYPO_A, TYPO_D, 0
    os2.usWinAscent, os2.usWinDescent = round(ro.usWinAscent * rk), round(ro.usWinDescent * rk)
    os2.ulCodePageRange1 |= ro.ulCodePageRange1
    os2.ulCodePageRange2 |= ro.ulCodePageRange2
    os2.usWeightClass = ro.usWeightClass
    bold = bool(ro.fsSelection & (1 << 5))
    os2.fsSelection = (os2.fsSelection & ~((1 << 5) | (1 << 6) | 1)) | ((1 << 5) if bold else (1 << 6))
    f['head'].macStyle = (f['head'].macStyle & ~0b11) | (1 if bold else 0)
    os2.fsType = 0
    style = 'Bold' if bold else 'Regular'
    name = f['name']
    name.names = [x for x in name.names if x.nameID not in (1, 2, 3, 4, 6, 16, 17, 18, 21, 22)]
    for nid, val in ((1, family), (2, style), (3, family + ' ' + style + ';DC4SH-CHT'),
                     (4, family + ' ' + style), (6, family + '-' + style)):
        name.setName(val, nid, 3, 1, 0x409)
    f['head'].fontRevision = 1.0
    f.save(out)
    return len(override)


def Glyph_copy(g):
    import copy
    return copy.deepcopy(g)


def outline_xform(gs, gname, k, s, cx, my, shift_x):
    """draw gname scaled by k (unit conversion), then by s about (cx, my), then shift x."""
    rec = DecomposingRecordingPen(gs); gs[gname].draw(rec)
    pen = TTGlyphPen(None)
    a = k * s
    m = (a, 0, 0, a, cx - cx * s + shift_x, my - my * s)
    rec.replay(TransformPen(pen, m))
    return pen.glyph()
