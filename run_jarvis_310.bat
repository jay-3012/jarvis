@echo off
echo Installing SpeechRecognition...
"C:\Users\vishw\AppData\Local\Programs\Python\Python310\python.exe" -m pip install SpeechRecognition
if %errorlevel% neq 0 (
    echo Installation failed!
    pause
    exit /b %errorlevel%
)
echo Installation successful.
echo Starting Jarvis...
"C:\Users\vishw\AppData\Local\Programs\Python\Python310\python.exe" main.py
pause
