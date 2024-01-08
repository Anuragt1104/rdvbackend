from django.db import models
import uuid

def upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'Events/Event/poster/{filename}'

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def get_count(self):
        return Event.objects.filter(tags__name=self.name).count()

    def __str__(self):
        return self.name
    
class Event(models.Model):
    name = models.CharField(max_length=255)
    poster = models.ImageField(upload_to=upload_path, blank=True, null=True)
    description = models.TextField()
    prizes = models.TextField()
    tags = models.ManyToManyField(Tag)
    type = models.CharField(max_length=40, choices=[('Competitive', 'Competitive'), ('Non-Competitive', 'Non-Competitive')])
    location = models.CharField(max_length=255)
    application_deadline = models.DateField()
    event_date_time = models.DateTimeField()
    team_size = models.CharField(max_length=20)
    registration_link = models.URLField()
    rulebook_link = models.URLField()

    def tag_list(self):
        return ", ".join([str(p) for p in self.tags.all()])

    def __str__(self):
        return self.name