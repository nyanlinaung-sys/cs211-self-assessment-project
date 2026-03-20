import streamlit as st
import pandas as pd
import os
import requests
from logic import load_questions, calculate_results, get_multi_label_prediction

# This helps debug if the app is even reaching this point
print("App is starting up...")

# --- 1. WEB DESIGN (CSS) ---
st.set_page_config(page_title="CS211 Placement Test", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    /* 1. Tighten the Layout */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }

    /* 2. Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 3. Header - Sleek & Smaller */
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 15px; /* Reduced gap */
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* 4. Fix Labels - Bold & Dark Blue */
    label, p, .stMarkdown {
        color: #1E293B !important; 
        font-weight: 700 !important;
        margin-bottom: 2px !important; /* Tightens gap between label and box */
    }
    
    /* Fix the "Candidate Registration" text specifically */
    h3 {
        color: #1E3A8A !important;
        padding-top: 0px !important;
        margin-top: 0px !important;
    }

    /* 5. Input Boxes - Clean & White */
    .stTextInput > div > div > input {
        background-color: white !important;
        color: #1E293B !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }

    /* 6. Tighten the Container */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important; /* This is the magic line that removes the huge gaps */
    }

    /* 7. Modern Button */
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 10px 25px;
        transition: 0.2s;
    }
    
    .stButton>button:hover {
        background-color: #1D4ED8;
        transform: scale(1.02);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURATION ---
DEV_MODE = True  
FORM_ID = "1Yj8KtJ-Nb4Yf856vC5tFXPIc6OXvkrxmzBWVRmCJNzY"

FEATURE_COLS = [
    "Basic: loop/ for-each", 
    "Basic: Method/parameter passing", 
    "Basic: If-else/Boolean zen", 
    "Arrays/ArrayList",
    "Classes", 
    "Inheritance/interfaces", 
    "Java Collections Framework -HashSet", 
    "Java Collections Framework -HashMap"
]
TARGET_COLS = [f"T_{c}" for c in FEATURE_COLS]
ALL_TRAINING_COLS = FEATURE_COLS + TARGET_COLS

if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.current_q = 0 
    st.session_state.answers = []  
    st.session_state.quiz_complete = False
    st.session_state.student_name = ""
    st.session_state.student_id = ""
    st.session_state.data_sent = False 

questions = load_questions()
total_questions = len(questions)

def send_to_google_sheets(sid, name, score, status):
    url = f"https://docs.google.com/forms/d/e/1FAIpQLSeJjxjL3WoG6NODAhdFS_RVjdHN3KGsIdag9Y71fxsDytyZAQ/formResponse"
    payload = {
        "entry.2042537524": sid,    
        "entry.1764834092": name,   
        "entry.1723464832": str(score), 
        "entry.1434025782": status  
    }
    try:
        r = requests.post(url, data=payload, timeout=5)
        return r.status_code == 200
    except:
        return False

# --- UI LOGIC ---
# Using the new Header Class
st.markdown('<div class="main-header"><h1>CS211 Placement Test</h1><p>Department of Computer Science, Bellevue College</p></div>', unsafe_allow_html=True)

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

else:
    points, feedback, cat_scores, status = calculate_results(st.session_state.answers, questions) 

    # 1. Sync to Google
    if not st.session_state.data_sent:
        success = send_to_google_sheets(st.session_state.student_id, st.session_state.student_name, points, status)
        if success:
            st.session_state.data_sent = True
            st.toast("Recorded in Cloud!", icon="✅")

    # 2. AI Prediction
    row_data = {cat: cat_scores.get(cat, {'correct': 0})['correct'] * 2 for cat in FEATURE_COLS}
    with st.spinner("AI analyzing focus areas..."):
        recommended_plans = get_multi_label_prediction(row_data)

    # 3. FIXED: SAVE WITH FORCED COLUMN ORDER
    training_dict = {}
    for cat in FEATURE_COLS:
        score = cat_scores.get(cat, {'correct': 0})['correct'] * 2
        training_dict[cat] = score
        training_dict[f"T_{cat}"] = 1 if score < 8 else 0

    df_training = pd.DataFrame([training_dict], columns=ALL_TRAINING_COLS)
    df_training.to_csv('student_training_data.csv', mode='a', index=False, header=not os.path.exists('student_training_data.csv'))
    
    # 4. UI Display
    st.header(f"Final Score: {points} / 80")
    col1, col2 = st.columns([1, 1.2]) 
    with col1:
        st.subheader("Category Breakdown")
        for cat in FEATURE_COLS:
            data = cat_scores.get(cat, {'correct': 0, 'total': 0})
            st.write(f"**{cat}**: {data['correct']} / {data['total']}")
            st.progress(data['correct'] / data['total'] if data['total'] > 0 else 0)

    with col2:
        st.subheader("Placement Result")
        if status == "Reject":
            st.error("Status: REJECT")
        else:
            st.success(f"Status: {status}")
            st.write("---")
            st.subheader("AI Study Recommendations For CS211")
            for cat in FEATURE_COLS:
                if cat_scores.get(cat, {'correct': 0})['correct'] < cat_scores.get(cat, {'total': 2})['total']:
                    with st.container(border=True):
                        st.markdown(f"**Focus: {cat}**")
                        tip = next((q['tip'] for q in questions if q['category'] == cat), "Review core concepts.")
                        st.info(f"💡 {tip}")

    if st.button("Restart Quiz"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()