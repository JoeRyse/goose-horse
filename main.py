import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import time
from datetime import date

# --- PAGE SETUP ---
st.set_page_config(page_title="PaceValue AI", page_icon="🏇", layout="wide")

st.title("🏇 PaceValue AI: Handicapper")
st.markdown("Upload your racing form PDF to extract hidden value.")

# --- 1. AUTHENTICATION ---
# This looks for .streamlit/secrets.toml automatically
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        st.sidebar.success("✅ API Key Loaded")
    else:
        st.error("❌ Missing API Key in .streamlit/secrets.toml")
        st.stop()
except FileNotFoundError:
    st.error("❌ Secrets file not found. Make sure you have .streamlit/secrets.toml")
    st.stop()

# --- 2. CONFIGURATION ---
model_choice = st.sidebar.selectbox(
    "Choose AI Model", 
    ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-3.0-pro-preview"],
    index=0
)

# --- 3. THE BRAIN (Functions) ---
def analyze_uploaded_file(uploaded_file):
    """Sends the PDF bytes directly to Gemini"""
    
    # We need to save the uploaded file temporarily to disk because 
    # the Gemini API upload_file expects a path, not just bytes.
    temp_filename = "temp_race_card.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    status_text = st.empty()
    status_text.info("📤 Uploading PDF to AI Brain...")
    
    try:
        # Upload to Google
        remote_file = genai.upload_file(path=temp_filename, mime_type="application/pdf")
        
        # Wait for processing
        while remote_file.state.name == "PROCESSING":
            status_text.info("⏳ AI is reading the file...")
            time.sleep(2)
            remote_file = genai.get_file(remote_file.name)
            
        status_text.info("🧠 Analyzing Pace & Value... (This takes 30s)")

        # The Prompt
        prompt = """
        You are a professional high-stakes horseplayer. Analyze this entire racing form (PDF).
        Extract data for EVERY horse in the file into a JSON object.
        
        Root object: { "horses": [ ... ] }
        
        Fields per horse:
        - "race_number": Integer
        - "program_number": String
        - "horse_name": String
        - "morning_line": String
        - "jockey": String
        - "running_style": String (E, P, or S)
        - "speed_last": Integer (0 if null)
        - "speed_best_3": Integer (Max of last 3 races)
        - "trouble_notes": String (Short keywords like "Wide", "Blocked", "Stumbled". Empty if none)
        - "value_score": Integer (1-10. 10 = Massive Value)
        - "ai_reasoning": String (Why is this a value bet?)
        """
        
        model = genai.GenerativeModel(model_choice)
        response = model.generate_content(
            [remote_file, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Cleanup
        remote_file.delete()
        status_text.empty() # Clear status
        
        # Parse JSON
        return json.loads(response.text).get("horses", [])

    except Exception as e:
        st.error(f"Analysis Failed: {e}")
        return []

# --- 4. THE INTERFACE ---
uploaded_file = st.file_uploader("Drop your PDF here (DRF, Brisnet, etc.)", type=["pdf"])

if uploaded_file:
    if st.button("🚀 Analyze Race Card"):
        with st.spinner("Handicapping..."):
            race_data = analyze_uploaded_file(uploaded_file)
            
            if race_data:
                # Add Date for Optimizer
                for horse in race_data:
                    horse['date_analyzed'] = date.today().strftime("%Y-%m-%d")
                    horse['source_file'] = uploaded_file.name

                # Show Data
                df = pd.DataFrame(race_data)
                
                st.success(f"Found {len(df)} horses across {df['race_number'].nunique()} races!")
                
                # Highlight High Value Bets
                st.subheader("🔥 Top Value Picks")
                high_value = df[df['value_score'] >= 8]
                st.dataframe(
                    high_value[["race_number", "program_number", "horse_name", "morning_line", "value_score", "ai_reasoning"]],
                    hide_index=True,
                    use_container_width=True
                )

                st.subheader("📋 Full Card Data")
                edited_df = st.data_editor(
                    df, 
                    num_rows="dynamic",
                    use_container_width=True
                )
                
                # Save Button
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "💾 Download CSV for Power BI",
                    csv,
                    "race_data.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.warning("No horses found in the response.")