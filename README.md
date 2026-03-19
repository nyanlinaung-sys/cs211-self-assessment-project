# CS211 Placement Test Project
### Bellevue College - Computer Science Department

This is a Streamlit-based web application designed to assess student readiness for the CS211 course. It features an automated grading system, AI-driven study recommendations, and real-time cloud synchronization.

## 🚀 Features
* **Registration:** Collects Student ID and Name before starting.
* **Assessment:** Interactive quiz covering Java fundamentals (Loops, OOP, Collections).
* **AI Logic:** Uses a Multi-Output Decision Tree to identify specific focus areas for students.
* **Cloud Sync:** Automatically sends results to a Google Sheet via Google Forms API.
* **Responsive UI:** Built with Streamlit for a clean, professional look.

## 🛠️ Installation & Local Setup
1. Clone the repository.
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate the environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `streamlit run app.py`

## 📦 Deployment
This app is configured for deployment on **AWS App Runner**, linked directly to this GitHub repository.