# Generated by Django 4.2.4 on 2023-08-28 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0002_alter_profile_college_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='isVerified',
            field=models.BooleanField(default=False),
        ),
    ]