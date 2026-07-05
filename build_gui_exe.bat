@echo off
REM build_gui_exe.bat
REM Packages the chat-window GUI version of the voice assistant into a
REM standalone Windows .exe with no console window.
REM Run this from inside your project folder (where gui.py lives).

echo Installing PyInstaller if needed...
pip install pyinstaller

echo.
echo Building VoiceAssistantGUI.exe ...
echo.

pyinstaller --onefile --windowed --name VoiceAssistantGUI ^
    --hidden-import=pyttsx3.drivers ^
    --hidden-import=pyttsx3.drivers.sapi5 ^
    --hidden-import=speech_recognition ^
    --collect-all webview ^
    --collect-all pywhatkit ^
    --collect-all wikipedia ^
    --collect-all pyaudio ^
    gui.py

echo.
echo Done. Your exe is at: dist\VoiceAssistantGUI.exe
pause