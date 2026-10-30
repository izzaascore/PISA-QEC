@echo off
echo ===================================================
echo EduMaster Platformasini Ishga Tushirish
echo ===================================================

echo 1. Ma'lumotlar bazasi (Backend) ishga tushirilmoqda...
start "Backend Server" /D "%~dp0backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo 2. O'qituvchi Paneli (Teacher) ishga tushirilmoqda...
start "Teacher Panel" /D "%~dp0frontend\teacher" cmd /k "npm run dev"

echo 3. O'quvchi Paneli (Student) ishga tushirilmoqda...
start "Student Panel" /D "%~dp0frontend\student" cmd /k "npm run dev"

echo ===================================================
echo Barcha tizimlar ishga tushirildi!
echo.
echo 1. Backend Server:    http://localhost:8000
echo 2. O'qituvchi Paneli: http://localhost:5173
echo 3. O'quvchi Paneli:   http://localhost:5174
echo.
echo DIQQAT: Oynalar ichiga sichqoncha bilan bosmang!
echo Agar oyna sarlavhasida "Выбрать" (Select) chiqib qolsa,
echo jarayon qotib qoladi. Davom ettirish uchun shu oynada ENTER yoki ESC bosing!
echo.
echo Iltimos, ochilgan yangi qora oynalarni yopmang.
echo ===================================================
pause
