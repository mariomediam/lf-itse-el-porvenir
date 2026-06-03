import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { licenciasApi } from '@api/licenciasApi'
import { personasApi } from '@api/personasApi'

// ── Constantes ────────────────────────────────────────────────────────────────

const CODIGO_DNI = '01'
const CODIGO_CE  = '04'

const MESES = [
  'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
  'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

const getAnio = (fechaStr) => {
  if (!fechaStr) return ''
  return new Date(fechaStr).getUTCFullYear()
}

const getDia = (fechaStr) => {
  if (!fechaStr) return ''
  return new Date(fechaStr).getUTCDate()
}

const getMes = (fechaStr) => {
  if (!fechaStr) return ''
  return MESES[new Date(fechaStr).getUTCMonth()]
}

const formatHora12 = (hora) => {
  if (hora == null) return ''
  const h = Number(hora)
  if (h === 0) return '12:00 A.M.'
  if (h === 12) return '12:00 P.M.'
  if (h < 12) return `${String(h).padStart(2, '0')}:00 A.M.`
  return `${String(h - 12).padStart(2, '0')}:00 P.M.`
}

const quitarPalabraRiesgo = (nombre) => {
  if (!nombre) return ''
  return nombre.replace(/riesgo\s*/gi, '').trim()
}

// ── Estilos comunes ───────────────────────────────────────────────────────────

const estilos = {
  campo: {
    fontSize: '15px',
    lineHeight: '2',
    margin: '0',
  },
  etiqueta: {
    fontWeight: 'normal',
  },
  valor: {
    fontWeight: 'bold',
  },
}

// ── Campo de formulario ───────────────────────────────────────────────────────

function CampoFormulario({ etiqueta, valor, inline }) {
  if (inline) {
    return (
      <p style={estilos.campo}>
        <span style={estilos.etiqueta}>{etiqueta}: </span>
        <span style={estilos.valor}>{valor || '-'}</span>
      </p>
    )
  }
  return (
    <p style={estilos.campo}>
      <span style={estilos.etiqueta}>{etiqueta}:</span>{' '}
      <span style={estilos.valor}>{valor || '-'}</span>
    </p>
  )
}

// ── Página ────────────────────────────────────────────────────────────────────

const LicenciaImprimirPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [licencia, setLicencia] = useState(null)
  const [giros, setGiros] = useState([])
  const [docConductor, setDocConductor] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const cargar = async () => {
      try {
        setCargando(true)
        const [licRes, girosRes] = await Promise.all([
          licenciasApi.buscar('ID', id),
          licenciasApi.getGiros(id),
        ])

        const lic = licRes.data[0]
        if (!lic) { setError('Licencia no encontrada.'); return }

        setLicencia(lic)
        setGiros(girosRes.data)

        if (lic.conductor_id) {
          try {
            const docRes = await personasApi.getDocumentos(lic.conductor_id)
            const docs = docRes.data
            const docDni = docs.find((d) => d.tipos_documento_identidad_codigo === CODIGO_DNI)
            const docCe = docs.find((d) => d.tipos_documento_identidad_codigo === CODIGO_CE)
            setDocConductor(docDni || docCe || null)
          } catch { /* continuar sin documento */ }
        }
      } catch {
        setError('Error al cargar los datos de la licencia.')
      } finally {
        setCargando(false)
      }
    }
    cargar()
  }, [id])

  if (cargando) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-3 text-sm text-gray-600">Cargando licencia...</p>
        </div>
      </div>
    )
  }

  if (error || !licencia) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <p className="text-red-600 font-medium">{error || 'Licencia no encontrada.'}</p>
          <button onClick={() => navigate(-1)}
            className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700">
            Volver
          </button>
        </div>
      </div>
    )
  }

  // ── Datos calculados ──────────────────────────────────────────────────────

  const numLic = licencia.numero_licencia
  const numExp = String(licencia.numero_expediente ?? '').padStart(4, '0')
  const anioExp = getAnio(licencia.fecha_recepcion)
  const girosTexto = giros.map((g) => g.nombre).join(', ').toUpperCase()
  const nivelRiesgoLimpio = quitarPalabraRiesgo(licencia.nivel_riesgo_nombre)
  const tipoLetrero = licencia.tipo_letrero_nombre || ''
  const observaciones = licencia.observaciones?.trim()
    ? licencia.observaciones.trim()
    : '************************************************************'

  const docEtiqueta = docConductor
    ? (docConductor.tipos_documento_identidad_nombre || 'D.N.I.')
    : 'D.N.I.'
  const docNumero = docConductor?.numero_documento || ''

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <style>{`
        @media print {
          @page { size: A4; margin: 0; }
          html, body { margin: 0; padding: 0; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          .fondo-gris { background: none !important; padding: 0 !important; }
          .hoja-a4 { margin: 0 !important; box-shadow: none !important; }
        }
      `}</style>

      {/* Barra de acciones */}
      <div className="no-print bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3 shadow-sm sticky top-0 z-10">
        <button onClick={() => window.print()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          Imprimir
        </button>
        <button onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Volver
        </button>
        <span className="text-sm text-gray-500 ml-2">
          Vista previa — LIC. N° {numLic} - {getAnio(licencia.fecha_emision)}
        </span>
      </div>

      {/* Fondo gris */}
      <div className="fondo-gris" style={{ backgroundColor: '#d1d5db', minHeight: '100vh', paddingTop: '32px', paddingBottom: '32px' }}>

        {/* Hoja A4 */}
        <div className="hoja-a4" style={{
          width: '210mm',
          minHeight: '297mm',
          margin: '0 auto',
          backgroundColor: '#ffffff',
          boxSizing: 'border-box',
          fontFamily: 'Arial, sans-serif',
          color: '#000000',
          display: 'flex',
          flexDirection: 'column',
        }}>

          {/* ── HEADER (imagen) ── */}
          <img
            src="/images/header-lf.png"
            alt="Encabezado Municipalidad Provincial Sánchez Carrión"
            style={{ width: '100%', display: 'block' }}
            onError={(e) => { e.target.style.display = 'none' }}
          />

          {/* ── CUERPO ── */}
          <div style={{ flex: 1, marginTop: '-10mm', padding: '0mm 16mm 8mm 16mm', display: 'flex', flexDirection: 'column' }}>

            {/* Título */}
            <h1 style={{
              textAlign: 'center',
              fontSize: '26px',
              fontWeight: '900',
              margin: '0 0 2px 0',
              letterSpacing: '1px',
            }}>
              LICENCIA DE FUNCIONAMIENTO
            </h1>

            {/* Ley y número */}
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'baseline', gap: '60px', marginBottom: '12px' }}>
              <span style={{ fontSize: '16px', fontWeight: '900' }}>Ley N.° 28976</span>
              <span style={{ fontSize: '14px' }}>
                <span style={{ fontWeight: 'bold', color: '#c00' }}>N°</span>{' '}
                <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{numLic.toString().padStart(4, '0')}</span>
              </span>
            </div>

            {/* Párrafo introductorio */}
            <p style={{ fontSize: '15px', textAlign: 'justify', lineHeight: '1.2', margin: '0 0 10px 0' }}>
              Visto el expediente N.°{' '}
              <strong>{numExp}-{anioExp}MPSC/TD</strong>{' '}
              con las constancias registradas en la solicitud y declaración jurada de cumplimiento de las
              condiciones de seguridad de la edificación presentadas por el administrado, de acuerdo con
              el Decreto Supremo N.° 163-2020-PCM que aprueba el Texto Único Ordenado de la Ley 28976,
              Ley Marco de Licencia de Funcionamiento y los formatos actualizados de declaración jurada,
              las facultades conferidas por la Ley Orgánica de Municipalidades N.° 27972 y con Resolución
              de Gerencia N.°{' '}
              <strong>{licencia.resolucion_numero || '-'}</strong>
            </p>

            {/* SE RESUELVE */}
            <p style={{ textAlign: 'center', fontWeight: '900', fontSize: '16px', margin: '6px 0 6px 0'}}>
              SE RESUELVE:
            </p>

            <p style={{ fontSize: '15px', margin: '0 0 10px 0' }}>
              Otorgar LICENCIA DE FUNCIONAMIENTO de apertura de establecimiento a:
            </p>

            {/* ── Campos tipo formulario ── */}
            <div style={{ fontSize: '15px', lineHeight: '2' }}>
              <CampoFormulario etiqueta="NOMBRE O RAZÓN SOCIAL" valor={(licencia.titular_nombre || '').toUpperCase()} />
              <CampoFormulario etiqueta="REPRESENTANTE LEGAL" valor={(licencia.conductor_nombre || '').toUpperCase()} />

              {/* RUC y DNI en la misma línea */}
              <p style={estilos.campo}>
                <span style={estilos.etiqueta}>N.° R.U.C.: </span>
                <span style={estilos.valor}>{licencia.titular_ruc || '-'}</span>
                <span style={{ marginLeft: '30px' }} />
                <span style={estilos.etiqueta}>N.° {docEtiqueta}: </span>
                <span style={estilos.valor}>{docNumero || '-'}</span>
              </p>

              <CampoFormulario
                etiqueta="HORARIO"
                valor={`${formatHora12(licencia.hora_desde)} A ${formatHora12(licencia.hora_hasta)}`}
              />
              <CampoFormulario etiqueta="NOMBRE COMERCIAL" valor={(licencia.nombre_comercial || '').toUpperCase()} />
              <CampoFormulario etiqueta="GIRO COMERCIAL" valor={girosTexto} />
              <CampoFormulario etiqueta="ACTIVIDAD" valor={(licencia.actividad || '').toUpperCase()} />

              {/* Nivel de riesgo + tipo letrero en la misma línea */}
              <p style={estilos.campo}>
                <span style={estilos.etiqueta}>NIVEL DE RIESGO: </span>
                <span style={estilos.valor}>{nivelRiesgoLimpio.toUpperCase()}</span>
                {tipoLetrero && (
                  <>
                    <span style={{ marginLeft: '40px' }} />
                    <span style={estilos.valor}>{tipoLetrero.toUpperCase()}.</span>
                  </>
                )}
              </p>

              <CampoFormulario etiqueta="DIRECCIÓN" valor={(licencia.direccion || '').toUpperCase()} />
              <CampoFormulario etiqueta="ZONIFICACIÓN" valor={(licencia.zonificacion_nombre || '').toUpperCase()} />
              <CampoFormulario etiqueta="OBSERVACIÓN" valor={observaciones} />
            </div>

            {/* ── Fecha ── */}
            <p style={{ fontSize: '13px', textAlign: 'center', margin: '16px 0 0 0' }}>
              Huamachuco, <strong>{getDia(licencia.fecha_emision)}</strong> de{' '}
              <strong>{getMes(licencia.fecha_emision)}</strong> del{' '}
              <strong>{getAnio(licencia.fecha_emision)}</strong>.
            </p>

            {/* Espaciador */}
            <div style={{ flex: 1 }} />

            {/* ── PIE DE PÁGINA ── */}
            <div style={{
              borderTop: '2px solid #8B0000',
              paddingTop: '6px',
              marginTop: '12px',
            }}>
              <p style={{
                fontSize: '10px',
                textAlign: 'justify',
                lineHeight: '1.4',
                margin: '0 0 6px 0',
                color: '#333',
              }}>
                Prohibido usar la vía pública (calles y veredas), fachadas como muestrario de productos,
                carteles, pizarras y/o avisos publicitarios sin autorización municipal. Prohibida la
                contaminación ambiental y sonora (ruidos no permisibles).
              </p>
              <p style={{
                fontSize: '11px',
                fontWeight: 'bold',
                textAlign: 'center',
                margin: 0,
                color: '#8B0000',
                letterSpacing: '0.5px',
              }}>
                COLOCAR EN UN LUGAR VISIBLE DEL ESTABLECIMIENTO
              </p>
            </div>

          </div>{/* fin cuerpo */}
        </div>{/* fin hoja A4 */}
      </div>{/* fin fondo gris */}
    </>
  )
}

export default LicenciaImprimirPage
