# Generated by Django 4.2.4 on 2023-09-30 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Users", "0007_merge_20230924_1645"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="college_name",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
