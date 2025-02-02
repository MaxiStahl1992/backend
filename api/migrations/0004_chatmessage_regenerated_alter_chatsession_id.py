# Generated by Django 5.1.2 on 2024-11-03 19:28

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_alter_chatsession_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="regenerated",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="chatsession",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]
