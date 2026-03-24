import os
import pandas as pd
import requests
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# Import from your logic.py
from logic import load_questions, calculate_results, get_multi_label_prediction

app = FastAPI()

# ROBUST PATHING: This ensures it finds the templates folder on both Mac and AWS
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# AWS-READY PATH: /tmp/ is the only writable directory on App Runner
CSV_PATH = '/tmp/student_training_data.csv'

FEATURE_COLS = [
    "Basic: loop/ for-each", "Basic: Method/parameter passing", 
    "Basic: If-else/Boolean zen", "Arrays/ArrayList",
    "Classes", "Inheritance/interfaces", 
    "Java Collections Framework -HashSet", "Java Collections Framework -HashMap"
]

def send_to_google_sheets(sid, name, score, status):
    """Sends student data to Google Forms/Sheets"""
    url = "https://docs.google.com/forms/d/e/1FAIpQLSeJjxjL3WoG6NODAhdFS_RVjdHN3KGsIdag9Y71fxsDytyZAQ/formResponse"
    payload = {
        "entry.2042537524": sid, 
        "entry.1764834092": name,
        "entry.1723464832": str(score), 
        "entry.1434025782": status  
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Sheets Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/quiz", response_class=HTMLResponse)
async def start_quiz(request: Request, sid: str = Form(...), name: str = Form(...)):
    questions = load_questions()
    return templates.TemplateResponse("quiz.html", {
        "request": request, "sid": sid, "name": name, "questions": questions
    })

@app.post("/submit", response_class=HTMLResponse)
async def handle_submit(request: Request, sid: str = Form(...), name: str = Form(...)):
    try:
        form_data = await request.form()
        questions = load_questions()
        
        # 1. Collect answers
        user_answers = []
        for q in questions:
            # Matches name="q_{{ q.id }}" in your quiz.html
            ans = form_data.get(f"q_{q['id']}")
            user_answers.append(ans if ans else "")
        
        # 2. Run Logic
        points, feedback, cat_scores, status = calculate_results(user_answers, questions)
        
        # 3. External integrations
        send_to_google_sheets(sid, name, points, status)
        
        # 4. AI Recommendation Logic
        row_data = {cat: cat_scores.get(cat, {'correct': 0})['correct'] * 2 for cat in FEATURE_COLS}
        recommendations = get_multi_label_prediction(row_data)

        # 5. Save training data to CSV
        training_dict = {cat: row_data[cat] for cat in FEATURE_COLS}
        for cat in FEATURE_COLS:
            training_dict[f"T_{cat}"] = 1 if training_dict[cat] < 8 else 0
        
        pd.DataFrame([training_dict]).to_csv(CSV_PATH, mode='a', index=False, header=not os.path.exists(CSV_PATH))

        # 6. Show results
        return templates.TemplateResponse("result.html", {
            "request": request, 
            "points": points, 
            "status": status, 
            "cat_scores": cat_scores,
            "recommendations": recommendations,
            "feedback": feedback  # <--- ADD THIS LINE
        })
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return HTMLResponse(content=f"<html><body><h1>Error: {e}</h1><p>Check your terminal logs.</p></body></html>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    # Port 8080 is standard for AWS App Runner
    uvicorn.run(app, host="0.0.0.0", port=8080)