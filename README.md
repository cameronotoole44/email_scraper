# email scraper to enhance job search ᕙ(ಠ_ಠ‶)ᕗ

a Python script that helps you keep track of your job search by automatically organizing emails into categories like applications, interviews, offers, and rejections

- python
- postgreSQL
- Google Cloud & Gmail API to fetch emails
- OAuth2 for secure authentication
- Tkinter for a simple GUI

if you want to use it for your own, just:

1. clone the repo

```bash
git clone [https://github.com/cameronotoole44/email_scraper]
```

2. set up your virtual environment (venv)

```bash
# windows
python -m venv venv
# git bash
python -m venv venv
# linux/mac
python3 -m venv venv
```

3. activate your environment

```bash
# windows
venv\Scripts\activate
# git bash
source venv/Scripts/activate
# linux/mac
source venv/bin/activate
```

4. install the requirements

```bash
pip install -r requirements.txt
```

5. create your .env file with your credentials:

```bash
DB_NAME=your_db_name
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
CLIENT_SECRET_JSON=your_secret
```

6. run the app:

```bash
# windows
python main.py
# git bash
python main.py
# linux/mac
python3 main.py
```

note, make sure you have:

- postgreSQL installed and running
- google cloud project set up with Gmail API enabled
- your google cloud OAuth credentials

happy job hunting! ᕦ( ᴼ ڡ ᴼ )ᕤ
