# Automated Job Scraper & Resume Matcher 
Created by Siddharth Gaikwad 

Disclaimer: This project is created strictly for educational and learning purposes. It is not intended for commercial use, production deployment, or to replace any official job platform.

Automated Job Finder & Resume Matcher

Job searching has become increasingly stressful and time-consuming in today’s competitive environment. Candidates usually spend hours uploading resumes to multiple portals, repeating the same searches, and manually checking job descriptions to see whether they match their skills.

To address this problem, I designed and implemented an automated system that extracts skills directly from a user’s PDF or DOCX resume, scrapes relevant job postings from Naukri.com and Indeed.com using Playwright, evaluates each job with a custom relevance score, and generates a ranked list of job opportunities. The results are exported into a clean Excel file for easy viewing and tracking.

This project demonstrates practical applications of automation, web scraping, resume parsing, and rule-based job recommendation techniques using Python.

## Features
- Resume parsing (PDF, DOCX)
- Job scraping using Playwright
- BeautifulSoup HTML parsing
- Skill extraction
- Relevance scoring
- Excel export
- Duplicate job removal
- Fully automated workflow

## Installation
pip install -r requirements.txt
python -m playwright install

## Usage
Place your resume in the /resumes folder:
python src/Job_finder.py

## Output
Generated Excel file containing:
- Job Title
- Company
- Matched Skills
- Score
- Apply Link
- Source

## Tech Stack
Python, Playwright, BeautifulSoup, pandas, PyPDF2, python-docx




