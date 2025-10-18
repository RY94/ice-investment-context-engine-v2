# Location: /updated_architectures/implementation/check_email_attachments.py
# Purpose: Verify if sample .eml files contain attachments
# Why: Determine if AttachmentProcessor integration is needed (Phase 3)
# Relevant Files: data_ingestion.py, ../imap_email_ingestion_pipeline/attachment_processor.py

import email
from pathlib import Path
from collections import defaultdict

def check_attachments_in_emails():
    """
    Scan all .eml files in data/emails_samples/ to check for attachments

    Returns:
        dict: Statistics about attachments found
    """
    emails_dir = Path(__file__).parent.parent.parent / 'data' / 'emails_samples'

    stats = {
        'total_emails': 0,
        'emails_with_attachments': 0,
        'attachment_types': defaultdict(int),
        'total_attachments': 0,
        'sample_files_with_attachments': []
    }

    eml_files = sorted(emails_dir.glob('*.eml'))
    stats['total_emails'] = len(eml_files)

    print(f"Scanning {len(eml_files)} .eml files in {emails_dir}")
    print("=" * 60)

    for eml_file in eml_files:
        with open(eml_file, 'rb') as f:
            msg = email.message_from_binary_file(f)

        # Check for attachments
        attachments = []
        for part in msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == 'multipart':
                continue

            # Check if this is an attachment (has Content-Disposition: attachment)
            content_disposition = part.get('Content-Disposition', '')
            if 'attachment' in content_disposition.lower():
                filename = part.get_filename()
                content_type = part.get_content_type()

                attachments.append({
                    'filename': filename,
                    'content_type': content_type
                })

                stats['total_attachments'] += 1
                stats['attachment_types'][content_type] += 1

        if attachments:
            stats['emails_with_attachments'] += 1
            if len(stats['sample_files_with_attachments']) < 5:
                stats['sample_files_with_attachments'].append({
                    'email': eml_file.name,
                    'attachments': attachments
                })

            print(f"✓ {eml_file.name}: {len(attachments)} attachment(s)")
            for att in attachments:
                print(f"  - {att['filename']} ({att['content_type']})")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total emails scanned: {stats['total_emails']}")
    print(f"Emails with attachments: {stats['emails_with_attachments']}")
    print(f"Total attachments: {stats['total_attachments']}")

    if stats['attachment_types']:
        print(f"\nAttachment types found:")
        for content_type, count in stats['attachment_types'].items():
            print(f"  - {content_type}: {count}")
    else:
        print("\n❌ NO ATTACHMENTS FOUND IN ANY EMAIL")
        print("   → AttachmentProcessor integration NOT needed")
        print("   → .eml files contain email text only")

    return stats

if __name__ == '__main__':
    stats = check_attachments_in_emails()
