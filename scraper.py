import os
import json
import time
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from playwright.sync_api import sync_playwright

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
URL          = "https://www3.ha.org.hk/career/?lang=en&category=alliedhealth"
GMAIL_USER   = os.environ["GMAIL_USER"]
GMAIL_PASS   = os.environ["GMAIL_PASS"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]
KEYWORD      = os.environ.get("KEYWORD", "").strip().lower()
STATE_FILE   = "seen_jobs.json"

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_seen_jobs() -> set:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(jobs: set) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(list(jobs), f, indent=2)


def fetch_jobs() -> list[dict]:
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        log.info("Loading %s …", URL)
        page.goto(URL, wait_until="networkidle", timeout=60_000)

        # Wait for table rows with actual data (td elements inside the table)
        log.info("Waiting for job rows to appear…")
        try:
            page.wait_for_selector("table td", timeout=30_000)
        except Exception:
            log.warning("Timed out waiting for table rows — page may be empty")

        # Extra buffer to let JS finish rendering
        time.sleep(3)

        # Log raw HTML around the table for debugging
        table_html = page.inner_html("table") if page.query_selector("table") else "NO TABLE FOUND"
        log.info("Table HTML (first 500 chars): %s", table_html[:500])

        rows = page.query_selector_all("table tr")
        log.info("Found %d table rows total", len(rows))

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) < 7:
                continue
            job = {
                "issue_date":   cells[1].inner_text().strip(),
                "vnc_no":       cells[2].inner_text().strip(),
                "post":         cells[3].inner_text().strip(),
                "closing_date": cells[4].inner_text().strip(),
                "staff_group":  cells[5].inner_text().strip(),
                "cluster":      cells[6].inner_text().strip(),
            }
            link_el = cells[3].query_selector("a")
            job["url"] = link_el.get_attribute("href") if link_el else URL
            if job["url"] and not job["url"].startswith("http"):
                job["url"] = "https://www3.ha.org.hk" + job["url"]
            log.info("Found job: %s", job["post"])
            jobs.append(job)

        browser.close()
    log.info("Fetched %d jobs from page.", len(jobs))
    return jobs


def matches_keyword(job: dict) -> bool:
    if not KEYWORD:
        return True
    return KEYWORD in job["post"].lower()


def send_email(new_jobs: list[dict]) -> None:
    subject = f"[HA Careers] {len(new_jobs)} new job(s) posted!"

    lines = [f"New job posting(s) on HA Careers ({datetime.now().strftime('%Y-%m-%d %H:%M')}):\n"]
    for j in new_jobs:
        lines.append(f"• {j['post']}")
        lines.append(f"  VNC No:  {j['vnc_no']}")
        lines.append(f"  Cluster: {j['cluster']}")
        lines.append(f"  Closes:  {j['closing_date']}")
        lines.append(f"  Link:    {j['url']}\n")
    lines.append("—\nThis alert was sent by your HA Job Monitor.")
    text_body = "\n".join(lines)

    rows_html = ""
    for j in new_jobs:
        rows_html += f"""
        <tr>
          <td style="padding:8px;border:1px solid #ddd;">{j['post']}</td>
          <td style="padding:8px;border:1px solid #ddd;">{j['vnc_no']}</td>
          <td style="padding:8px;border:1px solid #ddd;">{j['cluster']}</td>
          <td style="padding:8px;border:1px solid #ddd;">{j['closing_date']}</td>
          <td style="padding:8px;border:1px solid #ddd;"><a href="{j['url']}">View</a></td>
        </tr>"""
    html_body = f"""
    <html><body>
      <h2 style="color:#0056b3;">New HA Careers Posting(s)</h2>
      <p>Checked at {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
      <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px;">
        <tr style="background:#0056b3;color:#fff;">
          <th style="padding:8px;">Post</th>
          <th style="padding:8px;">VNC No</th>
          <th style="padding:8px;">Cluster</th>
          <th style="padding:8px;">Closing Date</th>
          <th style="padding:8px;">Link</th>
        </tr>
        {rows_html}
      </table>
      <p style="color:#888;font-size:12px;">Sent by your HA Job Monitor</p>
    </body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
    log.info("Email sent to %s.", NOTIFY_EMAIL)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    seen = load_seen_jobs()
    jobs = fetch_jobs()

    new_jobs = []
    for job in jobs:
        job_id = job["vnc_no"] or f"{job['post']}|{job['issue_date']}"
        if job_id and job_id not in seen and matches_keyword(job):
            new_jobs.append(job)
            seen.add(job_id)

    if new_jobs:
        log.info("Found %d new job(s). Sending email…", len(new_jobs))
        send_email(new_jobs)
    else:
        log.info("No new jobs found.")

    save_seen_jobs(seen)


if __name__ == "__main__":
    main()
