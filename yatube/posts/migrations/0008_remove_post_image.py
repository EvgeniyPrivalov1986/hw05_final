# Generated by Django 2.2.16 on 2022-05-14 10:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_post_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
    ]
