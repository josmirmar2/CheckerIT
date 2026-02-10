from django.db import migrations, models
import django.db.models.deletion


def backfill_movimiento_partida(apps, schema_editor):
    Movimiento = apps.get_model("game", "Movimiento")

    # Turno.partida es obligatoria, así que es el origen de verdad.
    # Si hubiera datos antiguos con partida NULL, los rellenamos.
    qs = Movimiento.objects.filter(partida__isnull=True).select_related("turno")

    for mov in qs.iterator():
        partida_id = getattr(mov.turno, "partida_id", None)
        if not partida_id:
            raise RuntimeError(
                f"No se pudo inferir partida para Movimiento id_movimiento={mov.id_movimiento}. "
                "Asigna una partida manualmente o elimina este registro antes de migrar."
            )
        Movimiento.objects.filter(pk=mov.pk).update(partida_id=partida_id)


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0015_alter_ia_nivel_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_movimiento_partida, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="movimiento",
            name="partida",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="movimientos",
                to="game.partida",
            ),
        ),
    ]
