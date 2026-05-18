# Job Monitor 🏥

Automatically checks the job listing twice a day and emails you when a certain new job appears.

Runs entirely on **GitHub Actions** — free forever, no credit card, no server needed.

---

## How it works

1. GitHub runs the script automatically twice a day (or whenever you trigger it manually)
2. Opens the HA Careers page in a headless browser
3. Compares listings to the last run
4. Emails you if any new pharmacist jobs are found

---

## Setup (one-time, ~10 minutes)

### Step 1 — Create a spare Gmail and App Password

> This Gmail is the "sender" — all alerts land in your real inbox.

1. Create a new Gmail account (e.g. `hajobmonitor@gmail.com`)
2. Go to **Security** → turn on **2-Step Verification**
3. Search for **App passwords** → name it `Job Monitor` → click **Generate**
4. Copy the 16-character password shown — you'll need it shortly

---

### Step 2 — Put the files on GitHub

1. Go to [github.com](https://github.com) and sign in (or sign up free)
2. Click **+** → **New repository** → name it `job-monitor` → **Create repository**
3. Click **uploading an existing file** and upload these 3 files:
   - `scraper.py`
   - `requirements.txt`
   - `.github/workflows/monitor.yml` *(make sure to keep the folder structure)*
4. Click **Commit changes**

> **Uploading the workflow file with folders:** On the upload page, you can drag the entire `.github` folder directly — GitHub will preserve the folder structure automatically.

---

### Step 3 — Add your secrets

Your Gmail credentials are stored as **Secrets** — encrypted, never visible to anyone.

1. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add each of these:

| Secret name | Value |
|---|---|
| `GMAIL_USER` | your spare Gmail (e.g. `hajobmonitor@gmail.com`) |
| `GMAIL_PASS` | the 16-char App Password (no spaces) |
| `NOTIFY_EMAIL` | your real Gmail — where alerts are delivered |
| `KEYWORD` | `pharmacist` |

---

### Step 4 — Test it manually

1. In your repo, click the **Actions** tab
2. Click **Job Monitor** on the left
3. Click **Run workflow** → **Run workflow**
4. Watch it run — green tick means success ✅
5. Check your inbox — first run saves all current jobs, won't email you. From then on, new pharmacist jobs trigger an alert.

---

## Schedule

The script runs **twice a day** (every 12 hours). You can change this in `.github/workflows/monitor.yml`:

```yaml
- cron: "0 */12 * * *"   # every 12 hours
- cron: "0 9 * * *"      # once a day at 9am
- cron: "0 9 */2 * *"    # every 2 days at 9am
```

---

## Cost

**Completely free.** GitHub gives you 2,000 free Action minutes per month. This script uses about 15 minutes per month total.
