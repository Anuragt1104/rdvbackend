# Generated by Django 4.2.4 on 2023-08-28 14:35

import Users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_profile_isverified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_photo',
            field=models.ImageField(default='static/images/default.jpg', upload_to=Users.models.upload_path),
        ),
    ]
