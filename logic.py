import json
import pandas as pd
import os
import streamlit as st
from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier

PASSING_CONFIG = {
    "Group_1_4": {
        "categories": [
            "Basic: loop/ for-each", "Basic: Method/parameter passing", 
            "Basic: If-else/Boolean zen", "Arrays/ArrayList"
        ],
        "abs_min": 4,          
        "pass_min": 6,         
        "min_pass_count": 3    
    },
    "Group_5_6": {
        "categories": ["Classes", "Inheritance/interfaces"],
        "abs_min": 5,          
        "pass_min": 7,         
        "min_pass_count": 1
    },
    "Group_7_8": {
        "categories": ["Java Collections Framework -HashSet", "Java Collections Framework -HashMap"],
        "abs_min": 4,          
        "pass_min": 5,         
        "min_pass_count": 1
    }
}

@st.cache_data
def load_questions():
    """Loads questions with a fallback to prevent app-wide hangs."""
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, 'questions.json')
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing {file_path}")
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        # Returns a dummy question so the UI still loads
        return [{
            "category": "Basic: loop/ for-each", 
            "question": f"Error loading questions. Check logs. ({e})", 
            "options": ["Error"], "answer": "Error", "tip": "Contact Admin"
        }]

def check_passing_status(category_scores):
    all_groups_passed = True
    for group_name, rules in PASSING_CONFIG.items():
        group_points = [category_scores.get(cat, {"correct": 0})["correct"] * 2 for cat in rules["categories"]]
        if not all(p >= rules["abs_min"] for p in group_points):
            return "Reject"
        high_scores = sum(1 for p in group_points if p >= rules["pass_min"])
        if high_scores < rules["min_pass_count"]:
            all_groups_passed = False 
    return "Pass" if all_groups_passed else "Pass with Review"

def calculate_results(user_answers, questions):
    raw_correct = 0
    feedback = []
    category_scores = {cat: {"correct": 0, "total": 0} for group in PASSING_CONFIG.values() for cat in group["categories"]}

    for i, q in enumerate(questions):
        cat = q['category']
        if cat in category_scores:
            category_scores[cat]["total"] += 1
        if i < len(user_answers) and user_answers[i] == q['answer']:
            raw_correct += 1
            category_scores[cat]["correct"] += 1
        else:
            feedback.append({"category": cat, "tip": q['tip']})
                
    display_points = int((raw_correct / len(questions)) * 80)
    status = check_passing_status(category_scores)
    return display_points, feedback, category_scores, status

def get_multi_label_prediction(row_data):
    """Predicts focus areas using ML, with a robust simple fallback."""
    csv_file = '/tmp/student_training_data.csv'
    feature_cols = list(row_data.keys())
    target_cols = [f"T_{col}" for col in feature_cols]

    try:
        # Check if file exists and has enough data (around 5 rows)
        if not os.path.exists(csv_file) or os.path.getsize(csv_file) < 500:
            return [cat for cat, score in row_data.items() if score < 6]
            
        df = pd.read_csv(csv_file)
        if len(df) < 5: 
            return [cat for cat, score in row_data.items() if score < 6]

        X, y = df[feature_cols], df[target_cols]
        model = MultiOutputClassifier(DecisionTreeClassifier(max_depth=5))
        model.fit(X, y)  # type: ignore
        
        current_input = pd.DataFrame([row_data])[feature_cols]
        prediction = model.predict(current_input)[0]  # type: ignore
        return [feature_cols[i] for i, val in enumerate(prediction) if val == 1]
    except Exception:
        # If ML fails for any reason, use logic-based recommendation
        return [cat for cat, score in row_data.items() if score < 6]