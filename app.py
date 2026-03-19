import streamlit as st
import pandas as pd
import os
import requests
from logic import load_questions, calculate_results, get_multi_label_prediction

# --- CONFIGURATION ---
DEV_MODE = True  # Set to False before final submission to professor
FORM_ID = "1Yj8KtJ-Nb4Yf856vC5tFXPIc6OXvkrxmzBWVRmCJNzY"

st.set_page_config(page_title="CS211 Placement Test", page_icon="🧠", layout="wide")

# 1. Initialize Session State
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.current_q = 0 
    st.session_state.answers = []  
    st.session_state.quiz_complete = False
    st.session_state.student_name = ""
    st.session_state.student_id = ""

questions = load_questions()
total_questions = len(questions)

# --- CLOUD SYNC FUNCTION ---
def send_to_google_sheets(sid, name, score, status):
    url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
    # !!! IMPORTANT: Replace these entry numbers with your actual Google Form IDs !!!
    payload = {
        "entry.2042537524": sid,    # Student ID ID
        "entry.1764834092": name,   # Name ID
        "entry.1723464832": str(score), # Score ID
        "entry.1434025782": status  # Status ID
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass # Prevents app crash if internet blips

# --- UI LOGIC ---
st.title("CS211 Placement Test")
st.subheader("Department of Computer Science, Bellevue College")

# A. WELCOME SCREEN
if not st.session_state.quiz_started:
    with st.container(border=True):
        st.subheader("Candidate Registration")
        sid_input = st.text_input("Student ID (8 digits):")
        name_input = st.text_input("Full Name:")
        if st.button("Start Assessment"):
            if sid_input.strip() and name_input.strip():
                st.session_state.student_id = sid_input
                st.session_state.student_name = name_input
                st.session_state.quiz_started = True
                st.rerun()
            else:
                st.error("Please enter both ID and Name.")

# B. QUIZ SCREEN
elif not st.session_state.quiz_complete:
    q_index = st.session_state.current_q
    q = questions[q_index]

    st.write(f"Candidate: **{st.session_state.student_name}** ({st.session_state.student_id})")
    st.subheader(f"Question {q_index + 1} of {total_questions}")
    st.progress(q_index / total_questions) 

    st.markdown(f"### {q['question']}")
    
    if q.get("image"):
        try:
            st.image(q["image"], caption="Analyze this code snippet", width=400)
        except:
            st.error("Image file not found.")

    # Auto-select answer if in DEV_MODE
    default_index = q["options"].index(q["answer"]) if DEV_MODE else None

    user_choice = st.radio("Select your answer:", q["options"], index=default_index, key=f"q_{q_index}")
    
    if st.button("Next Question" if q_index < total_questions - 1 else "Finish Quiz"):
        st.session_state.answers.append(user_choice)
        if q_index < total_questions - 1:
            st.session_state.current_q += 1
            st.rerun() 
        else:
            st.session_state.quiz_complete = True
            st.rerun()

# C. RESULTS PAGE
else:
    # 1. Calculate Results using logic.py
    points, feedback, cat_scores, status = calculate_results(st.session_state.answers, questions) 

    # 2. Sync to Google Sheets
    send_to_google_sheets(st.session_state.student_id, st.session_state.student_name, points, status)

    # 3. Prepare data for AI model (Must match logic.py feature_cols exactly)
    # Scales scores to 10-point scale for the AI model
    row_data = {cat: data['correct'] * 2 for cat, data in cat_scores.items()}

    with st.spinner("AI is analyzing study focus areas..."):
        recommended_plans = get_multi_label_prediction(row_data)

    # 4. Save to local CSV (for AI training backup)
    save_data = row_data.copy()
    save_data['student_id'] = st.session_state.student_id
    save_data['student_name'] = st.session_state.student_name
    df_new = pd.DataFrame([save_data])
    df_new.to_csv('student_training_data.csv', mode='a', index=False, header=not os.path.exists('student_training_data.csv'))
    
    # 5. UI DISPLAY
    st.header(f"Final Score: {points} / 80 Points")
    col1, col2 = st.columns([1, 1.2]) 
    
    with col1:
        st.subheader("Results by Category")
        for cat, data in cat_scores.items():
            st.write(f"**{cat}**: {data['correct']} / {data['total']} Correct")
            st.progress(data['correct'] / data['total'] if data['total'] > 0 else 0)

    with col2:
        st.subheader("Enrollment Status")
        if status == "Reject":
            st.error("### ❌ Status: REJECT")
            st.warning("Requirements for CS211 not met.")
        else:
            if status == "Pass":
                st.success("### ✅ Status: PASS")
                st.balloons()
            else: 
                st.warning("### ⚠️ Status: ADVICE")
            
            st.write("---")
            st.subheader("AI Optimized Study Plan")
            # Only show focus areas if user didn't get 100% in that category
            for cat, data in cat_scores.items():
                if data['correct'] < data['total']:
                    with st.container(border=True):
                        st.markdown(f"**Focus Area: {cat}**")
                        tip = next((q_obj['tip'] for q_obj in questions if q_obj['category'] == cat), "Review notes.")
                        st.info(f"💡 {tip}")

    if st.button("Restart Quiz"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()