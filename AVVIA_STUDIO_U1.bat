@echo off
title Snapmaker U1 - Studio Parametrico 3D
echo ========================================================
echo   AVVIO SNAPMAKER U1 - 3D PARAMETRIC STUDIO
echo ========================================================
echo.
echo Avvio del server web locale in corso...
echo Una volta avviato, apri il browser all'indirizzo:
echo.
echo    http://localhost:8000
echo.
echo ========================================================
"C:\Users\AirGT\AppData\Local\Programs\Qwen\resources\python\uv.exe" run --with fastapi --with uvicorn --with python-multipart --with matplotlib --with shapely --with trimesh --with mapbox-earcut --with svgpath2mpl python "run_web.py"
pause
