web: gunicorn main:app --workers=2 --threads=3 --worker-class=uvicorn.workers.UvicornWorker
send_scheduled_emails: python app/processes/send_scheduled_emails.py
send_reminder_emails: python app/processes/send_reminder_emails.py
