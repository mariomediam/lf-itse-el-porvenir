import { useState, useEffect, useRef } from 'react'
import { Modal, ModalHeader, ModalBody, ModalFooter } from 'flowbite-react'
import { toast } from 'sonner'
import { personasApi } from '@api/personasApi'

// ── Estilos comunes ───────────────────────────────────────────────────────────

const inputClass =
  'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 bg-white ' +
  'focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary ' +
  'disabled:bg-gray-50 disabled:text-gray-400 placeholder:text-gray-400'

const labelClass = 'block text-xs font-medium text-gray-600 mb-1'

// ── Estado inicial del formulario ─────────────────────────────────────────────

const estadoInicial = {
  tipo_documento_id: '',
  numero_documento: '',
  apellido_paterno: '',
  apellido_materno: '',
  nombres: '',
  sexo: 'X',
  razon_social: '',
  direccion: '',
  departamento: '',
  provincia: '',
  distrito: '',
  telefono: '',
  correo_electronico: '',
}

// ── Iconos ────────────────────────────────────────────────────────────────────

const IconoPersonaNatural = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
)

const IconoPersonaJuridica = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
  </svg>
)

const IconoCheck = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
  </svg>
)

const IconoSync = ({ className = 'w-4 h-4' }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
)

const IconoMas = () => (
  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
)

const IconoEliminar = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
)

const IconoGuardar = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
  </svg>
)

const IconoCancelar = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
)

// ── Encabezado de sección ─────────────────────────────────────────────────────

function SeccionTitulo({ children }) {
  return (
    <p className="text-xs font-semibold text-primary uppercase tracking-wide mb-3 pb-1.5 border-b border-gray-100">
      {children}
    </p>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────

/**
 * Modal para agregar o modificar una persona.
 *
 * Props
 * -----
 * isOpen   : bool
 * onClose  : () => void
 * onSuccess: (persona) => void  — callback tras guardar con éxito
 * persona  : object | null      — si se pasa, es modo edición (pendiente de implementar)
 */
export default function PersonaFormModal({ isOpen, onClose, onSuccess, persona = null }) {
  const esEdicion = !!persona

  const [tipoPersona, setTipoPersona] = useState('N')
  const [sexos, setSexos] = useState([])
  const [tiposDocumento, setTiposDocumento] = useState([])
  const [formData, setFormData] = useState(estadoInicial)
  const [otrosDocumentos, setOtrosDocumentos] = useState([])
  const [consultando, setConsultando] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Controla si ya se cargaron los datos de la persona en modo edición
  const editCargadoRef = useRef(false)

  // Cargar lista de sexos una sola vez al abrir
  useEffect(() => {
    if (!isOpen) return
    personasApi.getSexos()
      .then(res => setSexos(res.data))
      .catch(() => {})
  }, [isOpen])

  // En modo edición: sincronizar tipoPersona con la persona recibida
  useEffect(() => {
    if (!isOpen) return
    if (persona) {
      setTipoPersona(persona.tipo_persona)
    } else {
      setTipoPersona('N')
    }
  }, [isOpen, persona])

  // Recargar tipos de documento al cambiar tipo de persona
  useEffect(() => {
    if (!isOpen) return
    setTiposDocumento([])

    // En modo creación: limpiar campos de documento al cambiar tipo
    if (!esEdicion) {
      setFormData(prev => ({ ...prev, tipo_documento_id: '', numero_documento: '' }))
      setOtrosDocumentos([])
    }

    personasApi.getTiposDocumento(tipoPersona)
      .then(res => {
        setTiposDocumento(res.data)
        // En modo creación: preseleccionar el primer tipo de documento
        if (res.data.length > 0 && !esEdicion) {
          setFormData(prev => ({ ...prev, tipo_documento_id: String(res.data[0].id) }))
        }
      })
      .catch(() => toast.error('No se pudieron cargar los tipos de documento'))
  }, [tipoPersona, isOpen])

  // En modo edición: poblar el formulario una vez que tiposDocumento estén disponibles
  useEffect(() => {
    if (!isOpen || !persona || tiposDocumento.length === 0 || editCargadoRef.current) return
    editCargadoRef.current = true

    personasApi.obtener(persona.id)
      .then(res => {
        const p = res.data
        const isJuridica = p.tipo_persona === 'J'
        const docs = p.documentos || []
        const [principal, ...resto] = docs

        setFormData({
          tipo_documento_id:   principal ? String(principal.tipo_documento_identidad) : '',
          numero_documento:    principal?.numero_documento || '',
          apellido_paterno:    p.apellido_paterno || '',
          apellido_materno:    p.apellido_materno || '',
          nombres:             isJuridica ? '' : (p.nombres || ''),
          sexo:                p.sexo || 'X',
          razon_social:        isJuridica ? (p.nombres || '') : '',
          direccion:           p.direccion || '',
          departamento:        p.departamento || '',
          provincia:           p.provincia || '',
          distrito:            p.distrito || '',
          telefono:            p.telefono || '',
          correo_electronico:  p.correo_electronico || '',
        })

        setOtrosDocumentos(
          resto.map(d => ({
            tipo_documento_identidad_id: String(d.tipo_documento_identidad),
            numero_documento:            d.numero_documento,
          }))
        )
      })
      .catch(() => toast.error('No se pudieron cargar los datos de la persona'))
  }, [isOpen, persona, tiposDocumento])

  // ── Helpers ───────────────────────────────────────────────────────────────

  const tipoDocSeleccionado = tiposDocumento.find(t => String(t.id) === formData.tipo_documento_id)

  const puedeConsultarReniec =
    tipoPersona === 'N' &&
    tipoDocSeleccionado?.nombre === 'DNI' &&
    formData.numero_documento.trim().length === 8

  const puedeConsultarSunat =
    tipoPersona === 'J' &&
    tipoDocSeleccionado?.nombre === 'RUC' &&
    formData.numero_documento.trim().length === 11

  const mostrarBotonConsulta =
    (tipoPersona === 'N' && tipoDocSeleccionado?.nombre === 'DNI') ||
    (tipoPersona === 'J' && tipoDocSeleccionado?.nombre === 'RUC')

  // Tipos disponibles para "otros documentos" (excluye el principal)
  const tiposParaOtros = tiposDocumento.filter(
    t => String(t.id) !== formData.tipo_documento_id
  )

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleCambioTipoPersona = (tipo) => {
    if (tipo === tipoPersona) return
    setTipoPersona(tipo)
    setFormData(estadoInicial)
    setOtrosDocumentos([])
  }

  const handleCambioTipoDoc = (e) => {
    setFormData(prev => ({
      ...prev,
      tipo_documento_id: e.target.value,
      numero_documento: '',
      apellido_paterno: '',
      apellido_materno: '',
      nombres: '',
      razon_social: '',
      direccion: '',
      departamento: '',
      provincia: '',
      distrito: '',
    }))
    setOtrosDocumentos([])
  }

  const handleConsultarReniec = async () => {
    setConsultando(true)
    try {
      const res = await personasApi.consultarReniec(formData.numero_documento.trim())
      const datos = res.data?.consultarResponse?.return?.datosPersona
      if (!datos) throw new Error('Respuesta inesperada')
      const ubigeo = datos.ubigeo?.split('/') ?? []
      setFormData(prev => ({
        ...prev,
        apellido_paterno: datos.apPrimer?.trim() ?? '',
        apellido_materno: datos.apSegundo?.trim() ?? '',
        nombres: datos.prenombres?.trim() ?? '',
        direccion: datos.direccion?.trim() ?? '',
        departamento: ubigeo[0]?.trim() ?? '',
        provincia: ubigeo[1]?.trim() ?? '',
        distrito: ubigeo[2]?.trim() ?? '',
      }))
      toast.success('Datos obtenidos de RENIEC')
    } catch {
      toast.error('No se pudo consultar RENIEC. Ingrese los datos manualmente.')
    } finally {
      setConsultando(false)
    }
  }

  const handleConsultarSunat = async () => {
    setConsultando(true)
    try {
      const res = await personasApi.consultarSunat(formData.numero_documento.trim())
      const m = res.data?.list?.multiRef
      if (!m) throw new Error('Respuesta inesperada')

      const direccion = [
        m.desc_tipzon?.$,
        m.ddp_nomzon?.$,
        m.desc_tipvia?.$,
        m.ddp_nomvia?.$,
        m.ddp_numer1?.$,
      ].filter(v => v && String(v).trim()).map(v => String(v).trim()).join(' ')

      setFormData(prev => ({
        ...prev,
        razon_social: String(m.ddp_nombre?.$ ?? '').trim(),
        direccion,
        departamento: String(m.desc_dep?.$ ?? '').trim(),
        provincia: String(m.desc_prov?.$ ?? '').trim(),
        distrito: String(m.desc_dist?.$ ?? '').trim(),
      }))
      toast.success('Datos obtenidos de SUNAT')

      if (m.esActivo?.$ === false || m.esActivo?.$ === 'false') {
        const estado = String(m.desc_estado?.$ ?? 'INACTIVO').trim()
        setTimeout(() => {
          toast.warning(`El contribuyente se encuentra: ${estado}`, { duration: 8000 })
        }, 300)
      }
    } catch {
      toast.error('No se pudo consultar SUNAT. Ingrese los datos manualmente.')
    } finally {
      setConsultando(false)
    }
  }

  const agregarDocumento = () => {
    if (tiposParaOtros.length === 0) return
    setOtrosDocumentos(prev => [
      ...prev,
      { tipo_documento_identidad_id: String(tiposParaOtros[0].id), numero_documento: '' },
    ])
  }

  const actualizarOtroDoc = (idx, field, value) => {
    setOtrosDocumentos(prev =>
      prev.map((d, i) => (i === idx ? { ...d, [field]: value } : d))
    )
  }

  const eliminarOtroDoc = (idx) => {
    setOtrosDocumentos(prev => prev.filter((_, i) => i !== idx))
  }

  const handleClose = () => {
    editCargadoRef.current = false
    setTipoPersona('N')
    setFormData(estadoInicial)
    setOtrosDocumentos([])
    onClose()
  }

  const handleSubmit = async () => {
    if (!formData.tipo_documento_id || !formData.numero_documento.trim()) {
      toast.error('Seleccione el tipo de documento e ingrese el número')
      return
    }
    if (tipoPersona === 'N') {
      if (!formData.apellido_paterno.trim() || !formData.nombres.trim()) {
        toast.error('Ingrese el primer apellido y los nombres')
        return
      }
    } else {
      if (!formData.razon_social.trim()) {
        toast.error('Ingrese la razón social')
        return
      }
    }

    const documentos = [
      {
        tipo_documento_identidad_id: Number(formData.tipo_documento_id),
        numero_documento: formData.numero_documento.trim(),
      },
    ]

    for (const d of otrosDocumentos) {
      if (d.tipo_documento_identidad_id && d.numero_documento.trim()) {
        documentos.push({
          tipo_documento_identidad_id: Number(d.tipo_documento_identidad_id),
          numero_documento: d.numero_documento.trim(),
        })
      }
    }

    const body = {
      tipo_persona: tipoPersona,
      sexo: tipoPersona === 'N' ? formData.sexo : 'X',
      apellido_paterno: tipoPersona === 'N' ? formData.apellido_paterno.trim() : '',
      apellido_materno: tipoPersona === 'N' ? formData.apellido_materno.trim() : '',
      nombres: tipoPersona === 'N' ? formData.nombres.trim() : formData.razon_social.trim(),
      direccion: formData.direccion.trim(),
      departamento: formData.departamento.trim(),
      provincia: formData.provincia.trim(),
      distrito: formData.distrito.trim(),
      telefono: formData.telefono.trim(),
      correo_electronico: formData.correo_electronico.trim(),
      documentos,
    }

    setIsSubmitting(true)
    try {
      const res = esEdicion
        ? await personasApi.actualizar(persona.id, body)
        : await personasApi.crearPersona(body)
      toast.success(esEdicion ? 'Persona actualizada correctamente' : 'Persona guardada correctamente')
      onSuccess?.(res.data)
      handleClose()
    } catch (err) {
      const data = err.response?.data
      const detail =
        data?.error ||
        data?.detail ||
        (data?.non_field_errors?.[0]) ||
        (typeof data === 'string' ? data : null) ||
        'Error al guardar la persona'
      toast.error(detail)
    } finally {
      setIsSubmitting(false)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <Modal show={isOpen} size="2xl" onClose={handleClose}>

      {/* ── Cabecera ── */}
      <ModalHeader className="bg-white border-b border-gray-200">
        <div className="flex items-center gap-2.5">
          <span className="text-primary">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </span>
          <span className="text-base font-semibold text-gray-800">
            {esEdicion ? 'Modificar persona' : 'Agregar persona'}
          </span>
        </div>
      </ModalHeader>

      {/* ── Cuerpo ── */}
      <ModalBody className="bg-white overflow-y-auto max-h-[70vh] px-6 py-5 space-y-6">
        

        {/* ── Clasificación de persona ── */}
        <div>
          <SeccionTitulo>Clasificación de persona</SeccionTitulo>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => handleCambioTipoPersona('N')}
              disabled={esEdicion}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                tipoPersona === 'N'
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary hover:text-primary'
              } disabled:opacity-60 disabled:cursor-not-allowed`}
            >
              <IconoPersonaNatural />
              Persona natural
              {tipoPersona === 'N' && <IconoCheck />}
            </button>
            <button
              type="button"
              onClick={() => handleCambioTipoPersona('J')}
              disabled={esEdicion}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                tipoPersona === 'J'
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary hover:text-primary'
              } disabled:opacity-60 disabled:cursor-not-allowed`}
            >
              <IconoPersonaJuridica />
              Persona jurídica
              {tipoPersona === 'J' && <IconoCheck />}
            </button>
          </div>
        </div>

        {/* ── Información de identidad ── */}
        <div>
          <SeccionTitulo>Información de identidad</SeccionTitulo>

          {/* Tipo y número de documento */}
          <div className="grid grid-cols-2 gap-4 mb-3">
            <div>
              <label className={labelClass}>Tipo de documento</label>
              <select
                name="tipo_documento_id"
                value={formData.tipo_documento_id}
                onChange={handleCambioTipoDoc}
                className={inputClass}
              >
                {tiposDocumento.map(t => (
                  <option key={t.id} value={String(t.id)}>{t.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Número de documento</label>
              <input
                type="text"
                name="numero_documento"
                value={formData.numero_documento}
                onChange={handleChange}
                placeholder="Ingrese el número"
                className={inputClass}
                maxLength={20}
              />
            </div>
          </div>

          {/* Botón consulta RENIEC / SUNAT */}
          {mostrarBotonConsulta && (
            <button
              type="button"
              onClick={tipoPersona === 'N' ? handleConsultarReniec : handleConsultarSunat}
              disabled={
                consultando ||
                (tipoPersona === 'N' ? !puedeConsultarReniec : !puedeConsultarSunat)
              }
              className="w-full flex items-center justify-center gap-2 px-4 py-2 mb-4
                border border-tertiary text-tertiary rounded-lg text-sm font-medium
                hover:bg-tertiary hover:text-white transition-all
                disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-tertiary"
            >
              <IconoSync className={`w-4 h-4 ${consultando ? 'animate-spin' : ''}`} />
              {consultando
                ? 'Consultando...'
                : tipoPersona === 'N'
                  ? 'Consultar RENIEC'
                  : 'Consultar SUNAT'}
            </button>
          )}

          {/* Campos para Persona Natural */}
          {tipoPersona === 'N' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>Primer apellido</label>
                  <input
                    type="text"
                    name="apellido_paterno"
                    value={formData.apellido_paterno}
                    onChange={handleChange}
                    placeholder="Apellido paterno"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Segundo apellido</label>
                  <input
                    type="text"
                    name="apellido_materno"
                    value={formData.apellido_materno}
                    onChange={handleChange}
                    placeholder="Apellido materno"
                    className={inputClass}
                  />
                </div>
              </div>
              <div>
                <label className={labelClass}>Nombres completos</label>
                <input
                  type="text"
                  name="nombres"
                  value={formData.nombres}
                  onChange={handleChange}
                  placeholder="Nombres"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Sexo</label>
                <select
                  name="sexo"
                  value={formData.sexo}
                  onChange={handleChange}
                  className={inputClass}
                >
                  {sexos.map(s => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Campos para Persona Jurídica */}
          {tipoPersona === 'J' && (
            <div>
              <label className={labelClass}>Razón Social</label>
              <input
                type="text"
                name="razon_social"
                value={formData.razon_social}
                onChange={handleChange}
                placeholder="Razón social de la empresa"
                className={inputClass}
              />
            </div>
          )}
        </div>

        {/* ── Dirección y contacto ── */}
        <div>
          <SeccionTitulo>Dirección y contacto</SeccionTitulo>
          <div className="space-y-3">
            <div>
              <label className={labelClass}>Dirección domiciliaria</label>
              <input
                type="text"
                name="direccion"
                value={formData.direccion}
                onChange={handleChange}
                placeholder="Av. / Jr. / Calle..."
                className={inputClass}
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className={labelClass}>Departamento</label>
                <input
                  type="text"
                  name="departamento"
                  value={formData.departamento}
                  onChange={handleChange}
                  placeholder="Departamento"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Provincia</label>
                <input
                  type="text"
                  name="provincia"
                  value={formData.provincia}
                  onChange={handleChange}
                  placeholder="Provincia"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Distrito</label>
                <input
                  type="text"
                  name="distrito"
                  value={formData.distrito}
                  onChange={handleChange}
                  placeholder="Distrito"
                  className={inputClass}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Teléfono / Celular</label>
                <input
                  type="tel"
                  name="telefono"
                  value={formData.telefono}
                  onChange={handleChange}
                  placeholder="999 999 999"
                  className={inputClass}
                  maxLength={15}
                />
              </div>
              <div>
                <label className={labelClass}>Correo electrónico</label>
                <input
                  type="email"
                  name="correo_electronico"
                  value={formData.correo_electronico}
                  onChange={handleChange}
                  placeholder="correo@ejemplo.com"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        </div>

        {/* ── Otros documentos de identidad (solo persona natural) ── */}
        {tipoPersona === 'N' && (
          <div>
            <div className="flex items-center justify-between mb-3 pb-1.5 border-b border-gray-100">
              <p className="text-xs font-semibold text-primary uppercase tracking-wide">
                Otros documentos de identidad
              </p>
              {tiposParaOtros.length > 0 && (
                <button
                  type="button"
                  onClick={agregarDocumento}
                  className="flex items-center gap-1 text-xs font-medium text-tertiary hover:text-tertiary/80 transition-colors"
                >
                  <IconoMas />
                  Agregar documento
                </button>
              )}
            </div>

            {otrosDocumentos.length === 0 && (
              <p className="text-xs text-gray-400 italic">
                Sin documentos adicionales.
                {tiposParaOtros.length > 0 && ' Use "Agregar documento" para añadir.'}
              </p>
            )}

            <div className="space-y-2">
              {otrosDocumentos.map((doc, idx) => (
                <div key={idx} className="flex gap-3 items-end">
                  <div className="flex-1">
                    <label className={labelClass}>Tipo de documento</label>
                    <select
                      value={doc.tipo_documento_identidad_id}
                      onChange={e => actualizarOtroDoc(idx, 'tipo_documento_identidad_id', e.target.value)}
                      className={inputClass}
                    >
                      {tiposParaOtros.map(t => (
                        <option key={t.id} value={String(t.id)}>{t.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className={labelClass}>Número de documento</label>
                    <input
                      type="text"
                      value={doc.numero_documento}
                      onChange={e => actualizarOtroDoc(idx, 'numero_documento', e.target.value)}
                      placeholder="Número"
                      className={inputClass}
                      maxLength={20}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => eliminarOtroDoc(idx)}
                    className="mb-0.5 p-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
                    title="Eliminar"
                  >
                    <IconoEliminar />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </ModalBody>

      {/* ── Pie ── */}
      <ModalFooter className="border-t border-gray-200 bg-white flex justify-end gap-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={isSubmitting}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-600
            rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <IconoCancelar />
          Cancelar
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="flex items-center gap-2 px-5 py-2 bg-primary text-white
            rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <IconoGuardar />
          {isSubmitting ? 'Guardando...' : 'Guardar persona'}
        </button>
      </ModalFooter>
    </Modal>
  )
}
