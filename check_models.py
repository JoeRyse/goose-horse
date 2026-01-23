import google.generativeai as genai
import os

# Ask user for key at runtime so we don't hardcode it
api_key = input("Paste your API Key here: ").strip() 
genai.configure(api_key=api_key)

print("\n--- AVAILABLE MODELS ---") 
try: 
    for m in genai.list_models(): 
        if 'generateContent' in m.supported_generation_methods: 
            print(f"Name: {m.name}") 
except Exception as e: 
    print(f"Error: {e}") 
print("------------------------\n")
