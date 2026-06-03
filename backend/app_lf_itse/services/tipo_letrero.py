"""
Servicios de negocio para TipoLetrero.

Centraliza la lógica del dominio separándola de la capa HTTP (views/serializers),
lo que facilita reutilización, pruebas unitarias y futuros cambios.
"""

from ..models import TipoLetrero


def listar_tipos_letrero(
    *,
    id: int | None = None,
    esta_activo: bool | None = None,
) -> list[TipoLetrero]:
    """
    Retorna los tipos de letrero ordenados por id.

    Parámetros
    ----------
    id : int | None
        Si se proporciona, filtra por el id exacto.
    esta_activo : bool | None
        ``True``  → solo activos.
        ``False`` → solo inactivos.
        ``None``  → todos (sin filtro).

    Retorna
    -------
    list[TipoLetrero]
        Registros de la tabla ``tipos_letrero`` ordenados por id.
    """
    qs = TipoLetrero.objects.all()
    if id is not None:
        qs = qs.filter(id=id)
    if esta_activo is not None:
        qs = qs.filter(esta_activo=esta_activo)
    return list(qs.order_by('id'))
