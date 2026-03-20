@echo off
echo Building PortDetector...
pyinstaller --onefile --noconsole --name PortDetector --icon assets/icon.ico ^
  --add-data "frontend/templates;frontend/templates" ^
  --add-data "frontend/static;frontend/static" ^
  --add-data "assets;assets" ^
  --hidden-import simple_websocket ^
  --hidden-import engineio.async_drivers.threading ^
  app.py
echo.
echo Build complete! Check dist/PortDetector.exe
pause
