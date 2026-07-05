@echo off
REM build_tray_exe.bat
REM Packages the tray version of the voice assistant into a standalone
REM Windows .exe with no visible console window.
REM Run this from inside your project folder (where tray.py lives).

echo Installing PyInstaller if needed...
pip install pyinstaller

echo.
echo Building VoiceAssistantTray.exe ...
echo.

pyinstaller --onefile --windowed --name VoiceAssistantTray ^
    --hidden-import=pyttsx3.drivers ^
    --hidden-import=pyttsx3.drivers.sapi5 ^
    --hidden-import=speech_recognition ^
    --hidden-import=pystray._win32 ^
    --collect-all pystray ^
    --collect-all PIL ^
    --collect-all pywhatkit ^
    --collect-all wikipedia ^
    --collect-all pyaudio ^
    tray.py

echo.
echo Done. Your exe is at: dist\VoiceAssistantTray.exe
echo No console window will appear - look for the mic icon in your system tray.
pause