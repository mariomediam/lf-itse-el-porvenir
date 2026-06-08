from django.db import transaction
from django.shortcuts import get_object_or_404

from ..models import PlantillaGlosaLicencia


def listar_plantillas_glosa_licencia(
    *,
    esta_activo: bool | None = None,
) -> list[PlantillaGlosaLicencia]:
    qs = PlantillaGlosaLicencia.objects.all()
    if esta_activo is not None:
        qs = qs.filter(esta_activo=esta_activo)
    return list(qs.order_by('nombre'))


def obtener_plantilla_glosa_licencia(pk: int) -> PlantillaGlosaLicencia:
    return get_object_or_404(PlantillaGlosaLicencia, pk=pk)


def crear_plantilla_glosa_licencia(data: dict) -> PlantillaGlosaLicencia:
    with transaction.atomic():
        return PlantillaGlosaLicencia.objects.create(**data)


def actualizar_plantilla_glosa_licencia(pk: int, data: dict) -> PlantillaGlosaLicencia:
    plantilla = get_object_or_404(PlantillaGlosaLicencia, pk=pk)
    with transaction.atomic():
        for campo, valor in data.items():
            setattr(plantilla, campo, valor)
        plantilla.save()
    return plantilla


def eliminar_plantilla_glosa_licencia(pk: int) -> None:
    plantilla = get_object_or_404(PlantillaGlosaLicencia, pk=pk)
    with transaction.atomic():
        plantilla.delete()
