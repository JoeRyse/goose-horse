@echo off
cd %~dp0
echo 🚀 Deploying to GitHub...
git add .
git commit -m "New Race Card Update"
git push origin main
echo ✅ Site is Live!
pause