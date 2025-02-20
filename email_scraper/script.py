import os
import pickle
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

JOB_KEYWORDS = {
    "Application": [
        "application received",
        "thank you for applying",
        "your application",
        "we have received your application",
        "application confirmation"
    ],
    "Interview": [
        "interview",
        "schedule",
        "meeting",
        "hiring manager",
        "technical assessment",
        "coding challenge",
        "phone screen"
    ],
    "Offer": [
        "offer letter",
        "congratulations",
        "we are pleased to offer",
        "formal offer",
        "compensation package"
    ],
    "Rejection": [
        "we regret to inform you",
        "not selected",
        "unfortunately",
        "not moving forward",
        "other candidates",
        "best of luck",
        "future opportunities"
    ],
    "Other": []
}

class GmailManager:
    def __init__(self):
        self.service = None

    def authenticate(self):
        try:
            creds = None
            if os.path.exists("token.pickle"):
                with open("token.pickle", "rb") as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    client_secret_json = os.getenv("CLIENT_SECRET_JSON")
                    if not client_secret_json:
                        raise ValueError("CLIENT_SECRET_JSON environment variable not found")
                    
                    client_config = json.loads(client_secret_json)
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=8080)

                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)

            self.service = build("gmail", "v1", credentials=creds)
            return True

        except Exception as e:
            print(f"(+_+) authentication error: {e}")
            return False

    def fetch_emails(self, days=30):
        if not self.service:
            raise ValueError("Not authenticated. Call authenticate() first.")

        try:
            date_after = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            query = f'after:{date_after}'
            
            results = self.service.users().messages().list(
                userId="me",
                maxResults=50,
                q=query
            ).execute()

            messages = results.get("messages", [])
            processed_emails = []

            for msg in messages:
                try:
                    msg_data = self.service.users().messages().get(
                        userId="me", 
                        id=msg["id"]
                    ).execute()

                    headers = msg_data['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                    received_date = datetime.fromtimestamp(int(msg_data['internalDate'])/1000)
                    
                    snippet = msg_data.get("snippet", "").lower()
                    label = "Other"
                    for category, keywords in JOB_KEYWORDS.items():
                        if any(keyword.lower() in snippet for keyword in keywords):
                            label = category
                            break

                    processed_emails.append({
                        'subject': subject,
                        'sender': sender,
                        'received_date': received_date,
                        'label': label
                    })

                except Exception as e:
                    print(f"error processing message {msg['id']}: {e}")
                    continue

            return processed_emails

        except HttpError as error:
            print(f"(+_+) error fetching emails: {error}")
            return []