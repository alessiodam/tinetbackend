# Generated by Django 5.0.2 on 2024-03-06 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_userdb'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userdb',
            name='password',
        ),
        migrations.AddField(
            model_name='userdb',
            name='database_password',
            field=models.CharField(max_length=32, null=True, unique=True),
        ),
    ]
