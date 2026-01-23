import google.generativeai as genai
import os

# 1. PASTE YOUR NEW KEY INSIDE THE QUOTES BELOW
MY_KEY = "AIzaSyDV4UQHm7pBYo5P2767HvUYAe2EzOsM-VI"

print(f"Testing Key ending in: ...{MY_KEY[-4:]}")

try:
    genai.configure(api_key=MY_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Reply with the word 'Success'")
    print(f"✅ RESULT: {response.text}")
except Exception as e:
    print(f"❌ FAILED: {e}")