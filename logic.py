import json
import pandas as pd
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier

# CONFIGURATION: No magic numbers. Each question is worth 2 points.
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
        "categories": [
            "Java Collections Framework -HashSet", 
            "Java Collections Framework -HashMap"
        ],
        "abs_min": 4,          
        "pass_min": 5,         
        "min_pass_count": 1
    }
}

def load_questions():
    # Make sure questions.json is in your root GitHub folder
    with open('questions.json', 'r') as f:
        return json.load(f)

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
    category_scores = {}
    
    for group in PASSING_CONFIG.values():
        for cat in group["categories"]:
            category_scores[cat] = {"correct": 0, "total": 0}

    for i, q in enumerate(questions):
        cat = q['category']
        if cat in category_scores:
            category_scores[cat]["total"] += 1
        
        if i < len(user_answers):
            if user_answers[i] == q['answer']:
                raw_correct += 1
                if cat in category_scores:
                    category_scores[cat]["correct"] += 1
            else:
                feedback.append({"category": cat, "tip": q['tip']})
                
    display_points = int((raw_correct / len(questions)) * 80)
    status = check_passing_status(category_scores)
    
    return display_points, feedback, category_scores, status

def get_multi_label_prediction(row_data):
    # CHANGED: Use /tmp path for AWS compatibility
    csv_file = '/tmp/student_training_data.csv'
    
    feature_cols = [
        "Basic: loop/ for-each", 
        "Basic: Method/parameter passing", 
        "Basic: If-else/Boolean zen", 
        "Arrays/ArrayList",
        "Classes", 
        "Inheritance/interfaces", 
        "Java Collections Framework -HashSet", 
        "Java Collections Framework -HashMap"
    ]
    target_cols = [f"T_{col}" for col in feature_cols]

    try:
        # If the file doesn't exist yet or has no data, use fallback
        if not os.path.exists(csv_file) or os.path.getsize(csv_file) < 100:
            return [cat for cat, score in row_data.items() if score < 6]
            
        df = pd.read_csv(csv_file)
        
        # Need at least 2 rows to train a model safely
        if len(df) < 2:
            return [cat for cat, score in row_data.items() if score < 6]

        X = df[feature_cols]
        y = df[target_cols]

        model = MultiOutputClassifier(DecisionTreeClassifier(criterion='entropy', max_depth=5))
        model.fit(X, y) 

        current_input = pd.DataFrame([row_data])[feature_cols]
        prediction = model.predict(current_input)[0] 
        results = [feature_cols[i] for i, val in enumerate(prediction) if val == 1]
        
        return results if results else ["General Review"]
    except Exception:
        # Fallback logic if ML training fails
        return [cat for cat, score in row_data.items() if score < 6]