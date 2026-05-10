from django.db import migrations, models


def make_trigram_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    schema_editor.execute(
        "CREATE INDEX IF NOT EXISTS posts_caption_trgm_idx "
        "ON posts USING gin (caption gin_trgm_ops);"
    )


def drop_trigram_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_editor.execute("DROP INDEX IF EXISTS posts_caption_trgm_idx;")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["-timestamp"], name="posts_time_idx"),
        ),
        migrations.RunPython(make_trigram_index, drop_trigram_index),
    ]
