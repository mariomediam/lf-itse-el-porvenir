import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_lf_itse', '0001_initial'),
    ]

    operations = [
        # The SQL script migrar_tipo_letrero_a_texto.sql already converted
        # tipo_letrero from a FK (tipo_letrero_id) to a CharField in the DB.
        # Use SeparateDatabaseAndState so Django's state catches up without
        # touching the database for changes that were already applied.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='licenciafuncionamiento',
                    name='tipo_letrero',
                    field=models.CharField(max_length=200),
                ),
                migrations.DeleteModel(
                    name='TipoLetrero',
                ),
                migrations.AddField(
                    model_name='licenciafuncionamiento',
                    name='dias_atencion',
                    field=models.CharField(blank=True, max_length=50, null=True),
                ),
                migrations.AlterField(
                    model_name='licenciafuncionamiento',
                    name='actividad',
                    field=models.CharField(max_length=500),
                ),
                migrations.AlterField(
                    model_name='licenciafuncionamiento',
                    name='hora_desde',
                    field=models.IntegerField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name='licenciafuncionamiento',
                    name='hora_hasta',
                    field=models.IntegerField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name='licenciafuncionamiento',
                    name='medidas',
                    field=models.CharField(blank=True, max_length=500, null=True),
                ),
                migrations.AlterField(
                    model_name='licenciafuncionamiento',
                    name='zonificacion',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='zonificacion_id',
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='app_lf_itse.zonificacion',
                    ),
                ),
            ],
            database_operations=[],
        ),
        # Now apply the actual DB change: make tipo_letrero nullable.
        migrations.AlterField(
            model_name='licenciafuncionamiento',
            name='tipo_letrero',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
