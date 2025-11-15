from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading
from gmail_logic import get_unread_messages, move_to_spam, mark_as_read, auto_spam_scan

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# ------------------------------------------------
# Propositional Logic Rules
# ------------------------------------------------
def extract_props(sender, subject, body):
    text = (subject + " " + body).lower()
    sender = (sender or "").lower()

    P1 = "free" in text
    P2 = any(k in text for k in ["win", "winner", "prize", "cash", "lottery"])
    P3 = any(k in text for k in ["http", "www", "click", "verify", "login"])
    P4 = text.count("!!!") > 0
    P5 = not any(domain in sender for domain in [
        "google.com", "linkedin.com", "zomato.com", "bank.com", "company.com", "youtube.com"
    ])
    return P1, P2, P3, P4, P5


def apply_rules(P1, P2, P3, P4, P5):
    rules = []
    if P1 or P2:
        rules.append("R1: (P1 ∨ P2) → SPAM")
        return True, rules
    if P3 and P5:
        rules.append("R2: (P3 ∧ P5) → SPAM")
        return True, rules
    if P4 and P1:
        rules.append("R3: (P4 ∧ P1) → SPAM")
        return True, rules
    rules.append("No spam rules triggered → NOT spam")
    return False, rules


# ------------------------------------------------
# API 1: Classify & Move Spam
# ------------------------------------------------
@app.route("/gmail/spam_check", methods=["GET"])
def gmail_spam_check():
    unread_emails = get_unread_messages(max_count=10)
    results = []

    for email in unread_emails:
        sender, subject, body = email["sender"], email["subject"], email["body"]
        P1, P2, P3, P4, P5 = extract_props(sender, subject, body)
        is_spam, rules = apply_rules(P1, P2, P3, P4, P5)

        if is_spam:
            move_to_spam(email["id"])
            mark_as_read(email["id"])

        results.append({
            "id": email["id"],
            "sender": sender,
            "subject": subject,
            "spam": is_spam,
            "rules_fired": rules
        })
    return jsonify(results)


# ------------------------------------------------
# API 2: Trigger Background Auto Scan
# ------------------------------------------------
@app.route("/gmail/start_auto_scan", methods=["GET"])
def start_auto_scan():
    thread = threading.Thread(target=auto_spam_scan, args=(extract_props, 24))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "Auto-scan started successfully!"})


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(port=8080, debug=True)




from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gmail_logic import (
    classify_email_logic,
    get_unread_messages,
    decode_mime_words
)
import os

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)


# -------------------------
# Root - Serve Frontend
# -------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# -------------------------
# A → Manual Email Classification API
# -------------------------
@app.route("/classify", methods=["POST"])
def classify_email():
    data = request.json

    sender = data.get("sender", "")
    subject = data.get("subject", "")
    body = data.get("body", "")

    result = classify_email_logic(sender, subject, body)

    return jsonify({
        "sender": sender,
        "subject": subject,
        "body": body,
        "spam": result["spam"],
        "rules_fired": result["rules"]
    })


# -------------------------
# B → Gmail Integration API
# -------------------------
@app.route("/gmail/spam_check", methods=["GET"])
def gmail_spam_check():
    try:
        unread_messages = get_unread_messages(max_count=10)
        results = []

        for msg in unread_messages:
            msg_id = msg["id"]
            sender = msg["sender"]
            subject = decode_mime_words(msg["subject"])
            body = msg["snippet"]

            result = classify_email_logic(sender, subject, body)

            results.append({
                "id": msg_id,
                "sender": sender,
                "subject": subject,
                "spam": result["spam"],
                "rules_fired": result["rules"]
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# 404 Fallback
# -------------------------
@app.errorhandler(404)
def not_found(e):
    return send_from_directory("static", "index.html")


# -------------------------
# Render Deployment Port Fix
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))   # Render gives PORT env variable
    app.run(host="0.0.0.0", port=port)



# import os
# import json
# from flask import Flask, request, jsonify, send_from_directory, redirect
# from flask_cors import CORS
# from google_auth_oauthlib.flow import Flow
# from gmail_logic import (
#     classify_email_logic,
#     get_unread_messages
# )

# app = Flask(__name__, static_folder="static", static_url_path="")
# CORS(app)

# os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Allow HTTPS for Render

# CLIENT_SECRETS_FILE = "credentials.json"
# REDIRECT_URI = "https://gmail-spam-filter.onrender.com/oauth2callback"


# # -----------------------------------
# # FRONTEND ROUTE
# # -----------------------------------
# @app.route("/")
# def index():
#     return send_from_directory("static", "index.html")


# # -----------------------------------
# # 1. MANUAL EMAIL CLASSIFICATION
# # -----------------------------------
# @app.route("/classify", methods=["POST"])
# def classify():
#     data = request.json

#     sender = data.get("sender", "")
#     subject = data.get("subject", "")
#     body = data.get("body", "")

#     result = classify_email_logic(sender, subject, body)

#     return jsonify(result)


# # -----------------------------------
# # 2. GOOGLE OAUTH LOGIN
# # -----------------------------------
# @app.route("/login")
# def login():
#     flow = Flow.from_client_secrets_file(
#         CLIENT_SECRETS_FILE,
#         scopes=["https://www.googleapis.com/auth/gmail.readonly"],
#         redirect_uri=REDIRECT_URI,
#     )

#     auth_url, _ = flow.authorization_url(
#         prompt="consent",
#         access_type="offline",
#         include_granted_scopes="true"
#     )

#     return jsonify({"auth_url": auth_url})


# # -----------------------------------
# # 3. OAUTH CALLBACK (GOOGLE → RENDER)
# # -----------------------------------
# @app.route("/oauth2callback")
# def oauth_callback():
#     flow = Flow.from_client_secrets_file(
#         CLIENT_SECRETS_FILE,
#         scopes=["https://www.googleapis.com/auth/gmail.readonly"],
#         redirect_uri=REDIRECT_URI,
#     )

#     flow.fetch_token(authorization_response=request.url)

#     credentials = flow.credentials
#     token_json = credentials.to_json()

#     # Return token to frontend
#     return jsonify({
#         "message": "Gmail login successful!",
#         "token": token_json
#     })


# # -----------------------------------
# # 4. FETCH USER EMAILS WITH TOKEN
# # -----------------------------------
# @app.route("/gmail/spam_check", methods=["POST"])
# def gmail_spam_check():
#     user_token = request.json.get("token", None)

#     if not user_token:
#         return jsonify({"error": "Missing token"}), 400

#     emails = get_unread_messages(user_token, max_count=10)

#     results = []
#     for mail in emails:
#         result = classify_email_logic(
#             mail["sender"],
#             mail["subject"],
#             mail["snippet"],
#         )

#         results.append({
#             "id": mail["id"],
#             "sender": mail["sender"],
#             "subject": mail["subject"],
#             "spam": result["spam"],
#             "rules_fired": result["rules"]
#         })

#     return jsonify(results)


# # -----------------------------------
# # FALLBACK (REACT-LIKE BEHAVIOR)
# # -----------------------------------
# @app.errorhandler(404)
# def not_found(e):
#     return send_from_directory("static", "index.html")


# # -----------------------------------
# # RENDER PORT BINDING
# # -----------------------------------
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)
