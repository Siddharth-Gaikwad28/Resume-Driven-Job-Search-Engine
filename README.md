# Automated Job Scraper & Resume Matcher

**Author:** Siddharth Gaikwad
**Project Type:** Educational / Portfolio Project
**Domain:** Automation, Web Scraping, Resume Parsing, Job Recommendation

---

## 📌 Overview

The **Automated Job Scraper & Resume Matcher** is a Python-based automation project designed to simplify and optimize the job search process. Instead of manually browsing multiple job portals and checking skill compatibility, this system automatically:

* Extracts skills from a candidate’s resume
* Scrapes relevant job listings from major job portals
* Evaluates how well each job matches the resume
* Produces a ranked list of opportunities in Excel format

This project demonstrates real-world applications of **web automation, resume parsing, and rule-based recommendation systems**, making it ideal for showcasing practical Python skills to recruiters.

---

## ⚠️ Disclaimer

> This project is created **strictly for educational and learning purposes**.
> It is **not intended for commercial use, production deployment**, or to violate the terms of service of any job platform.

---

## 🚀 Key Features

* 📄 **Resume Parsing**

  * Supports **PDF** and **DOCX** resumes
  * Automatically extracts text and skills

* 🤖 **Automated Job Scraping**

  * Scrapes job listings from:

    * Naukri.com
    * Indeed.com
  * Uses **Playwright** for dynamic content handling

* 🧠 **Skill Matching & Scoring**

  * Extracts skills from job descriptions
  * Computes a **custom relevance score** for each job

* 📊 **Excel Export**

  * Clean, structured Excel output
  * Easy to filter, sort, and track applications

* 🔁 **Duplicate Job Removal**

  * Ensures unique job listings across platforms

* ⚙️ **Fully Automated Workflow**

  * Minimal manual intervention required

---

## 🏗️ Project Workflow

1. User places resume in the `/resumes` folder
2. Resume text and skills are extracted
3. Job portals are scraped automatically
4. Job descriptions are parsed and analyzed
5. Skills are matched against the resume
6. Jobs are ranked using a relevance score
7. Final results are exported to an Excel file

---

## 🛠️ Tech Stack

* **Language:** Python
* **Web Automation:** Playwright
* **HTML Parsing:** BeautifulSoup
* **Data Processing:** pandas
* **Resume Parsing:** PyPDF2, python-docx
* **Output Format:** Excel (.xlsx)

---

## 📂 Project Structure

```
├── resumes/
│   └── your_resume.pdf
├── output/
│   └── matched_jobs.xlsx
├── Job_finder.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

1. Clone the repository:

   ```
   git clone https://github.com/your-username/automated-job-scraper.git
   cd automated-job-scraper
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:

   ```
   python -m playwright install
   ```

---

## ▶️ Usage

1. Place your resume inside the `/resumes` folder
2. Run the main script:

   ```
   python Job_finder.py
   ```
3. Wait for the scraping and matching process to complete

---

## 📈 Output

An Excel file is generated containing the following columns:

* **Job Title**
* **Company Name**
* **Matched Skills**
* **Relevance Score**
* **Apply Link**
* **Source (Naukri / Indeed)**

---

## 🎯 Learning Outcomes

This project showcases:

* Practical web scraping using Playwright
* Resume parsing from real-world file formats
* Rule-based recommendation logic
* Automation pipeline design
* Clean data export for decision-making

---

## 🔮 Future Improvements

* NLP-based semantic skill matching
* Location and experience filtering
* Email notifications for top matches
* Support for additional job platforms
* Streamlit or web-based UI

---

## 📬 Contact

If you’d like to discuss this project or explore improvements:

**Siddharth Gaikwad**
📧 Email: gaikwadsiddharth028@gmail.com

---

⭐ *If you found this project useful, consider starring the repository!*
