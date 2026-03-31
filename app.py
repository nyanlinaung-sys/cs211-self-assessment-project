import os
import pandas as pd
import requests
import mysql.connector
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse , RedirectResponse
from fastapi.templating import Jinja2Templates
from logic import load_questions, calculate_results, get_multi_label_prediction, CHAPTER_INSIGHTS
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="4bd2d0080b61c894776d980296eb1b5871405aec5990e65b")

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

CSV_PATH = '/tmp/student_training_data.csv'

PROFESSOR_KEYS = {
    "Taesik Kim": "pass123",
}

FEATURE_COLS = [
    "Basic: loop/ for-each", "Basic: Method/parameter passing", 
    "Basic: If-else/Boolean zen", "Arrays/ArrayList",
    "Classes", "Inheritance/interfaces", 
    "Java Collections Framework -HashSet", "Java Collections Framework -HashMap"
]

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

def send_to_google_sheets(sid, name, score, status, professor, session, quarter, year):
    url = "https://docs.google.com/forms/d/e/1FAIpQLSeJjxjL3WoG6NODAhdFS_RVjdHN3KGsIdag9Y71fxsDytyZAQ/formResponse"
    payload = {
        "entry.2042537524": sid, 
        "entry.1764834092": name,
        "entry.1723464832": str(score), 
        "entry.1434025782": status,
        "entry.1068536601": professor,  
        "entry.2117289351": session,    
        "entry.2104050879": quarter,    
        "entry.360230819": year        
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Sheets Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/quiz", response_class=HTMLResponse)
async def start_quiz(
    request: Request, 
    sid: str = Form(...), 
    name: str = Form(...),
    professor: str = Form(...),
    session: str = Form(...),
    quarter: str = Form(...),
    year: str = Form(...)
):
    sid = sid.strip()
    if not sid.isdigit() or len(sid) != 9:
        return HTMLResponse("<h1>Invalid Student ID. Must be exactly 9 digits.</h1>", status_code=400)
    
    questions = load_questions()
    return templates.TemplateResponse("quiz.html", {
        "request": request, "sid": sid, "name": name, "professor": professor,
        "session": session, "quarter": quarter, "year": year, "questions": questions
    })

@app.post("/submit", response_class=HTMLResponse)
async def handle_submit(
    request: Request, 
    sid: str = Form(...), 
    name: str = Form(...),
    professor: str = Form(...),
    session: str = Form(...),
    quarter: str = Form(...),
    year: str = Form(...)
):
    try:
        sid = sid.strip()
        form_data = await request.form()
        questions = load_questions()
        
        user_answers = []
        for q in questions:
            ans = form_data.get(f"q_{q['id']}")
            user_answers.append(ans if ans else "")
        
        points, feedback, cat_scores, status = calculate_results(user_answers, questions)
        
        # Mapping scores for Database columns (Score out of 5)
        s_map = {
            "loops": cat_scores.get("Basic: loop/ for-each", {}).get('correct', 0),
            "methods": cat_scores.get("Basic: Method/parameter passing", {}).get('correct', 0),
            "logic": cat_scores.get("Basic: If-else/Boolean zen", {}).get('correct', 0),
            "arrays": cat_scores.get("Arrays/ArrayList", {}).get('correct', 0),
            "classes": cat_scores.get("Classes", {}).get('correct', 0),
            "inheritance": cat_scores.get("Inheritance/interfaces", {}).get('correct', 0),
            "hashset": cat_scores.get("Java Collections Framework -HashSet", {}).get('correct', 0),
            "hashmap": cat_scores.get("Java Collections Framework -HashMap", {}).get('correct', 0)
        }

        send_to_google_sheets(sid, name, points, status, professor, session, quarter, year)
        
        # For ML logic (Score out of 10)
        row_data = {cat: cat_scores.get(cat, {'correct': 0})['correct'] * 2 for cat in FEATURE_COLS}
        recommendations = get_multi_label_prediction(row_data)

        detailed_recs = []
        for area in recommendations:
            detailed_recs.append({
                "topic": area,
                "summary": CHAPTER_INSIGHTS.get(area, "Reviewing this topic will help in CS211.")
            })

        # --- DATABASE LOGIC ---
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Updated Table Schema with category columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sid VARCHAR(50), name VARCHAR(255), professor VARCHAR(255),
                    session VARCHAR(50), quarter VARCHAR(50), year VARCHAR(50),
                    score INT, status VARCHAR(50),
                    loops INT, methods INT, logic INT, arrays INT, 
                    classes INT, inheritance INT, hashset INT, hashmap INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            sql = """INSERT INTO assessment_results 
                     (sid, name, professor, session, quarter, year, score, status, 
                      loops, methods, logic, arrays, classes, inheritance, hashset, hashmap) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            cursor.execute(sql, (sid, name, professor, session, quarter, year, points, status,
                                 s_map['loops'], s_map['methods'], s_map['logic'], s_map['arrays'], 
                                 s_map['classes'], s_map['inheritance'], s_map['hashset'], s_map['hashmap']))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as db_e:
            print(f"Database Error: {db_e}")

        # --- ML Training CSV ---
        training_dict = {cat: row_data[cat] for cat in FEATURE_COLS}
        for cat in FEATURE_COLS:
            training_dict[f"T_{cat}"] = 1 if training_dict[cat] < 8 else 0
        pd.DataFrame([training_dict]).to_csv(CSV_PATH, mode='a', index=False, header=not os.path.exists(CSV_PATH))

        return templates.TemplateResponse("result.html", {
            "request": request, "points": points, "status": status, 
            "cat_scores": cat_scores, "recommendations": detailed_recs, "feedback": feedback
        })
        
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error: {e}</h1></body></html>", status_code=500)
    
# THIS SHOWS THE LOGIN PAGE (GET)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# THIS HANDLES THE BUTTON CLICK (POST)
@app.post("/login")
async def login_submit(request: Request, professor: str = Form(...), key: str = Form(...)):
    # Verify the password first
    if professor in PROFESSOR_KEYS and PROFESSOR_KEYS[professor] == key:
        # Save info to the session cookie (hidden from the URL)
        request.session["user"] = professor
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return HTMLResponse(content="<h1>Access Denied</h1>", status_code=403)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Check if the user is logged in via the session
    prof_f = request.session.get("user")
    
    sess_f = request.query_params.get("sess_f")
    qtr_f = request.query_params.get("qtr_f")
    yr_f = request.query_params.get("yr_f")
    
    if not prof_f or prof_f not in PROFESSOR_KEYS:
        return RedirectResponse(url="/login") # Send them back to login if not authorized

    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM assessment_results", conn)
        conn.close()
        df = df.rename(columns={'name': 'Student_Name', 'score': 'Total_Score', 'professor': 'Professor', 'session': 'Session', 'quarter': 'Quarter', 'year': 'Year'})
        
        for col in ['Professor', 'Session', 'Quarter', 'Year']:
            df[col] = df[col].astype(str).str.strip()

        df = df[df['Professor'] == str(prof_f).strip()]

        filters = {
            "sessions": sorted(df['Session'].unique().tolist()),
            "quarters": sorted(df['Quarter'].unique().tolist()),
            "years": sorted(df['Year'].unique().tolist())
        }

        if sess_f: df = df[df['Session'] == str(sess_f).strip()]
        if qtr_f: df = df[df['Quarter'] == str(qtr_f).strip()]
        if yr_f: df = df[df['Year'] == str(yr_f).strip()]

        # Calculation for Chart (Multiply mean by 2 to get score out of 10)
        averages = {
            "Basic: loop/ for-each": round(df['loops'].mean() * 2, 1) if not df.empty else 0,
            "Basic: Method/parameter passing": round(df['methods'].mean() * 2, 1) if not df.empty else 0,
            "Basic: If-else/Boolean zen": round(df['logic'].mean() * 2, 1) if not df.empty else 0,
            "Arrays/ArrayList": round(df['arrays'].mean() * 2, 1) if not df.empty else 0,
            "Classes": round(df['classes'].mean() * 2, 1) if not df.empty else 0,
            "Inheritance/interfaces": round(df['inheritance'].mean() * 2, 1) if not df.empty else 0,
            "Java Collections Framework -HashSet": round(df['hashset'].mean() * 2, 1) if not df.empty else 0,
            "Java Collections Framework -HashMap": round(df['hashmap'].mean() * 2, 1) if not df.empty else 0
        }
        recent_students = df[['Student_Name', 'Total_Score']].tail(5).to_dict('records')
        
        return templates.TemplateResponse("admin.html", {
            "request": request, "filters": filters, "averages": averages, "recent": recent_students,
            "selections": {"prof": prof_f, "sess": sess_f, "qtr": qtr_f, "yr": yr_f},
            "total_students": len(df)
        })
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return HTMLResponse("Error loading dashboard.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)