import core.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_auto_20220624_0744"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="api_token",
            field=models.TextField(default=core.models._default_api_token, unique=True),
        ),
    ]
