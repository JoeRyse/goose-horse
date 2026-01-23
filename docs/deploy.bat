@echo off
cd /d "C:\Users\joery\OneDrive\Desktop\RacingAI\world-handicapper"
echo 🚀 Deploying to GitHub...
git add .
git commit -m "Daily Update: %date%"
git push origin main
echo ✅ Site is Live!
timeout /t 5