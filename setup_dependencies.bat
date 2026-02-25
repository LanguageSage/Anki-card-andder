@echo off
setlocal
chcp 65001 >nul
echo ========================================
echo   Установка зависимостей Wordy
echo ========================================
echo.

set "PY_CMD=python"

REM Ищем Python 3.11 как наиболее стабильный
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3.11"
    echo [ИНФО] Использование Python 3.11
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ОШИБКА] Python не найден! Установите Python 3.11+
        pause
        exit /b 1
    )
    echo [ИНФО] Использование Python по умолчанию
)

REM Если .venv существует, но сломано - удаляем
if exist .venv\pyvenv.cfg (
    echo [ИНФО] Проверка виртуального окружения...
    .venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo [ПРЕДУПРЕЖДЕНИЕ] Окружение повреждено. Пересоздаём...
        rmdir /s /q .venv
    )
)

REM Создаём .venv если его нет
if not exist .venv (
    echo [ИНФО] Создание виртуального окружения...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать окружение.
        pause
        exit /b 1
    )
)

echo [ОК] Окружение готово.
echo.

echo [ИНФО] Установка библиотек...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install pyinstaller

echo.
echo ✅ Все зависимости установлены!
echo.
pause
exit /b
