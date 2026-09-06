@echo off
REM ============================================================================
REM KisanSetu AI - Application Stopper
REM Stops any running services on ports 8000 (Backend) and 3000 (Frontend)
REM ============================================================================

title KisanSetu AI Stopper

echo ============================================================================
echo   KisanSetu AI - Stopping Running Services
echo ============================================================================
echo.

powershell -NoProfile -Command "$ports = @(8000, 3000); $conns = Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue; if ($conns) { $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($p in $pids) { $proc = Get-Process -Id $p -ErrorAction SilentlyContinue; if ($proc) { Write-Host ('[*] Stopping ' + $proc.ProcessName + ' (PID: ' + $p + ')...'); Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; } }; Write-Host '[OK] Ports 8000 and 3000 are now clear.'; } else { Write-Host '[*] No active services detected on ports 8000 or 3000.'; }"

echo.
ping 127.0.0.1 -n 3 >nul
exit /b 0
