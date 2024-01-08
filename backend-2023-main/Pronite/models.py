from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.

class Slot(models.Model):
    pronite_choices = (
        ('S', 'Spectrum'),
        ('K', 'Kaleidoscope'),
        ('M', 'Melange'),
        ('D', 'Dhoom'),
    )
    eligibility_choices = (
        ('E', 'External'),
        ('T', 'Team'),
        ('S', 'IITD Students'),
        ('F', 'IITD Faculty and Staff'),
        ('X', 'Others'),
    )
    eligibility = models.CharField(max_length=1, choices=eligibility_choices, default='E')
    pronite = models.CharField(max_length=1, choices=pronite_choices)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField(default=0)
    booked = models.IntegerField(default=0)
    exhaust_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.pronite + str(self.id)
    
    def save(self, *args, **kwargs):
        if self.booked >= self.capacity:
            self.exhaust_time = timezone.now()
        super(Slot, self).save(*args, **kwargs)
    
class Booking(models.Model):
    user = models.ForeignKey('Users.Profile', on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    ticket_id = models.CharField(max_length=16, unique=True)
    booking_time = models.DateTimeField(auto_now_add=True)
    cancelled = models.BooleanField(default=False)
    admitted = models.BooleanField(default=False)
    admission_time = models.DateTimeField(blank=True, null=True)
    pass_emailed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.rdv_id

class ScanningSchedule(models.Model):
    pronite_choices = (
        ('S', 'Spectrum'),
        ('K', 'Kaleidoscope'),
        ('M', 'Melange'),
        ('D', 'Dhoom'),
    )
    pronite = models.CharField(max_length=1, choices=pronite_choices)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    admissions = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_pronite_display()} Scanning Schedule"
    
class Log(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action + " by " + self.user.username + " at " + str(self.time)