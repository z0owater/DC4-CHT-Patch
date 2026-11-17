# D.C.4 Traditional Chinese Patch

[![English](https://img.shields.io/badge/English-0969da?style=for-the-badge)](README.md)
[![繁體中文](https://img.shields.io/badge/%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-555555?style=for-the-badge)](README.zh-TW.md)

One patch for ***D.C.4 Plus Harmony*** and ***D.C.4 Sweet Harmony***. It converts the Simplified Chinese fan translation by acies, once you've installed it, to Traditional Chinese (Taiwan standard). It also fixes the text rendering and lets you choose the text size. Only the characters change; the wording stays the same.

This repo contains no game files, translation text or fonts. Everything is generated on your own computer from your copy of the game, the patch you installed, and the Microsoft JhengHei font that comes with Windows. Please buy the games from [CIRCUS](https://circus-co.jp/): [D.C.4 Plus Harmony](https://circus-co.jp/product/dc4ph/) / [D.C.4 Sweet Harmony](https://circus-co.jp/product/dc4sh/).

## Features

- **Traditional Chinese (Taiwan)**: converted with OpenCC. Character names keep their original kanji (有里咲, 有里栖, 琴里, 叶方).
- **Clearer font**: built from Microsoft JhengHei Bold, with Taiwan character forms. Adds the missing ♪ and makes `——` and `……` join up.
- **Choose your text size**: default 28 px, adjustable from 16 to 31.
- **English text displays correctly**:
  - Plus Harmony: half-width letters no longer overlap (e.g. `MyTuber`), y/g/p/q/j are no longer cut off, and there's no garbled text on non-Japanese Windows.
  - Sweet Harmony: text gets bigger without squeezing the gaps between letters.
- **Switch between Traditional and Simplified** at any time.
- **Optional**: keeps the 1280×720 window sharp on scaled displays (125% / 150%).

## Install

1. Install the game, then install the **Simplified Chinese patch by acies** (see [Credits](#credits)) as its instructions say.
2. Download **`DC4_CHT_Patch.exe`** from [Releases](../../releases/latest).
3. **Double-click it** and choose your game folder (the one with `DC4PHDL.exe` or `DC4_SH.exe`).
4. Press **Enter** for the default text size (28), or type another size.
5. Done. Start the game as usual.

Do this once for each game. It takes about a minute.

> **Tip:** if you put `DC4_CHT_Patch.exe` inside the game folder, it skips the folder question. You can also drag the game folder onto the exe.

## Change the text size

Run `DC4_CHT_Patch.exe` again, press **Enter**, then type the new size. Nothing is reinstalled.

You can also edit `FontHook.ini` in the game folder with Notepad and then restart the game:

| Game | Line in `FontHook.ini` | Example |
|---|---|---|
| Plus Harmony | `EngineFontSize=` size in pixels | `EngineFontSize=27` |
| Sweet Harmony | `FontHeightScale1000=` size × 1000 ÷ 26 | `FontHeightScale1000=1077` (= 28 px) |

25–28 is recommended. If you edit the file by hand, run the patch once more so the language-switch copies get the same size.

## Switch language

Close the game, then run one of these in the game folder:

- `切換繁體中文(CHT).bat` → Traditional Chinese
- `切换简体中文(CHS).bat` → the original Simplified Chinese

The text fixes and your text size apply to both languages.

## Undo

- **Back to Simplified Chinese:** run `切换简体中文(CHS).bat`. The original patch files are kept in `DC4PH_CHT\SC_backup` and `DC4SH_CHT\SC_backup`.
- **Original `DC4PHDL.exe`** (Plus Harmony): copy `DC4PH_CHT\DC4PHDL.exe.original` over `DC4PHDL.exe`. Sweet Harmony's `DC4_SH.exe` is never modified.
- **Sharp window:** right-click the game exe → Properties → Compatibility → Change high DPI settings → untick "Override high DPI scaling behavior".

## FAQ

**My antivirus flags the exe.** The exe is a Python program packed with PyInstaller, which antivirus software often flags by mistake. The full source is in [`src/`](src/); you can read it or run it directly (see [Run from source](#run-from-source)).

**"The Simplified Chinese patch by acies was not found".** Install the acies patch first. If you converted the game to Traditional Chinese by some other method, reinstall the Simplified Chinese patch first.

**I used the older CHT installer v2.0 or DC4PH_TextFix.** Just run this patch; it replaces both. Your saved Simplified Chinese backup is reused.

**Requirements.** Windows 10 or 11 (uses the built-in Microsoft JhengHei font, `msjhbd.ttc` / `msjh.ttc`).

## Run from source

```bat
pip install -r requirements.txt
python src\dc4_cht_patch.py "C:\path\to\game folder"
```

Options: `--size N`, `--reinstall`, `--sharp` / `--no-sharp`, `--yes` (accept defaults), `--no-pause`.
`build.bat` builds `DC4_CHT_Patch.exe` with PyInstaller.

<details>
<summary>How it works</summary>

- **Plus Harmony (Circus engine).** The scripts in `Advdata\MES` are converted in place. Characters that Shift-JIS can't hold are stored as private-use codes, which the generated font maps back. `DC4PHDL.exe` gets two patches: a Shift-JIS fix, and hyther1111's text fix ([`src/ph_textfix.py`](src/ph_textfix.py)). The text fix measures every half-width glyph instead of using a fixed half-em cell, makes the glyph surface tall enough for descenders, and reads `EngineFontSize` from `FontHook.ini` when the game starts.
- **Sweet Harmony (KiriKiri Z).** Each script in `patch.xp3` is decrypted with the key from that patch release, its on-screen text is converted, and it's re-encrypted. KiriKiri already lays text out by real glyph widths, so the size is set through the acies patch's FontHook (`FontHeightScale1000`), which scales the letter spacing too.

</details>

## Credits

- **acies**: the Simplified Chinese translations these patches build on (Japanese → Simplified Chinese).
  - Plus Harmony: [2DFan](https://2dfan.com/downloads/47006) · [ai2.moe](https://www.ai2.moe/files/file/14897-circusdc4-plus-harmonydeepseek-v41-flash-1017%E7%AB%99%E5%86%85%E5%AD%98%E5%82%A8%E8%A1%A5%E4%B8%81/)
  - Sweet Harmony: [2DFan](https://2dfan.com/downloads/47045) · [ai2.moe](https://www.ai2.moe/files/file/14910-circusdc4-sweet-harmonydeepseek-v41-flash-1017%E7%AB%99%E5%86%85%E5%AD%98%E5%82%A8%E8%A1%A5%E4%B8%81/)
- **[hyther1111](https://github.com/hyther1111)**: *DC4PH_TextFix*, the Plus Harmony text fix (overlapping half-width letters, clipped descenders, `EngineFontSize` in `FontHook.ini`). hyther1111 also traced the overlap to the earlier +5% text enlargement, which left no room between letters, and suggested making the size a setting in `FontHook.ini`. Both changes are in this version.
- Built with [OpenCC](https://github.com/yichen0831/opencc-python) (opencc-python-reimplemented), [fontTools](https://github.com/fonttools/fonttools) and [PyInstaller](https://pyinstaller.org/).

*D.C.4 Plus Harmony* and *D.C.4 Sweet Harmony* © CIRCUS. This is an unofficial fan project, not affiliated with CIRCUS or with the translators.
