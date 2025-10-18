# Location: /imap_email_ingestion_pipeline/test_email_classifier.py
# Purpose: Simple test script for email classification
# Why: Validate 2-tier classifier (whitelist + vector similarity) works correctly
# Relevant Files: email_classifier.py

from email_classifier import classify_email

# Test cases
test_emails = [
    # Investment emails (should be classified as INVESTMENT)
    {
        "subject": "NVDA Q3 Earnings Beat - Upgrade to BUY",
        "body": "Goldman Sachs raises price target to $500 on strong AI demand. Data center revenue up 120% YoY.",
        "sender": "research@example.com",
        "expected": "INVESTMENT"
    },
    {
        "subject": "Daily Market Update",
        "body": "Tech sector rally continues. Semiconductor stocks surge on AI chip demand. NVDA, AMD, TSMC all up >5%.",
        "sender": "analyst@example.com",
        "expected": "INVESTMENT"
    },
    {
        "subject": "Research Report",
        "body": "Portfolio recommendation: Overweight technology sector. Target allocation 35%.",
        "sender": "research@goldmansachs.com",  # Whitelisted domain
        "expected": "INVESTMENT"
    },
    # Non-investment emails (should be classified as NON_INVESTMENT)
    {
        "subject": "Your Amazon Order Has Shipped",
        "body": "Your order #123-456 has been shipped. Track your package here. Estimated delivery: Friday.",
        "sender": "no-reply@amazon.com",
        "expected": "NON_INVESTMENT"
    },
    {
        "subject": "Team Meeting Tomorrow",
        "body": "Reminder: Weekly standup at 10 AM in Conference Room B. Please prepare your updates.",
        "sender": "manager@company.com",
        "expected": "NON_INVESTMENT"
    },
    {
        "subject": "IT Password Reset",
        "body": "Your password expires in 3 days. Click here to reset your password now.",
        "sender": "it@company.com",
        "expected": "NON_INVESTMENT"
    }
]

print("="*60)
print("EMAIL CLASSIFICATION TEST")
print("="*60)

correct = 0
total = len(test_emails)

for i, email in enumerate(test_emails, 1):
    classification, confidence = classify_email(
        subject=email["subject"],
        body=email["body"],
        sender=email["sender"]
    )

    is_correct = classification == email["expected"]
    correct += is_correct

    status = "✅" if is_correct else "❌"

    print(f"\nTest {i}/{total} {status}")
    print(f"Subject: {email['subject'][:50]}...")
    print(f"Sender: {email['sender']}")
    print(f"Expected: {email['expected']}")
    print(f"Got: {classification} (confidence: {confidence:.2f})")

print("\n" + "="*60)
print(f"RESULTS: {correct}/{total} correct ({100*correct/total:.1f}% accuracy)")
print("="*60)
