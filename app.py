# from flask import Flask, request, jsonify
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# # ---------------------
# # Propositional Features
# # ---------------------
# def extract_props(sender, subject, body):
#     text = (subject + " " + body).lower()
#     sender = (sender or "").lower()

#     # Propositions
#     P1 = "free" in text
#     P2 = any(k in text for k in ["win", "winner", "prize", "cash", "lottery"])
#     P3 = any(k in text for k in ["http", "www", "click here", "link", "verify"])
#     P4 = text.count("!!!") > 0
#     P5 = sender not in [
#         "boss@company.com",
#         "support@google.com",
#         "billing@bank.com",
#         "mom@family.com"
#     ]

#     return P1, P2, P3, P4, P5


# # ---------------------
# # Inference Rules
# # ---------------------
# def apply_rules(P1, P2, P3, P4, P5):
#     rules_triggered = []

#     # R1: (P1 ∨ P2) → Spam
#     if P1 or P2:
#         rules_triggered.append("R1: P1 OR P2 → Spam")
#         return True, rules_triggered

#     # R2: (P3 ∧ P5) → Spam
#     if P3 and P5:
#         rules_triggered.append("R2: P3 AND P5 → Spam")
#         return True, rules_triggered

#     # R3: (P4 ∧ P1) → Spam
#     if P4 and P1:
#         rules_triggered.append("R3: P4 AND P1 → Spam")
#         return True, rules_triggered

#     # If no rules trigger → Not Spam
#     rules_triggered.append("No spam rules triggered → NOT Spam")
#     return False, rules_triggered


# # ---------------------
# # API Endpoint
# # ---------------------
# @app.route("/classify", methods=["POST"])
# def classify_email():
#     data = request.json
#     sender = data.get("sender", "")
#     subject = data.get("subject", "")
#     body = data.get("body", "")

#     # Extract propositions
#     P1, P2, P3, P4, P5 = extract_props(sender, subject, body)

#     # Apply Inference Rules
#     is_spam, rules = apply_rules(P1, P2, P3, P4, P5)

#     return jsonify({
#         "spam": is_spam,
#         "rules_fired": rules,
#         "propositions": {
#             "P1": P1,
#             "P2": P2,
#             "P3": P3,
#             "P4": P4,
#             "P5": P5
#         }
#     })


# @app.route("/")
# def home():
#     return "Propositional Logic Spam Filter Running!"


# if __name__ == "__main__":
#     app.run(port=8080, debug=True)




# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from gmail_logic import get_unread_messages

# app = Flask(__name__)
# CORS(app)


# # ---------------------
# # Propositional Features
# # ---------------------
# def extract_props(sender, subject, body):
#     text = (subject + " " + body).lower()
#     sender = (sender or "").lower()

#     P1 = "free" in text
#     P2 = any(k in text for k in ["win", "winner", "prize", "cash", "lottery"])
#     P3 = any(k in text for k in ["http", "www", "click", "verify", "login"])
#     P4 = text.count("!!!") > 0
#     P5 = not any(domain in sender for domain in [
#         "google.com", "bank.com", "company.com", "family.com"
#     ])

#     return P1, P2, P3, P4, P5


# # ---------------------
# # Logical Inference Rules
# # ---------------------
# def apply_rules(P1, P2, P3, P4, P5):
#     rules = []

#     if P1 or P2:
#         rules.append("R1: (P1 ∨ P2) → SPAM")
#         return True, rules

#     if P3 and P5:
#         rules.append("R2: (P3 ∧ P5) → SPAM")
#         return True, rules

#     if P4 and P1:
#         rules.append("R3: (P4 ∧ P1) → SPAM")
#         return True, rules

#     rules.append("No spam rules triggered → NOT spam")
#     return False, rules


# # ---------------------
# # API: Classify Single Email
# # ---------------------
# @app.route("/classify", methods=["POST"])
# def classify_email():
#     data = request.json

#     sender = data.get("sender", "")
#     subject = data.get("subject", "")
#     body = data.get("body", "")

#     P1, P2, P3, P4, P5 = extract_props(sender, subject, body)
#     is_spam, rules = apply_rules(P1, P2, P3, P4, P5)

#     return jsonify({
#         "spam": is_spam,
#         "rules_fired": rules,
#         "propositions": {"P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5}
#     })


# # ---------------------
# # API: Gmail Spam Check
# # ---------------------
# @app.route("/gmail/spam_check", methods=["GET"])
# def gmail_spam_check():
#     unread_emails = get_unread_messages(max_count=10)
#     results = []

#     for email in unread_emails:
#         sender = email["sender"]
#         subject = email["subject"]
#         body = email["body"]

#         P1, P2, P3, P4, P5 = extract_props(sender, subject, body)
#         is_spam, rules = apply_rules(P1, P2, P3, P4, P5)

#         results.append({
#             "id": email["id"],
#             "sender": sender,
#             "subject": subject,
#             "spam": is_spam,
#             "rules_fired": rules
#         })

#     return jsonify(results)


# @app.route("/")
# def home():
#     return "Propositional Logic Gmail Spam Filter Running!"


# if __name__ == "__main__":
#     app.run(port=8080, debug=True)




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
