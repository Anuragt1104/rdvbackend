from django.db import models
from django.contrib.auth.models import User
import uuid

def upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'Users/Profile/profile_photo/{filename}'

class College(models.Model):
    college_id = models.CharField(max_length=10, unique=True)
    college_name = models.CharField(max_length=200)
    college_city = models.CharField(max_length=100)
    college_state = models.CharField(max_length=50)

    def __str__(self):
        return f"{str(self.college_id).zfill(6)} - {self.college_name}"

class Profile(models.Model):
    rdv_id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    user_category_choices = (
        ('E', 'External'),
        ('T', 'Team'),
        ('S', 'IITD Student'),
        ('F', 'IITD Faculty/Staff'),
        ('X', 'Others'),
    )
    user_category = models.CharField(max_length=1, choices=user_category_choices, default='E')
    email = models.EmailField()
    mobile_number = models.CharField(max_length=10, blank=True, null=True)
    college_id = models.IntegerField()
    college_name = models.CharField(max_length=200, blank=True, null=True)
    profile_photo = models.ImageField(upload_to=upload_path, default='images/default.jpg')
    otp = models.CharField(max_length=6, blank=True, null=True)
    isVerified = models.BooleanField(default=False)
    is_ca = models.BooleanField(default=False)
    ca_id = models.CharField(max_length=10, null=True, blank=True)
    instagram_link = models.URLField(max_length=200, null=True, blank=True)
    linkedin_link = models.URLField(max_length=200, null=True, blank=True)
    BlockedFromPronite = models.BooleanField(default=False)

    def __str__(self):
        return self.rdv_id
    
class TeamData(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    vertical = models.CharField(max_length=100)

    def __str__(self):
        return self.name + " - " + self.vertical
    
class FacultyData(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name