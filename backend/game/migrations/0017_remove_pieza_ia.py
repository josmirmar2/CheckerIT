"""Remove redundant Pieza -> IA relation.

This migration is intentionally resilient if the database column was already
removed manually or in a divergent schema: it will only attempt to drop
`game_pieza.ia_id` if it exists.
"""

from django.db import migrations


def _drop_column_if_exists(schema_editor, *, table_name: str, column_name: str) -> None:
    # Introspect columns; if the column is missing, do nothing.
    with schema_editor.connection.cursor() as cursor:
        try:
            description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
        except Exception:
            return

    cols = {col.name for col in description}
    if column_name not in cols:
        return

    qn = schema_editor.quote_name
    try:
        schema_editor.execute(f"ALTER TABLE {qn(table_name)} DROP COLUMN {qn(column_name)}")
    except Exception:
        # If the backend does not support DROP COLUMN or the schema changed mid-flight,
        # we prefer to leave the unused column rather than aborting the migration.
        return


def drop_pieza_ia_column(apps, schema_editor):
    _drop_column_if_exists(schema_editor, table_name="game_pieza", column_name="ia_id")


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0016_movimiento_partida_not_null'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(drop_pieza_ia_column, reverse_code=migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='pieza',
                    name='ia',
                ),
            ],
        )
    ]
