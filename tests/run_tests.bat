@echo off
echo Running Fast Renderer UI Tests...
echo.

cd %~dp0
if not exist node_modules (
    echo Installing dependencies...
    npm install
)

echo.
echo Running tests...
npm test

echo.
if %ERRORLEVEL% EQU 0 (
    echo All tests passed successfully!
) else (
    echo Tests failed with error code %ERRORLEVEL%
)

pause
