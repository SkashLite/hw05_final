# Generated by Django 2.2.16 on 2022-11-15 15:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20221026_1909'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Comment',
        ),
    ]