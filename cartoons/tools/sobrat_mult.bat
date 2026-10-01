@echo off
chcp 65001 >nul
rem Собирает мультфильм: заставка + сцены по порядку имён (s01, s02, ...).
rem Положить этот файл в папку с роликами и запустить двойным щелчком.
rem Нужен ffmpeg (ffmpeg.exe и ffprobe.exe в PATH или в этой же папке).
cd /d "%~dp0"
if exist _tmp rmdir /s /q _tmp
mkdir _tmp
set n=100

for /f "delims=" %%F in ('dir /b /on zastavka*.mp4 2^>nul') do call :norm "%%F"
for /f "delims=" %%F in ('dir /b /on s*.mp4 2^>nul') do call :norm "%%F"

ffmpeg -v error -y -f concat -safe 0 -i _tmp\list.txt -c copy "мульт_готовый.mp4"
rmdir /s /q _tmp
echo.
echo Готово: мульт_готовый.mp4
pause
exit /b

:norm
set /a n+=1
set out=_tmp\%n%.mp4
set hasA=
for /f %%A in ('ffprobe -v error -select_streams a -show_entries stream^=index -of csv^=p^=0 "%~1"') do set hasA=1
set VF=scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1
echo Обрабатываю %~1
if defined hasA (
  ffmpeg -v error -y -i "%~1" -vf "%VF%" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 "%out%"
) else (
  ffmpeg -v error -y -i "%~1" -f lavfi -i anullsrc=r=48000:cl=stereo -shortest -map 0:v -map 1:a -vf "%VF%" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac "%out%"
)
echo file '%n%.mp4'>>_tmp\list.txt
exit /b
