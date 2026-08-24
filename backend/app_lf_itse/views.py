import logging
from datetime import date

import mimetypes

from django.conf import settings as django_settings
from django.core.files.storage import default_storage
from django.db.models import ProtectedError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import (
    Expediente,
    ExpedienteArchivo,
    Itse,
    ItseArchivo,
    LicenciaFuncionamiento,
    LicenciaFuncionamientoArchivo,
    Persona,
)
from .serializers import (
    AmpliacionPlazoSerializer,
    AutorizacionImprocedenteSerializer,
    DenegarLicenciaSerializer,
    ExpedienteArchivoSerializer,
    ExpedienteArchivoUploadSerializer,
    LicenciaFuncionamientoArchivoSerializer,
    LicenciaFuncionamientoArchivoUploadSerializer,
    ExpedienteCreateSerializer,
    ExpedienteSerializer,
    ExpedienteUpdateSerializer,
    GiroSerializer,
    GiroWriteSerializer,
    ItseArchivoSerializer,
    ItseArchivoUploadSerializer,
    ItseCreateSerializer,
    ItseInactivarSerializer,
    ItseNotificacionSerializer,
    ItseUpdateSerializer,
    LicenciaFuncionamientoCreateSerializer,
    LicenciaFuncionamientoInactivarSerializer,
    LicenciaFuncionamientoNotificacionSerializer,
    LicenciaFuncionamientoUpdateSerializer,
    ExpedienteConsultaQuerySerializer,
    ItseConsultaQuerySerializer,
    ItsePorRenovarQuerySerializer,
    LicenciasFuncionamientoConsultaQuerySerializer,
    LicenciasFuncionamientoReporteQuerySerializer,
    NivelRiesgoSerializer,
    PlantillaGlosaLicenciaSerializer,
    PlantillaGlosaLicenciaWriteSerializer,
    TipoLicenciaSerializer,
    UnidadOrganicaSerializer,
    ZonificacionSerializer,
    ZonificacionWriteSerializer,
    InspectorSerializer,
    InspectorWriteSerializer,
    ItseInspectorCreateSerializer,
    PersonaDocumentoListSerializer,
    PersonaSerializer,
    PersonaWriteSerializer,
    TipoDocumentoIdentidadSerializer,
    TipoProcedimientoTupaSerializer,
    TipoProcedimientoTupaWriteSerializer,
    CambiarPasswordSerializer,
    UsuarioSerializer,
    UsuarioWriteSerializer,
)
from .services.expediente import (
    ExpedienteConItseError,
    ExpedienteConLicenciaError,
    ExpedienteDuplicadoError,
    actualizar_expediente,
    ampliar_plazo_expediente,
    buscar_expedientes_con_plazo,
    consultar_expedientes,
    crear_expediente,
    eliminar_expediente,
    listar_expedientes_pendientes_con_plazo,
)
from .services.itse import (
    EstadoInactivacionItseDuplicadoError,
    ExpedienteNoExisteError,
    ItseDenegadaError,
    ItseTieneDependientesError,
    ItseNumeroDuplicadoError,
    ItseNotificacionFechaInvalidaError,
    buscar_itse,
    consultar_itse,
    itse_por_renovar,
    crear_itse,
    eliminar_itse,
    listar_estados_itse,
    modificar_itse,
    registrar_inactivacion_itse,
    registrar_notificacion_itse,
    verificar_numero_expediente_para_itse,
)
from .services.licencia_funcionamiento import (
    EstadoInactivacionDuplicadoError,
    LicenciaDenegadaError,
    LicenciaDuplicadaError,
    LicenciaTieneDependientesError,
    NotificacionFechaInvalidaError,
    ReciboPagoDuplicadoError,
    buscar_licencias,
    consultar_licencias,
    crear_licencia,
    eliminar_licencia,
    listar_estados_licencia,
    modificar_licencia,
    registrar_inactivacion_licencia,
    registrar_notificacion,
    reporte_licencias,
    verificar_numero_expediente_para_licencia,
)
from .services.estado import listar_estados_inactivos_para_itse, listar_estados_inactivos_para_lf
from .services.giro import (
    actualizar_giro,
    buscar_giros,
    crear_giro,
    eliminar_giro,
    listar_giros,
    listar_giros_por_itse,
    listar_giros_por_licencia,
    obtener_giro,
)
from .services.nivel_riesgo import listar_niveles_riesgo
from .services.plantilla_glosa_licencia import (
    listar_plantillas_glosa_licencia,
    obtener_plantilla_glosa_licencia,
    crear_plantilla_glosa_licencia,
    actualizar_plantilla_glosa_licencia,
    eliminar_plantilla_glosa_licencia,
)
from .services.tipo_licencia import listar_tipos_licencia
from .services.unidad_organica import listar_unidades_organicas
from .services.zonificacion import (
    actualizar_zonificacion,
    crear_zonificacion,
    eliminar_zonificacion,
    listar_zonificaciones,
    obtener_zonificacion,
)
from .services.inspector import (
    actualizar_inspector,
    buscar_inspectores,
    crear_inspector,
    crear_itse_inspector,
    eliminar_inspector,
    eliminar_itse_inspectores,
    listar_inspectores,
    listar_itse_inspectores,
    obtener_inspector,
)
from .services.persona import (
    DocumentoDuplicadoError,
    actualizar_persona,
    buscar_personas,
    crear_persona,
    eliminar_persona,
    listar_documentos_persona,
    listar_personas,
    obtener_persona,
)
from .services.tipo_documento_identidad import listar_tipos_documento_identidad
from .services.reniec import ReniecError, consultar_por_dni
from .services.sunat import SunatError, consultar_por_ruc
from .services.tipo_procedimiento_tupa import (
    actualizar_tipo_procedimiento_tupa,
    crear_tipo_procedimiento_tupa,
    eliminar_tipo_procedimiento_tupa,
    listar_tipos_procedimiento_tupa,
    obtener_tipo_procedimiento_tupa,
)
from .services.expediente_archivo import eliminar_archivo_expediente, subir_archivo_expediente
from .services.licencia_funcionamiento_archivo import (
    eliminar_archivo_licencia_funcionamiento,
    subir_archivo_licencia_funcionamiento,
)
from .services.itse_archivo import (
    eliminar_archivo_itse,
    subir_archivo_itse,
)
from .services.autorizacion_improcedente import (
    ItseYaEmitidaError,
    LicenciaYaEmitidaError,
    TipoAutorizacionInvalidoError,
    buscar_autorizacion_improcedente,
    denegar_itse,
    denegar_licencia_funcionamiento,
)
from .services.usuario import (
    UsuarioTieneRegistrosError,
    actualizar_usuario,
    cambiar_password,
    construir_menu_usuario,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
)

logger = logging.getLogger(__name__)


class ExpedienteCreateView(APIView):
    """
    POST /api/lf-itse/expedientes/

    Crea un nuevo expediente.
    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer_in = ExpedienteCreateSerializer(data=request.data)
            serializer_in.is_valid(raise_exception=True)

            expediente = crear_expediente(
                data=serializer_in.validated_data,
                usuario=request.user,
            )

            serializer_out = ExpedienteSerializer(expediente)
            return Response(serializer_out.data, status=status.HTTP_201_CREATED)

        except ExpedienteDuplicadoError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al crear expediente')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedienteUpdateView(APIView):
    """
    PUT /api/lf-itse/expedientes/<pk>/

    Modifica un expediente existente y recalcula sus fechas de vencimiento
    y alerta.  Si el expediente ya tiene una ampliación de plazo registrada,
    los días de ampliación se aplican sobre la nueva fecha base calculada.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            serializer_in = ExpedienteUpdateSerializer(data=request.data)
            serializer_in.is_valid(raise_exception=True)

            expediente = actualizar_expediente(
                pk=pk,
                data=serializer_in.validated_data,
                usuario=request.user,
            )

            serializer_out = ExpedienteSerializer(expediente)
            return Response(serializer_out.data, status=status.HTTP_200_OK)

        except ExpedienteDuplicadoError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al actualizar expediente')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_expediente(pk=pk, usuario=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ExpedienteConLicenciaError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except ExpedienteConItseError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar expediente pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FechaServidorView(APIView):
    """
    GET /api/lf-itse/fecha-servidor/

    Retorna la fecha actual del servidor en formato ISO (YYYY-MM-DD).
    Utilizado por el frontend para calcular rangos de fechas relativas
    sin depender del reloj del cliente.

    Respuesta
    ---------
    { "fecha": "2026-05-11" }

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        import datetime
        return Response({'fecha': datetime.date.today().isoformat()}, status=status.HTTP_200_OK)


class ExpedientesPendientesView(APIView):
    """
    GET /api/lf-itse/expedientes/pendientes/

    Lista todos los expedientes con al menos una autorización pendiente
    (LF o ITSE), incluyendo los días hábiles restantes hasta el vencimiento.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pendientes = listar_expedientes_pendientes_con_plazo()
            return Response(pendientes, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar expedientes pendientes')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedientesBuscarView(APIView):
    """
    GET /api/lf-itse/expedientes/buscar/?filtro=<FILTRO>&valor=<VALOR>

    Busca expedientes según el filtro y valor indicados.
    Incluye ``dias_habiles_restantes`` para cada resultado.

    Parámetros de query string
    --------------------------
    filtro : str  (obligatorio)
        NUMERO | FECHA_RECEPCION | FECHA_VENCIMIENTO |
        NOMBRE_SOLICITANTE | RUC_SOLICITANTE
    valor  : str  (obligatorio)
        Valor a buscar según el filtro elegido.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            filtro = request.query_params.get('filtro', '').strip()
            valor  = request.query_params.get('valor',  '').strip()

            if not filtro:
                return Response(
                    {'error': "El parámetro 'filtro' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not valor:
                return Response(
                    {'error': "El parámetro 'valor' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            resultados = buscar_expedientes_con_plazo(filtro, valor)
            return Response(resultados, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception('Error al buscar expedientes (filtro=%s)', filtro)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedientesConsultaView(APIView):
    """
    GET /api/lf-itse/expedientes/consulta/

    Busca expedientes según uno o más filtros opcionales.
    Al menos uno debe estar presente.

    Query params (todos opcionales, pero se requiere al menos uno)
    --------------------------------------------------------------
    solicitante_nombre             – str  búsqueda parcial en nombre/razón social del solicitante
    numero_expediente              – int  número de expediente (exacto)
    anio_expediente                – int  año de recepción del expediente (exacto)
    solicitante_numero_documento   – str  número de documento del solicitante (exacto)
    representante_numero_documento – str  número de documento del representante legal (exacto)

    Respuesta por expediente
    ------------------------
    numero_expediente, tipo_procedimiento_tupa_nombre, fecha_recepcion,
    solicitante_nombre, solicitante_documentos,
    representante_nombre, representante_documentos,
    licencia_funcionamiento  – número si existe / 'IMPROCEDENTE' si fue denegada / '' si no aplica,
    itse                     – número si existe / 'DESFAVORABLE' si fue denegada / '' si no aplica.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = ExpedienteConsultaQuerySerializer(
                data=request.query_params.dict()
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            resultados = consultar_expedientes(serializer.validated_data)
            return Response(resultados, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al consultar expedientes')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UnidadOrganicaListView(APIView):
    """
    GET /api/lf-itse/unidades-organicas/

    Retorna las unidades orgánicas ordenadas por nombre.

    Parámetros de query string
    --------------------------
    esta_activo : str  (opcional)
        'true'  → solo activas.
        'false' → solo inactivas.
        Si se omite se devuelven todas.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            param = request.query_params.get('esta_activo', '').strip().lower()

            if param == 'true':
                esta_activo = True
            elif param == 'false':
                esta_activo = False
            elif param == '':
                esta_activo = None
            else:
                return Response(
                    {'error': "El parámetro 'esta_activo' debe ser 'true' o 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            unidades = listar_unidades_organicas(esta_activo)
            serializer = UnidadOrganicaSerializer(unidades, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar unidades orgánicas')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TipoProcedimientoTupaListView(APIView):
    """
    GET  /api/lf-itse/tipos-procedimiento-tupa/
        Lista todos los tipos de procedimiento TUPA.

    POST /api/lf-itse/tipos-procedimiento-tupa/
        Crea un nuevo tipo de procedimiento TUPA.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            solo_activos = request.query_params.get('esta_activo', '').lower() == 'true'
            tipos = listar_tipos_procedimiento_tupa(solo_activos=solo_activos)
            serializer = TipoProcedimientoTupaSerializer(tipos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar tipos de procedimiento TUPA')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            serializer = TipoProcedimientoTupaWriteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            tipo = crear_tipo_procedimiento_tupa(
                data=serializer.validated_data,
                usuario=request.user,
            )
            return Response(
                TipoProcedimientoTupaSerializer(tipo).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al crear tipo de procedimiento TUPA')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TipoProcedimientoTupaDetailView(APIView):
    """
    GET    /api/lf-itse/tipos-procedimiento-tupa/<pk>/
        Retorna un tipo de procedimiento TUPA específico.

    PUT    /api/lf-itse/tipos-procedimiento-tupa/<pk>/
        Actualiza un tipo de procedimiento TUPA.

    DELETE /api/lf-itse/tipos-procedimiento-tupa/<pk>/
        Elimina físicamente un tipo de procedimiento TUPA.
        Retorna 409 si tiene expedientes asociados.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            tipo = obtener_tipo_procedimiento_tupa(pk)
            return Response(
                TipoProcedimientoTupaSerializer(tipo).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al obtener tipo de procedimiento TUPA pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            tipo = obtener_tipo_procedimiento_tupa(pk)
            serializer = TipoProcedimientoTupaWriteSerializer(tipo, data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            tipo = actualizar_tipo_procedimiento_tupa(pk, serializer.validated_data, request.user)
            return Response(
                TipoProcedimientoTupaSerializer(tipo).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al actualizar tipo de procedimiento TUPA pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_tipo_procedimiento_tupa(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ProtectedError:
            return Response(
                {'error': 'No se puede eliminar: el registro tiene expedientes asociados.'},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar tipo de procedimiento TUPA pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PersonaListCreateView(APIView):
    """
    GET  /api/lf-itse/personas/
        Lista todas las personas con sus documentos.

    POST /api/lf-itse/personas/
        Crea una nueva persona junto con sus documentos de identidad.
        Verifica que ningún documento esté ya asignado a otra persona.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            personas = listar_personas()
            serializer = PersonaSerializer(personas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar personas')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        serializer = PersonaWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            persona = crear_persona(
                data=serializer.validated_data,
                usuario=request.user,
            )
            return Response(
                PersonaSerializer(persona).data,
                status=status.HTTP_201_CREATED,
            )

        except DocumentoDuplicadoError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al crear persona')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PersonaDetailView(APIView):
    """
    GET    /api/lf-itse/personas/<pk>/
        Retorna una persona con sus documentos.

    PUT    /api/lf-itse/personas/<pk>/
        Actualiza una persona y reemplaza todos sus documentos.

    DELETE /api/lf-itse/personas/<pk>/
        Elimina físicamente la persona y sus documentos (CASCADE).

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            persona = obtener_persona(pk)
            return Response(
                PersonaSerializer(persona).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al obtener persona pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            persona_instance = obtener_persona(pk)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = PersonaWriteSerializer(persona_instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            persona = actualizar_persona(pk, serializer.validated_data, request.user)
            return Response(
                PersonaSerializer(persona).data,
                status=status.HTTP_200_OK,
            )

        except DocumentoDuplicadoError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al actualizar persona pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_persona(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception('Error al eliminar persona pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PersonasBuscarView(APIView):
    """
    GET /api/lf-itse/personas/buscar/?filtro=<FILTRO>&valor=<VALOR>

    Busca personas según el filtro y valor indicados.
    Retorna una fila por persona con todos sus documentos de identidad
    concatenados en el campo ``documento_concatenado``.

    Parámetros de query string
    --------------------------
    filtro : str  (obligatorio)
        NOMBRE | DOCUMENTO | ID
    valor  : str  (obligatorio)
        Valor a buscar según el filtro elegido.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            filtro = request.query_params.get('filtro', '').strip()
            valor  = request.query_params.get('valor',  '').strip()

            if not filtro:
                return Response(
                    {'error': "El parámetro 'filtro' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not valor:
                return Response(
                    {'error': "El parámetro 'valor' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            resultados = buscar_personas(filtro, valor)
            return Response(resultados, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception('Error al buscar personas (filtro=%s)', filtro)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TipoDocumentoIdentidadListView(APIView):
    """
    GET /api/lf-itse/tipos-documento-identidad/?tipo_persona=<N|J>

    Retorna los tipos de documento de identidad disponibles según el
    tipo de persona indicado.

    Parámetros de query string
    --------------------------
    tipo_persona : str  (obligatorio)
        'N' → documentos para persona natural
        'J' → documentos para persona jurídica

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipo_persona = request.query_params.get('tipo_persona', '').strip()

        if not tipo_persona:
            return Response(
                {'error': "El parámetro 'tipo_persona' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tipos = listar_tipos_documento_identidad(tipo_persona)
            serializer = TipoDocumentoIdentidadSerializer(tipos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PersonaSexosView(APIView):
    """
    GET /api/lf-itse/personas/sexos/

    Retorna los valores disponibles para el campo sexo de Persona.
    Útil para poblar listas desplegables en el frontend.

    Respuesta de ejemplo:
        [
            {"value": "M", "label": "Masculino"},
            {"value": "F", "label": "Femenino"},
            {"value": "X", "label": "Prefiero no decirlo"}
        ]

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sexos = [
            {'value': value, 'label': label}
            for value, label in Persona.Sexo.choices
        ]
        return Response(sexos, status=status.HTTP_200_OK)


class PersonaDocumentosListView(APIView):
    """
    GET /api/lf-itse/personas/<pk>/documentos/

    Lista los documentos de identidad de la persona indicada, incluyendo
    el código y nombre del tipo de documento.

    Parámetros de ruta
    ------------------
    pk : int
        PK de la persona.

    Retorna
    -------
    200  Lista de documentos con:
         id, persona_id, tipo_documento_identidad_id, numero_documento,
         tipos_documento_identidad_codigo, tipos_documento_identidad_nombre.
    404  Si la persona no existe.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            documentos = listar_documentos_persona(pk)
            serializer = PersonaDocumentoListSerializer(documentos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar documentos de la persona pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReniecConsultarView(APIView):
    """
    GET /api/lf-itse/reniec/consultar/?dni=<DNI>

    Consulta los datos de una persona en RENIEC a través de la
    plataforma PIDE.

    Parámetros de query string
    --------------------------
    dni : str  (obligatorio)
        Número de DNI a consultar (8 dígitos numéricos).

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        dni = request.query_params.get('dni', '').strip()

        if not dni:
            return Response(
                {'error': "El parámetro 'dni' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = consultar_por_dni(dni)
            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ReniecError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except Exception as e:
            logger.exception('Error al consultar RENIEC (dni=%s)', dni)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SunatConsultarView(APIView):
    """
    GET /api/lf-itse/sunat/consultar/?ruc=<RUC>

    Consulta los datos principales de un contribuyente en SUNAT a través
    de la plataforma PIDE.

    Parámetros de query string
    --------------------------
    ruc : str  (obligatorio)
        Número de RUC a consultar (11 dígitos numéricos).

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ruc = request.query_params.get('ruc', '').strip()

        if not ruc:
            return Response(
                {'error': "El parámetro 'ruc' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = consultar_por_ruc(ruc)
            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except SunatError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except Exception as e:
            logger.exception('Error al consultar SUNAT (ruc=%s)', ruc)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedienteAmpliacionPlazoView(APIView):
    """
    POST /api/lf-itse/expedientes/<pk>/ampliacion-plazo/

    Registra la ampliación de plazo de un expediente y recalcula
    sus fechas de vencimiento y alerta.

    Parámetros de URL
    -----------------
    pk : int  — id del expediente a ampliar.

    Body (JSON)
    -----------
    {
        "fecha_suspension"  : "YYYY-MM-DD",
        "dias_ampliacion"   : <entero positivo>,
        "motivo_ampliacion" : "<texto>"
    }

    Retorna
    -------
    200 OK  — el expediente completo con los campos actualizados.
    400     — datos inválidos.
    404     — expediente no encontrado.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = AmpliacionPlazoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            expediente = ampliar_plazo_expediente(pk, serializer.validated_data, request.user)
            return Response(
                ExpedienteSerializer(expediente).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al ampliar plazo del expediente pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedienteArchivoUploadView(APIView):
    """
    GET  /api/lf-itse/expedientes/<pk>/archivos/
    POST /api/lf-itse/expedientes/<pk>/archivos/

    GET  — lista todos los archivos asociados al expediente.
    POST — sube un archivo digital y lo asocia al expediente.
           El request debe enviarse como ``multipart/form-data`` con el campo:
               archivo : file

    Parámetros de URL
    -----------------
    pk : int  — id del expediente.

    Retorna (GET)
    -------------
    200 OK  — lista de metadatos de archivos (ExpedienteArchivo[]).
    404     — expediente no encontrado.

    Retorna (POST)
    --------------
    201 Created  — metadatos del archivo guardado (ExpedienteArchivo).
    400          — no se envió ningún archivo o datos inválidos.
    404          — expediente no encontrado.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        archivos = ExpedienteArchivo.objects.filter(expediente=expediente).order_by('fecha_digitacion')
        return Response(
            ExpedienteArchivoSerializer(archivos, many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, pk):
        serializer = ExpedienteArchivoUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            archivo_obj = subir_archivo_expediente(
                pk,
                serializer.validated_data['archivo'],
                request.user,
            )
            return Response(
                ExpedienteArchivoSerializer(archivo_obj).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al subir archivo al expediente pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedienteArchivoDetailView(APIView):
    """
    DELETE /api/lf-itse/expedientes/archivos/<pk>/

    Elimina el registro de metadatos en BD y el archivo físico del disco.

    Parámetros de URL
    -----------------
    pk : int  — id del registro ExpedienteArchivo a eliminar.

    Retorna
    -------
    204 No Content — eliminación exitosa.
    404            — registro no encontrado.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            eliminar_archivo_expediente(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception('Error al eliminar archivo pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExpedienteArchivoDownloadView(APIView):
    """
    GET /api/lf-itse/expedientes/archivos/<uuid>/descargar/

    Retorna el archivo físico asociado al registro ``ExpedienteArchivo``
    identificado por su UUID.

    El header ``Content-Disposition`` se establece como ``inline`` para que
    el navegador pueda visualizarlo directamente (PDFs, imágenes, etc.).
    El nombre original del archivo se incluye para que al guardarlo conserve
    el nombre correcto.

    Parámetros de URL
    -----------------
    uuid : UUID  — uuid del registro ExpedienteArchivo.

    Retorna
    -------
    200 OK  — stream del archivo con el Content-Type apropiado.
    404     — registro no encontrado o archivo físico inexistente en disco.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        archivo_obj = get_object_or_404(ExpedienteArchivo, uuid=uuid)

        if not default_storage.exists(archivo_obj.ruta_archivo):
            return Response(
                {'error': 'El archivo físico no se encontró en el servidor.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        archivo_abierto = default_storage.open(archivo_obj.ruta_archivo, 'rb')

        content_type, _ = mimetypes.guess_type(archivo_obj.nombre_original)
        content_type = content_type or 'application/octet-stream'

        response = FileResponse(
            archivo_abierto,
            content_type=content_type,
        )
        response['Content-Disposition'] = (
            f'inline; filename="{archivo_obj.nombre_original}"'
        )
        return response


class LicenciaFuncionamientoArchivoUploadView(APIView):
    """
    GET  /api/lf-itse/licencias-funcionamiento/<pk>/archivos/
    POST /api/lf-itse/licencias-funcionamiento/<pk>/archivos/

    GET  — lista todos los archivos asociados a la licencia de funcionamiento.
    POST — sube un archivo digital (``multipart/form-data``, campo ``archivo``).

    Parámetros de URL
    -----------------
    pk : int  — id de la licencia de funcionamiento.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get(self, request, pk):
        licencia = get_object_or_404(LicenciaFuncionamiento, pk=pk)
        archivos = LicenciaFuncionamientoArchivo.objects.filter(
            licencia_funcionamiento=licencia,
        ).order_by('fecha_digitacion')
        return Response(
            LicenciaFuncionamientoArchivoSerializer(archivos, many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, pk):
        serializer = LicenciaFuncionamientoArchivoUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            archivo_obj = subir_archivo_licencia_funcionamiento(
                pk,
                serializer.validated_data['archivo'],
                request.user,
            )
            return Response(
                LicenciaFuncionamientoArchivoSerializer(archivo_obj).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al subir archivo a la licencia pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoArchivoDetailView(APIView):
    """
    DELETE /api/lf-itse/licencias-funcionamiento/archivos/<pk>/

    Elimina el registro de metadatos y el archivo físico del disco.

    pk : int  — id del registro ``LicenciaFuncionamientoArchivo``.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            eliminar_archivo_licencia_funcionamiento(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception('Error al eliminar archivo de licencia pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoArchivoDownloadView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/archivos/<uuid>/descargar/

    Retorna el archivo físico asociado al registro identificado por UUID.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        archivo_obj = get_object_or_404(LicenciaFuncionamientoArchivo, uuid=uuid)

        if not default_storage.exists(archivo_obj.ruta_archivo):
            return Response(
                {'error': 'El archivo físico no se encontró en el servidor.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        archivo_abierto = default_storage.open(archivo_obj.ruta_archivo, 'rb')

        content_type, _ = mimetypes.guess_type(archivo_obj.nombre_original)
        content_type = content_type or 'application/octet-stream'

        response = FileResponse(
            archivo_abierto,
            content_type=content_type,
        )
        response['Content-Disposition'] = (
            f'inline; filename="{archivo_obj.nombre_original}"'
        )
        return response


class ItseArchivoUploadView(APIView):
    """
    GET  /api/lf-itse/itse/<pk>/archivos/
    POST /api/lf-itse/itse/<pk>/archivos/

    GET  — lista todos los archivos asociados al certificado ITSE.
    POST — sube un archivo digital (``multipart/form-data``, campo ``archivo``).

    Parámetros de URL
    -----------------
    pk : int  — id del certificado ITSE.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get(self, request, pk):
        itse = get_object_or_404(Itse, pk=pk)
        archivos = ItseArchivo.objects.filter(itse=itse).order_by('fecha_digitacion')
        return Response(
            ItseArchivoSerializer(archivos, many=True).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, pk):
        serializer = ItseArchivoUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            archivo_obj = subir_archivo_itse(
                pk,
                serializer.validated_data['archivo'],
                request.user,
            )
            return Response(
                ItseArchivoSerializer(archivo_obj).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al subir archivo al ITSE pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseArchivoDetailView(APIView):
    """
    DELETE /api/lf-itse/itse/archivos/<pk>/

    Elimina el registro de metadatos y el archivo físico del disco.

    pk : int  — id del registro ``ItseArchivo``.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            eliminar_archivo_itse(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception('Error al eliminar archivo de ITSE pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseArchivoDownloadView(APIView):
    """
    GET /api/lf-itse/itse/archivos/<uuid>/descargar/

    Retorna el archivo físico asociado al registro identificado por UUID.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        archivo_obj = get_object_or_404(ItseArchivo, uuid=uuid)

        if not default_storage.exists(archivo_obj.ruta_archivo):
            return Response(
                {'error': 'El archivo físico no se encontró en el servidor.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        archivo_abierto = default_storage.open(archivo_obj.ruta_archivo, 'rb')

        content_type, _ = mimetypes.guess_type(archivo_obj.nombre_original)
        content_type = content_type or 'application/octet-stream'

        response = FileResponse(
            archivo_abierto,
            content_type=content_type,
        )
        response['Content-Disposition'] = (
            f'inline; filename="{archivo_obj.nombre_original}"'
        )
        return response


class DenegarLicenciaView(APIView):
    """
    POST /api/lf-itse/expedientes/<pk>/denegar-licencia/

    Registra la denegación de emisión de una licencia de funcionamiento
    para el expediente indicado.

    Parámetros de URL
    -----------------
    pk : int  — id del expediente.

    Body (JSON)
    -----------
    {
        "fecha_rechazo" : "YYYY-MM-DD",
        "documento"     : "<número o referencia del documento>",
        "observaciones" : "<texto>"
    }

    Retorna
    -------
    201 Created  — el registro de autorización improcedente creado.
    400          — datos inválidos o licencia ya emitida.
    404          — expediente no encontrado.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = DenegarLicenciaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            autorizacion = denegar_licencia_funcionamiento(pk, serializer.validated_data, request.user)
            return Response(
                AutorizacionImprocedenteSerializer(autorizacion).data,
                status=status.HTTP_201_CREATED,
            )

        except LicenciaYaEmitidaError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception('Error al denegar licencia del expediente pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DenegarItseView(APIView):
    """
    POST /api/lf-itse/expedientes/<pk>/denegar-itse/

    Registra la ITSE desfavorable para el expediente indicado.

    Parámetros de URL
    -----------------
    pk : int  — id del expediente.

    Body (JSON)
    -----------
    {
        "fecha_rechazo" : "YYYY-MM-DD",
        "documento"     : "<número o referencia del documento>",
        "observaciones" : "<texto>"
    }

    Retorna
    -------
    201 Created  — el registro de autorización improcedente creado.
    400          — datos inválidos o ITSE ya emitida.
    404          — expediente no encontrado.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = DenegarLicenciaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            autorizacion = denegar_itse(pk, serializer.validated_data, request.user)
            return Response(
                AutorizacionImprocedenteSerializer(autorizacion).data,
                status=status.HTTP_201_CREATED,
            )

        except ItseYaEmitidaError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception('Error al registrar ITSE desfavorable del expediente pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AutorizacionImprocedenteView(APIView):
    """
    GET /api/lf-itse/expedientes/<pk>/autorizacion-improcedente/?tipo=LF
    GET /api/lf-itse/expedientes/<pk>/autorizacion-improcedente/?tipo=ITSE

    Consulta si un expediente tiene una autorización improcedente registrada
    para el tipo indicado.

    Parámetros de ruta
    ------------------
    pk : int  — id del expediente.

    Query params
    ------------
    tipo : str  — 'LF' (licencia denegada) o 'ITSE' (ITSE desfavorable).

    Retorna
    -------
    200  — objeto con los datos del registro, o ``null`` si no existe.
    400  — parámetro ``tipo`` ausente o inválido.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        tipo = request.query_params.get('tipo', '').strip()
        if not tipo:
            return Response(
                {'error': "El parámetro 'tipo' es requerido ('LF' o 'ITSE')."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            autorizacion = buscar_autorizacion_improcedente(pk, tipo)
            data = AutorizacionImprocedenteSerializer(autorizacion).data if autorizacion else None
            return Response(data, status=status.HTTP_200_OK)
        except TipoAutorizacionInvalidoError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                'Error al consultar autorización improcedente expediente pk=%s tipo=%s', pk, tipo
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MenuUsuarioView(APIView):
    """
    GET /api/lf-itse/usuarios/menus/

    Retorna la estructura de menús a los que tiene acceso el usuario autenticado.
    El user.id se obtiene del token JWT; no se requiere ningún parámetro en la URL.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            menus = construir_menu_usuario(request.user.id)
            return Response(menus, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al construir menú del usuario %s', request.user.id)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UsuarioListCreateView(APIView):
    """
    GET  /api/lf-itse/usuarios/
        Lista todos los usuarios del sistema con su perfil de permisos.

    POST /api/lf-itse/usuarios/
        Crea un nuevo usuario y su perfil de acceso al sistema.
        No permite asignar is_superuser ni is_staff.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            usuarios = listar_usuarios()
            serializer = UsuarioSerializer(usuarios, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar usuarios')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            serializer = UsuarioWriteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            usuario = crear_usuario(serializer.validated_data, digitador=request.user)
            return Response(
                UsuarioSerializer(usuario).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al crear usuario')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UsuarioDetailView(APIView):
    """
    GET    /api/lf-itse/usuarios/<pk>/
        Retorna la información de un usuario, excluyendo el password.
        Incluye el perfil de permisos del sistema.

    PUT    /api/lf-itse/usuarios/<pk>/
        Actualiza los datos del usuario y su perfil de acceso.
        No permite modificar is_superuser ni is_staff.
        Si no se envía password, se mantiene el existente.

    DELETE /api/lf-itse/usuarios/<pk>/
        Elimina el usuario y su perfil. Retorna 409 si tiene registros digitados.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from django.contrib.auth import get_user_model
        usuario = get_object_or_404(
            get_user_model().objects.select_related('perfil_lf_itse'),
            pk=pk,
        )
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            serializer = UsuarioWriteSerializer(
                data=request.data,
                context={'instance_pk': pk},
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            usuario = actualizar_usuario(pk, serializer.validated_data, request.user)
            return Response(
                UsuarioSerializer(usuario).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al actualizar usuario pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_usuario(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except UsuarioTieneRegistrosError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            logger.exception('Error al eliminar usuario pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UsuarioCambiarPasswordView(APIView):
    """
    PATCH /api/lf-itse/usuarios/<pk>/cambiar-password/

    Cambia la contraseña de un usuario.
    Requiere enviar ``password`` y ``password_confirm`` con el mismo valor.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            serializer = CambiarPasswordSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            cambiar_password(pk, serializer.validated_data['password'])
            return Response(
                {'mensaje': 'Contraseña actualizada correctamente.'},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al cambiar contraseña del usuario pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ── Licencias de Funcionamiento ────────────────────────────────────────────────

class LicenciaFuncionamientoCreateView(APIView):
    """
    POST /api/lf-itse/licencias-funcionamiento/

    Crea una nueva licencia de funcionamiento con sus giros asociados.
    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer_in = LicenciaFuncionamientoCreateSerializer(data=request.data)
            serializer_in.is_valid(raise_exception=True)

            licencia = crear_licencia(
                data=serializer_in.validated_data,
                usuario=request.user,
            )

            return Response({'id': licencia.id}, status=status.HTTP_201_CREATED)

        except LicenciaDenegadaError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except LicenciaDuplicadaError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except ReciboPagoDuplicadoError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al crear licencia de funcionamiento')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoVerificarExpedienteView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/verificar-expediente/
        ?numero_expediente=<N>&anio=<YYYY>

    Verifica si un expediente puede tener una licencia de funcionamiento emitida.

    Parámetros de query string
    --------------------------
    numero_expediente : int  (obligatorio)
    anio              : int  (obligatorio) — año de recepción del expediente

    Respuesta
    ---------
    {
        "se_puede_emitir_licencia": true | false,
        "expediente_id": <int> | null,
        "mensaje": ""
    }

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        numero_str = request.query_params.get('numero_expediente', '').strip()
        anio_str   = request.query_params.get('anio', '').strip()

        if not numero_str:
            return Response(
                {'error': "El parámetro 'numero_expediente' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not anio_str:
            return Response(
                {'error': "El parámetro 'anio' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            numero_expediente = int(numero_str)
            anio = int(anio_str)
        except ValueError:
            return Response(
                {'error': "Los parámetros 'numero_expediente' y 'anio' deben ser números enteros."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = verificar_numero_expediente_para_licencia(numero_expediente, anio)
            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                'Error al verificar expediente para licencia (numero=%s, anio=%s)',
                numero_expediente, anio,
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseVerificarExpedienteView(APIView):
    """
    GET /api/lf-itse/itse/verificar-expediente/
        ?numero_expediente=<N>&anio=<YYYY>

    Verifica si un expediente puede tener un ITSE emitido.

    Parámetros de query string
    --------------------------
    numero_expediente : int  (obligatorio)
    anio              : int  (obligatorio) — año de recepción del expediente

    Respuesta
    ---------
    {
        "se_puede_emitir_itse": true | false,
        "expediente_id": <int> | null,
        "mensaje": ""
    }

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        numero_str = request.query_params.get('numero_expediente', '').strip()
        anio_str = request.query_params.get('anio', '').strip()

        if not numero_str:
            return Response(
                {'error': "El parámetro 'numero_expediente' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not anio_str:
            return Response(
                {'error': "El parámetro 'anio' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            numero_expediente = int(numero_str)
            anio = int(anio_str)
        except ValueError:
            return Response(
                {'error': "Los parámetros 'numero_expediente' y 'anio' deben ser números enteros."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = verificar_numero_expediente_para_itse(numero_expediente, anio)
            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                'Error al verificar expediente para ITSE (numero=%s, anio=%s)',
                numero_expediente,
                anio,
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciasFuncionamientoBuscarView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/buscar/?filtro=<FILTRO>&valor=<VALOR>

    Busca licencias de funcionamiento según el filtro y valor indicados.

    Parámetros de query string
    --------------------------
    filtro : str  (obligatorio)
        NUMERO | EXPEDIENTE | NOMBRE_COMERCIAL | FECHA_EMISION |
        NOMBRES_TITULAR | RUC_TITULAR | NOMBRES_CONDUCTOR |
        DIRECCION | RECIBO_PAGO | RESOLUCION_NUMERO
    valor  : str  (obligatorio)
        Valor a buscar según el filtro elegido.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            filtro = request.query_params.get('filtro', '').strip()
            valor  = request.query_params.get('valor',  '').strip()

            if not filtro:
                return Response(
                    {'error': "El parámetro 'filtro' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not valor:
                return Response(
                    {'error': "El parámetro 'valor' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            resultados = buscar_licencias(filtro, valor)
            return Response(resultados, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception('Error al buscar licencias de funcionamiento (filtro=%s)', filtro)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseCreateView(APIView):
    """
    POST /api/lf-itse/itse/

    Crea un nuevo ITSE con sus giros asociados.
    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer_in = ItseCreateSerializer(data=request.data)
            serializer_in.is_valid(raise_exception=True)

            itse = crear_itse(serializer_in.validated_data, request.user)
            return Response({'id': itse.id}, status=status.HTTP_201_CREATED)

        except ExpedienteNoExisteError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except (ItseDenegadaError, ItseYaEmitidaError, ItseNumeroDuplicadoError, ReciboPagoDuplicadoError) as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            logger.exception('Error al crear ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseUpdateView(APIView):
    """
    PUT /api/lf-itse/itse/<pk>/

    Modifica un ITSE existente. Los giros enviados reemplazan por completo
    los asociados. Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        from .models import Itse

        serializer = ItseUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            itse = modificar_itse(pk, serializer.validated_data, request.user)
            return Response(
                {'id': itse.id, 'mensaje': 'ITSE modificada correctamente.'},
                status=status.HTTP_200_OK,
            )

        except Itse.DoesNotExist:
            return Response(
                {'error': 'La ITSE no existe.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ExpedienteNoExisteError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except (ItseDenegadaError, ItseYaEmitidaError, ItseNumeroDuplicadoError, ReciboPagoDuplicadoError) as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            logger.exception('Error al modificar ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        """
        DELETE /api/lf-itse/itse/<pk>/

        Elimina la ITSE y todos sus registros dependientes:
          - itse_estados
          - itse_giros
          - itse_archivos y sus archivos físicos
          - itse

        Respuestas
        ----------
        204  Eliminación exitosa.
        404  La ITSE no existe.
        409  La ITSE tiene ITSE dependientes.
        500  Error interno.

        Requiere autenticación JWT.
        """
        try:
            eliminar_itse(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ItseTieneDependientesError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar la ITSE pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseNotificacionView(APIView):
    """
    PATCH /api/lf-itse/itse/<pk>/notificacion/

    Registra la fecha de notificación de entrega de un ITSE actualizando
    la columna ``fecha_notificacion``.

    Parámetros de ruta
    ------------------
    pk : int
        PK del ITSE.

    Body (JSON)
    -----------
    fecha_notificacion : str  (formato YYYY-MM-DD)

    Respuestas
    ----------
    200  Fecha de notificación registrada correctamente.
    400  Datos de entrada inválidos.
    404  El ITSE no existe.
    409  La fecha de notificación es anterior a la fecha de expedición.
    500  Error interno.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        from .models import Itse
        serializer = ItseNotificacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            registrar_notificacion_itse(
                pk,
                serializer.validated_data['fecha_notificacion'],
                request.user,
            )
            return Response(
                {'mensaje': 'Fecha de notificación registrada correctamente.'},
                status=status.HTTP_200_OK,
            )
        except Itse.DoesNotExist:
            return Response(
                {'error': 'El ITSE no existe.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ItseNotificacionFechaInvalidaError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception('Error al registrar la notificación del ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseBuscarView(APIView):
    """
    GET /api/lf-itse/itse/buscar/?filtro=<FILTRO>&valor=<VALOR>

    Busca ITSE según el filtro y valor indicados.

    Parámetros de query string
    --------------------------
    filtro : str  (obligatorio)
        ID | NUMERO | EXPEDIENTE | NOMBRE_COMERCIAL | FECHA_EXPEDICION | FECHA_EMISION |
        NOMBRES_TITULAR | RUC_TITULAR | NOMBRES_CONDUCTOR |
        DIRECCION | RECIBO_PAGO | RESOLUCION_NUMERO
    valor  : str  (obligatorio)
        Valor a buscar según el filtro elegido.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            filtro = request.query_params.get('filtro', '').strip()
            valor = request.query_params.get('valor', '').strip()

            if not filtro:
                return Response(
                    {'error': "El parámetro 'filtro' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not valor:
                return Response(
                    {'error': "El parámetro 'valor' es obligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            resultados = buscar_itse(filtro, valor)
            return Response(resultados, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.exception('Error al buscar ITSE (filtro=%s)', filtro)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseConsultaView(APIView):
    """
    GET /api/lf-itse/itse/consulta/

    Busca ITSE según uno o más filtros opcionales.
    Si no se pasa ningún filtro, retorna todos los registros.

    Query params (todos opcionales)
    --------------------------------
    numero_itse                  – int   número de ITSE (exacto)
    numero_expediente            – int   número de expediente (exacto)
    anio_expediente              – int   año de recepción del expediente (exacto)
    emision_desde                – date  inicio del rango de fecha de expedición (YYYY-MM-DD)
    emision_hasta                – date  fin del rango de fecha de expedición (YYYY-MM-DD)
    titular_nombre               – str   búsqueda parcial en apellidos + nombres del titular
    titular_numero_documento     – str   número de documento exacto del titular
    conductor_nombre             – str   búsqueda parcial en apellidos + nombres del conductor
    conductor_numero_documento   – str   número de documento exacto del conductor
    nombre_comercial             – str   búsqueda parcial en nombre comercial
    nivel_riesgo_id              – int   ID del nivel de riesgo
    direccion                    – str   búsqueda parcial en dirección
    numero_recibo_pago           – str   número de recibo de pago (exacto)
    fecha_notificacion_desde     – date  inicio del rango de fecha de notificación (YYYY-MM-DD)
    fecha_notificacion_hasta     – date  fin del rango de fecha de notificación (YYYY-MM-DD)
    esta_activo                  – bool  true = solo activas, false = solo inactivas
    giro_nombre                  – str   búsqueda parcial en nombre de giro

    Requiere autenticación JWT.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = ItseConsultaQuerySerializer(
                data=request.query_params.dict()
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            resultados = consultar_itse(serializer.validated_data)
            return Response(resultados, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al consultar ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItsePorRenovarView(APIView):
    """
    GET /api/lf-itse/itse/por-renovar/

    Lista las ITSE que deben ser renovadas dentro de un periodo determinado.

    Solo se incluyen ITSE que cumplan los tres criterios:
    - No han sido renovadas aún (ninguna otra ITSE las referencia como itse_principal_id).
    - Están activas (no tienen estados inactivos en su historial).
    - Su fecha de caducidad cae dentro del rango [fecha_desde, fecha_hasta].

    Query params (obligatorios)
    ---------------------------
    fecha_desde : date  — extremo inferior del rango (YYYY-MM-DD).
    fecha_hasta : date  — extremo superior del rango (YYYY-MM-DD).

    Respuesta por registro
    ----------------------
    id, numero_itse, fecha_expedicion, fecha_solicitud_renovacion,
    fecha_caducidad, nombre_comercial, direccion.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = ItsePorRenovarQuerySerializer(
                data=request.query_params.dict()
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            resultados = itse_por_renovar(
                str(data['fecha_desde']),
                str(data['fecha_hasta']),
            )
            return Response(resultados, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar ITSE por renovar')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PlantillaGlosaLicenciaListCreateView(APIView):
    """
    GET  /api/lf-itse/plantillas-glosa-licencia/
        Lista las plantillas de glosa. Filtro opcional: ?esta_activo=true|false

    POST /api/lf-itse/plantillas-glosa-licencia/
        Crea una nueva plantilla de glosa.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            activo_param = request.query_params.get('esta_activo', '').strip().lower()
            if activo_param == 'true':
                esta_activo = True
            elif activo_param == 'false':
                esta_activo = False
            elif activo_param == '':
                esta_activo = None
            else:
                return Response(
                    {'error': "El parámetro 'esta_activo' debe ser 'true' o 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            plantillas = listar_plantillas_glosa_licencia(esta_activo=esta_activo)
            serializer = PlantillaGlosaLicenciaSerializer(plantillas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar plantillas de glosa')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        serializer = PlantillaGlosaLicenciaWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            plantilla = crear_plantilla_glosa_licencia(serializer.validated_data)
            return Response(
                PlantillaGlosaLicenciaSerializer(plantilla).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al crear plantilla de glosa')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PlantillaGlosaLicenciaDetailView(APIView):
    """
    GET    /api/lf-itse/plantillas-glosa-licencia/<pk>/
        Retorna una plantilla de glosa específica.

    PUT    /api/lf-itse/plantillas-glosa-licencia/<pk>/
        Actualiza una plantilla de glosa.

    DELETE /api/lf-itse/plantillas-glosa-licencia/<pk>/
        Elimina una plantilla de glosa.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            plantilla = obtener_plantilla_glosa_licencia(pk)
            return Response(
                PlantillaGlosaLicenciaSerializer(plantilla).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al obtener plantilla de glosa pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            obtener_plantilla_glosa_licencia(pk)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = PlantillaGlosaLicenciaWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            plantilla = actualizar_plantilla_glosa_licencia(pk, serializer.validated_data)
            return Response(
                PlantillaGlosaLicenciaSerializer(plantilla).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al actualizar plantilla de glosa pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_plantilla_glosa_licencia(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception('Error al eliminar plantilla de glosa pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NivelRiesgoListView(APIView):
    """
    GET /api/lf-itse/niveles-riesgo/

    Retorna los niveles de riesgo ordenados por id.

    Parámetros de query string
    --------------------------
    esta_activo : str  (opcional)
        'true'  → solo activos.
        'false' → solo inactivos.
        Si se omite se devuelven todos.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            param = request.query_params.get('esta_activo', '').strip().lower()

            if param == 'true':
                esta_activo = True
            elif param == 'false':
                esta_activo = False
            elif param == '':
                esta_activo = None
            else:
                return Response(
                    {'error': "El parámetro 'esta_activo' debe ser 'true' o 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            niveles = listar_niveles_riesgo(esta_activo)
            serializer = NivelRiesgoSerializer(niveles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar niveles de riesgo')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EstadosInactivosItseListView(APIView):
    """
    GET /api/lf-itse/estados/inactivos-itse/

    Lista los estados inactivos que pueden aplicarse a un ITSE
    (``esta_activo = FALSE`` y ``es_para_itse = TRUE``).

    Equivalente PostgreSQL de la consulta SQL Server original::

        SELECT id, nombre, es_para_lf, es_para_itse, esta_activo
        FROM estados
        WHERE esta_activo = FALSE AND es_para_itse = TRUE

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            estados = listar_estados_inactivos_para_itse()
            return Response(estados, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Error al listar estados inactivos para ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EstadosInactivosLfListView(APIView):
    """
    GET /api/lf-itse/estados/inactivos-lf/

    Lista los estados inactivos que pueden aplicarse a una licencia de
    funcionamiento (``esta_activo = FALSE`` y ``es_para_lf = TRUE``).

    Equivalente PostgreSQL de la consulta SQL Server original::

        SELECT id, nombre, es_para_lf, es_para_itse, esta_activo
        FROM estados
        WHERE esta_activo = FALSE AND es_para_lf = TRUE

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            estados = listar_estados_inactivos_para_lf()
            return Response(estados, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Error al listar estados inactivos para LF')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TipoLicenciaListView(APIView):
    """
    GET /api/lf-itse/tipos-licencia/

    Retorna los tipos de licencia ordenados por id.

    Parámetros de query string
    --------------------------
    esta_activo : str  (opcional)
        'true'  → solo activos.
        'false' → solo inactivos.
        Si se omite se devuelven todos.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            param = request.query_params.get('esta_activo', '').strip().lower()

            if param == 'true':
                esta_activo = True
            elif param == 'false':
                esta_activo = False
            elif param == '':
                esta_activo = None
            else:
                return Response(
                    {'error': "El parámetro 'esta_activo' debe ser 'true' o 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tipos = listar_tipos_licencia(esta_activo)
            serializer = TipoLicenciaSerializer(tipos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar tipos de licencia')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ZonificacionListView(APIView):
    """
    GET  /api/lf-itse/zonificaciones/
        Retorna las zonificaciones ordenadas por id.
        Parámetro opcional: esta_activo (true/false).

    POST /api/lf-itse/zonificaciones/
        Crea una nueva zonificacion.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            param = request.query_params.get('esta_activo', '').strip().lower()

            if param == 'true':
                esta_activo = True
            elif param == 'false':
                esta_activo = False
            elif param == '':
                esta_activo = None
            else:
                return Response(
                    {'error': "El parámetro 'esta_activo' debe ser 'true' o 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            zonificaciones = listar_zonificaciones(esta_activo)
            serializer = ZonificacionSerializer(zonificaciones, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar zonificaciones')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        serializer = ZonificacionWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            zonificacion = crear_zonificacion(
                data=serializer.validated_data,
                usuario=request.user,
            )
            return Response(
                ZonificacionSerializer(zonificacion).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al crear zonificacion')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ZonificacionDetailView(APIView):
    """
    GET    /api/lf-itse/zonificaciones/<pk>/
        Retorna una zonificacion específica.

    PUT    /api/lf-itse/zonificaciones/<pk>/
        Actualiza una zonificacion.

    DELETE /api/lf-itse/zonificaciones/<pk>/
        Elimina físicamente una zonificacion.
        Retorna 409 si tiene licencias de funcionamiento asociadas.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            zonificacion = obtener_zonificacion(pk)
            return Response(
                ZonificacionSerializer(zonificacion).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al obtener zonificacion pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            zonificacion_instance = obtener_zonificacion(pk)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = ZonificacionWriteSerializer(zonificacion_instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            zonificacion = actualizar_zonificacion(pk, serializer.validated_data)
            return Response(
                ZonificacionSerializer(zonificacion).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al actualizar zonificacion pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_zonificacion(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ProtectedError:
            return Response(
                {'error': 'No se puede eliminar: la zonificación está asignada a licencias de funcionamiento.'},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar zonificacion pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GiroListCreateView(APIView):
    """
    GET  /api/lf-itse/giros/
        Lista todos los giros ordenados por nombre.

    POST /api/lf-itse/giros/
        Crea un nuevo giro.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            giros = listar_giros()
            serializer = GiroSerializer(giros, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar giros')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        serializer = GiroWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            giro = crear_giro(
                data=serializer.validated_data,
                usuario=request.user,
            )
            return Response(
                GiroSerializer(giro).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al crear giro')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GiroDetailView(APIView):
    """
    GET    /api/lf-itse/giros/<pk>/
        Retorna un giro específico.

    PUT    /api/lf-itse/giros/<pk>/
        Actualiza un giro.

    DELETE /api/lf-itse/giros/<pk>/
        Elimina físicamente un giro.
        Retorna 409 si está referenciado por licencias o certificados ITSE.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            giro = obtener_giro(pk)
            return Response(
                GiroSerializer(giro).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al obtener giro pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            giro_instance = obtener_giro(pk)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = GiroWriteSerializer(giro_instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            giro = actualizar_giro(pk, serializer.validated_data, request.user)
            return Response(
                GiroSerializer(giro).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al actualizar giro pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_giro(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ProtectedError:
            return Response(
                {'error': 'No se puede eliminar: el giro está asignado a licencias o certificados ITSE.'},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar giro pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GirosBuscarView(APIView):
    """
    GET /api/lf-itse/giros/buscar/

    Busca giros por nombre o código CIIU, con filtro opcional por estado.

    Parámetros de query string
    --------------------------
    busqueda   : str   (opcional)
        Texto libre que se busca en ``nombre`` (parcial) y en ``ciiu_id``
        (exacto, solo cuando el valor es numérico).
        Si se omite se devuelven todos los registros.
    esta_activo : str  (opcional)
        'true'  → solo activos.
        'false' → solo inactivos.
        Si se omite se devuelven todos.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            busqueda = request.query_params.get('busqueda', '').strip() or None

            param = request.query_params.get('esta_activo', '').strip().lower()
            if param == 'true':
                esta_activo = True
            elif param == 'false':
                esta_activo = False
            elif param == '':
                esta_activo = None
            else:
                return Response(
                    {'error': "El parámetro 'esta_activo' debe ser 'true' o 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            giros = buscar_giros(busqueda=busqueda, esta_activo=esta_activo)
            serializer = GiroSerializer(giros, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al buscar giros')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseGirosListView(APIView):
    """
    GET /api/lf-itse/itse/<id>/giros/

    Lista los giros asociados a un ITSE.

    Parámetros de ruta
    ------------------
    pk : int
        PK del ITSE.

    Retorna
    -------
    200  Lista de giros con: id, itse_id, giro_id, ciiu_id, nombre.
    404  Si el ITSE no existe.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from .models import Itse

        try:
            if not Itse.objects.filter(pk=pk).exists():
                return Response(
                    {'error': 'El ITSE no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            giros = listar_giros_por_itse(pk)
            return Response(giros, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Error al listar giros del ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseEstadosListView(APIView):
    """
    GET /api/lf-itse/itse/<pk>/estados/

    Lista el historial de estados de un ITSE.

    Parámetros de ruta
    ------------------
    pk : int
        PK del ITSE.

    Retorna
    -------
    200  Lista de estados con: id, itse_id, estado_id, fecha_estado,
         documento, observaciones, usuario_id, fecha_digitacion,
         estado_nombre, es_para_lf, es_para_itse, esta_activo.
    404  Si el ITSE no existe.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            if not Itse.objects.filter(pk=pk).exists():
                return Response(
                    {'error': 'El ITSE no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            estados = listar_estados_itse(pk)
            return Response(estados, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Error al listar estados del ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoGirosListView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/<id>/giros/

    Lista los giros asociados a una licencia de funcionamiento.

    Parámetros de ruta
    ------------------
    pk : int
        PK de la licencia de funcionamiento.

    Retorna
    -------
    200  Lista de giros con: id, licencia_funcionamiento_id, giro_id,
         ciiu_id, nombre.
    404  Si la licencia no existe.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from .models import LicenciaFuncionamiento
        try:
            if not LicenciaFuncionamiento.objects.filter(pk=pk).exists():
                return Response(
                    {'error': 'La licencia de funcionamiento no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            giros = listar_giros_por_licencia(pk)
            return Response(giros, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Error al listar giros de la licencia')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoEstadosListView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/<pk>/estados/

    Lista el historial de estados de una licencia de funcionamiento.

    Parámetros de ruta
    ------------------
    pk : int
        PK de la licencia de funcionamiento.

    Retorna
    -------
    200  Lista de estados con: id, licencia_funcionamiento_id, estado_id,
         fecha_estado, documento, observaciones, usuario_id, fecha_digitacion,
         estado_nombre, es_para_lf, es_para_itse, esta_activo.
    404  Si la licencia no existe.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            if not LicenciaFuncionamiento.objects.filter(pk=pk).exists():
                return Response(
                    {'error': 'La licencia de funcionamiento no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            estados = listar_estados_licencia(pk)
            return Response(estados, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Error al listar estados de la licencia')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoUpdateView(APIView):
    """
    PUT /api/lf-itse/licencias-funcionamiento/<pk>/

    Modifica una licencia de funcionamiento existente.

    Parámetros de ruta
    ------------------
    pk : int
        PK de la licencia a modificar.

    Body (JSON)
    -----------
    Todos los campos de la licencia (ver ``LicenciaFuncionamientoUpdateSerializer``).
    Los giros se reemplazan completamente con la lista enviada.

    Respuestas
    ----------
    200  Licencia modificada correctamente.
    400  Datos de entrada inválidos.
    404  La licencia no existe.
    409  Número de licencia duplicado, recibo de pago duplicado o
         expediente con licencia denegada.
    500  Error interno.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        from .models import LicenciaFuncionamiento
        serializer = LicenciaFuncionamientoUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            licencia = modificar_licencia(pk, serializer.validated_data, request.user)
            return Response(
                {'id': licencia.id, 'mensaje': 'Licencia modificada correctamente.'},
                status=status.HTTP_200_OK,
            )

        except LicenciaFuncionamiento.DoesNotExist:
            return Response(
                {'error': 'La licencia de funcionamiento no existe.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (LicenciaDenegadaError, LicenciaDuplicadaError, ReciboPagoDuplicadoError) as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception('Error al modificar la licencia de funcionamiento')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        """
        DELETE /api/lf-itse/licencias-funcionamiento/<pk>/

        Elimina la licencia de funcionamiento y todos sus registros dependientes:
          - licencias_funcionamiento_estados
          - licencias_funcionamiento_giros
          - licencias_funcionamiento_archivos y sus archivos físicos
          - licencias_funcionamiento

        Respuestas
        ----------
        204  Eliminación exitosa.
        404  La licencia no existe.
        409  La licencia tiene licencias dependientes.
        500  Error interno.

        Requiere autenticación JWT.
        """
        try:
            eliminar_licencia(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except LicenciaTieneDependientesError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar la licencia de funcionamiento pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoNotificacionView(APIView):
    """
    PATCH /api/lf-itse/licencias-funcionamiento/<pk>/notificacion/

    Registra la fecha de notificación de entrega de una licencia de
    funcionamiento actualizando la columna ``fecha_notificacion``.

    Parámetros de ruta
    ------------------
    pk : int
        PK de la licencia.

    Body (JSON)
    -----------
    fecha_notificacion : str  (formato YYYY-MM-DD)

    Respuestas
    ----------
    200  Fecha de notificación registrada correctamente.
    400  Datos de entrada inválidos.
    404  La licencia no existe.
    409  La fecha de notificación es anterior a la fecha de emisión.
    500  Error interno.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        from .models import LicenciaFuncionamiento
        serializer = LicenciaFuncionamientoNotificacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            registrar_notificacion(
                pk,
                serializer.validated_data['fecha_notificacion'],
                request.user,
            )
            return Response(
                {'mensaje': 'Fecha de notificación registrada correctamente.'},
                status=status.HTTP_200_OK,
            )
        except LicenciaFuncionamiento.DoesNotExist:
            return Response(
                {'error': 'La licencia de funcionamiento no existe.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except NotificacionFechaInvalidaError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception('Error al registrar la notificación de la licencia')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseInactivarView(APIView):
    """
    POST /api/lf-itse/itse/inactivar/

    Registra la inactivación de un ITSE insertando una fila en ``itse_estados``.

    Body (JSON)
    -----------
    itse_id       : int
    estado_id     : int
    fecha_estado  : str  (YYYY-MM-DD)
    documento     : str  (máx. 100 caracteres)
    observaciones : str  (máx. 1000 caracteres)

    ``usuario_id`` y ``fecha_digitacion`` se asignan automáticamente desde el
    JWT y la fecha/hora del servidor.

    Respuestas
    ----------
    201  Registro creado correctamente.
    400  Datos de entrada inválidos.
    404  El ITSE no existe.
    409  Ya existe un registro con el mismo par itse + estado.
    500  Error interno.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Itse
        serializer = ItseInactivarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            registro = registrar_inactivacion_itse(
                itse_id=data['itse_id'],
                estado_id=data['estado_id'],
                fecha_estado=data['fecha_estado'],
                documento=data['documento'].strip(),
                observaciones=data['observaciones'].strip(),
                usuario=request.user,
            )
            return Response(
                {
                    'id': registro.id,
                    'mensaje': 'Inactivación del ITSE registrada correctamente.',
                },
                status=status.HTTP_201_CREATED,
            )
        except Itse.DoesNotExist:
            return Response(
                {'error': 'El ITSE no existe.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except EstadoInactivacionItseDuplicadoError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception('Error al registrar la inactivación del ITSE')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciaFuncionamientoInactivarView(APIView):
    """
    POST /api/lf-itse/licencias-funcionamiento/inactivar/

    Registra la inactivación de una licencia de funcionamiento insertando una
    fila en ``licencias_funcionamiento_estados``.

    Body (JSON)
    -----------
    licencia_funcionamiento_id : int
    estado_id                  : int
    fecha_estado               : str  (YYYY-MM-DD)
    documento                  : str  (máx. 100 caracteres)
    observaciones              : str  (máx. 1000 caracteres)

    ``usuario_id`` y ``fecha_digitacion`` se asignan automáticamente desde el
    JWT y la fecha/hora del servidor.

    Respuestas
    ----------
    201  Registro creado correctamente.
    400  Datos de entrada inválidos.
    404  La licencia de funcionamiento no existe.
    409  Ya existe un registro con el mismo par licencia + estado.
    500  Error interno.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import LicenciaFuncionamiento
        serializer = LicenciaFuncionamientoInactivarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            registro = registrar_inactivacion_licencia(
                licencia_funcionamiento_id=data['licencia_funcionamiento_id'],
                estado_id=data['estado_id'],
                fecha_estado=data['fecha_estado'],
                documento=data['documento'].strip(),
                observaciones=data['observaciones'].strip(),
                usuario=request.user,
            )
            return Response(
                {
                    'id': registro.id,
                    'mensaje': 'Inactivación de la licencia registrada correctamente.',
                },
                status=status.HTTP_201_CREATED,
            )
        except LicenciaFuncionamiento.DoesNotExist:
            return Response(
                {'error': 'La licencia de funcionamiento no existe.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except EstadoInactivacionDuplicadoError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception('Error al registrar la inactivación de la licencia')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciasFuncionamientoConsultaView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/consulta/

    Busca licencias de funcionamiento según uno o más filtros opcionales.
    Si no se pasa ningún filtro, retorna todos los registros.

    Query params (todos opcionales, pero se requiere al menos uno)
    --------------------------------------------------------------
    numero_licencia              – int   número de licencia (exacto)
    numero_expediente            – int   número de expediente (exacto)
    anio_expediente              – int   año de recepción del expediente (exacto)
    emision_desde                – date  inicio del rango de fecha de emisión (YYYY-MM-DD)
    emision_hasta                – date  fin del rango de fecha de emisión (YYYY-MM-DD)
    titular_nombre               – str   búsqueda parcial en apellidos + nombres del titular
    titular_numero_documento     – str   número de documento exacto del titular
    conductor_nombre             – str   búsqueda parcial en apellidos + nombres del conductor
    conductor_numero_documento   – str   número de documento exacto del conductor
    nombre_comercial             – str   búsqueda parcial en nombre comercial
    nivel_riesgo_id              – int   ID del nivel de riesgo
    direccion                    – str   búsqueda parcial en dirección
    zonificacion_id              – int   ID de la zonificación
    numero_recibo_pago           – str   número de recibo de pago (exacto)
    fecha_notificacion_desde     – date  inicio del rango de fecha de notificación (YYYY-MM-DD)
    fecha_notificacion_hasta     – date  fin del rango de fecha de notificación (YYYY-MM-DD)
    esta_activo                  – bool  true = solo activas, false = solo inactivas
    giro_nombre                  – str   búsqueda parcial en nombre de giro

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = LicenciasFuncionamientoConsultaQuerySerializer(
                data=request.query_params.dict()
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            resultados = consultar_licencias(serializer.validated_data)
            return Response(resultados, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al consultar licencias de funcionamiento')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LicenciasFuncionamientoReporteView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/reporte/

    Genera el reporte de licencias de funcionamiento aplicando los filtros
    opcionales recibidos como query params.

    Query params (todos opcionales)
    --------------------------------
    numero_licencia              – int
    numero_expediente            – int
    anio_expediente              – int
    emision_desde                – date  (YYYY-MM-DD)
    emision_hasta                – date  (YYYY-MM-DD; se requiere junto con emision_desde)
    titular_nombre               – str   (búsqueda parcial)
    titular_numero_documento     – str
    conductor_nombre             – str   (búsqueda parcial)
    conductor_numero_documento   – str
    nombre_comercial             – str   (búsqueda parcial)
    vigencia_desde               – date  (YYYY-MM-DD)
    vigencia_hasta               – date  (YYYY-MM-DD; se requiere junto con vigencia_desde)
    nivel_riesgo_id              – int
    direccion                    – str   (búsqueda parcial)
    zonificacion_id              – int
    numero_recibo_pago           – str
    fecha_notificacion_desde     – date  (YYYY-MM-DD)
    fecha_notificacion_hasta     – date  (YYYY-MM-DD; se requiere junto con fecha_notificacion_desde)
    esta_activo                  – bool  (true / false)
    giro_nombre                  – str   (búsqueda parcial)

    Respuesta
    ---------
    200 OK  – lista de licencias (puede estar vacía).
    400     – parámetros de consulta inválidos.
    500     – error interno del servidor.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = LicenciasFuncionamientoReporteQuerySerializer(
                data=request.query_params.dict()
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            resultados = reporte_licencias(serializer.validated_data)
            return Response(resultados, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al generar el reporte de licencias de funcionamiento')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InspectorListCreateView(APIView):
    """
    GET  /api/lf-itse/inspectores/
        Lista todos los inspectores ordenados por apellido paterno y nombres.

    POST /api/lf-itse/inspectores/
        Crea un nuevo inspector.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            inspectores = listar_inspectores()
            serializer = InspectorSerializer(inspectores, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar inspectores')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        serializer = InspectorWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            inspector = crear_inspector(
                data=serializer.validated_data,
                usuario=request.user,
            )
            return Response(
                InspectorSerializer(inspector).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al crear inspector')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InspectorDetailView(APIView):
    """
    GET    /api/lf-itse/inspectores/<pk>/
        Retorna un inspector específico.

    PUT    /api/lf-itse/inspectores/<pk>/
        Actualiza un inspector.

    DELETE /api/lf-itse/inspectores/<pk>/
        Elimina físicamente un inspector.
        Retorna 409 si está asignado a certificados ITSE.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            inspector = obtener_inspector(pk)
            return Response(
                InspectorSerializer(inspector).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al obtener inspector pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            inspector_instance = obtener_inspector(pk)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = InspectorWriteSerializer(inspector_instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            inspector = actualizar_inspector(pk, serializer.validated_data)
            return Response(
                InspectorSerializer(inspector).data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception('Error al actualizar inspector pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            eliminar_inspector(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ProtectedError:
            return Response(
                {'error': 'No se puede eliminar: el inspector está asignado a certificados ITSE.'},
                status=status.HTTP_409_CONFLICT,
            )

        except Exception as e:
            logger.exception('Error al eliminar inspector pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InspectorBuscarView(APIView):
    """
    GET /api/lf-itse/inspectores/buscar/

    Busca inspectores por nombre completo (apellido paterno + apellido materno
    + nombres), insensible a mayúsculas y minúsculas.

    Parámetros de query string
    --------------------------
    busqueda : str (opcional)
        Texto libre a buscar en el nombre completo del inspector.
        Si se omite se devuelven todos los registros.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            busqueda = request.query_params.get('busqueda', '').strip() or None
            inspectores = buscar_inspectores(busqueda=busqueda)
            serializer = InspectorSerializer(inspectores, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al buscar inspectores')
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ItseInspectoresView(APIView):
    """
    GET  /api/lf-itse/itse/<pk>/inspectores/
        Lista los inspectores asignados al certificado ITSE.

    POST /api/lf-itse/itse/<pk>/inspectores/
        Asigna un inspector al certificado ITSE.
        Body: { inspector_id: int }

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            if not Itse.objects.filter(pk=pk).exists():
                return Response(
                    {'error': 'El certificado ITSE no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            inspectores = listar_itse_inspectores(pk)
            return Response(inspectores, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al listar inspectores del ITSE pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, pk):
        serializer = ItseInspectorCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            itse_inspector = crear_itse_inspector(
                itse_id=pk,
                inspector_id=serializer.validated_data['inspector_id'],
                usuario=request.user,
            )
            return Response(
                {'id': itse_inspector.id, 'itse_id': pk,
                 'inspector_id': itse_inspector.inspector_id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception('Error al asignar inspector al ITSE pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        """Elimina TODOS los inspectores asignados al certificado ITSE."""
        try:
            if not Itse.objects.filter(pk=pk).exists():
                return Response(
                    {'error': 'El certificado ITSE no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            eliminados = eliminar_itse_inspectores(pk)
            return Response({'eliminados': eliminados}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Error al eliminar inspectores del ITSE pk=%s', pk)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS — Verificación QR
# ══════════════════════════════════════════════════════════════════════════════

class VerificacionPublicaThrottle(AnonRateThrottle):
    rate = '60/min'


class ConfigPublicaView(APIView):
    """
    GET /api/lf-itse/config-publica/

    Retorna la configuración pública del sistema (sin autenticación).
    Permite al frontend saber si el QR de verificación está habilitado
    y cuál es la URL base de la aplicación.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'qr_verificacion_habilitado': django_settings.QR_VERIFICACION_HABILITADO,
            'qr_url_verificar_licencia': django_settings.QR_URL_VERIFICAR_LICENCIA,
            'qr_url_verificar_itse': django_settings.QR_URL_VERIFICAR_ITSE,
        })


class VerificarLicenciaPublicaView(APIView):
    """
    GET /api/lf-itse/verificar/licencia/<uuid>/

    Verificación pública de licencia de funcionamiento.
    Retorna datos mínimos del certificado para validar su autenticidad.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [VerificacionPublicaThrottle]

    def get(self, request, uuid):
        licencia = LicenciaFuncionamiento.objects.filter(
            uuid=uuid,
        ).select_related(
            'nivel_riesgo', 'titular',
        ).prefetch_related(
            'giros__giro',
        ).first()

        if not licencia:
            return Response(
                {'error': 'Documento no encontrado o no disponible para consulta pública.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        tiene_estado_inactivo = licencia.historial_estados.filter(
            estado__esta_activo=False,
        ).exists()
        activa = not tiene_estado_inactivo

        if activa and not licencia.es_vigencia_indeterminada and licencia.fecha_fin_vigencia:
            activa = licencia.fecha_fin_vigencia >= date.today()

        if licencia.es_vigencia_indeterminada:
            vigencia = 'Indeterminada'
        elif licencia.fecha_inicio_vigencia and licencia.fecha_fin_vigencia:
            vigencia = f'{licencia.fecha_inicio_vigencia.isoformat()} - {licencia.fecha_fin_vigencia.isoformat()}'
        else:
            vigencia = '-'

        titular = licencia.titular
        titular_nombre = f'{titular.apellido_paterno} {titular.apellido_materno} {titular.nombres}'.strip() if titular else '-'

        giros = [
            {
                'ciiu': str(lg.giro.ciiu_id).zfill(4) if lg.giro.ciiu_id else '-',
                'nombre': lg.giro.nombre,
            }
            for lg in licencia.giros.all()
        ]

        return Response({
            'tipo': 'licencia_funcionamiento',
            'numero_licencia': licencia.numero_licencia,
            'fecha_emision': licencia.fecha_emision.isoformat(),
            'vigencia': vigencia,
            'nivel_riesgo': licencia.nivel_riesgo.nombre if licencia.nivel_riesgo else '',
            'horario': f'{licencia.hora_desde}:00 - {licencia.hora_hasta}:00' if licencia.hora_desde is not None and licencia.hora_hasta is not None else '',
            'titular': titular_nombre,
            'nombre_comercial': licencia.nombre_comercial,
            'actividad_economica': licencia.actividad,
            'direccion': licencia.direccion,
            'area': f'{licencia.area} m²' if licencia.area is not None else '-',
            'giros': giros,
            'activa': activa,
            'mensaje': 'Documento registrado en la Municipalidad Distrital de El Porvenir.',
        })


class VerificarItsePublicaView(APIView):
    """
    GET /api/lf-itse/verificar/itse/<uuid>/

    Verificación pública de certificado ITSE.
    Retorna datos mínimos del certificado para validar su autenticidad.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [VerificacionPublicaThrottle]

    def get(self, request, uuid):
        itse = Itse.objects.filter(
            uuid=uuid,
        ).select_related(
            'nivel_riesgo', 'titular',
        ).prefetch_related(
            'giros__giro',
        ).first()

        if not itse:
            return Response(
                {'error': 'Documento no encontrado o no disponible para consulta pública.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        tiene_estado_inactivo = itse.historial_estados.filter(
            estado__esta_activo=False,
        ).exists()
        activa = not tiene_estado_inactivo

        if activa:
            activa = itse.fecha_caducidad >= date.today()

        titular = itse.titular
        titular_nombre = f'{titular.apellido_paterno} {titular.apellido_materno} {titular.nombres}'.strip() if titular else '-'

        giros = [
            {
                'ciiu': str(ig.giro.ciiu_id).zfill(4) if ig.giro.ciiu_id else '-',
                'nombre': ig.giro.nombre,
            }
            for ig in itse.giros.all()
        ]

        return Response({
            'tipo': 'certificado_itse',
            'numero_itse': itse.numero_itse,
            'fecha_expedicion': itse.fecha_expedicion.isoformat(),
            'fecha_solicitud_renovacion': itse.fecha_solicitud_renovacion.isoformat(),
            'fecha_caducidad': itse.fecha_caducidad.isoformat(),
            'nivel_riesgo': itse.nivel_riesgo.nombre if itse.nivel_riesgo else '',
            'titular': titular_nombre,
            'nombre_comercial': itse.nombre_comercial,
            'direccion': itse.direccion,
            'area': f'{itse.area} m²' if itse.area is not None else '-',
            'capacidad_aforo': itse.capacidad_aforo,
            'giros': giros,
            'activa': activa,
            'mensaje': 'Documento registrado en la Municipalidad Distrital de El Porvenir.',
        })




# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS — Búsqueda desde portal web institucional
# ══════════════════════════════════════════════════════════════════════════════

MAX_RESULTADOS_BUSQUEDA_PUBLICA = 50


class BusquedaPublicaThrottle(AnonRateThrottle):
    rate = '30/min'

class BuscarLicenciaPublicaView(APIView):
    """
    GET /api/lf-itse/publico/licencias/buscar/?numero_licencia=1
    GET /api/lf-itse/publico/licencias/buscar/?nombre_comercial=cafeteria

    Búsqueda pública de licencias de funcionamiento para el portal web.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [BusquedaPublicaThrottle]

    def get(self, request):
        numero_licencia = request.query_params.get('numero_licencia', '').strip()
        nombre_comercial = request.query_params.get('nombre_comercial', '').strip()

        if not numero_licencia and not nombre_comercial:
            return Response(
                {'error': 'Debe proporcionar al menos un criterio de búsqueda: numero_licencia o nombre_comercial.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = LicenciaFuncionamiento.objects.select_related(
            'nivel_riesgo', 'titular',
        ).prefetch_related(
            'giros__giro',
            'historial_estados__estado',
        )

        if numero_licencia:
            if not numero_licencia.isdigit():
                return Response(
                    {'error': 'El número de licencia debe ser un valor numérico.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(numero_licencia=int(numero_licencia))
        elif nombre_comercial:
            if len(nombre_comercial) < 3:
                return Response(
                    {'error': 'El nombre comercial debe tener al menos 3 caracteres.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(nombre_comercial__icontains=nombre_comercial)

        licencias = qs[:MAX_RESULTADOS_BUSQUEDA_PUBLICA]

        resultados = []
        for licencia in licencias:
            tiene_estado_inactivo = any(
                not he.estado.esta_activo for he in licencia.historial_estados.all()
            )
            activa = not tiene_estado_inactivo

            if activa and not licencia.es_vigencia_indeterminada and licencia.fecha_fin_vigencia:
                activa = licencia.fecha_fin_vigencia >= date.today()

            if licencia.es_vigencia_indeterminada:
                vigencia = 'Indeterminada'
            elif licencia.fecha_inicio_vigencia and licencia.fecha_fin_vigencia:
                vigencia = f'{licencia.fecha_inicio_vigencia.isoformat()} - {licencia.fecha_fin_vigencia.isoformat()}'
            else:
                vigencia = '-'

            titular = licencia.titular
            titular_nombre = f'{titular.apellido_paterno} {titular.apellido_materno} {titular.nombres}'.strip() if titular else '-'

            giros = [
                {
                    'ciiu': str(lg.giro.ciiu_id).zfill(4) if lg.giro.ciiu_id else '-',
                    'nombre': lg.giro.nombre,
                }
                for lg in licencia.giros.all()
            ]

            resultados.append({
                'numero_licencia': licencia.numero_licencia,
                'fecha_emision': licencia.fecha_emision.isoformat(),
                'vigencia': vigencia,
                'nivel_riesgo': licencia.nivel_riesgo.nombre if licencia.nivel_riesgo else '',
                'horario': f'{licencia.hora_desde}:00 - {licencia.hora_hasta}:00' if licencia.hora_desde is not None and licencia.hora_hasta is not None else '',
                'titular': titular_nombre,
                'nombre_comercial': licencia.nombre_comercial,
                'actividad_economica': licencia.actividad,
                'direccion': licencia.direccion,
                'area': f'{licencia.area} m²' if licencia.area is not None else '-',
                'giros': giros,
                'activa': activa,
            })

        return Response(resultados)


class BuscarItsePublicaView(APIView):
    """
    GET /api/lf-itse/publico/itse/buscar/?numero_itse=1
    GET /api/lf-itse/publico/itse/buscar/?nombre_comercial=cafeteria

    Búsqueda pública de certificados ITSE para el portal web.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [BusquedaPublicaThrottle]

    def get(self, request):
        numero_itse = request.query_params.get('numero_itse', '').strip()
        nombre_comercial = request.query_params.get('nombre_comercial', '').strip()

        if not numero_itse and not nombre_comercial:
            return Response(
                {'error': 'Debe proporcionar al menos un criterio de búsqueda: numero_itse o nombre_comercial.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Itse.objects.select_related(
            'nivel_riesgo', 'titular',
        ).prefetch_related(
            'giros__giro',
            'historial_estados__estado',
        )

        if numero_itse:
            if not numero_itse.isdigit():
                return Response(
                    {'error': 'El número de ITSE debe ser un valor numérico.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(numero_itse=int(numero_itse))
        elif nombre_comercial:
            if len(nombre_comercial) < 3:
                return Response(
                    {'error': 'El nombre comercial debe tener al menos 3 caracteres.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(nombre_comercial__icontains=nombre_comercial)

        itses = qs[:MAX_RESULTADOS_BUSQUEDA_PUBLICA]

        resultados = []
        for itse in itses:
            tiene_estado_inactivo = any(
                not he.estado.esta_activo for he in itse.historial_estados.all()
            )
            activa = not tiene_estado_inactivo

            if activa:
                activa = itse.fecha_caducidad >= date.today()

            titular = itse.titular
            titular_nombre = f'{titular.apellido_paterno} {titular.apellido_materno} {titular.nombres}'.strip() if titular else '-'

            giros = [
                {
                    'ciiu': str(ig.giro.ciiu_id).zfill(4) if ig.giro.ciiu_id else '-',
                    'nombre': ig.giro.nombre,
                }
                for ig in itse.giros.all()
            ]

            resultados.append({
                'numero_itse': itse.numero_itse,
                'fecha_expedicion': itse.fecha_expedicion.isoformat(),
                'fecha_solicitud_renovacion': itse.fecha_solicitud_renovacion.isoformat(),
                'fecha_caducidad': itse.fecha_caducidad.isoformat(),
                'nivel_riesgo': itse.nivel_riesgo.nombre if itse.nivel_riesgo else '',
                'titular': titular_nombre,
                'nombre_comercial': itse.nombre_comercial,
                'direccion': itse.direccion,
                'area': f'{itse.area} m²' if itse.area is not None else '-',
                'capacidad_aforo': itse.capacidad_aforo,
                'giros': giros,
                'activa': activa,
            })

        return Response(resultados)


# ── PDF de licencia de funcionamiento ────────────────────────────────────────

class LicenciaFuncionamientoPdfView(APIView):
    """
    GET /api/lf-itse/licencias-funcionamiento/<pk>/pdf/

    Genera y retorna un PDF del certificado de licencia de funcionamiento
    con tamaño de página 240 mm × 160 mm.

    Requiere autenticación JWT.
    """

    permission_classes = [IsAuthenticated]

    PAGE_W_MM = 240
    PAGE_H_MM = 160

    MESES = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
    ]

    def get(self, request, pk):
        from io import BytesIO

        import qrcode
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas as pdf_canvas

        from .models import (
            LicenciaFuncionamientoGiro,
            PersonaDocumento,
        )
        from .services.licencia_funcionamiento import buscar_licencias

        rows = buscar_licencias('ID', str(pk))
        if not rows:
            return Response(
                {'error': 'Licencia de funcionamiento no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        lic = rows[0]

        giros_qs = (
            LicenciaFuncionamientoGiro.objects
            .filter(licencia_funcionamiento_id=pk)
            .select_related('giro')
        )
        giros_nombres = [g.giro.nombre for g in giros_qs]

        doc_titular_texto = ''
        titular_id = lic.get('titular_id')
        if titular_id:
            doc = (
                PersonaDocumento.objects
                .filter(persona_id=titular_id, tipo_documento_identidad__codigo__in=['01', '04'])
                .select_related('tipo_documento_identidad')
                .order_by('tipo_documento_identidad__codigo')
                .first()
            )
            if doc:
                doc_titular_texto = f'{doc.tipo_documento_identidad.nombre} N\u00b0{doc.numero_documento}'

        anio_emision = lic['fecha_emision'].year if lic.get('fecha_emision') else ''
        num_lic = f"{str(lic['numero_licencia']).zfill(4)}-{anio_emision}"

        num_exp_raw = lic.get('numero_expediente', '')
        anio_recepcion = ''
        if lic.get('fecha_recepcion'):
            fr = lic['fecha_recepcion']
            anio_recepcion = fr.year if hasattr(fr, 'year') else ''
        num_exp = f"{num_exp_raw}-{anio_recepcion}"

        if lic.get('es_vigencia_indeterminada'):
            vencimiento = 'INDEFINIDA'
        elif lic.get('fecha_inicio_vigencia') and lic.get('fecha_fin_vigencia'):
            fi = lic['fecha_inicio_vigencia']
            ff = lic['fecha_fin_vigencia']
            vencimiento = f"{fi.strftime('%d/%m/%Y')} - {ff.strftime('%d/%m/%Y')}"
        else:
            vencimiento = '-'

        titular_nombre = (lic.get('titular_nombre') or '').upper()
        titular_ruc = lic.get('titular_ruc') or ''
        nombre_comercial = (lic.get('nombre_comercial') or '').upper()
        direccion = (lic.get('direccion') or '').upper()
        actividad = lic.get('actividad') or '-'
        area_val = lic.get('area')
        area_texto = f"{int(area_val)} m\u00b2" if area_val is not None else '-'
        zonificacion_codigo = lic.get('zonificacion_codigo') or 'RDM'
        tipo_letrero = lic.get('tipo_letrero_nombre') or ''
        medidas = lic.get('medidas') or ''
        hora_desde = lic.get('hora_desde')
        hora_hasta = lic.get('hora_hasta')
        dias_atencion = lic.get('dias_atencion') or ''
        glosa = lic.get('glosa') or ''

        fecha_larga = ''
        if lic.get('fecha_emision'):
            fe = lic['fecha_emision']
            fecha_larga = f"{str(fe.day).zfill(2)} de {self.MESES[fe.month - 1]} del {fe.year}"

        qr_habilitado = django_settings.QR_VERIFICACION_HABILITADO
        qr_url_base = django_settings.QR_URL_VERIFICAR_LICENCIA
        lic_uuid = str(lic.get('uuid') or '')
        qr_url = None
        if qr_habilitado and qr_url_base and lic_uuid:
            qr_url = f"{qr_url_base.rstrip('/')}/{lic_uuid}"

        # ── Build PDF ──
        page_w = self.PAGE_W_MM * mm
        page_h = self.PAGE_H_MM * mm
        buf = BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=(page_w, page_h))

        color_brown = (74 / 255, 32 / 255, 0)

        def set_brown():
            c.setFillColorRGB(*color_brown)
            c.setStrokeColorRGB(*color_brown)

        set_brown()

        # CSS px to PDF pt: 1 CSS px ≈ 0.75 pt
        def px(css_px):
            return css_px * 0.75

        # Margins matching HTML: padding 8mm top, 12mm sides
        pad_top = 8 * mm
        pad_side = 12 * mm
        # Fields inner padding: additional 9mm each side
        fields_pad = 9 * mm
        fields_x = pad_side + fields_pad
        fields_right = page_w - pad_side - fields_pad

        # Font sizes matching CSS px → pt
        fs_numlic = px(20)       # 20px
        fs_exp = px(18)          # 18px
        fs_title = px(18)        # 18px
        fs_subtitle = px(8.5)    # 8.5px
        fs_field = px(12)        # 12px
        fs_horario_label = px(11.5)
        fs_glosa = px(12.5)

        label_w = 34 * mm
        line_h = px(12) * 1.8    # 12px * 1.8 line-height

        def wrap_text(text, font_name, font_size, max_width):
            """Split text into lines that fit within max_width."""
            words = str(text).split()
            lines = []
            current = ''
            for word in words:
                test = f'{current} {word}'.strip()
                if c.stringWidth(test, font_name, font_size) <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
            return lines or ['']

        def draw_field(label, value, y_pos, label_font_size=fs_field, right_limit=None):
            """Draw a label: value field with underline, wrapping long values."""
            if right_limit is None:
                right_limit = fields_right
            c.setFont('Helvetica-Bold', label_font_size)
            c.drawString(fields_x, y_pos, label)
            colon_x = fields_x + label_w
            c.setFont('Helvetica-Bold', fs_field)
            c.drawString(colon_x, y_pos, ':')
            value_x = colon_x + 2 * mm
            available_w = right_limit - value_x
            lines = wrap_text(value, 'Helvetica-Bold', fs_field, available_w)
            c.setLineWidth(0.5)
            for i, text_line in enumerate(lines):
                ly = y_pos - (i * line_h)
                c.setFont('Helvetica-Bold', fs_field)
                c.drawString(value_x, ly, text_line)
                c.line(value_x, ly - 1, right_limit, ly - 1)
            total_lines = len(lines)
            return y_pos - (total_lines * line_h)

        # ── License number box ──
        box_x = pad_side + 52 * mm
        box_y = page_h - pad_top - 18 * mm - px(20) - 2 * mm
        c.setFont('Helvetica-Bold', fs_numlic)
        text_w = c.stringWidth(num_lic, 'Helvetica-Bold', fs_numlic)
        box_pad_x = 5 * mm
        box_pad_y = 2 * mm
        box_h = fs_numlic + box_pad_y * 2
        c.setLineWidth(3.5)
        c.rect(box_x, box_y, text_w + box_pad_x * 2, box_h)
        c.drawString(box_x + box_pad_x, box_y + box_pad_y, num_lic)

        # ── Expediente (top right) ──
        c.setFont('Helvetica-Bold', fs_exp)
        exp_x = page_w - pad_side - 33 * mm
        exp_y = page_h - pad_top - 14 * mm - fs_exp
        c.drawRightString(exp_x, exp_y, num_exp)

        # ── Vencimiento (below expediente) ──
        venc_x = page_w - pad_side - 23 * mm
        venc_y = exp_y - 3 * mm - fs_exp
        c.setFont('Helvetica-Bold', fs_exp)
        c.drawRightString(venc_x, venc_y, vencimiento)

        # ── Title ──
        title_y = box_y - 2 * mm - fs_title
        c.setFont('Helvetica-Bold', fs_title)
        c.drawCentredString(page_w / 2, title_y, 'CERTIFICADO DE LICENCIA DE FUNCIONAMIENTO')

        subtitle_y = title_y - 1 * mm - fs_subtitle
        c.setFont('Helvetica', fs_subtitle)
        c.drawCentredString(
            page_w / 2, subtitle_y,
            u'Ley Org\u00e1nica de Municipalidades N\u00b0 27972, '
            u'Ley Marco de Licencia de Funcionamiento N\u00b0 28976.',
        )

        # ── Fields ──
        current_y = subtitle_y - 3 * mm - line_h

        # OTORGADO A
        otorgado_value = titular_nombre
        if doc_titular_texto:
            otorgado_value += f'    {doc_titular_texto}'
        if titular_ruc:
            otorgado_value += f'    RUC N\u00b0{titular_ruc}'
        current_y = draw_field('OTORGADO A', otorgado_value, current_y)

        # GIRO O ACTIVIDAD
        current_y = draw_field('GIRO O ACTIVIDAD', actividad, current_y)

        # NOMBRE COMERCIAL
        current_y = draw_field('NOMBRE COMERCIAL', nombre_comercial, current_y)

        # DIRECCI\u00d3N
        current_y = draw_field(u'DIRECCI\u00d3N', direccion, current_y)

        # \u00c1REA COMERCIAL + C\u00d3DIGO CATASTRAL (split row)
        catastral_zone_w = 78 * mm
        area_right = fields_right - catastral_zone_w
        c.setFont('Helvetica-Bold', fs_field)
        c.drawString(fields_x, current_y, u'\u00c1REA COMERCIAL')
        c.drawString(fields_x + label_w, current_y, ':')
        area_value_x = fields_x + label_w + 2 * mm
        c.drawString(area_value_x, current_y, area_texto)
        c.setLineWidth(0.5)
        c.line(area_value_x, current_y - 1, area_right, current_y - 1)

        catastral_x = area_right + 2 * mm
        cat_label = u'C\u00d3DIGO CATASTRAL:'
        c.drawString(catastral_x, current_y, cat_label)
        cat_label_w = c.stringWidth(cat_label, 'Helvetica-Bold', fs_field)
        cat_value_x = catastral_x + cat_label_w + 2 * mm
        c.drawString(cat_value_x, current_y, zonificacion_codigo)
        c.line(cat_value_x, current_y - 1, fields_right, current_y - 1)
        current_y -= line_h

        # TIPO DE ANUNCIO (optional) + MEDIDAS
        if tipo_letrero:
            medidas_zone_w = 60 * mm if medidas else 0
            anuncio_right = fields_right - medidas_zone_w if medidas else fields_right
            current_y = draw_field('TIPO DE ANUNCIO', tipo_letrero, current_y, right_limit=anuncio_right)

            if medidas:
                medidas_x = fields_right - medidas_zone_w + 2 * mm
                row_y = current_y + line_h
                c.setFont('Helvetica-Bold', fs_field)
                c.drawString(medidas_x, row_y, 'MEDIDAS:')
                medidas_val_x = medidas_x + c.stringWidth('MEDIDAS:', 'Helvetica-Bold', fs_field) + 2 * mm
                c.setLineWidth(0.5)
                for i, medida in enumerate(medidas.split(';')):
                    y_m = row_y - (i * line_h)
                    c.drawString(medidas_val_x, y_m, medida.strip())
                    c.line(medidas_val_x, y_m - 1, fields_right, y_m - 1)

        # HORARIO DE ATENCI\u00d3N (optional)
        if hora_desde and hora_hasta:
            horario_texto = f'{dias_atencion} {hora_desde}:00 A {hora_hasta}:00 HORAS'
            current_y = draw_field(
                u'HORARIO DE ATENCI\u00d3N', horario_texto, current_y,
                label_font_size=fs_horario_label,
            )

        # ── GLOSA ──
        if glosa:
            current_y -= 1 * mm
            c.setFont('Helvetica-Bold', fs_glosa)
            glosa_w = fields_right - fields_x
            for raw_line in glosa.split('\n'):
                wrapped = wrap_text(raw_line.strip(), 'Helvetica-Bold', fs_glosa, glosa_w)
                for wl in wrapped:
                    c.drawString(fields_x, current_y, wl)
                    current_y -= px(12.5) * 1.4

        # ── FECHA ──
        current_y -= 1 * mm
        c.setFont('Helvetica-Bold', fs_glosa)
        c.drawRightString(fields_right, current_y, f'El Porvenir, {fecha_larga}')

        # ── QR ──
        if qr_url:
            qr_img = qrcode.make(qr_url, box_size=6, border=1)
            qr_buf = BytesIO()
            qr_img.save(qr_buf, format='PNG')
            qr_buf.seek(0)
            qr_reader = ImageReader(qr_buf)
            qr_size = 18 * mm
            qr_x = pad_side + 17 * mm
            qr_y = 25 * mm
            c.drawImage(qr_reader, qr_x, qr_y, qr_size, qr_size)
            c.setFont('Helvetica', px(6))
            c.drawCentredString(qr_x + qr_size / 2, qr_y - 3 * mm, 'Verificar documento')

        c.showPage()
        c.save()

        buf.seek(0)
        response = FileResponse(
            buf,
            content_type='application/pdf',
            filename=f'licencia_{num_lic}.pdf',
        )
        response['Content-Disposition'] = f'inline; filename="licencia_{num_lic}.pdf"'
        return response