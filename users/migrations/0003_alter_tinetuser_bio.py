# Generated by Django 5.0.1 on 2024-02-12 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_tinetuser_bio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tinetuser',
            name='bio',
            field=models.CharField(default='This user doesnt have a bio yet.', max_length=300),
        ),
    ]
