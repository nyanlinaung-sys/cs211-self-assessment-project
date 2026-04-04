# CS211 Self-Assessment Project
### Bellevue College - Computer Science Department

This is a production-grade web application designed to assess student readiness for the CS211 course. The project utilizes a **FastAPI** backend and an **AWS RDS (MySQL)** database to provide a robust, persistent architecture for student assessments and real-time instructor analytics.

## 🚀 Features
* **Secure Registration:** Collects Student ID, Name, and specific course metadata with an integrated **Welcome Modal** for student instructions.
* **Data Validation:** Strict **9-digit numeric validation** for Student IDs (Frontend & Backend) to ensure data integrity and prevent SQL errors.
* **Multi-Step Assessment:** Interactive quiz covering 8 core Java categories including Loops, OOP, Collections, and Interfaces.
* **AI Study Recommendations:** Utilizes a **Multi-Output Decision Tree Classifier** to identify mastery gaps. The model trains dynamically using historical data stored in the RDS instance.
* **Instructor Dashboard:** A secured analytics portal for professors to view class averages, filter by quarter/session, and track recent submissions.
* **Cloud Persistence:** * **AWS RDS (MySQL):** Permanent storage for all student attempts and metadata.
    * **Google Sheets Sync:** Secondary automatic backup via Google Forms API for redundancy.

## 🛠️ Technical Stack
* **Backend:** FastAPI (Python 3.x), Uvicorn
* **Database:** AWS RDS (MySQL)
* **Frontend:** Jinja2 Templates, Bootstrap 5, JavaScript (Modals & Pattern Validation)
* **Machine Learning:** Scikit-learn (Decision Tree), Pandas
* **Deployment:** AWS App Runner (Containerized)

## 📊 Instructor Dashboard & Security
The dashboard is protected by a login system defined in `app.py`. Professors can access filtered analytics specific to their own students.
* **Login Route:** `/login`
* **Features:** Real-time calculation of category mastery and a "Recent Submissions" table.
* **Filtering:** Robust filtering logic for Sessions, Quarters, and Years that handles data stripping and case sensitivity.

## 💻 Local Setup
1.  **Clone the repository.**
2.  **Configure Environment Variables:**
    Set `DB_HOST`, `DB_USER`, `DB_PASS`, and `DB_NAME` in your local environment.
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python app.py
    ```

## 📦 AWS Deployment Notes (CRITICAL)
This application is optimized for **AWS App Runner**.
* **Inbound Rules:** Ensure the RDS Security Group allows inbound traffic on **Port 3306** from the App Runner service.
* **Statelessness:** While the `/tmp/` directory is used for temporary ML training files, the **RDS Database** serves as the primary source of truth for all persistent data.
* **Environment Variables:** All `DB_` variables must be explicitly defined in the App Runner service configuration to allow the application to connect to the MySQL instance.

---
*Developed for the Bellevue College Computer Science Department Placement Assessment Program.*