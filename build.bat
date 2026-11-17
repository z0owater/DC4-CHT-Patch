@echo off
rem Builds dist\DC4_CHT_Patch.exe (the launcher window).
rem Needs: pip install -r requirements.txt pyinstaller
cd /d "%~dp0"
python -m PyInstaller --onefile --windowed --clean --noconfirm --name DC4_CHT_Patch --icon assets\icon.ico --add-data "assets\icon.png;assets" --collect-data opencc --paths src src\launcher.py
