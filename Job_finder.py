#!/usr/bin/env python3
"""
job_scraper_playwright.py

Requirements:
  pip install playwright beautifulsoup4 pandas openpyxl python-dotenv PyPDF2 python-docx
  python -m playwright install

This script:
 - Extracts basic skills & experience from a PDF/DOCX resume
 - Scrapes Indeed (in.indeed.com) and Naukri using Playwright
 - Filters by simple keyword overlap (no external LLM required)
 - Exports results to an Excel file (openpyxl via pandas)
"""

import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

# Playwright
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("job-scraper")

# -------------------------
# Resume extraction helpers
# -------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(docx_path: str) -> str:
    doc = Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_resume_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(path)
    else:
        raise ValueError("Unsupported resume file format (supported: .pdf, .docx, .doc)")


# Simple keyword-based skill extraction (robust fallback)
DEFAULT_TECH_KEYWORDS = [
    "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
    "scikit-learn", "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "aws", "azure", "gcp", "docker", "kubernetes",
    "react", "node", "django", "flask", "git", "spark", "hadoop", "r", "matlab",
    "java", "c++", "c#", "javascript"
]


def basic_skill_extraction(text: str, keywords: List[str] = DEFAULT_TECH_KEYWORDS) -> List[str]:
    t = text.lower()
    found = []
    for k in keywords:
        if k.lower() in t:
            found.append(k)
    # dedupe & title-case for display
    return sorted(set([s.title() for s in found]))


def basic_experience_extract(text: str, max_chars: int = 1000) -> str:
    lower = text.lower()
    idx = lower.find("experience")
    if idx != -1:
        snippet = text[idx: idx + max_chars]
        return snippet.strip()
    # fallback
    return text[:max_chars].strip() + ("..." if len(text) > max_chars else "")


# -------------------------
# Scraper implementation
# -------------------------
class JobScraper:
    def __init__(self, headless: bool = True, user_agent: Optional[str] = None):
        self.headless = headless
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.jobs: List[dict] = []

    def _parse_jobs_from_html(self, html: str) -> List[dict]:
        soup = BeautifulSoup(html, "html.parser")

        selectors = [
            "div.job_seen_beacon",
            "div.jobCard_mainContent",
            "div.css-1m4cu6j",
            "article.jobsearch-SerpJobCard",
            "div.result",
        ]

        cards = []
        for sel in selectors:
            found = soup.select(sel)
            if found:
                cards = found
                logger.debug(f"Found {len(found)} cards with selector {sel}")
                break

        if not cards:
            anchors = soup.select("a.jcs-JobTitle, a[href*='/rc/clk'], a[href*='/pagead/']")
            logger.debug(f"Fallback anchors found: {len(anchors)}")
            for a in anchors:
                parent = a.find_parent()
                if parent:
                    cards.append(parent)

        results: List[dict] = []
        for card in cards:
            try:
                title = ""
                company = "N/A"
                description = ""
                link = ""

                t = card.select_one("h2.jobTitle span") or card.select_one("h2 span") or card.select_one("a.jcs-JobTitle") or card.select_one("a.jobtitle")
                if t:
                    title = t.get_text(strip=True)

                c = card.select_one("span.companyName") or card.select_one("span.company") or card.select_one("div.company")
                if c:
                    company = c.get_text(strip=True)

                d = card.select_one("div.job-snippet") or card.select_one("div[data-testid='snippet']") or card.select_one("div.summary")
                if d:
                    description = d.get_text(separator=" ", strip=True)

                a = card.select_one("a.jcs-JobTitle") or card.select_one("a[href*='/rc/clk']") or card.select_one("a.jobTitle")
                if a and a.has_attr("href"):
                    href = a["href"]
                    if href.startswith("http"):
                        link = href
                    else:
                        link = "https://in.indeed.com" + href

                if title:
                    results.append({
                        "title": title,
                        "company": company,
                        "description": description,
                        "link": link,
                        "source": "Indeed"
                    })
            except Exception as e:
                logger.debug(f"Card parse error: {e}")
                continue

        return results

    def scrape_indeed(self, job_title: str, location: str, pages: int = 2, max_jobs: Optional[int] = 200) -> List[dict]:
        logger.info(f"Starting Indeed scrape for '{job_title}' in '{location}' (pages={pages})")
        base_url = "https://in.indeed.com/jobs"
        q = job_title.replace(" ", "+")
        l = location.replace(" ", "+")
        params = f"q={q}&l={l}&sort=date"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.user_agent, viewport={"width": 1280, "height": 800})
            page = context.new_page()

            try:
                for page_idx in range(pages):
                    start = page_idx * 10
                    url = f"{base_url}?{params}&start={start}"
                    logger.info(f"Loading page: {url}")
                    try:
                        page.goto(url, timeout=60000)
                    except PlaywrightTimeoutError:
                        logger.warning("Page load timed out, continuing...")

                    # Wait a little for dynamic content
                    try:
                        page.wait_for_timeout(3500)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass

                    html = page.content()
                    found_jobs = self._parse_jobs_from_html(html)
                    logger.info(f"Found {len(found_jobs)} jobs on page {page_idx + 1}")
                    for j in found_jobs:
                        if max_jobs and len(self.jobs) >= max_jobs:
                            break
                        key = (j.get("title", ""), j.get("company", ""), j.get("link", ""))
                        if not any((k.get("title", ""), k.get("company", ""), k.get("link", "")) == key for k in self.jobs):
                            self.jobs.append(j)
                    time.sleep(1.2)

                    if max_jobs and len(self.jobs) >= max_jobs:
                        break

            finally:
                try:
                    context.close()
                    browser.close()
                except Exception:
                    pass

        logger.info(f"Total Indeed jobs scraped (cumulative): {len(self.jobs)}")
        return self.jobs

    def scrape_naukri(self, job_title: str, location: str, pages: int = 1) -> List[dict]:
        """
        Scrape Naukri.com job listings (public search pages).
        Note: Naukri uses many redirect domains and ads; this attempts the public listing pages.
        """
        logger.info(f"Starting Naukri scrape for '{job_title}' in '{location}' (pages={pages})")

        results: List[dict] = []
        # example pattern: https://www.naukri.com/data-scientist-jobs-in-pune
        job_title_clean = job_title.lower().strip().replace(" ", "-")
        location_clean = location.lower().strip().replace(" ", "-")
        base_url = f"https://www.naukri.com/{job_title_clean}-jobs-in-{location_clean}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self.user_agent)
            page = context.new_page()

            try:
                for pg in range(1, pages + 1):
                    url = f"{base_url}-{pg}" if pages > 1 else base_url
                    logger.info(f"Loading Naukri page: {url}")
                    try:
                        page.goto(url, timeout=60000)
                    except PlaywrightTimeoutError:
                        logger.warning("Naukri page load timed out, skipping this page...")
                        continue

                    page.wait_for_timeout(3000)
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    # Typical Naukri job card container
                    job_cards = soup.select("article.jobTuple") or soup.select("div.jobTuple") or soup.select("li.jobTuple")
                    logger.info(f"Naukri: found {len(job_cards)} cards on page {pg}")

                    for card in job_cards:
                        try:
                            title_el = card.select_one("a.title") or card.select_one("a.jobTitle")
                            company_el = (
                                card.select_one("a.subTitle")
                                or card.select_one("span.comp-name")
                                or card.select_one("div.companyInfo span")
                            ) 
                            desc_el = card.select_one("div.job-description") or card.select_one("div.lt")
                            link = ""
                            if title_el and title_el.has_attr("href"):
                                link = title_el["href"]
                            title_text = title_el.get_text(strip=True) if title_el else ""
                            company_text = company_el.get_text(strip=True) if company_el else ""
                            desc_text = desc_el.get_text(separator=" ", strip=True) if desc_el else ""

                            results.append({
                                "title": title_text,
                                "company": company_text,
                                "description": desc_text,
                                "link": link,
                                "source": "Naukri"
                            })
                        except Exception as e:
                            logger.debug(f"Naukri parse error: {e}")
                            continue
                    time.sleep(1.0)
            finally:
                try:
                    context.close()
                    browser.close()
                except Exception:
                    pass

        logger.info(f"Naukri scraped {len(results)} jobs")
        # extend internal job list
        for r in results:
            key = (r.get("title", ""), r.get("company", ""), r.get("link", ""))
            if not any((k.get("title", ""), k.get("company", ""), k.get("link", "")) == key for k in self.jobs):
                self.jobs.append(r)

        return results


# -------------------------
# Simple relevance filter
# -------------------------
def score_job_against_skills(job: dict, skills: List[str]) -> float:
    if not skills:
        return 0.0
    text = (job.get("title", "") + " " + job.get("description", "") + " " + job.get("company", "")).lower()
    matches = 0
    for s in skills:
        if s.lower() in text:
            matches += 1
    return matches / max(1, len(skills))


# -------------------------
# Export to Excel
# -------------------------
def export_jobs_to_excel(jobs: List[dict], out_path: Optional[str] = None) -> str:
    if out_path is None:
        out_path = f"output/job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    rows = []
    for j in jobs:
        rows.append({
            "Job Title": j.get("title"),
            "Company": j.get("company"),
            "Required Skills (matched)": ", ".join(j.get("matched_skills", [])),
            "Relevance Score": f"{j.get('relevance_score', 0):.2f}",
            "Apply Link": j.get("link"),
            "Source": j.get("source", "Unknown")
        })
    df = pd.DataFrame(rows)
    df.to_excel(out_path, index=False, engine="openpyxl")
    logger.info(f"Exported {len(rows)} jobs to {out_path}")
    return out_path


# -------------------------
# CLI-style main
# -------------------------
def main():
    print("=== Job Scraper (Playwright) ===\n")

    resume_dir = Path("resumes")
    resume_dir.mkdir(exist_ok=True)

    resume_files = [p for p in resume_dir.iterdir() if p.suffix.lower() in [".pdf", ".docx", ".doc"]]
    if not resume_files:
        print("No resumes found in './resumes'. Place a PDF or DOCX resume there and re-run.")
        return

    print("Available resumes:")
    for i, p in enumerate(resume_files, 1):
        print(f"{i}. {p.name}")
    while True:
        try:
            choice = int(input(f"Select resume (1-{len(resume_files)}): ").strip())
            if 1 <= choice <= len(resume_files):
                break
        except ValueError:
            pass
        print("Invalid choice. Try again.")
    resume_path = str(resume_files[choice - 1])

    job_title = input("Enter job title to search for (e.g., 'Data Scientist'): ").strip() or "Data Scientist"
    location = input("Enter location (e.g., 'Pune, India' or 'Remote'): ").strip() or "India"
    pages_input = input("Number of pages to scrape (default 2): ").strip()
    try:
        pages = int(pages_input)
    except Exception:
        pages = 2

    # Extract resume info
    print("\nExtracting resume text...")
    try:
        resume_text = extract_resume_text(resume_path)
    except Exception as e:
        logger.error(f"Failed to read resume: {e}")
        return

    skills = basic_skill_extraction(resume_text)
    experience_snippet = basic_experience_extract(resume_text)
    print(f"Auto-extracted skills (sample): {', '.join(skills[:10]) or 'None found'}")

    # Scrape
    scraper = JobScraper(headless=True)
    jobs_indeed = scraper.scrape_indeed(job_title, location, pages=pages)
    jobs_naukri = scraper.scrape_naukri(job_title, location, pages=pages)

    # Merge both job sources (dedup performed in class methods; ensure unique list)
    jobs = scraper.jobs.copy()  # contains combined Indeed+Naukri from the scraper object

    if not jobs:
        print("No jobs found. Try changing job title / location or increase pages.")
        return

    # Score jobs
    for job in jobs:
        score = score_job_against_skills(job, skills)
        job["relevance_score"] = score
        matched = [s for s in skills if s.lower() in (job.get("title", "") + " " + job.get("description", "")).lower()]
        job["matched_skills"] = matched

    # Keep only relevant ones >= 0.2 (tunable)
    MIN_SCORE = 0.005
    relevant = [j for j in jobs if j.get("relevance_score", 0) >= MIN_SCORE]
    relevant.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    if not relevant:
        print("Found jobs, but none matched your skills strongly. Showing all scraped jobs instead.")
        relevant = jobs

    out_file = export_jobs_to_excel(relevant)
    print(f"\n✅ Done. Saved {len(relevant)} job(s) to: {out_file}")
    print("Top matches:")
    for i, j in enumerate(relevant[:10], 1):
        print(f"{i}. {j.get('title')} at {j.get('company')} (score: {j.get('relevance_score', 0):.2f})")


if __name__ == "__main__":
    main()
