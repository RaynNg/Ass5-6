from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalogs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="catalog",
            name="icon",
            field=models.CharField(blank=True, default="📚", max_length=20),
        ),
    ]
