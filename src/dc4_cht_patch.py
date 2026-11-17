"""D.C.4 Traditional Chinese Patch - Plus Harmony + Sweet Harmony.

Double-click to run. It finds the game folder (this exe's folder, a folder dropped
on the exe, or one you pick in a dialog), converts the installed Simplified Chinese
patch by acies to Traditional Chinese, applies the text fixes and sets the text size.
Run it again any time to change the text size.

Command line (optional):  DC4_CHT_Patch.exe [game folder] [--size N] [--reinstall]
                          [--sharp | --no-sharp] [--yes] [--no-pause]
"""
import os
import sys
import traceback

from common import say, ask, DEFAULT_SIZE, SIZE_MIN, SIZE_MAX, display_scale, set_sharp_window, sharp_window_is_on

VERSION = '3.0'
GAMES = (('DC4PHDL.exe', 'D.C.4 Plus Harmony'), ('DC4_SH.exe', 'D.C.4 Sweet Harmony'))


def game_in(folder):
    for exe, name in GAMES:
        if folder and os.path.isfile(os.path.join(folder, exe)):
            return exe, name
    return None


def pick_folder():
    """Windows folder dialog; loops until a game folder is picked or the user cancels."""
    try:
        import tkinter
        from tkinter import filedialog, messagebox
    except Exception:
        return None
    root = tkinter.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    try:
        while True:
            d = filedialog.askdirectory(parent=root, mustexist=True,
                                        title='Select the D.C.4 game folder (with DC4PHDL.exe or DC4_SH.exe) / 選擇遊戲資料夾')
            if not d:
                return None
            d = os.path.normpath(d)
            if game_in(d):
                return d
            for sub in sorted(os.listdir(d)):          # also accept the folder one level up
                if game_in(os.path.join(d, sub)):
                    return os.path.join(d, sub)
            messagebox.showwarning('D.C.4 CHT Patch', 'DC4PHDL.exe or DC4_SH.exe was not found in:\n%s\n\n'
                                   '找不到 DC4PHDL.exe 或 DC4_SH.exe，請重新選擇遊戲資料夾。' % d, parent=root)
    finally:
        root.destroy()


def find_game():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args and os.path.isdir(args[0]):
        return os.path.abspath(args[0])
    here = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    for d in (here, os.getcwd()):
        if game_in(d):
            return d
    say('Choose your game folder in the window that just opened.')
    say('請在跳出的視窗中選擇遊戲資料夾。\n')
    return pick_folder()


def arg_value(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def ask_size(current):
    default = current or DEFAULT_SIZE
    v = arg_value('--size')
    while True:
        if v is None:
            v = ask('Text size in pixels / 文字大小 (%d-%d) [Enter = %d]: ' % (SIZE_MIN, SIZE_MAX, default), str(default))
        try:
            n = int(v)
            if SIZE_MIN <= n <= SIZE_MAX:
                return n
        except ValueError:
            pass
        say('  Please type a number from %d to %d. / 請輸入 %d 到 %d 的數字。' % (SIZE_MIN, SIZE_MAX, SIZE_MIN, SIZE_MAX))
        if '--yes' in sys.argv or arg_value('--size') is not None:
            raise RuntimeError('--size must be %d-%d' % (SIZE_MIN, SIZE_MAX))
        v = None


def sharp_step(exe):
    path = os.path.abspath(exe)
    scale = display_scale()
    if '--no-sharp' in sys.argv or sharp_window_is_on(path):
        return
    if '--sharp' not in sys.argv:
        if scale is not None and scale <= 100:
            return
        say('\n[Optional] Sharp window / 清晰視窗  (Windows display scaling: %s)' % (('%d%%' % scale) if scale else 'unknown'))
        say('  Above 100% Windows stretches the 1280x720 game window, which makes it blurry.')
        say('  Turning this on keeps it sharp (the window looks smaller).')
        if not ask('  Make the window sharp? 讓視窗清晰？ [Y/n]: ', 'y').lower().startswith('y'):
            say('  skipped')
            return
    old, new = set_sharp_window(path)
    say('  ON. Undo: right-click %s > Properties > Compatibility > Change high DPI settings.' % exe)


def main():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    say('D.C.4 Traditional Chinese Patch v%s  /  D.C.4 繁體中文補丁' % VERSION)
    say('Plus Harmony + Sweet Harmony\n')

    game = find_game()
    if not game:
        raise RuntimeError('No game folder selected. / 未選擇遊戲資料夾。')
    exe, name = game_in(game)
    os.chdir(game)
    say('Game:   %s' % name)
    say('Folder: %s\n' % game)
    if exe == 'DC4PHDL.exe':
        import ph as part
    else:
        import sh as part

    installed = part.is_installed() and '--reinstall' not in sys.argv
    if installed:
        cur = part.current_size()
        say('Traditional Chinese is already installed (text size %s).' % (cur or '?'))
        say('已安裝繁體中文。')
        a = ask('  [Enter] change the text size / 調整文字大小    [R] reinstall / 重新安裝: ', '').lower()
        if a.startswith('r'):
            installed = False
    else:
        cur = None
        say('Close the game before continuing. / 請先關閉遊戲。')

    size = ask_size(cur)
    say('')
    try:
        if installed:
            part.set_size(size)
            say('Text size set to %d. / 文字大小已設為 %d。' % (size, size))
        else:
            part.install(size, VERSION)
            say('      text size: %d' % size)
    except PermissionError as ex:
        raise RuntimeError('A game file is in use (%s).\nClose the game, then run this again. / 請關閉遊戲後再執行一次。'
                           % getattr(ex, 'filename', ex))
    sharp_step(exe)

    say('\nDone! Start the game with %s.  完成！請直接開啟遊戲。' % exe)
    say('  Change the text size: run this patch again.  調整文字大小：再執行一次本補丁。')
    say('  Switch language (game closed): 切換繁體中文(CHT).bat / 切换简体中文(CHS).bat')


if __name__ == '__main__':
    code = 0
    try:
        main()
    except Exception as ex:
        code = 1
        say('\n[ERROR] %s' % ex)
        if not isinstance(ex, RuntimeError):
            traceback.print_exc()
    if '--no-pause' not in sys.argv:
        try:
            input('\nPress Enter to exit... / 按 Enter 結束')
        except EOFError:
            pass
    sys.exit(code)
