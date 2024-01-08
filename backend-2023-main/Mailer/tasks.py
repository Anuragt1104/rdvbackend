from magic import from_buffer
from celery import shared_task
from .models import Mail
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
import random

def is_email_valid(email):
    if len(email) <= 7:
        return False
    if '@' not in email:
        return False
    if '.' not in email:
        return False
    if email.count('@') > 1:
        return False
    eList = email.split('.')
    if len(eList[-1]) < 2:
        return False
    return True

@shared_task()
def mailerSendMail(id):
    mail = Mail.objects.get(id=id)
    csvFile = mail.data.read().decode('utf-8')
    if '\r\n' in csvFile:
        csvFile = csvFile.split('\r\n')
    else:
        csvFile = csvFile.split('\n')
    csvFile = csvFile[1:]
    nameRequired = "[name]" in mail.message
    logFile = ContentFile(b"", name="logfile.txt")
    if mail.attachment:
        with mail.attachment.open() as f:
            attachment = f.read()
        attachmentType = from_buffer(attachment, mime=True)
        attachmentName = "attachment." + mail.attachment.name.split('.')[-1]
    for row in csvFile:
        row = row.split(',')
        emailAddress = row[0]
        if not is_email_valid(emailAddress):
            mail.failed += 1 ; mail.save()
            logFile.write(f"EMAIL_VALIDATION_FAILED: {emailAddress}\n".encode())
            continue
        name = row[1]
        if not name and nameRequired:
            mail.failed += 1 ; mail.save()
            logFile.write(f"NAME_REQUIRED: {emailAddress}\n".encode())
            continue
        message = mail.message.replace('[name]', name)
        if len(row) == 3:
            message = message.replace('[param1]', row[2])
        if len(row) == 4:
            message = message.replace('[param1]', row[2])
            message = message.replace('[param2]', row[3])
        if len(row) == 5:
            message = message.replace('[param1]', row[2])
            message = message.replace('[param2]', row[3])
            message = message.replace('[param3]', row[4])
        try:
            email = EmailMessage(mail.subject, message, mail.senderId, [emailAddress])
            if mail.attachment:
                email.attach(attachmentName, attachment, attachmentType)
            email.send()
        except:
            mail.failed += 1 ; mail.save()
            logFile.write(f"FAILED_UNKNOWN_ERROR: {emailAddress}\n".encode())
            continue
        mail.success += 1 ; mail.save()
        logFile.write(f"SUCCESS: {emailAddress}\n".encode())
    mail.logFile = logFile
    mail.save()
