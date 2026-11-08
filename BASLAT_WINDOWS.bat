@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo OTOMOTIV KAHOOT - CANLI YARISMA
python --version >nul 2>&1
if errorlevel 1 (
 echo Python bulunamadi. Python 3.10+ yukleyin ve PATH secenegini etkinlestirin.
 pause
 exit /b 1
)
echo QR kutuphanesi kontrol ediliyor...
python -m pip install -r requirements.txt
if errorlevel 1 (
 echo Kutuphane yukleme basarisiz.
 pause
 exit /b 1
)
echo.
echo Ogretmen tarayicisinda http://localhost:8000 acin.
echo Telefonlarla ayni Wi-Fi aginda oynamak icin yerel IP adresinizi kullanin.
echo Terminali kapatmayin. Durdurmak icin Ctrl+C.
echo.
python server.py
pause
