from django.contrib import admin
from .models import *

admin.site.register([Submission, SubmissionImage, Notification, Message, PointsLedger, Task])