from django.db import migrations


class Migration(migrations.Migration):
    """Миграция для удаления поля likes_count из таблицы reviews_review.
    
    Поле было добавлено напрямую в базу данных, но не должно существовать,
    так как количество лайков считается через GenericRelation.
    """

    dependencies = [
        ('reviews', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE reviews_review DROP COLUMN IF EXISTS likes_count;',
            reverse_sql='ALTER TABLE reviews_review ADD COLUMN likes_count integer NOT NULL DEFAULT 0;'
        ),
    ] 