import json
import pandas as pd
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier

# Keep your exact passing logic
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

def load_questions():
    """Standard JSON loader (No Streamlit decorators)"""
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, 'questions.json')
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

def check_passing_status(category_scores):
    all_groups_passed = True
    for group_name, rules in PASSING_CONFIG.items():
        # Calculate points for each category in the group
        group_points = [category_scores.get(cat, {"correct": 0})["correct"] * 2 for cat in rules["categories"]]
        
        # Absolute minimum check (Reject if any category is too low)
        if not all(p >= rules["abs_min"] for p in group_points):
            return "Reject"
            
        # High score check (Must have X number of categories above pass_min)
        high_scores = sum(1 for p in group_points if p >= rules["pass_min"])
        if high_scores < rules["min_pass_count"]:
            all_groups_passed = False 
            
    return "Pass" if all_groups_passed else "Pass with Review"

def calculate_results(user_answers, questions):
    raw_correct = 0
    # We will use this to store which categories didn't get 100%
    needs_review = []
    
    category_scores = {}
    for group in PASSING_CONFIG.values():
        for cat in group["categories"]:
            category_scores[cat] = {"correct": 0, "total": 0}

    for i, q in enumerate(questions):
        cat = q['category']
        if cat in category_scores:
            category_scores[cat]["total"] += 1
            
        if i < len(user_answers) and user_answers[i] == q['answer']:
            raw_correct += 1
            category_scores[cat]["correct"] += 1

    # Logic: If they didn't get the 'total' amount correct, add to review list
    for cat, score in category_scores.items():
        if score["correct"] < score["total"]:
            needs_review.append(cat)
                
    display_points = int(raw_correct * 2)
    status = check_passing_status(category_scores)
    
    # We return needs_review instead of the old feedback list
    return display_points, needs_review, category_scores, status

def get_multi_label_prediction(row_data):
    """Predicts focus areas using ML with your CSV fallback."""
    csv_file = '/tmp/student_training_data.csv'
    feature_cols = list(row_data.keys())
    target_cols = [f"T_{col}" for col in feature_cols]

    try:
        if not os.path.exists(csv_file) or os.path.getsize(csv_file) < 500:
            return [cat for cat, score in row_data.items() if score < 6]
            
        df = pd.read_csv(csv_file)
        if len(df) < 5: 
            return [cat for cat, score in row_data.items() if score < 6]

        X, y = df[feature_cols], df[target_cols]
        model = MultiOutputClassifier(DecisionTreeClassifier(max_depth=5))
        model.fit(X, y) # type: ignore
        
        current_input = pd.DataFrame([row_data])[feature_cols]
        prediction = model.predict(current_input)[0] # type: ignore
        return [feature_cols[i] for i, val in enumerate(prediction) if val == 1]
    except Exception:
        return [cat for cat, score in row_data.items() if score < 6]