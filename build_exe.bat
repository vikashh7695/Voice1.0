@echo off
REM build_exe.bat
REM Packages the voice assistant into a standalone Windows .exe using PyInstaller.
REM Run this from inside your project folder (where main.py lives).

echo Installing PyInstaller if needed...
pip install pyinstaller

echo.
echo Building VoiceAssistant.exe ...
echo.

pyinstaller --onefile --console --name VoiceAssistant ^
    --hidden-import=pyttsx3.drivers ^
    --hidden-import=pyttsx3.drivers.sapi5 ^
    --hidden-import=speech_recognition ^
    --collect-all pywhatkit ^
    --collect-all wikipedia ^
    --collect-all pyaudio ^
    main.py

echo.
echo Done. Your exe is at: dist\VoiceAssistant.exe
echo Double-click it, or run it from cmd, to test.
pause