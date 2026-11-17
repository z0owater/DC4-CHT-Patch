# D.C.4 繁體中文補丁

[![English](https://img.shields.io/badge/English-555555?style=for-the-badge)](README.md)
[![繁體中文](https://img.shields.io/badge/%E7%B9%81%E9%AB%94%E4%B8%AD%E6%96%87-0969da?style=for-the-badge)](README.zh-TW.md)

一個補丁，***D.C.4 Plus Harmony*** 和 ***D.C.4 Sweet Harmony*** 都能用。把已安裝的 acies 簡體中文漢化轉成繁體中文（台灣用字），同時修正文字顯示問題，並可自訂文字大小。只轉換字形，翻譯內容不變。

本專案不含任何遊戲檔案、翻譯文本或字型檔。所有檔案都在你的電腦上，用你自己的遊戲、你安裝的漢化補丁，以及 Windows 內建的微軟正黑體生成。請支持正版：[CIRCUS](https://circus-co.jp/) — [D.C.4 Plus Harmony](https://circus-co.jp/product/dc4ph/) / [D.C.4 Sweet Harmony](https://circus-co.jp/product/dc4sh/)。

## 功能

- **繁體中文（台灣用字）**：使用 OpenCC 轉換，角色名保留原名（有里咲、有里栖、琴里、叶方）。
- **更清晰的字型**：以微軟正黑體 Bold 生成（台灣字形），補上 ♪ 等缺字，`——`、`……` 連貫顯示。
- **自訂文字大小**：預設 28 px，可設定 16–31。
- **英文正常顯示**：
  - Plus Harmony：半形英文不再重疊、擠在一起（例如 `MyTuber`），y/g/p/q/j 下緣不再被切掉，非日文 Windows 也不會亂碼。
  - Sweet Harmony：放大文字時不會壓縮字母間距。
- **繁體／簡體隨時切換**。
- **（可選）清晰視窗**：螢幕縮放 125% / 150% 時，讓 1280×720 視窗保持清晰。

## 安裝

1. 安裝遊戲，再照說明安裝 **acies 的簡體中文漢化補丁**（連結見[致謝](#致謝)）。
2. 到 [Releases](../../releases/latest) 下載 **`DC4_CHT_Patch.exe`**。
3. **雙擊執行**，選擇遊戲資料夾（有 `DC4PHDL.exe` 或 `DC4_SH.exe` 的那個）。
4. 按 **Enter** 使用預設文字大小（28），或輸入其他大小。
5. 完成！照常開啟遊戲即可。

每款遊戲各執行一次，約需一分鐘。

> **小技巧：** 把 `DC4_CHT_Patch.exe` 放進遊戲資料夾就不用選資料夾；也可以把遊戲資料夾直接拖到 exe 上。

## 調整文字大小

再執行一次 `DC4_CHT_Patch.exe`，按 **Enter**，輸入新的大小即可，不會重新安裝。

也可以用記事本編輯遊戲資料夾裡的 `FontHook.ini`，存檔後重開遊戲：

| 遊戲 | `FontHook.ini` 裡的這一行 | 範例 |
|---|---|---|
| Plus Harmony | `EngineFontSize=` 像素大小 | `EngineFontSize=27` |
| Sweet Harmony | `FontHeightScale1000=` 大小 × 1000 ÷ 26 | `FontHeightScale1000=1077`（= 28 px） |

推薦 25–28。手動修改後，再執行一次補丁，切換語言用的備份也會同步成同樣大小。

## 切換語言

先關閉遊戲，再執行遊戲資料夾裡的：

- `切換繁體中文(CHT).bat` → 繁體中文
- `切换简体中文(CHS).bat` → 原本的簡體中文

文字修正和文字大小在兩種語言下都有效。

## 還原

- **換回簡體中文：** 執行 `切换简体中文(CHS).bat`。原本的漢化檔案保存在 `DC4PH_CHT\SC_backup` 和 `DC4SH_CHT\SC_backup`。
- **原本的 `DC4PHDL.exe`**（Plus Harmony）：把 `DC4PH_CHT\DC4PHDL.exe.original` 複製回去覆蓋 `DC4PHDL.exe`。Sweet Harmony 的 `DC4_SH.exe` 完全不會被修改。
- **清晰視窗：** 右鍵遊戲 exe → 內容 → 相容性 → 變更高 DPI 設定 → 取消勾選「覆寫高 DPI 縮放行為」。

## 常見問題

**防毒軟體報毒。** 這是用 PyInstaller 打包的 Python 程式，常被誤判。完整原始碼在 [`src/`](src/)，可以自行檢查，或直接用 Python 執行（見[從原始碼執行](#從原始碼執行)）。

**出現「The Simplified Chinese patch by acies was not found」。** 請先安裝 acies 的簡體中文漢化。如果之前用其他方式轉過繁體，請先重新安裝簡體中文漢化。

**之前用過 CHT 安裝器 v2.0 或 DC4PH_TextFix。** 直接執行本補丁即可，它取代了這兩個工具，並會沿用已保存的簡體中文備份。

**系統需求。** Windows 10 或 11（使用內建的微軟正黑體 `msjhbd.ttc` / `msjh.ttc`）。

## 從原始碼執行

```bat
pip install -r requirements.txt
python src\dc4_cht_patch.py "C:\遊戲資料夾路徑"
```

參數：`--size N`、`--reinstall`、`--sharp` / `--no-sharp`、`--yes`（全部使用預設值）、`--no-pause`。
`build.bat` 會用 PyInstaller 打包出 `DC4_CHT_Patch.exe`。

<details>
<summary>運作原理</summary>

- **Plus Harmony（Circus 引擎）：** 直接轉換 `Advdata\MES` 裡的腳本。Shift-JIS 裡沒有的字存成私用區編碼，再由生成的字型對應回正確的字。`DC4PHDL.exe` 打兩個補丁：Shift-JIS 修正，以及 hyther1111 的文字修正（[`src/ph_textfix.py`](src/ph_textfix.py)）。文字修正會實際量測每個半形字的寬度（不再用固定的半格），加高字形繪製區讓下緣完整顯示，並在遊戲啟動時從 `FontHook.ini` 讀取 `EngineFontSize`。
- **Sweet Harmony（吉里吉里 Z）：** 用該版本漢化的金鑰逐一解密 `patch.xp3` 裡的腳本，轉換畫面文字後再加密回去。吉里吉里本來就依實際字寬排版，所以文字大小交給漢化附帶的 FontHook（`FontHeightScale1000`）設定，字距也會一起等比例放大。

</details>

## 致謝

- **acies**：本補丁所使用的簡體中文漢化（日文 → 簡體中文）。
  - Plus Harmony：[2DFan](https://2dfan.com/downloads/47006) · [ai2.moe](https://www.ai2.moe/files/file/14897-circusdc4-plus-harmonydeepseek-v41-flash-1017%E7%AB%99%E5%86%85%E5%AD%98%E5%82%A8%E8%A1%A5%E4%B8%81/)
  - Sweet Harmony：[2DFan](https://2dfan.com/downloads/47045) · [ai2.moe](https://www.ai2.moe/files/file/14910-circusdc4-sweet-harmonydeepseek-v41-flash-1017%E7%AB%99%E5%86%85%E5%AD%98%E5%82%A8%E8%A1%A5%E4%B8%81/)
- **[hyther1111](https://github.com/hyther1111)**：*DC4PH_TextFix*，Plus Harmony 的文字修正（半形字重疊、下緣被切、`FontHook.ini` 的 `EngineFontSize`）。也是他發現英文重疊源自之前「文字放大 5%」卻沒有留出字距，並建議把文字大小做成 `FontHook.ini` 的設定。這兩點都已納入本版本。
- **[z0owater](https://github.com/z0owater)**：*DC4_CHT_Installer*，兩款遊戲的繁體轉換與字型。本專案由它和 DC4PH_TextFix 合併而成。
- 使用 [OpenCC](https://github.com/yichen0831/opencc-python)（opencc-python-reimplemented）、[fontTools](https://github.com/fonttools/fonttools) 與 [PyInstaller](https://pyinstaller.org/)。

*D.C.4 Plus Harmony* 與 *D.C.4 Sweet Harmony* © CIRCUS。本專案為非官方同人工具，與 CIRCUS 及漢化者無關。
