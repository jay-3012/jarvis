@echo off
REM Install Python dependencies for Jarvis

echo Installing Jarvis dependencies...
"C:\Users\vishw\AppData\Local\Programs\Python\Python310\python.exe" -m pip install --upgrade pip
"C:\Users\vishw\AppData\Local\Programs\Python\Python310\python.exe" -m pip install -r requirements.txt

echo.
echo Installation complete!
pause
