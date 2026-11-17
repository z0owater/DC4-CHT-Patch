@echo off
rem Builds dist\DC4_CHT_Patch.exe (needs: pip install -r requirements.txt pyinstaller)
cd /d "%~dp0"
python -m PyInstaller --onefile --console --clean --noconfirm --name DC4_CHT_Patch --collect-data opencc --paths src src\dc4_cht_patch.py
