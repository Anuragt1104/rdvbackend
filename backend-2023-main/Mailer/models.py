from django.db import models
import uuid
from django.contrib.auth.models import User

# Create your models here.

def generate_random_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"Mailer/Mail/data/{filename}"

def generate_logfile_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"Mailer/Mail/logs/{filename}"

def generate_attachment_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"Mailer/Mail/attachments/{filename}"

class Mail(models.Model):
    createdBy = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    senderId = models.CharField(default="Rendezvous IIT Delhi <noreply@rendezvousiitd.com>")
    attachment = models.FileField(upload_to=generate_attachment_name, blank=True, null=True)
    mailCount = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    success = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    data = models.FileField(upload_to=generate_random_filename, blank=True, null=True)
    logFile = models.FileField(upload_to=generate_logfile_name, blank=True, null=True)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.mailCount} Emails sent by {self.createdBy.username} with subject {self.subject}"