# Generated by Django 5.1.2 on 2024-11-02 18:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_chatsession_chatmessage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatsession",
            name="id",
            field=models.UUIDField(editable=False, primary_key=True, serialize=False),
        ),
    ]