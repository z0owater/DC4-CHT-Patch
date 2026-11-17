"""D.C.4 Plus Harmony - text rendering fix for DC4PHDL.exe.

Original work: DC4PH_TextFix by hyther1111 (https://github.com/hyther1111), included
here unchanged apart from this header.

The Circus engine draws half-width characters on a fixed half-em grid, so
proportional Latin letters (e.g. "MyTuber") overlapped or were cramped, and the
glyph surface was too short for descenders (y/g/p/q/j). patch_exe_bytes() adds a
small code section that measures every half-width glyph with GetGlyphOutline,
enlarges the glyph surface, and reads the text size from FontHook.ini
([FontHook] EngineFontSize, 16-31) when the game starts. It also applies the
Shift-JIS GetACP fix (garbled text on non-Japanese Windows) if still needed.

Standard library only.
"""
import re
import struct

DEFAULT_FONT_SIZE = 28


def _u16(b, off):
    return struct.unpack_from('<H', b, off)[0]


def _u32(b, off):
    return struct.unpack_from('<I', b, off)[0]


def _cstr_at(b, off):
    end = b.index(0, off)
    return b[off:end].decode('ascii', 'ignore')


def parse_pe(data):
    """Minimal 32-bit PE parser using only the standard library."""
    if len(data) < 0x100 or data[:2] != b'MZ':
        raise RuntimeError('Not a valid Windows executable (missing MZ header).')
    nt_off = _u32(data, 0x3C)
    if nt_off + 24 > len(data) or data[nt_off:nt_off + 4] != b'PE\x00\x00':
        raise RuntimeError('Not a valid PE executable.')
    magic = _u16(data, nt_off + 24)
    if magic != 0x010B:
        raise RuntimeError('Unsupported PE format (expected 32-bit PE32).')

    num_sec = _u16(data, nt_off + 6)
    opt_sz = _u16(data, nt_off + 20)
    opt_off = nt_off + 24
    base = _u32(data, opt_off + 28)
    sec_align = _u32(data, opt_off + 32)
    file_align = _u32(data, opt_off + 36)
    size_of_headers = _u32(data, opt_off + 60)
    imp_rva = _u32(data, opt_off + 96 + 8)

    sec_tbl = opt_off + opt_sz
    sections = []
    for idx in range(num_sec):
        so = sec_tbl + idx * 40
        sections.append({
            'name': data[so:so + 8].rstrip(b'\x00'),
            'vsize': _u32(data, so + 8),
            'va': _u32(data, so + 12),
            'rsize': _u32(data, so + 16),
            'raw': _u32(data, so + 20),
            'chars': _u32(data, so + 36),
        })

    def rva_to_off(rva):
        for s in sections:
            span = max(s['vsize'], s['rsize'])
            if s['va'] <= rva < s['va'] + span:
                return s['raw'] + (rva - s['va'])
        raise RuntimeError('RVA 0x%X outside sections.' % rva)

    iat = {}
    if imp_rva:
        desc_off = rva_to_off(imp_rva)
        while desc_off + 20 <= len(data):
            ilt_rva = _u32(data, desc_off)
            name_rva = _u32(data, desc_off + 12)
            iat_rva = _u32(data, desc_off + 16)
            if ilt_rva == 0 and name_rva == 0 and iat_rva == 0:
                break
            thunk_rva = ilt_rva or iat_rva
            t_off = rva_to_off(thunk_rva)
            k = 0
            while t_off + k * 4 + 4 <= len(data):
                val = _u32(data, t_off + k * 4)
                if val == 0:
                    break
                if (val & 0x80000000) == 0:
                    fn = _cstr_at(data, rva_to_off(val) + 2)
                    iat[fn] = base + iat_rva + k * 4
                k += 1
            desc_off += 20

    return {
        'nt_off': nt_off,
        'opt_sz': opt_sz,
        'base': base,
        'sec_align': sec_align,
        'file_align': file_align,
        'size_of_headers': size_of_headers,
        'sections': sections,
        'rva_to_off': rva_to_off,
        'iat': iat,
    }


def _compile_sig(pat):
    parts = []
    for tok in pat.split():
        if tok == '??':
            parts.append(b'.')
        elif tok == '(':
            parts.append(b'(')
        elif tok == ')':
            parts.append(b')')
        else:
            parts.append(re.escape(bytes.fromhex(tok)))
    return re.compile(b''.join(parts), re.DOTALL)


def _find_sites(pe, data):
    """Locate all text-renderer hook and constant sites dynamically via byte patterns."""
    PATS = {
        'h_init_m': '57 ( c7 44 24 14 ?? 00 00 00 ) 89 44 24 18 89 44 24 1c 89 44 24 20',
        'h_init_w': '89 83 18 01 00 00 ( c7 44 24 54 ?? 00 00 00 c7 44 24 58 ?? 00 00 00 ) ff d5',
        'h_58_A':   '2b c2 01 45 7c ( 8b 45 5c 68 ?? ?? ?? ?? ) 56 89 45 58 e8 ?? ?? ?? ??',
        'h_p1fw_A': '( 01 7d 54 83 c3 02 e9 ?? ?? 00 00 ) 80 3b 40 0f 85',
        'h_p1hw_A': '( 83 7c 24 34 00 74 0a 8b c7 99 2b c2 d1 f8 01 45 54 8b c7 99 2b c2 d1 f8 01 45 54 43 ) 80 3b 00',
        'p_surf_A': '8b 45 58 8b 55 54 6a 01 51 ( 83 c0 ?? ) 56 50 a1 ?? ?? ?? ?? 8b 88 fc 00 00 00 83 c2 04',
        'h_p2fw_A': '8a 08 40 84 c9 75 f9 ( 8b 44 24 1c 89 44 24 60 e9 ?? ?? 00 00 ) 8a 06',
        'h_p2hw_A': '( 8b 4c 24 1c 0f be f8 ) 8b c1 99 46 2b c2 81 e7 ff 00 00 00',
        'h_p2s0_A': '89 44 24 4c 85 c0 75 0d ( 8b 54 24 40 01 54 24 24 e9 ?? ?? 00 00 )',
        'h_p2va_A': 'ff 15 ?? ?? ?? ?? ( 8b 44 24 6c 83 c0 03 ) 25 fc ff 00 00 83 7c 24 70 00',
        'p_y1_A':   '2b 44 24 78 2b 44 24 60 03 44 24 44 ( 8d 74 10 ?? ) 8b 44 24 58',
        'p_y2_A':   '03 f3 03 74 24 74 ( 8d 4c 11 ?? ) 03 f0 03 74 24 24',
        'h_58_W':   '2b c2 d1 f8 8d 14 00 ( 8b 45 5c 01 55 7c ) 68 ?? ?? ?? ?? 56 89 45 58',
        'h_p1_W':   '( 83 7c 24 2c 00 74 05 03 c3 89 45 54 01 5d 54 83 c7 02 ) 66 83 3f 00',
        'p_surf_W': '8b 55 54 6a 01 51 ( 83 c0 ?? ) 56 50 a1 ?? ?? ?? ?? 8b 88 fc 00 00 00 83 c2 02',
        'h_p2_W':   'e9 ?? ?? 00 00 0f b7 f0 ( 8b 44 24 1c 89 44 24 50 89 44 24 7c ) 33 c0 33 c9',
        'h_p2s0_W': '89 44 24 4c 85 c0 75 0d ( 8b 54 24 50 01 54 24 24 e9 ?? ?? 00 00 )',
        'h_p2vw_W': 'ff 15 ?? ?? ?? ?? ( 8b 44 24 68 83 c0 03 ) 25 fc ff 00 00 83 7c 24 6c 00',
        'p_y1_W':   '2b 44 24 74 2b 44 24 7c 03 44 24 34 ( 8d 74 10 ?? ) 8b 44 24 5c',
        'p_y2_W':   '03 4c 24 34 ( 8d 4c 11 ?? ) 99 83 e2 03 03 c2 0f bf 54 24 78',
    }
    base = pe['base']
    code_secs = [s for s in pe['sections'] if (s['chars'] & 0x20000000) or s['name'] == b'.text']
    sites = {}
    for name, pat in PATS.items():
        rx = _compile_sig(pat)
        hits = []
        for s in code_secs:
            chunk = bytes(data[s['raw']:s['raw'] + s['rsize']])
            for m in rx.finditer(chunk):
                va = base + s['va'] + m.start(1)
                cap = m.group(1)
                hits.append((va, cap))
        if len(hits) != 1:
            raise RuntimeError(
                'Incompatible DC4PHDL.exe (pattern "%s" matched %d times; expected 1).' % (name, len(hits))
            )
        sites[name] = hits[0]
    return sites


def patch_exe_bytes(src_bytes, default_font_size=DEFAULT_FONT_SIZE):
    """Apply Shift-JIS GetACP patch (if needed) and text-rendering .patch code cave."""
    pe = parse_pe(src_bytes)
    data = bytearray(src_bytes)

    # Ensure GetACP returns 932 (idempotent if already patched by CHT installer)
    acp_n = 0
    if 'GetACP' in pe['iat']:
        pat = b'\xff\x15' + struct.pack('<I', pe['iat']['GetACP'])
        for s in pe['sections']:
            lo, hi = s['raw'], s['raw'] + s['rsize']
            i = lo
            while True:
                i = data.find(pat, i, hi)
                if i < 0:
                    break
                data[i:i + 6] = b'\xb8\xa4\x03\x00\x00\x90'
                acp_n += 1
                i += 6

    if any(s['name'] == b'.patch' for s in pe['sections']):
        return bytes(data), acp_n, False

    sites = _find_sites(pe, data)
    va_of = lambda k: sites[k][0]
    cap_of = lambda k: sites[k][1]
    jmp_dst = lambda k, off: (va_of(k) + off + 5) + struct.unpack_from('<i', cap_of(k), off + 1)[0]

    TAG_M = 0x16
    SURF_PAD = 0x0E
    Y_OFF = 0x07
    FONT_PATCHES = (
        (va_of('p_surf_A') + 2, 1, SURF_PAD),
        (va_of('p_y1_A') + 3, 1, Y_OFF),
        (va_of('p_y2_A') + 3, 1, Y_OFF),
        (va_of('p_surf_W') + 2, 1, SURF_PAD),
        (va_of('p_y1_W') + 3, 1, Y_OFF),
        (va_of('p_y2_W') + 3, 1, Y_OFF),
    )

    base = pe['base']
    iat = pe['iat']
    rva_to_off = lambda va: pe['rva_to_off'](va - base)

    for req in ('CreateCompatibleDC', 'SelectObject', 'GetGlyphOutlineA', 'GetGlyphOutlineW',
                'GetModuleHandleA', 'GetProcAddress', 'GetModuleFileNameA'):
        if req not in iat:
            raise RuntimeError('Required WinAPI import "%s" not found in DC4PHDL.exe.' % req)

    sec_align = pe['sec_align']
    file_align = pe['file_align']
    last = pe['sections'][-1]
    patch_rva = ((last['va'] + last['vsize']) + sec_align - 1) & ~(sec_align - 1)
    patch_raw = (len(data) + file_align - 1) & ~(file_align - 1)
    patch_va = base + patch_rva

    buf = bytearray()
    labels = {}
    fixups = []
    def label(name): labels[name] = patch_va + len(buf)
    def emit(b): buf.extend(b)
    def cstr(s):
        va = patch_va + len(buf)
        buf.extend(s.encode('ascii') + b'\x00')
        return va
    def u32(v): return struct.pack('<I', v)
    def i32(v): return struct.pack('<i', v)
    def rel(op, target):
        emit(op)
        fixups.append((len(buf), target))
        emit(b'\x00\x00\x00\x00')

    g_hdc_va = patch_va
    emit(u32(0))
    g_font_size_va = patch_va + len(buf)
    emit(u32(default_font_size))
    g_mat2_va = patch_va + len(buf)
    emit(struct.pack('<HHHHHHHH', 0, 1, 0, 0, 0, 0, 0, 1))
    s_k32 = cstr('kernel32.dll')
    s_gppi = cstr('GetPrivateProfileIntA')
    s_sec = cstr('FontHook')
    s_key = cstr('EngineFontSize')
    s_ini = cstr('FontHook.ini')

    label('init_font_size')
    emit(b'\x50\x51\x52\x53\x56\x57')
    emit(b'\x81\xec\x10\x01\x00\x00')
    emit(b'\x89\xe3')
    emit(b'\x68\x04\x01\x00\x00\x53\x6a\x00')
    emit(b'\xff\x15' + u32(iat['GetModuleFileNameA']))
    emit(b'\x85\xc0')
    rel(b'\x0f\x84', 'ifs_done')
    emit(b'\x8d\x3c\x03')
    label('ifs_scan')
    emit(b'\x4f\x39\xdf')
    rel(b'\x0f\x82', 'ifs_noslash')
    emit(b'\x8a\x0f\x80\xf9\x5c')
    rel(b'\x0f\x84', 'ifs_slash')
    emit(b'\x80\xf9\x2f')
    rel(b'\x0f\x85', 'ifs_scan')
    label('ifs_slash')
    emit(b'\x47')
    rel(b'\xe9', 'ifs_copy')
    label('ifs_noslash')
    emit(b'\x89\xdf')
    label('ifs_copy')
    emit(b'\xbe' + u32(s_ini))
    emit(b'\xb9\x0d\x00\x00\x00\xf3\xa4')
    emit(b'\x68' + u32(s_k32))
    emit(b'\xff\x15' + u32(iat['GetModuleHandleA']))
    emit(b'\x85\xc0')
    rel(b'\x0f\x84', 'ifs_done')
    emit(b'\x68' + u32(s_gppi))
    emit(b'\x50')
    emit(b'\xff\x15' + u32(iat['GetProcAddress']))
    emit(b'\x85\xc0')
    rel(b'\x0f\x84', 'ifs_done')
    emit(b'\x53')
    emit(b'\x6a' + bytes([default_font_size]))
    emit(b'\x68' + u32(s_key))
    emit(b'\x68' + u32(s_sec))
    emit(b'\xff\xd0')
    emit(b'\x83\xf8\x10\x7d\x05\xb8\x10\x00\x00\x00')
    emit(b'\x83\xf8\x1f\x7e\x05\xb8\x1f\x00\x00\x00')
    emit(b'\xa3' + u32(g_font_size_va))
    label('ifs_done')
    emit(b'\x81\xc4\x10\x01\x00\x00')
    emit(b'\x5f\x5e\x5b\x5a\x59\x58')
    emit(b'\x51')
    emit(b'\x8b\x0d' + u32(g_font_size_va))
    emit(b'\x89\x4c\x24\x18')
    emit(b'\x59')
    rel(b'\xe9', va_of('h_init_m') + len(cap_of('h_init_m')))

    label('init_w_font')
    emit(b'\xa1' + u32(g_font_size_va))
    emit(b'\x89\x44\x24\x54')
    emit(b'\x01\xc0')
    emit(b'\x89\x44\x24\x58')
    rel(b'\xe9', va_of('h_init_w') + len(cap_of('h_init_w')))

    label('init_58_A')
    emit(b'\x8b\x45\x5c\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(cap_of('h_58_A')[3:8])
    rel(b'\xe9', va_of('h_58_A') + len(cap_of('h_58_A')))

    label('init_58_W')
    emit(b'\x8b\x45\x5c\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(b'\x01\x55\x7c')
    rel(b'\xe9', va_of('h_58_W') + len(cap_of('h_58_W')))

    label('pass1_fw_A')
    emit(b'\x89\xf8\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(b'\x01\x45\x54\x83\xc3\x02')
    rel(b'\xe9', jmp_dst('h_p1fw_A', 6))

    label('p2_fw_A')
    emit(b'\x8b\x44\x24\x1c\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(b'\x89\x44\x24\x60')
    rel(b'\xe9', jmp_dst('h_p2fw_A', 8))

    label('p2_hw_A')
    emit(b'\x0f\xbe\xf8')
    emit(b'\x8b\x4c\x24\x1c\x83\xf9' + bytes([TAG_M]))
    emit(b'\x75\x06\x8b\x0d' + u32(g_font_size_va))
    rel(b'\xe9', va_of('h_p2hw_A') + len(cap_of('h_p2hw_A')))

    label('p2_W')
    emit(b'\x8b\x44\x24\x1c\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(b'\x89\x44\x24\x50\x89\x44\x24\x7c')
    rel(b'\xe9', va_of('h_p2_W') + len(cap_of('h_p2_W')))

    label('measure_adv')
    emit(b'\x53\x56\x57\x55')
    emit(b'\x83\xec\x14')
    emit(b'\x8b\x1d' + u32(g_hdc_va))
    emit(b'\x85\xdb')
    rel(b'\x0f\x85', 'have_hdc')
    emit(b'\x6a\x00')
    emit(b'\xff\x15' + u32(iat['CreateCompatibleDC']))
    emit(b'\xa3' + u32(g_hdc_va))
    emit(b'\x89\xc3')
    emit(b'\x85\xdb')
    rel(b'\x0f\x84', 'fallback')
    label('have_hdc')
    emit(b'\x8b\x4c\x24\x28')
    emit(b'\x8b\x44\x24\x2c')
    emit(b'\x8b\x51\x04')
    emit(b'\x83\x7c\x24\x34\x00')
    rel(b'\x0f\x84', 'check_sz')
    emit(b'\x83\xf8' + bytes([TAG_M]))
    rel(b'\x0f\x85', 'check_sz')
    emit(b'\x8b\x51\x08')
    rel(b'\xe9', 'got_hf')
    label('check_sz')
    for sz, off in ((0x20, 0x18), (0x14, 0x0C), (0x12, 0x10), (0x0C, 0x14), (0x10, 0x1C), (0x0A, 0x20)):
        emit(b'\x83\xf8' + bytes([sz]))
        emit(b'\x75\x08')
        emit(b'\x8b\x51' + bytes([off]))
        rel(b'\xe9', 'got_hf')
    label('got_hf')
    emit(b'\x52\x53')
    emit(b'\xff\x15' + u32(iat['SelectObject']))
    emit(b'\x89\xc6')
    emit(b'\x8b\x6c\x24\x30')
    emit(b'\x8b\x7c\x24\x38')
    emit(b'\x89\xe0')
    emit(b'\x68' + u32(g_mat2_va))
    emit(b'\x6a\x00\x6a\x00')
    emit(b'\x50')
    emit(b'\x6a\x00')
    emit(b'\x55\x53')
    emit(b'\xff\x17')
    emit(b'\x89\xc7')
    emit(b'\x56\x53')
    emit(b'\xff\x15' + u32(iat['SelectObject']))
    emit(b'\x83\xff\xff')
    rel(b'\x0f\x84', 'fallback')
    emit(b'\x0f\xbf\x44\x24\x10')
    emit(b'\x83\xf8\x01')
    rel(b'\x0f\x8d', 'done')
    label('fallback')
    emit(b'\x8b\x44\x24\x2c')
    emit(b'\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(b'\xd1\xf8')
    emit(b'\x83\x7c\x24\x34\x00')
    emit(b'\x74\x02\x01\xc0')
    emit(b'\x85\xc0\x7f\x05\xb8\x01\x00\x00\x00')
    label('done')
    emit(b'\x83\xc4\x14\x5d\x5f\x5e\x5b')
    emit(b'\xc2\x14\x00')

    label('pass1_A')
    emit(b'\x0f\xb6\x03')
    emit(b'\x68' + u32(iat['GetGlyphOutlineA']))
    emit(b'\xff\x74\x24\x38')
    emit(b'\x50\x57\x55')
    rel(b'\xe8', 'measure_adv')
    emit(b'\x01\x45\x54\x43')
    rel(b'\xe9', va_of('h_p1hw_A') + len(cap_of('h_p1hw_A')))

    label('pass1_W')
    emit(b'\x0f\xb7\x07')
    emit(b'\x3d\x00\x01\x00\x00')
    rel(b'\x0f\x82', 'p1w_hw')
    emit(b'\x3d\x61\xff\x00\x00')
    rel(b'\x0f\x82', 'p1w_fw')
    emit(b'\x3d\x9f\xff\x00\x00')
    rel(b'\x0f\x86', 'p1w_hw')
    label('p1w_fw')
    emit(b'\x89\xd8\x83\xf8' + bytes([TAG_M]))
    emit(b'\x75\x05\xa1' + u32(g_font_size_va))
    emit(b'\x83\x7c\x24\x2c\x00\x74\x02\x01\xc0')
    emit(b'\x01\x45\x54\x83\xc7\x02')
    rel(b'\xe9', va_of('h_p1_W') + len(cap_of('h_p1_W')))
    label('p1w_hw')
    emit(b'\x68' + u32(iat['GetGlyphOutlineW']))
    emit(b'\xff\x74\x24\x30')
    emit(b'\x50\x53\x55')
    rel(b'\xe8', 'measure_adv')
    emit(b'\x01\x45\x54\x83\xc7\x02')
    rel(b'\xe9', va_of('h_p1_W') + len(cap_of('h_p1_W')))

    label('pass2_sz0_A')
    emit(b'\x8b\x54\x24\x40')
    emit(b'\xf7\xc7\x00\xff\xff\xff')
    rel(b'\x0f\x85', 'p2s0a_add')
    emit(b'\x0f\xbf\x44\x24\x7c')
    emit(b'\x83\xf8\x01\x7c\x02\x89\xc2')
    label('p2s0a_add')
    emit(b'\x01\x54\x24\x24')
    rel(b'\xe9', jmp_dst('h_p2s0_A', 8))

    label('pass2_vis_A')
    emit(b'\xf7\xc7\x00\xff\xff\xff')
    rel(b'\x0f\x85', 'p2va_done')
    emit(b'\x0f\xbf\x44\x24\x7c')
    emit(b'\x83\xf8\x01\x7c\x04\x89\x44\x24\x40')
    label('p2va_done')
    emit(b'\x8b\x44\x24\x6c\x83\xc0\x03')
    rel(b'\xe9', va_of('h_p2va_A') + len(cap_of('h_p2va_A')))

    label('pass2_sz0_W')
    emit(b'\x8b\x54\x24\x50')
    emit(b'\x81\xfe\x00\x01\x00\x00')
    rel(b'\x0f\x82', 'p2s0w_hw')
    emit(b'\x81\xfe\x61\xff\x00\x00')
    rel(b'\x0f\x82', 'p2s0w_add')
    emit(b'\x81\xfe\x9f\xff\x00\x00')
    rel(b'\x0f\x87', 'p2s0w_add')
    label('p2s0w_hw')
    emit(b'\x0f\xbf\x44\x24\x78')
    emit(b'\x83\xf8\x01\x7c\x02\x89\xc2')
    label('p2s0w_add')
    emit(b'\x01\x54\x24\x24')
    rel(b'\xe9', jmp_dst('h_p2s0_W', 8))

    label('pass2_vis_W')
    emit(b'\x81\xfe\x00\x01\x00\x00')
    rel(b'\x0f\x82', 'p2vw_hw')
    emit(b'\x81\xfe\x61\xff\x00\x00')
    rel(b'\x0f\x82', 'p2vw_done')
    emit(b'\x81\xfe\x9f\xff\x00\x00')
    rel(b'\x0f\x87', 'p2vw_done')
    label('p2vw_hw')
    emit(b'\x0f\xbf\x44\x24\x78')
    emit(b'\x83\xf8\x01\x7c\x04\x89\x44\x24\x50')
    label('p2vw_done')
    emit(b'\x8b\x44\x24\x68\x83\xc0\x03')
    rel(b'\xe9', va_of('h_p2vw_W') + len(cap_of('h_p2vw_W')))

    for pos, target in fixups:
        dst_va = labels[target] if isinstance(target, str) else target
        buf[pos:pos + 4] = i32(dst_va - (patch_va + pos + 4))

    for va, sz, val in FONT_PATCHES:
        off = rva_to_off(va)
        data[off:off + sz] = struct.pack('<I', val)[:sz]

    def write_jmp(site_key, label_name):
        src_va = va_of(site_key)
        total_len = len(cap_of(site_key))
        off = rva_to_off(src_va)
        data[off:off + 5] = b'\xe9' + i32(labels[label_name] - (src_va + 5))
        if total_len > 5:
            data[off + 5:off + total_len] = b'\x90' * (total_len - 5)

    write_jmp('h_init_m', 'init_font_size')
    write_jmp('h_init_w', 'init_w_font')
    write_jmp('h_58_A',   'init_58_A')
    write_jmp('h_p1fw_A', 'pass1_fw_A')
    write_jmp('h_p1hw_A', 'pass1_A')
    write_jmp('h_p2fw_A', 'p2_fw_A')
    write_jmp('h_p2hw_A', 'p2_hw_A')
    write_jmp('h_p2s0_A', 'pass2_sz0_A')
    write_jmp('h_p2va_A', 'pass2_vis_A')
    write_jmp('h_58_W',   'init_58_W')
    write_jmp('h_p1_W',   'pass1_W')
    write_jmp('h_p2_W',   'p2_W')
    write_jmp('h_p2s0_W', 'pass2_sz0_W')
    write_jmp('h_p2vw_W', 'pass2_vis_W')

    if len(data) < patch_raw:
        data.extend(b'\x00' * (patch_raw - len(data)))
    sec_vsize = len(buf)
    sec_rsize = (sec_vsize + file_align - 1) & ~(file_align - 1)
    data.extend(buf)
    if sec_rsize > sec_vsize:
        data.extend(b'\x00' * (sec_rsize - sec_vsize))

    nt_off = pe['nt_off']
    n_sec = len(pe['sections'])
    sec_hdr_off = nt_off + 24 + pe['opt_sz'] + n_sec * 40
    if sec_hdr_off + 40 > pe['size_of_headers']:
        raise RuntimeError('No space in PE header for .patch section.')
    struct.pack_into('<H', data, nt_off + 6, n_sec + 1)
    new_img_sz = (patch_rva + sec_vsize + sec_align - 1) & ~(sec_align - 1)
    struct.pack_into('<I', data, nt_off + 24 + 56, new_img_sz)
    sec_hdr = struct.pack(
        '<8sIIIIIIHHI',
        b'.patch\x00\x00', sec_vsize, patch_rva, sec_rsize, patch_raw, 0, 0, 0, 0, 0xE0000020
    )
    data[sec_hdr_off:sec_hdr_off + 40] = sec_hdr
    return bytes(data), acp_n, True
