@echo off
title PSYCHE SIMULACRA — Simulacion nocturna
cd /d "%~dp0"
echo.
echo  ============================================================
echo   PSYCHE SIMULACRA — Iniciando simulacion nocturna
echo   Stop automatico a las 04:00
echo  ============================================================
echo.
python scripts\run_overnight.py
echo.
echo  [FIN] Simulacion completada.
pause
