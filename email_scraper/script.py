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
    "application": [
        "application received", "thank you for applying", "your application",
        "we have received your application", "application confirmation", "application submitted",
        "applied", "we've received your application", "resume received",
        "job application", "talent acquisition", "we've received your interest",
        "your candidacy", "application status", "applicant tracking",
        "in review", "under consideration", "reviewing your credentials",
        "do not reply", "noreply", "automated response", 
        "under review", "being reviewed", "thank you for your interest",
        "we have received your resume", "your profile", "thank you for submitting",
        "has been submitted", "have submitted", "successfully applied",
        "confirmation number", "candidate id", "application id",
        "thank you for expressing interest", "review process", "initial review"
    ],
    "interview": [
        "interview", "schedule", "meeting", 
        "hiring manager", "technical assessment", "coding challenge",
        "phone screen", "virtual interview", "in-person interview", 
        "technical interview", "screening call", "interview invitation", 
        "meet the team", "video meeting", "zoom interview", 
        "talent assessment", "online assessment", "virtual meeting", 
        "take-home assignment", "behavioral interview", "team interview", 
        "panel interview", "technical screen", "availability", 
        "confirm your time", "reschedule", "calendar invite",
        "preparation", "prepare", "what to expect", 
        "teams meeting", "google meet", "microsoft teams", 
        "webex", "skype", "interview preparation", 
        "interview confirmation", "looking forward to meeting", "chat with",
        "speak with", "talking with", "interview process", 
        "next steps", "follow-up interview", "second round", 
        "final round", "assessment test", "skills assessment", 
        "homework", "case study", "problem solving",
        "meet our team", "conversation", "discussion"
        
    ],
    "offer": [
        "offer letter", "congratulations", "we are pleased to offer",
        "formal offer", "compensation package", "job offer", 
        "welcome to the team", "employment offer", "position offer",
        "benefits package", "employment contract", "salary offer",
        "start date", "we're excited to offer", "offer of employment",      
        "paperwork", "onboarding documents", "sign and return",
        "negotiate", "terms", "compensation discussion", 
        "offer details", "pleased to inform", 
        "pleased to offer", "accept our offer", "offer acceptance", 
        "decision deadline", "formal offer letter", "salary details", 
        "signing bonus", "equity", "stock options", 
        "benefits enrollment", "orientation", "start date", 
        "official offer", "pre-employment", "background check",
        "drug screen", "employment agreement", "new hire", 
        "new employee", "we're delighted", "successful candidacy"
    ],
    "rejection": [
        "we regret to inform you", "not selected",
        "unfortunately", "not moving forward",
        "other candidates", "best of luck", "future opportunities",
        "position has been filled", "moving forward with other candidates", "not a match",
        "we decided to proceed with", "no longer under consideration", "we appreciate your interest",
        "candidate pool", "better suited candidates", "thank you for your time",
        "not proceeding", "competitive pool", "many qualified applicants",
        "closed position", "position is filled", "pursuing other candidates",
        "difficult decision", "not the right fit", "will not be proceeding", 
        "unable to offer", "have decided to move forward", "on this occasion",
        "we have identified", "we have chosen", "after careful consideration",
        "at this time", "application status: closed", "wish you the best",
        "keep your resume on file", "talent pool", "future positions",
        "pursue other opportunities", "not successful", "high volume of applications",
        "keep you in mind", "qualifications did not match", "requirements"
    ],
    "other": []  # only job related emails that dont have an assigned category get defaulted to other
}

JOB_RELATED_KEYWORDS = [
    "job", "career", "position", "employment", "opportunity", "recruiting",
    "recruiter", "talent", "hiring", "hr department", "human resources",
    "application", "apply", "applied", "role", "interview", "resume", 
    "cover letter", "candidate", "recruitment", "employer", "company career",
    "hiring team", "staff", "team member", "onboarding", "work", "vacancy",
    "job search", "job listing", "job posting", "job requisition", "job id",
    "career opportunity", "team", "organization", "join us", "join our team", 
    "senior", "junior", "manager", "associate", "specialist", "intern", "internship",
    "status update", "follow-up", "application status", "consideration",
    "thank you for your interest", "applicant", "qualification", "background check",
    "reference", "profile", "portal", "candidate portal", "salary", "compensation",
    "benefits", "position", "remote work", "remote position", "hybrid", "full-time", 
    "part-time", "contract", "temporary", "permanent", "staffing", "talent acquisition"
]

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
                    subject_lower = subject.lower()
                    combined_text = f"{subject_lower} {snippet}"

                    # check if the email is job-related
                    is_job_related = any(keyword.lower() in combined_text for keyword in JOB_RELATED_KEYWORDS)
                    
                    if is_job_related:
                        label = "other"  # default to "other"
                        for category, keywords in JOB_KEYWORDS.items():
                            if category != "other" and any(keyword.lower() in combined_text for keyword in keywords):
                                label = category
                                break

                        processed_emails.append({
                            'subject': subject,
                            'sender': sender,
                            'received_date': received_date,
                            'label': label,
                            'message_id': msg["id"]
                        })

                except Exception as e:
                    print(f"error processing message {msg['id']}: {e}")
                    continue

            return processed_emails

        except HttpError as error:
            print(f"(+_+) error fetching emails: {error}")
            return []