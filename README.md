CS211 Placement Test Project
Bellevue College - Computer Science Department
This is a production-grade web application designed to assess student readiness for the CS211 course. The project utilizes a FastAPI backend to provide a robust, asynchronous architecture for student assessments and real-time instructor analytics.

🚀 Features
Secure Registration: Collects Student ID, Name, and specific course metadata (Professor, Session, Quarter, Year).
Multi-Step Assessment: Interactive quiz covering 8 core Java categories including Loops, OOP, Collections, and Interfaces.
AI Study Recommendations: Utilizes a Multi-Output Decision Tree Classifier to identify mastery gaps and predict focus areas in upcoming CS211 chapters (Recursion, Stacks, Trees, etc.).
Instructor Dashboard: A secured analytics portal where professors can log in to view class averages, filter by quarter/session, and track recent submissions.
Dual-Layer Data Persistence: * Local/Cloud CSV: High-speed data logging for the ML model and Dashboard.
Google Sheets Sync: Automatic backup via Google Forms API to ensure data is never lost, even if the cloud server restarts.

🛠️ Technical Stack
Backend: FastAPI (Python 3.x)
Frontend: Jinja2 Templates, Bootstrap 5, Chart.js
Machine Learning: Scikit-learn (Decision Tree), Pandas
Deployment: AWS App Runner (Containerized)

📊 Instructor Dashboard & Security
The dashboard is protected by a login system defined in app.py. Professors can access filtered analytics specific to their own students.
Login Route: /login
Features: Real-time bar charts of category mastery and a "Recent Submissions" table.
Filtering: Robust filtering logic that handles data type mismatches and case sensitivity for Sessions, Quarters, and Years.

💻 Local Setup
Clone the repository.

Install dependencies:

Bash
pip install -r requirements.txt
Run the application:

Bash
python app.py
Access the app: * Student Quiz: http://localhost:8080/

Instructor Login: http://localhost:8080/login

📦 AWS Deployment Notes (CRITICAL)
This application is configured for AWS App Runner. Because AWS App Runner uses a stateless file system:

Storage: All CSV files are stored in the /tmp/ directory.
Persistence: Files in /tmp/ are deleted when the service restarts.
Recovery: The Google Sheets Backup is the "Source of Truth." If the dashboard appears empty after a deployment, data can be exported from Google Sheets and re-uploaded as dashboard_analytics.csv to restore the charts.
Uvicorn: The app is configured to bind to 0.0.0.0 on port 8080 for AWS compatibility.

Summary of what I updated:
Dashboard Section: Added details about the new /login flow and Chart.js integration.
Data Logic: Explained the Dual-CSV system (one for ML, one for Metadata).
Robustness: Mentioned the new filtering logic that prevents the "0 students found" error.
AWS Instructions: Added a specific warning about the /tmp/ folder so your professor knows why Google Sheets is important.