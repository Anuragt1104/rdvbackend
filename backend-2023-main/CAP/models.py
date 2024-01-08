from django.db import models
from Users.models import Profile
from django.contrib.auth.models import User
import uuid

def upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'CAP/SubmissionImage/image/{filename}'

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    points = models.IntegerField()
    deadline = models.DateTimeField()
    multiple_uploads_allowed = models.BooleanField()

    def __str__(self):
        return f"{self.title}"

class Submission(models.Model):
    PLATFORM_CHOICES = [
        ('WP', 'WhatsApp'),
        ('IG', 'Instagram'),
        ('FB', 'Facebook'),
        ('LB', 'LinkedIn'),
        ('OT', 'Others'),
    ]

    STATUS_CHOICES = [
        ('AP', 'Approved'),
        ('RJ', 'Rejected'),
        ('UR', 'Under Review'),
    ]

    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    datetime_of_submission = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True)
    platform_category = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UR')
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.ca_id} | {self.status}"

class SubmissionImage(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=upload_path)

    def __str__(self):
        return f"{self.submission.user.ca_id} | {self.submission.status} | {self.submission.id}"

class Notification(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    points = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.subject}"

class Message(models.Model):
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    datetime_of_sending = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"

class PointsLedger(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    points = models.IntegerField()

    def __str__(self):
        return f"{self.user.ca_id}"