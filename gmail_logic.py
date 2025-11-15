# # gmail_logic.py

# import os
# import base64
# from email import message_from_bytes

# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from dotenv import load_dotenv

# load_dotenv()

# SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# CREDENTIALS_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_JSON", "credentials.json")
# TOKEN_FILE = os.getenv("GMAIL_TOKEN_JSON", "token.json")


# # -------------------------------
# # Gmail Authentication
# # -------------------------------
# def gmail_service():
#     creds = None
    
#     if os.path.exists(TOKEN_FILE):
#         creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
#         creds = flow.run_local_server(port=0)

#         with open(TOKEN_FILE, "w") as token:
#             token.write(creds.to_json())

#     service = build("gmail", "v1", credentials=creds)
#     return service


# # -------------------------------
# # Fetch Gmail Unread Emails
# # -------------------------------
# def get_unread_messages(max_count=10):
#     service = gmail_service()

#     results = service.users().messages().list(
#         userId="me", q="is:unread", maxResults=max_count
#     ).execute()

#     messages = results.get("messages", [])
#     output = []

#     for msg in messages:
#         msg_id = msg["id"]

#         email_data = service.users().messages().get(
#             userId="me", id=msg_id, format="raw"
#         ).execute()

#         raw_email = base64.urlsafe_b64decode(email_data["raw"])
#         parsed = message_from_bytes(raw_email)

#         # Extract headers
#         sender = parsed.get("From", "")
#         subject = parsed.get("Subject", "")

#         # Extract body
#         if parsed.is_multipart():
#             body = ""
#             for part in parsed.walk():
#                 content_type = part.get_content_type()
#                 if content_type == "text/plain":
#                     try:
#                         body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
#                     except:
#                         pass
#         else:
#             body = parsed.get_payload(decode=True).decode("utf-8", errors="ignore")

#         output.append({
#             "id": msg_id,
#             "sender": sender,
#             "subject": subject,
#             "body": body,
#         })

#     return output




# gmail_logic.py

import os
import base64
import time
from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",  # <-- gives move-to-spam & read access
]

CREDENTIALS_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_JSON", "credentials.json")
TOKEN_FILE = os.getenv("GMAIL_TOKEN_JSON", "token.json")


# ------------------------------------------------
# Gmail Authentication
# ------------------------------------------------
def gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


# ------------------------------------------------
# Fetch unread messages
# ------------------------------------------------
def get_unread_messages(max_count=10):
    service = gmail_service()
    results = service.users().messages().list(
        userId="me", q="is:unread", maxResults=max_count
    ).execute()

    messages = results.get("messages", [])
    output = []

    for msg in messages:
        msg_id = msg["id"]

        raw_data = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
        raw_email = base64.urlsafe_b64decode(raw_data["raw"])
        parsed = message_from_bytes(raw_email)

        sender = parsed.get("From", "")
        subject = parsed.get("Subject", "")

        if parsed.is_multipart():
            body = ""
            for part in parsed.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except:
                        pass
        else:
            body = parsed.get_payload(decode=True).decode("utf-8", errors="ignore")

        output.append({
            "id": msg_id,
            "sender": sender,
            "subject": subject,
            "body": body
        })

    return output


# ------------------------------------------------
# Move spam email to Gmail Spam folder
# ------------------------------------------------
def move_to_spam(email_id):
    service = gmail_service()
    try:
        service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]}
        ).execute()
        return True
    except Exception as e:
        print("Error moving to spam:", e)
        return False


# ------------------------------------------------
# Mark email as read
# ------------------------------------------------
def mark_as_read(email_id):
    service = gmail_service()
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ------------------------------------------------
# Automated daily scan
# ------------------------------------------------
def auto_spam_scan(logic_fn, interval_hours=24):
    print("🚀 Auto Spam Scanner started...")
    while True:
        try:
            unread_emails = get_unread_messages(max_count=10)
            for email in unread_emails:
                sender = email["sender"]
                subject = email["subject"]
                body = email["body"]
                P1, P2, P3, P4, P5 = logic_fn(sender, subject, body)
                if (P1 or P2) or (P3 and P5) or (P4 and P1):
                    move_to_spam(email["id"])
                    mark_as_read(email["id"])
                    print(f"📩 Moved to spam: {subject}")
            print("✅ Scan completed. Sleeping...")
        except Exception as e:
            print("Error during auto scan:", e)
        time.sleep(interval_hours * 3600)
