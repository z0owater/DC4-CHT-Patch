"""D.C.4 Traditional Chinese Patch - launcher window (the exe's entry point).

Pick the game, choose the text size with a live preview, install, switch language,
toggle the sharp window and start the game - all from one window. The work itself is
done by ph.py / sh.py, exactly as in the command-line tool (dc4_cht_patch.py).
"""
import ctypes
import json
import os
import queue
import re
import subprocess
import sys
import threading
import traceback
import webbrowser

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import acies
import common
from common import (DEFAULT_SIZE, SIZE_MAX, SIZE_MIN, clear_sharp_window, display_scale,
                    set_sharp_window, sharp_window_is_on)
from dc4_cht_patch import VERSION, game_in

REPO = 'https://github.com/z0owater/DC4-CHT-Patch'
SAMPLE = '「……沒忘帶東西吧？」翻譯 by MyTuber · gjpqy'
SHORT = {'DC4PHDL.exe': 'Plus Harmony', 'DC4_SH.exe': 'Sweet Harmony'}

TEXT = {
    'en': dict(
        title='D.C.4 Traditional Chinese Patch', subtitle='Plus Harmony · Sweet Harmony',
        game='Game', browse='Browse…',
        pick_title='Select the D.C.4 game folder (with DC4PHDL.exe or DC4_SH.exe)',
        not_game='DC4PHDL.exe or DC4_SH.exe was not found in:\n%s',
        no_folder='Choose your D.C.4 game folder.',
        st_installed='Traditional Chinese installed', showing_chs='now showing Simplified Chinese',
        st_ready='Simplified Chinese patch found - ready to install',
        st_nosc='Needs the free Simplified Chinese patch by acies',
        st_import='Ready to install with %s',
        sc_label='acies patch',
        sc_hint='Download it, then press Select (the .zip, or any file in the extracted folder).',
        sc_found='Found in Downloads: %s',
        sc_picked='Selected: %s',
        get_patch='Download page ↗', pick_patch='Select…', searching='Looking in Downloads…',
        pick_patch_title='Select the acies patch you downloaded (.zip, or any file inside the extracted folder)',
        not_patch="This doesn't look like the Simplified Chinese patch by acies:\n%s",
        need_extract='Please extract this archive first (right-click > Extract All, or 7-Zip),\n'
                     'then select any file inside the extracted folder:\n%s',
        wrong_game='This is the %s patch, but the selected game is %s.',
        size='Text size', preview='Preview',
        lang='Language', cht='Traditional 繁體', chs='Simplified 简体',
        window='Window', sharp='Sharp window (display scaling %s)',
        install='Install', apply='Apply', reinstall='Reinstall', play='▶  Play',
        steps={0: 'Installing the Simplified Chinese patch…', 1: 'Checking the Simplified Chinese patch…', 2: 'Converting the text…',
               3: 'Building the font (about 1 minute)…', 4: 'Patching the game files…', 5: 'Installing…'},
        working='Working…', applying='Applying…',
        done_install='Installed! Press Play to start the game.', done_apply='Saved.',
        details='Details', err_title='Something went wrong',
        busy_file='A game file is in use or read-only:\n%s\n\nClose the game and try again. '
                  'If the game is in Program Files, run this launcher as administrator.',
        credits='Translation: acies  ·  Text fix: hyther1111', help='Help',
        reinstall_q='Rebuild the Traditional Chinese files from the saved Simplified Chinese backup?',
        quit_busy='Still working. Close anyway? The game may be left half-patched.',
    ),
    'zh': dict(
        title='D.C.4 繁體中文補丁', subtitle='Plus Harmony · Sweet Harmony',
        game='遊戲', browse='瀏覽…',
        pick_title='選擇 D.C.4 遊戲資料夾（有 DC4PHDL.exe 或 DC4_SH.exe）',
        not_game='在這個資料夾找不到 DC4PHDL.exe 或 DC4_SH.exe：\n%s',
        no_folder='請選擇 D.C.4 遊戲資料夾。',
        st_installed='已安裝繁體中文', showing_chs='目前顯示簡體中文',
        st_ready='已找到簡體中文漢化，可以安裝',
        st_nosc='需要 acies 的簡體中文漢化（免費）',
        st_import='可以安裝（使用 %s）',
        sc_label='acies 漢化',
        sc_hint='下載後按「選擇…」（選 .zip，或解壓後資料夾裡的任一檔案）。',
        sc_found='在下載資料夾找到：%s',
        sc_picked='已選擇：%s',
        get_patch='下載頁面 ↗', pick_patch='選擇…', searching='正在搜尋下載資料夾…',
        pick_patch_title='選擇下載的 acies 漢化（.zip，或解壓後資料夾裡的任一檔案）',
        not_patch='這看起來不是 acies 的簡體中文漢化：\n%s',
        need_extract='請先解壓這個壓縮檔（右鍵 > 解壓縮全部，或用 7-Zip），\n再選擇解壓後資料夾裡的任一檔案：\n%s',
        wrong_game='這是 %s 的漢化，但目前選擇的遊戲是 %s。',
        size='文字大小', preview='預覽',
        lang='語言', cht='繁體中文', chs='简体中文',
        window='視窗', sharp='清晰視窗（螢幕縮放 %s）',
        install='安裝', apply='套用', reinstall='重新安裝', play='▶  開始遊戲',
        steps={0: '安裝簡體中文漢化…', 1: '檢查簡體中文漢化…', 2: '轉換文字…', 3: '生成字型（約 1 分鐘）…',
               4: '修補遊戲檔案…', 5: '安裝中…'},
        working='處理中…', applying='套用中…',
        done_install='安裝完成！按「開始遊戲」即可遊玩。', done_apply='已儲存。',
        details='詳細資訊', err_title='發生錯誤',
        busy_file='遊戲檔案正在使用中或唯讀：\n%s\n\n請關閉遊戲後再試一次。'
                  '若遊戲裝在 Program Files，請以系統管理員身分執行本程式。',
        credits='翻譯：acies  ·  文字修正：hyther1111', help='說明',
        reinstall_q='要用已保存的簡體中文備份重新生成繁體中文檔案嗎？',
        quit_busy='仍在處理中，確定要關閉嗎？遊戲可能只修補了一半。',
    ),
}

ACCENT, ACCENT_DARK = '#2f6fdb', '#2459b3'
PLAY, PLAY_DARK = '#e0527e', '#c43f69'


# ---------------------------------------------------------------- settings
def cfg_path():
    return os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'DC4-CHT-Patch', 'launcher.json')


def load_cfg():
    try:
        with open(cfg_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_cfg(cfg):
    try:
        os.makedirs(os.path.dirname(cfg_path()), exist_ok=True)
        with open(cfg_path(), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def default_ui():
    try:
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return 'zh' if (lid & 0x3FF) == 0x04 else 'en'          # any Chinese UI -> 繁中
    except Exception:
        return 'en'


def resource(*parts):
    base = getattr(sys, '_MEIPASS', None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    return os.path.join(base, *parts)


# ---------------------------------------------------------------- window
class Launcher:
    def __init__(self, root, start_folder):
        self.root = root
        self.cfg = load_cfg()
        self.ui = self.cfg.get('ui') or default_ui()
        self.q = queue.Queue()
        self.busy = False
        self.folder = self.exe = self.part = None
        self.state = None                 # 'installed' | 'ready' | 'nosc' | None
        self.applied = None               # (size, lang, sharp) currently in the game files
        self.scale = display_scale() or 100
        self.size = tk.IntVar(value=DEFAULT_SIZE)
        self.lang = tk.StringVar(value='cht')
        self.sharp = tk.BooleanVar(value=False)
        self.status = tk.StringVar()
        self.message = tk.StringVar()
        self.show_log = False
        self.log_lines = []
        self.sc_src = None                # acies patch picked / found for a game that lacks it
        self.sc_how = None                # 'found' | 'picked'
        self.sc_note = tk.StringVar()
        self.scanned = set()              # game folders already searched in Downloads
        self.after_task = None
        common.set_output(lambda s: self.q.put(('log', s)))

        root.protocol('WM_DELETE_WINDOW', self.on_close)
        try:
            self.icon = tk.PhotoImage(file=resource('assets', 'icon.png'))
            root.iconphoto(True, self.icon)
        except Exception:
            pass
        self.build()
        root.after(50, self.poll)
        if start_folder:
            self.set_folder(start_folder)
            if '--install' in sys.argv:          # unattended: install as soon as the patch is found
                root.after(500, self.auto_install)
        else:
            self.refresh()
            root.after(400, self.browse)

    def auto_install(self, tries=60):
        if self.state in ('ready', 'import') and not self.busy:
            self.primary()
        elif self.state == 'nosc' and tries > 0:     # still looking in Downloads
            self.root.after(500, lambda: self.auto_install(tries - 1))

    @property
    def t(self):
        return TEXT[self.ui]

    # ------------------------------------------------------------ layout
    def build(self):
        for w in self.root.winfo_children():
            w.destroy()
        t = self.t
        self.root.title('%s v%s' % (t['title'], VERSION))
        family = 'Microsoft JhengHei UI' if self.ui == 'zh' else 'Segoe UI'
        for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont'):
            tkfont.nametofont(name).configure(family=family, size=10)
        self.f_title = tkfont.Font(family=family, size=17, weight='bold')
        self.f_sub = tkfont.Font(family=family, size=10)
        self.f_bold = tkfont.Font(family=family, size=10, weight='bold')
        self.f_small = tkfont.Font(family=family, size=9)
        self.f_button = tkfont.Font(family=family, size=11, weight='bold')

        st = ttk.Style(self.root)
        if 'vista' in st.theme_names():
            st.theme_use('vista')
        st.configure('Card.TFrame', background='white')
        st.configure('Card.TLabel', background='white')
        st.configure('Card.TRadiobutton', background='white')
        st.configure('Card.TCheckbutton', background='white')
        st.configure('Muted.TLabel', background='white', foreground='#6a6f78')
        st.configure('Section.TLabel', background='white', foreground='#30343b')
        st.configure('Card.Horizontal.TScale', background='white')
        st.configure('Link.TLabel', background='#f3f5f8', foreground=ACCENT)
        st.configure('Foot.TLabel', background='#f3f5f8', foreground='#6a6f78')
        st.configure('Foot.TFrame', background='#f3f5f8')
        self.root.configure(background='white')

        # header: gradient band with title + UI language toggle
        self.header = tk.Canvas(self.root, height=self.header_height(), highlightthickness=0, bd=0)
        self.header.pack(fill='x')
        self.header.bind('<Configure>', lambda e: self.draw_header())

        body = ttk.Frame(self.root, style='Card.TFrame', padding=(22, 16, 22, 8))
        body.pack(fill='both', expand=True)
        body.columnconfigure(1, weight=1)

        # game folder
        ttk.Label(body, text=t['game'], style='Section.TLabel', font=self.f_bold).grid(row=0, column=0, sticky='w', padx=(0, 14))
        self.combo = ttk.Combobox(body, state='readonly', width=58)
        self.combo.grid(row=0, column=1, sticky='ew')
        self.combo.bind('<<ComboboxSelected>>', self.on_combo)
        self.browse_btn = ttk.Button(body, text=t['browse'], command=self.browse)
        self.browse_btn.grid(row=0, column=2, padx=(8, 0))
        self.dot = tk.Label(body, text='●', bg='white', font=self.f_small)
        self.dot.grid(row=1, column=0, sticky='e', padx=(0, 6), pady=(6, 0))
        ttk.Label(body, textvariable=self.status, style='Card.TLabel').grid(row=1, column=1, columnspan=2, sticky='w', pady=(6, 0))

        # acies patch (only shown while the game doesn't have it)
        self.src_lbl = ttk.Label(body, text=t['sc_label'], style='Section.TLabel', font=self.f_bold)
        self.src_row = ttk.Frame(body, style='Card.TFrame')
        self.src_row.columnconfigure(0, weight=1)
        ttk.Label(self.src_row, textvariable=self.sc_note, style='Muted.TLabel', wraplength=round(430 * max(1.0, self.scale / 100)), justify='left').grid(
            row=0, column=0, sticky='w')
        self.get_btn = ttk.Button(self.src_row, text=t['get_patch'], command=self.open_patch_page)
        self.get_btn.grid(row=0, column=1, padx=(8, 0))
        self.pick_btn = ttk.Button(self.src_row, text=t['pick_patch'], command=self.pick_patch)
        self.pick_btn.grid(row=0, column=2, padx=(6, 0))

        ttk.Separator(body).grid(row=3, column=0, columnspan=3, sticky='ew', pady=14)

        # text size + preview
        ttk.Label(body, text=t['size'], style='Section.TLabel', font=self.f_bold).grid(row=4, column=0, sticky='w')
        sz = ttk.Frame(body, style='Card.TFrame')
        sz.grid(row=4, column=1, columnspan=2, sticky='ew')
        sz.columnconfigure(0, weight=1)
        self.scale_w = ttk.Scale(sz, from_=SIZE_MIN, to=SIZE_MAX, orient='horizontal',
                                 command=self.on_size, style='Card.Horizontal.TScale')
        self.scale_w.grid(row=0, column=0, sticky='ew')
        self.size_lbl = ttk.Label(sz, width=6, anchor='e', style='Card.TLabel', font=self.f_bold)
        self.size_lbl.grid(row=0, column=1, padx=(10, 0))
        self.minus = ttk.Button(sz, text='−', width=3, command=lambda: self.nudge(-1))
        self.minus.grid(row=0, column=2, padx=(8, 2))
        self.plus = ttk.Button(sz, text='+', width=3, command=lambda: self.nudge(1))
        self.plus.grid(row=0, column=3)

        k = max(1.0, self.scale / 100)
        self.pv = tk.Frame(body, bg='#203a5c', width=int(600 * k), height=int(78 * k))
        self.pv.grid(row=5, column=1, columnspan=2, sticky='ew', pady=(10, 0))
        self.pv.pack_propagate(False)
        self.pv_font = tkfont.Font(family='Microsoft JhengHei', weight='bold', size=-DEFAULT_SIZE)
        self.pv_lbl = tk.Label(self.pv, text=SAMPLE, font=self.pv_font, fg='white', bg='#203a5c', anchor='w', padx=14)
        self.pv_lbl.pack(fill='both', expand=True)
        ttk.Label(body, text=t['preview'], style='Muted.TLabel', font=self.f_small).grid(row=5, column=0, sticky='nw', pady=(12, 0))

        ttk.Separator(body).grid(row=6, column=0, columnspan=3, sticky='ew', pady=14)

        # language + window
        ttk.Label(body, text=t['lang'], style='Section.TLabel', font=self.f_bold).grid(row=7, column=0, sticky='w')
        lf = ttk.Frame(body, style='Card.TFrame')
        lf.grid(row=7, column=1, columnspan=2, sticky='w')
        self.rb_cht = ttk.Radiobutton(lf, text=t['cht'], value='cht', variable=self.lang, style='Card.TRadiobutton', command=self.update_buttons)
        self.rb_cht.pack(side='left', padx=(0, 18))
        self.rb_chs = ttk.Radiobutton(lf, text=t['chs'], value='chs', variable=self.lang, style='Card.TRadiobutton', command=self.update_buttons)
        self.rb_chs.pack(side='left')
        ttk.Label(body, text=t['window'], style='Section.TLabel', font=self.f_bold).grid(row=8, column=0, sticky='w', pady=(10, 0))
        self.cb_sharp = ttk.Checkbutton(body, text=t['sharp'] % ('%d%%' % self.scale), variable=self.sharp,
                                        style='Card.TCheckbutton', command=self.on_sharp)
        self.cb_sharp.grid(row=8, column=1, columnspan=2, sticky='w', pady=(10, 0))

        # progress + message + details
        pf = ttk.Frame(body, style='Card.TFrame')
        pf.grid(row=9, column=0, columnspan=3, sticky='ew', pady=(18, 0))
        pf.columnconfigure(0, weight=1)
        self.bar = ttk.Progressbar(pf, mode='determinate', maximum=100)
        self.bar.grid(row=0, column=0, columnspan=2, sticky='ew')
        ttk.Label(pf, textvariable=self.message, style='Muted.TLabel').grid(row=1, column=0, sticky='w', pady=(6, 0))
        self.det_btn = ttk.Label(pf, text=t['details'] + (' ▾' if self.show_log else ' ▸'), style='Muted.TLabel', cursor='hand2')
        self.det_btn.grid(row=1, column=1, sticky='e', pady=(6, 0))
        self.det_btn.bind('<Button-1>', lambda e: self.toggle_log())
        self.logbox = tk.Text(pf, height=9, wrap='word', font=('Consolas', 9), bg='#f6f8fa', relief='flat',
                              highlightthickness=1, highlightbackground='#d8dee4')
        self.logbox.insert('end', '\n'.join(self.log_lines) + ('\n' if self.log_lines else ''))
        self.logbox.configure(state='disabled')
        if self.show_log:
            self.logbox.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(6, 0))

        # action buttons
        bf = ttk.Frame(body, style='Card.TFrame')
        bf.grid(row=10, column=0, columnspan=3, sticky='ew', pady=(16, 6))
        self.re_btn = ttk.Label(bf, text=t['reinstall'], style='Muted.TLabel', cursor='hand2', font=self.f_small)
        self.re_btn.bind('<Button-1>', lambda e: self.reinstall())
        self.play_btn = self.big_button(bf, t['play'], PLAY, PLAY_DARK, self.play)
        self.play_btn.pack(side='right')
        self.main_btn = self.big_button(bf, t['install'], ACCENT, ACCENT_DARK, self.primary)
        self.main_btn.pack(side='right', padx=(0, 10))

        # footer
        foot = ttk.Frame(self.root, style='Foot.TFrame', padding=(22, 8))
        foot.pack(fill='x', side='bottom')
        ttk.Label(foot, text=t['credits'], style='Foot.TLabel', font=self.f_small).pack(side='left')
        hl = ttk.Label(foot, text=t['help'] + ' ↗', style='Link.TLabel', cursor='hand2', font=self.f_small)
        hl.pack(side='right')
        hl.bind('<Button-1>', lambda e: webbrowser.open(REPO + ('/blob/main/README.zh-TW.md' if self.ui == 'zh' else '#readme')))

        self.fill_combo()
        self.scale_w.set(self.size.get())
        self.on_size(self.size.get())
        self.refresh(reload=False)

    def big_button(self, parent, text, bg, dark, cmd):
        b = tk.Button(parent, text=text, command=cmd, font=self.f_button, fg='white', bg=bg,
                      activebackground=dark, activeforeground='white', disabledforeground='#e8ecf2',
                      relief='flat', bd=0, padx=22, pady=7, cursor='hand2')
        b.bind('<Enter>', lambda e: b.configure(bg=dark) if str(b['state']) == 'normal' else None)
        b.bind('<Leave>', lambda e: b.configure(bg=bg if str(b['state']) == 'normal' else '#b9c3d0'))
        b.colors = (bg, dark)
        return b

    def set_button(self, b, enabled):
        b.configure(state='normal' if enabled else 'disabled', bg=b.colors[0] if enabled else '#b9c3d0',
                    cursor='hand2' if enabled else 'arrow')

    def header_height(self):
        k = max(1.0, self.scale / 100)
        return int(self.f_title.metrics('linespace') + self.f_sub.metrics('linespace') + 30 * k)

    def draw_header(self):
        c = self.header
        c.delete('all')
        k = max(1.0, self.scale / 100)
        w, h = max(c.winfo_width(), 2), int(c['height'])
        th, sh = self.f_title.metrics('linespace'), self.f_sub.metrics('linespace')
        top = (h - th - sh - 4 * k) / 2
        a, b = (0xF4, 0x9A, 0xBD), (0x5B, 0x9C, 0xF0)          # sakura pink -> sky blue
        steps = 64
        for i in range(steps):
            r = i / (steps - 1)
            col = '#%02x%02x%02x' % tuple(round(a[j] + (b[j] - a[j]) * r) for j in range(3))
            x0, x1 = w * i // steps, w * (i + 1) // steps + 1
            c.create_rectangle(x0, 0, x1, h, outline='', fill=col)
        pad = round(22 * k)
        x = pad
        if getattr(self, 'icon', None):
            if getattr(self, 'icon_small', None) is None:
                self.icon_small = self.icon.subsample(max(1, round(self.icon.width() / (th + sh))))
            c.create_image(pad, h // 2, image=self.icon_small, anchor='w')
            x = pad + self.icon_small.width() + round(12 * k)
        c.create_text(x, top, text=self.t['title'], font=self.f_title, fill='white', anchor='nw')
        c.create_text(x + 1, top + th + 4 * k, text='%s   ·   v%s' % (self.t['subtitle'], VERSION),
                      font=self.f_sub, fill='white', anchor='nw')
        # UI language toggle, sized from the font so it fits at any display scaling
        bw = max(self.f_small.measure('中文'), self.f_small.measure('EN')) + round(18 * k)
        bh = self.f_small.metrics('linespace') + round(6 * k)
        y0 = round(12 * k)
        for i, (code, label) in enumerate((('zh', '中文'), ('en', 'EN'))):
            x1 = w - pad - i * (bw + round(6 * k))
            on = self.ui == code
            tag = 'ui_' + code
            c.create_rectangle(x1 - bw, y0, x1, y0 + bh, outline='white', width=1, fill='white' if on else '', tags=tag)
            c.create_text(x1 - bw / 2, y0 + bh / 2, text=label, fill=ACCENT if on else 'white', font=self.f_small, tags=tag)
            c.tag_bind(tag, '<Button-1>', lambda e, code=code: self.set_ui(code))
            c.tag_bind(tag, '<Enter>', lambda e: c.configure(cursor='hand2'))
            c.tag_bind(tag, '<Leave>', lambda e: c.configure(cursor=''))

    def set_ui(self, code):
        if code != self.ui and not self.busy:
            self.ui = code
            self.cfg['ui'] = code
            save_cfg(self.cfg)
            self.build()

    # ------------------------------------------------------------ game folders
    def folders(self):
        out = []
        for p in self.cfg.get('folders', []):
            if p not in out and game_in(p):
                out.append(p)
        return out

    def fill_combo(self):
        self.combo_paths = self.folders()
        self.combo['values'] = ['%s  —  %s' % (SHORT[game_in(p)[0]], p) for p in self.combo_paths]
        if self.folder in self.combo_paths:
            self.combo.current(self.combo_paths.index(self.folder))
        else:
            self.combo.set('')

    def on_combo(self, _e=None):
        i = self.combo.current()
        if 0 <= i < len(self.combo_paths) and not self.busy:
            self.set_folder(self.combo_paths[i])

    def browse(self):
        if self.busy:
            return
        d = filedialog.askdirectory(parent=self.root, mustexist=True, title=self.t['pick_title'],
                                    initialdir=self.folder or None)
        if not d:
            return
        d = os.path.normpath(d)
        if not game_in(d):
            sub = next((os.path.join(d, s) for s in sorted(os.listdir(d)) if game_in(os.path.join(d, s))), None)
            if not sub:
                messagebox.showwarning(self.t['title'], self.t['not_game'] % d, parent=self.root)
                return
            d = sub
        self.set_folder(d)

    def set_folder(self, d):
        self.folder = os.path.normpath(os.path.abspath(d))
        self.exe = game_in(self.folder)[0]
        os.chdir(self.folder)
        import ph, sh
        self.part = ph if self.exe == 'DC4PHDL.exe' else sh
        fl = [self.folder] + [p for p in self.cfg.get('folders', []) if os.path.normcase(p) != os.path.normcase(self.folder)]
        self.cfg['folders'] = fl[:6]
        save_cfg(self.cfg)
        self.fill_combo()
        self.message.set('')
        self.bar['value'] = 0
        self.refresh()

    # ------------------------------------------------------------ state
    def refresh(self, reload=True):
        t = self.t
        if not self.folder:
            self.state = None
            self.status.set(t['no_folder'])
            self.dot.configure(fg='#b9c3d0')
        else:
            os.chdir(self.folder)
            name = game_in(self.folder)[1]
            exe_path = os.path.join(self.folder, self.exe)
            if self.part.is_installed():
                self.state = 'installed'
                if reload:
                    self.size.set(self.part.current_size() or DEFAULT_SIZE)
                    self.lang.set(self.part.current_language())
                    self.sharp.set(sharp_window_is_on(exe_path))
                    self.applied = (self.size.get(), self.lang.get(), self.sharp.get())
                extra = ('  ·  ' + t['showing_chs']) if self.part.current_language() == 'chs' else ''
                self.status.set('%s  ·  %s%s' % (name, t['st_installed'], extra))
                self.dot.configure(fg='#2da44e')
            else:
                kind = acies.KIND_OF_EXE[self.exe]
                if self.sc_src and self.sc_src['kind'] != kind:
                    self.sc_src = None
                if self.part.sc_patch_present():
                    self.state = 'ready'
                else:
                    self.state = 'import' if self.sc_src else 'nosc'
                if reload:
                    self.lang.set('cht')
                    self.sharp.set(sharp_window_is_on(exe_path) or self.scale > 100)
                    self.applied = None
                if self.state == 'import':
                    self.status.set('%s  ·  %s' % (name, t['st_import'] % os.path.basename(self.sc_src['path'])))
                else:
                    self.status.set('%s  ·  %s' % (name, t['st_' + self.state]))
                self.dot.configure(fg={'ready': '#d4a72c', 'import': '#d4a72c'}.get(self.state, '#cf222e'))
                if self.state == 'nosc' and self.folder not in self.scanned:
                    self.scan_downloads(kind)
        self.show_src_row()
        self.scale_w.set(self.size.get())
        self.on_size(self.size.get())
        self.update_buttons()

    # ------------------------------------------------------------ acies patch
    def show_src_row(self):
        t = self.t
        if self.state in ('nosc', 'import'):
            if self.sc_src:
                p, dl = self.sc_src['path'], acies.downloads_dir()
                if self.sc_how == 'found' and dl and os.path.normcase(p).startswith(os.path.normcase(dl) + os.sep):
                    p = os.path.relpath(p, dl)
                elif self.sc_how == 'picked':
                    p = os.path.basename(p)
                self.sc_note.set(t['sc_found' if self.sc_how == 'found' else 'sc_picked'] % p)
            elif self.folder in self.scanning():
                self.sc_note.set(t['searching'])
            else:
                self.sc_note.set(t['sc_hint'])
            self.src_lbl.grid(row=2, column=0, sticky='nw', pady=(12, 0))
            self.src_row.grid(row=2, column=1, columnspan=2, sticky='ew', pady=(12, 0))
        else:
            self.src_lbl.grid_remove()
            self.src_row.grid_remove()

    def scanning(self):
        return getattr(self, '_scanning', set())

    def scan_downloads(self, kind):
        folder = self.folder
        self.scanned.add(folder)
        self._scanning = self.scanning() | {folder}

        def work():
            try:
                src = acies.find_in_downloads(kind)
            except Exception:
                src = None
            self.q.put(('found', (folder, src)))
        threading.Thread(target=work, daemon=True).start()

    def open_patch_page(self):
        if self.exe:
            webbrowser.open(acies.PAGES[acies.KIND_OF_EXE[self.exe]])

    def pick_patch(self):
        if self.busy or not self.exe:
            return
        p = filedialog.askopenfilename(parent=self.root, title=self.t['pick_patch_title'],
                                       initialdir=acies.downloads_dir() or None,
                                       filetypes=[('acies patch', '*.zip *.7z *.rar *.dll *.ini *.xp3 *.ttf *.txt'),
                                                  ('*', '*.*')])
        if not p:
            return
        try:
            src = acies.inspect(p)
        except acies.NeedsExtract:
            messagebox.showwarning(self.t['title'], self.t['need_extract'] % p, parent=self.root)
            return
        except (acies.NotAPatch, OSError):
            messagebox.showwarning(self.t['title'], self.t['not_patch'] % p, parent=self.root)
            return
        kind = acies.KIND_OF_EXE[self.exe]
        if src['kind'] != kind:
            messagebox.showwarning(self.t['title'], self.t['wrong_game'] % (acies.GAME_NAME[src['kind']], acies.GAME_NAME[kind]),
                                   parent=self.root)
            return
        self.sc_src, self.sc_how = src, 'picked'
        self.refresh(reload=False)

    def settings(self):
        return (self.size.get(), self.lang.get(), self.sharp.get())

    def update_buttons(self):
        t = self.t
        idle = not self.busy
        has = self.state is not None
        can_edit = idle and self.state in ('installed', 'ready', 'import')
        for w in (self.get_btn, self.pick_btn):
            w.state(['!disabled'] if idle else ['disabled'])
        for w in (self.scale_w, self.minus, self.plus, self.cb_sharp):
            w.state(['!disabled'] if can_edit else ['disabled'])
        for w in (self.rb_cht, self.rb_chs):
            w.state(['!disabled'] if (idle and self.state == 'installed') else ['disabled'])
        self.combo.state(['!disabled', 'readonly'] if idle else ['disabled'])
        self.browse_btn.state(['!disabled'] if idle else ['disabled'])
        if self.state == 'installed':
            self.main_btn.configure(text=t['apply'])
            self.set_button(self.main_btn, idle and self.settings() != self.applied)
            self.re_btn.pack(side='left')
        else:
            self.main_btn.configure(text=t['install'])
            self.set_button(self.main_btn, idle and self.state in ('ready', 'import'))
            self.re_btn.pack_forget()
        self.set_button(self.play_btn, idle and has)

    def on_size(self, v):
        n = int(round(float(v)))
        if self.size.get() != n:
            self.size.set(n)
        self.size_lbl.configure(text='%d px' % n)
        k = 1 if (self.sharp.get() or self.scale <= 100) else self.scale / 100
        self.pv_font.configure(size=-round(n * k))
        if hasattr(self, 'main_btn'):
            self.update_buttons()

    def nudge(self, d):
        n = min(SIZE_MAX, max(SIZE_MIN, self.size.get() + d))
        self.scale_w.set(n)
        self.on_size(n)

    def on_sharp(self):
        self.on_size(self.size.get())

    def toggle_log(self):
        self.show_log = not self.show_log
        self.det_btn.configure(text=self.t['details'] + (' ▾' if self.show_log else ' ▸'))
        if self.show_log:
            self.logbox.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(6, 0))
        else:
            self.logbox.grid_remove()

    # ------------------------------------------------------------ actions
    def primary(self):
        if self.state == 'installed':
            self.run(self.apply_settings, self.t['applying'], self.t['done_apply'])
        elif self.state in ('ready', 'import'):
            self.run(self.do_install, self.t['working'], self.t['done_install'])

    def reinstall(self):
        if self.busy or self.state != 'installed':
            return
        if messagebox.askyesno(self.t['title'], self.t['reinstall_q'], parent=self.root):
            self.run(self.do_install, self.t['working'], self.t['done_install'])

    def do_install(self):
        size, _, sharp = self.settings()
        if self.state == 'import' and self.sc_src:
            acies.install(self.sc_src, self.part.STORE)
        self.part.install(size, VERSION)
        self.apply_sharp(sharp)

    def apply_settings(self):
        size, lang, sharp = self.settings()
        old = self.applied or (None, None, None)
        if size != old[0]:
            self.part.set_size(size)
            common.say('Text size set to %d.' % size)
        if lang != old[1]:
            self.part.switch_language(lang)
            common.say('Language switched to %s.' % ('Traditional Chinese' if lang == 'cht' else 'Simplified Chinese'))
        if sharp != old[2]:
            self.apply_sharp(sharp)

    def apply_sharp(self, on):
        path = os.path.join(self.folder, self.exe)
        if on:
            set_sharp_window(path)
        else:
            clear_sharp_window(path)
        common.say('Sharp window: %s' % ('on' if on else 'off'))

    def run(self, fn, working, done):
        self.busy = True
        self.bar['value'] = 2
        self.message.set(working)
        self.update_buttons()
        folder = self.folder

        def work():
            try:
                os.chdir(folder)
                fn()
                self.q.put(('done', done))
            except PermissionError as ex:
                self.q.put(('error', self.t['busy_file'] % (getattr(ex, 'filename', None) or ex)))
            except RuntimeError as ex:
                self.q.put(('error', str(ex)))
            except Exception:
                self.q.put(('error', traceback.format_exc()))
        threading.Thread(target=work, daemon=True).start()

    def play(self):
        if self.busy or not self.folder:
            return
        if self.state == 'installed' and self.settings() != self.applied:
            self.after_task = self.launch_game
            self.run(self.apply_settings, self.t['applying'], self.t['done_apply'])
            return
        self.launch_game()

    def launch_game(self):
        subprocess.Popen([os.path.join(self.folder, self.exe)], cwd=self.folder)
        self.root.after(800, self.root.destroy)

    def on_close(self):
        if self.busy and not messagebox.askyesno(self.t['title'], self.t['quit_busy'], parent=self.root):
            return
        self.root.destroy()

    # ------------------------------------------------------------ worker messages
    def log(self, s):
        self.log_lines.append(s)
        self.logbox.configure(state='normal')
        self.logbox.insert('end', s + '\n')
        self.logbox.see('end')
        self.logbox.configure(state='disabled')

    def poll(self):
        try:
            while True:
                kind, s = self.q.get_nowait()
                if kind == 'log':
                    self.log(s)
                    m = re.match(r'\s*\[(\d)/5\]', s)
                    if m:
                        n = int(m.group(1))
                        self.bar['value'] = max(1, (n - 1) * 20 + 2)
                        self.message.set(self.t['steps'].get(n, s))
                    m = re.search(r'\.\.\. (\d+) / (\d+)', s)
                    if m:
                        self.bar['value'] = 20 + 20 * int(m.group(1)) / max(1, int(m.group(2)))
                elif kind == 'found':
                    folder, src = s
                    self._scanning = self.scanning() - {folder}
                    if src and not self.sc_src and folder == self.folder:
                        self.sc_src, self.sc_how = src, 'found'
                    if folder == self.folder and not self.busy:
                        self.refresh(reload=False)
                elif kind == 'done':
                    self.busy = False
                    self.bar['value'] = 100
                    self.message.set(s)
                    self.sc_src = None
                    self.refresh()
                    nxt = getattr(self, 'after_task', None)
                    self.after_task = None
                    if nxt:
                        nxt()
                elif kind == 'error':
                    self.busy = False
                    self.after_task = None
                    self.bar['value'] = 0
                    self.message.set(self.t['err_title'])
                    self.log(s)
                    self.refresh()
                    messagebox.showerror(self.t['err_title'], s, parent=self.root)
        except queue.Empty:
            pass
        self.root.after(50, self.poll)


def start_folder():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args and os.path.isdir(args[0]) and game_in(os.path.abspath(args[0])):
        return os.path.abspath(args[0])
    here = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    for d in (here, os.getcwd()):
        if game_in(d):
            return d
    cfg = load_cfg()
    for p in cfg.get('folders', []):
        if game_in(p):
            return p
    return None


def main():
    for name in ('stdout', 'stderr'):           # the windowed exe has no console
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, 'w', encoding='utf-8'))
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    root = tk.Tk()
    root.withdraw()
    Launcher(root, start_folder())
    root.update_idletasks()
    root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())
    root.resizable(True, False)
    root.deiconify()
    root.mainloop()


if __name__ == '__main__':
    main()
