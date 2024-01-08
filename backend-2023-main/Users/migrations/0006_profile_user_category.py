# Generated by Django 4.2.4 on 2023-09-19 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0005_alter_profile_profile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='user_category',
            field=models.CharField(choices=[('E', 'External'), ('S', 'IITD Student'), ('F', 'IITD Faculty/Staff'), ('X', 'Sponsor')], default='E', max_length=1),
        ),
    ]