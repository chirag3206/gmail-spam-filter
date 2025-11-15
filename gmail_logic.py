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



import base64
import re
from email import message_from_bytes
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import json

# ---------------------
# Gmail API Scopes
# ---------------------
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


# ---------------------
# Gmail API Service
# ---------------------
def gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service


# ---------------------
# Decode MIME Headers
# ---------------------
def decode_mime_words(s):
    try:
        import email.header
        decoded_fragments = email.header.decode_header(s)
        return ''.join(
            str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else t[0]
            for t in decoded_fragments
        )
    except Exception:
        return s


# ---------------------
# Get Unread Gmail Messages
# ---------------------
def get_unread_messages(max_count=10):
    service = gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])[:max_count]

    unread = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data.get("payload", {}).get("headers", [])
        snippet = msg_data.get("snippet", "")

        sender = subject = "Unknown"
        for h in headers:
            if h["name"] == "From":
                sender = h["value"]
            elif h["name"] == "Subject":
                subject = h["value"]

        unread.append({
            "id": msg['id'],
            "sender": sender,
            "subject": subject,
            "snippet": snippet
        })

    return unread


# ---------------------
# Core Logic Engine (Propositional Logic)
# ---------------------
def classify_email_logic(sender, subject, body):
    """
    Logical rule-based spam filter using propositional logic.
    Returns {spam: True/False, rules: [rules triggered]}.
    """
    subject = subject.lower()
    body = body.lower()
    sender = sender.lower()

    rules_fired = []
    spam = False

    # Proposition Definitions
    P1 = any(word in subject or word in body for word in ["free", "winner", "prize", "offer"])
    P2 = "click here" in body or "claim" in body
    P3 = "job" in subject or "intern" in subject or "hiring" in body
    P4 = sender.endswith("@linkedin.com") or sender.endswith("@jobs.com")
    P5 = any(word in body for word in ["unsubscribe", "promotion", "limited time"])

    # Logical Rules
    # R1: (P1 ∨ P2) → SPAM
    if P1 or P2:
        rules_fired.append("R1: (P1 ∨ P2) → SPAM")
        spam = True

    # R2: (P3 ∧ P5) → SPAM
    elif P3 and P5:
        rules_fired.append("R2: (P3 ∧ P5) → SPAM")
        spam = True

    # R3: (P4 ∧ P5) → SPAM
    elif P4 and P5:
        rules_fired.append("R3: (P4 ∧ P5) → SPAM")
        spam = True

    else:
        rules_fired.append("No spam rules triggered → NOT spam")

    return {"spam": spam, "rules": rules_fired}



# import base64
# import email
# import json
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials


# # -------------------------------
# # Decode MIME
# # -------------------------------
# def decode_mime(s):
#     try:
#         decoded = email.header.decode_header(s)
#         return "".join(
#             part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
#             for part, encoding in decoded
#         )
#     except:
#         return s


# # -------------------------------
# # Gmail API Service (Using Token)
# # -------------------------------
# def gmail_service(token_json):
#     creds = Credentials.from_authorized_user_info(json.loads(token_json))
#     return build("gmail", "v1", credentials=creds)


# # -------------------------------
# # FETCH UNREAD EMAILS
# # -------------------------------
# def get_unread_messages(token_json, max_count=10):
#     service = gmail_service(token_json)

#     results = service.users().messages().list(
#         userId="me",
#         labelIds=["INBOX"],
#         q="is:unread"
#     ).execute()

#     messages = results.get("messages", [])[:max_count]

#     extracted = []

#     for msg in messages:
#         full_msg = service.users().messages().get(
#             userId="me", id=msg["id"]
#         ).execute()

#         headers = full_msg.get("payload", {}).get("headers", [])
#         snippet = full_msg.get("snippet", "")

#         sender = subject = "Unknown"
#         for h in headers:
#             if h["name"].lower() == "from":
#                 sender = h["value"]
#             if h["name"].lower() == "subject":
#                 subject = decode_mime(h["value"])

#         extracted.append({
#             "id": msg["id"],
#             "sender": sender,
#             "subject": subject,
#             "snippet": snippet
#         })

#     return extracted


# # -------------------------------
# # PROPOSITIONAL LOGIC ENGINE
# # -------------------------------
# def classify_email_logic(sender, subject, body):
#     sender = sender.lower()
#     subject = subject.lower()
#     body = body.lower()

#     rules = []
#     spam = False

#     # Propositions
#     P1 = any(k in subject or k in body for k in ["free", "winner", "prize", "offer"])
#     P2 = "click here" in body or "claim" in body
#     P3 = any(k in subject for k in ["job", "intern", "hiring"])
#     P4 = any(sender.endswith(x) for x in ["@linkedin.com", "@jobs.com"])
#     P5 = any(k in body for k in ["unsubscribe", "promotion", "limited time"])

#     # Logical rules
#     if P1 or P2:
#         rules.append("R1: (P1 ∨ P2) → SPAM")
#         spam = True

#     elif P3 and P5:
#         rules.append("R2: (P3 ∧ P5) → SPAM")
#         spam = True

#     elif P4 and P5:
#         rules.append("R3: (P4 ∧ P5) → SPAM")
#         spam = True

#     else:
#         rules.append("No spam rules triggered → NOT spam")

#     return {
#         "spam": spam,
#         "rules": rules
#     }
