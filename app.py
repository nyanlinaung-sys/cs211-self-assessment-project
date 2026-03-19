import streamlit as st
import pandas as pd
import os
import requests  # Required for Google Sheets sync
from logic import load_questions, calculate_results, get_multi_label_prediction

# --- CONFIGURATION ---
DEV_MODE = True  
# Replace the ID below with your actual Google Form ID
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
    # IMPORTANT: Replace these entry numbers with the ones from your 'Pre-filled link'
    payload = {
        "entry.1111111": sid,    # Student ID
        "entry.2222222": name,   # Student Name
        "entry.3333333": str(score), # Final Score
        "entry.4444444": status  # Status
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Cloud sync failed: {e}")

st.title("CS211 Placement Test")
st.subheader(f"Department of Computer Science, Bellevue College")

# --- UI LOGIC ---

# A. WELCOME SCREEN
if not st.session_state.quiz_started:
    with st.container(border=True):
        st.markdown("### Candidate Registration")
        st.write("Please enter your details to begin the assessment.")
        sid_input = st.text_input("Student ID (8 digits):", placeholder="e.g., 20255500")
        name_input = st.text_input("Full Name:", placeholder="First Last")
        
        if st.button("Start Quiz"):
            if sid_input.strip() and name_input.strip():
                st.session_state.student_id = sid_input
                st.session_state.student_name = name_input
                st.session_state.quiz_started = True
                st.rerun()
            else:
                st.error("Both Student ID and Name are required.")

# B. QUIZ LOGIC
elif not st.session_state.quiz_complete:
    q_index = st.session_state.current_q
    q = questions[q_index]

    st.write(f"Candidate: **{st.session_state.student_name}** ({st.session_state.student_id})")
    st.subheader(f"Question {q_index + 1} of {total_questions}")
    progress_val = q_index / total_questions
    st.progress(progress_val) 

    st.markdown(f"### {q['question']}")
    
    if q.get("image"):
        try:
            st.image(q["image"], caption="Analyze this code snippet", width=400)
        except Exception:
            st.error("Image file not found.")

    # PRE-SELECTION LOGIC
    default_index = None
    if DEV_MODE:
        try:
            default_index = q["options"].index(q["answer"])
        except ValueError:
            default_index = 0

    user_choice = st.radio("Select your answer:", q["options"], index=default_index, key=f"q_{q_index}")
    
    button_label = "Next Question" if q_index < total_questions - 1 else "Finish Quiz"
    
    if st.button(button_label):
        st.session_state.answers.append(user_choice)
        if q_index < total_questions - 1:
            st.session_state.current_q += 1
            st.rerun() 
        else:
            st.session_state.quiz_complete = True
            st.rerun()

# C. RESULTS PAGE
else:
    points, feedback, cat_scores, status = calculate_results(st.session_state.answers, questions) 

    # --- CLOUD SYNC TRIGGER ---
    send_to_google_sheets(st.session_state.student_id, st.session_state.student_name, points, status)

    mapping = {
        'Basic: loop/ for-each': 'loops', 
        'Basic: Method/parameter passing': 'methods', 
        'Basic: If-else/Boolean zen': 'logic', 
        'Arrays/ArrayList': 'data_structs',
        'Classes': 'classes', 
        'Inheritance/interfaces': 'inheritance', 
        'Java Collections Framework -HashSet': 'hashset', 
        'Java Collections Framework -HashMap': 'hashmap'
    }   

    row_data = {mapping[cat]: round((data['correct']/data['total'])*5) for cat, data in cat_scores.items() if cat in mapping}

    with st.spinner("AI is determining focus areas..."):
        recommended_plans = get_multi_label_prediction(row_data)

    # Backup local CSV log (Note: On AWS App Runner, this file is temporary)
    save_data = row_data.copy()
    save_data['student_id'] = st.session_state.student_id
    save_data['name'] = st.session_state.student_name

    df_new_result = pd.DataFrame([save_data])
    csv_file = 'student_training_data.csv'
    file_exists = os.path.exists(csv_file)
    df_new_result.to_csv(csv_file, mode='a', index=False, header=not file_exists)
    
    # --- UI DISPLAY ---
    st.header(f"Final Score: {points} / 80 Points")
    col1, col2 = st.columns([1, 1.2]) 
    
    with col1:
        st.subheader("Results by Category")
        for cat, data in cat_scores.items():
            st.write(f"**{cat}**: {data['correct']} / {data['total']} Correct")
            perc = (data['correct'] / data['total']) if data['total'] > 0 else 0
            st.progress(perc)

    with col2:
        st.subheader("Enrollment Status")
        if status == "Reject":
            st.error("### ❌ Status: REJECT")
            st.warning("You do not currently meet requirements for CS211.")
        else:
            if status == "Pass":
                st.success("### ✅ Status: PASS")
                st.balloons()
            else: 
                st.warning("### ⚠️ Status: ADVICE")
            
            st.write("---")
            st.subheader("AI Optimized Study Plan")
            pretty_names = {
                'loops': 'Iterative Structures', 'methods': 'Parameter Passing',
                'logic': 'Boolean Zen', 'data_structs': 'Arrays/ArrayLists',
                'classes': 'OO Classes', 'inheritance': 'Inheritance',
                'hashset': 'HashSet', 'hashmap': 'HashMap'
            }

            for cat, data in cat_scores.items():
                if data['correct'] < data['total']:
                    plan_id = mapping.get(cat)
                    display_title = pretty_names.get(plan_id, cat) # type: ignore
                    with st.container(border=True):
                        st.markdown(f"**Focus Area: {display_title}**")
                        tip = next((q_obj['tip'] for q_obj in questions if q_obj['category'] == cat), "Review notes.")
                        st.info(f"💡 {tip}")

    if st.button("Restart Quiz"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()