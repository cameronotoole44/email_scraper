# Email scraper to enhance job search ᕙ(ಠ_ಠ‶)ᕗ

A Python tool that helps you track your job applications by automatically organizing emails into categories like **applications**, **interviews**, **offers**, and **rejections** with built-in search, filtering, and stats

### Tech used

- Python
- PostgreSQL
- Gmail API (Google Cloud)
- OAuth2 authentication
- Tkinter for the GUI

---

## Version 2.0

Major improvements in usability and data orginization

### What's new?

- **search bar** quickly find emails by subject or sender
- **label filter** show only applications, only interviews, only offers, etc.
- **pipeline stats** view your job funnel:
  - applications → interviews → offers
  - includes response rate and offer rate
- improved duplicate detection (now uses Gmail `message_id`)
- cleaner UI layout + better statistics panel

If you want to use it for your own, just:

1. Clone the repo

```bash
git clone [https://github.com/cameronotoole44/email_scraper]
```

2. Set up your virtual environment (venv)

```bash
# windows
python -m venv venv
# git bash
python -m venv venv
# linux/mac
python3 -m venv venv
```

3. Activate your environment

```bash
# windows
venv\Scripts\activate
# git bash
source venv/Scripts/activate
# linux/mac
source venv/bin/activate
```

4. Install the requirements

```bash
pip install -r requirements.txt
```

5. Create your .env file with your credentials:

```bash
DB_NAME=your_db_name
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
CLIENT_SECRET_JSON=your_secret
```

6. Run the app:

```bash
# windows
python main.py
# git bash
python main.py
# linux/mac
python3 main.py
```

Note, make sure you have:

- PostgreSQL installed and running
- Google Cloud project set up with Gmail API enabled
- Your google cloud OAuth credentials

Happy job hunting! ᕦ( ᴼ ڡ ᴼ )ᕤ
