@echo off
echo ===================================================
echo EduMaster Platformasini Ishga Tushirish
echo ===================================================

echo 1. Ma'lumotlar bazasi (Backend) ishga tushirilmoqda...
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo 2. O'qituvchi Paneli (Teacher) ishga tushirilmoqda...
start "Teacher Panel" cmd /k "cd teacher && npm run dev"

echo 3. O'quvchi Paneli (Student) ishga tushirilmoqda...
start "Student Panel" cmd /k "cd student && npm run dev"

echo ===================================================
echo Barcha tizimlar ishga tushirildi!
echo Iltimos, ochilgan yangi qora oynalarni yopmang.
echo ===================================================
pause
