@echo off
chcp 65001 >nul
cd /d "%~dp0"
title URLShortener-Runner

docker info >nul 2>&1
if errorlevel 1 (
    echo [!] Docker Desktop не запущен. Запусти его и повтори.
    pause
    exit /b 1
)

echo [1/4] Останавливаю старые контейнеры (чистый старт)...
docker compose down --remove-orphans >nul 2>&1

echo [2/4] Поднимаю сервисы (Docker Compose)...
docker compose up --build -d

echo [3/4] Жду готовности API...
set /a attempts=0
:wait
set /a attempts+=1
powershell -NoProfile -Command "try{$r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1/health' -TimeoutSec 3; '    попытка %attempts%: HTTP ' + $r.StatusCode; exit 0}catch{'    попытка %attempts%: ОШИБКА ' + $_.Exception.Message; exit 1}"
if not errorlevel 1 goto ready
if %attempts% geq 15 (
    echo [!] API не ответил за 30 секунд. Продолжаю без ожидания...
    goto ready
)
timeout /t 2 /nobreak >nul
goto wait
:ready
start http://127.0.0.1

rem Сторож: скрытый фоновый процесс (не создаёт окон и вкладок)
start "" wscript //b "%~dp0watchdogs.vbs" "%~dp0"

echo [4/4] Готово! Сервис работает.
echo.
echo Остановка: нажми любую клавишу в этом окне ИЛИ просто закрой окно.
pause >nul

docker compose down
echo Сервисы остановлены.
timeout /t 3 >nul