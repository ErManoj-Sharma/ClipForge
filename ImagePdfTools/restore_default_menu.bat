@echo off
rem Restore Windows 11's default compact right-click menu
rem (undoes the classic-menu tweak that setup.bat applied).
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -Verb RunAs -ArgumentList '-NoProfile','-Command','reg delete \"HKCU\Software\Classes\CLSID\{86ca1e77-a88c-4dc8-a587-e0cb6b5d8fb5}\" /f; Stop-Process -Name explorer -Force'"
