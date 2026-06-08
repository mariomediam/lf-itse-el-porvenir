from ..models import PlantillaGlosaLicencia


def listar_plantillas_glosa_licencia(
    *,
    esta_activo: bool | None = None,
) -> list[PlantillaGlosaLicencia]:
    qs = PlantillaGlosaLicencia.objects.all()
    if esta_activo is not None:
        qs = qs.filter(esta_activo=esta_activo)
    return list(qs.order_by('nombre'))
