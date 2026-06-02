import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { QRCode } from 'react-qr-code'
import { itseApi } from '@api/itseApi'
import { configPublicaApi } from '@api/configPublicaApi'

// ── Helpers ───────────────────────────────────────────────────────────────────

const MESES = [
  'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
  'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]

const NOTAS = [
  'DE ACUERDO A LO ESTABLECIDO EN EL REGLAMENTO DE INSPECCIONES TÉCNICAS DE SEGURIDAD EN EDIFICACIONES APROBADO POR DECRETO SUPREMO N° 002-2018 PCM, EL PRESENTE CERTIFICADO DEBERÁ SER FIRMADO POR EL RESPONSABLE DEL ÓRGANO EJECUTANTE.',
  'ESTE CERTIFICADO DEBERÁ COLOCARSE EN UN LUGAR VISIBLE DENTRO DEL ESTABLECIMIENTO OBJETO DE INSPECCIÓN.',
  'CUALQUIER TACHA O ENMENDADURA INVALIDA EL PRESENTE CERTIFICADO.',
]

const getAnio = (fechaStr) => {
  if (!fechaStr) return '-'
  return new Date(fechaStr).getUTCFullYear()
}

const formatFecha = (fechaStr) => {
  if (!fechaStr) return '-'
  const d = new Date(fechaStr)
  return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
}

const formatFechaLarga = (fechaStr) => {
  if (!fechaStr) return '-'
  const d = new Date(fechaStr)
  return `${d.getUTCDate()} DE ${MESES[d.getUTCMonth()]} DE ${d.getUTCFullYear()}`
}

const calcularVigencia = (fechaInicio, fechaFin) => {
  if (!fechaInicio || !fechaFin) return '-'
  const ms = new Date(fechaFin) - new Date(fechaInicio)
  const anios = Math.round(ms / (365.25 * 24 * 60 * 60 * 1000))
  if (anios >= 1) return `${anios} ${anios === 1 ? 'AÑO' : 'AÑOS'}`
  const meses = Math.round(ms / (30 * 24 * 60 * 60 * 1000))
  return `${meses} ${meses === 1 ? 'MES' : 'MESES'}`
}

// ── Página principal ──────────────────────────────────────────────────────────

const ItseImprimirPage = () => {
  const { id }   = useParams()
  const navigate = useNavigate()

  const [itse, setItse] = useState(null)
  const [giros, setGiros] = useState([])
  const [qrUrl, setQrUrl] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const cargar = async () => {
      try {
        setCargando(true)
        const [itseRes, girosRes, configRes] = await Promise.all([
          itseApi.buscar('ID', id),
          itseApi.getGiros(id),
          configPublicaApi.getConfig().catch(() => ({ data: {} })),
        ])
        const item = itseRes.data[0]
        if (!item) { setError('Certificado ITSE no encontrado.'); return }
        setItse(item)
        setGiros(girosRes.data)

        const cfg = configRes.data
        if (cfg.qr_verificacion_habilitado && cfg.qr_url_verificar_itse && item.uuid) {
          const base = cfg.qr_url_verificar_itse.replace(/\/+$/, '')
          setQrUrl(`${base}/${item.uuid}`)
        }
      } catch {
        setError('Error al cargar los datos del certificado ITSE.')
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
          <p className="mt-3 text-sm text-gray-600">Cargando certificado ITSE...</p>
        </div>
      </div>
    )
  }

  if (error || !itse) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <p className="text-red-600 font-medium">{error || 'Certificado ITSE no encontrado.'}</p>
          <button onClick={() => navigate(-1)} className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700">
            Volver
          </button>
        </div>
      </div>
    )
  }

  // ── Datos calculados ────────────────────────────────────────────────────────
  const anioItse = getAnio(itse.fecha_expedicion)
  const girosTexto = giros.map((g) => g.nombre).join(', ')
  const expedienteNum = itse.numero_expediente
    ? `${String(itse.numero_expediente).padStart(4, '0')} - ${getAnio(itse.fecha_recepcion)}`
    : '-'
  const vigencia = calcularVigencia(itse.fecha_expedicion, itse.fecha_caducidad)

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{`
        @media print {
          @page { size: A4; margin: 0; }
          html, body { margin: 0; padding: 0; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          .fondo-gris-itse { background: none !important; padding: 0 !important; }
          .hoja-a4-itse { margin: 0 !important; box-shadow: none !important; }
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
          Vista previa — ITSE N° {itse.numero_itse} - {anioItse}
        </span>
      </div>

      {/* Fondo gris */}
      <div className="fondo-gris-itse" style={{ backgroundColor: '#d1d5db', minHeight: '100vh', paddingTop: '32px', paddingBottom: '32px' }}>

        {/* Hoja A4 */}
        <div className="hoja-a4-itse" style={{
          width: '210mm',
          height: '297mm',
          margin: '0 auto',
          backgroundColor: '#ffffff',
          padding: '8mm',
          boxSizing: 'border-box',
          fontFamily: 'Arial, sans-serif',
          color: '#000000',
        }}>
        {/* Borde interior anaranjado */}
        <div style={{
          border: '4px solid #F89544',
          height: '100%',
          padding: '6mm 10mm',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
        }}>

          {/* ── ENCABEZADO: logos ── */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <img src="/images/logo-itse1.jpg" alt="Logo ITSE 1"
              style={{ height: '90px', width: 'auto', flexShrink: 0 }}
              onError={(e) => { e.target.style.display = 'none' }} />
            <img src="/images/logo-itse2.jpg" alt="Logo ITSE 2"
              style={{ height: '90px', width: 'auto', flexShrink: 0 }}
              onError={(e) => { e.target.style.display = 'none' }} />
          </div>

          {/* ── TÍTULO CERTIFICADO ── */}
          <div style={{ textAlign: 'center', marginBottom: '6px' }}>
            <p style={{ fontWeight: 'bold', fontSize: '17px', margin: '0 0 4px 0', lineHeight: '1.5', textTransform: 'uppercase' }}>
              Certificado de Inspección Técnica de Seguridad en Edificaciones para Establecimientos Objeto de Inspección Clasificados
            </p>
            <p style={{ fontWeight: 'bold', fontSize: '19px', margin: '0 0 4px 0', textTransform: 'uppercase' }}>
              Con Nivel de{' '}
              <span style={{ fontSize: '28px', color: "#FB0200" }}>{itse.nivel_riesgo_nombre || ''}</span>
            </p>
          </div>

          {/* ── N° ITSE ── */}
          <p style={{ fontWeight: 'bold', fontSize: '18px', textAlign: 'center', margin: '0 0 10px 0', letterSpacing: '1px' }}>
            Nº. {itse.numero_itse} - {anioItse}
          </p>

          {/* ── PÁRRAFO INTRODUCTORIO ── */}
          <p style={{ fontSize: '12px', textAlign: 'justify', margin: '0 0 8px 0', lineHeight: '1.6' }}>
            El Órgano Ejecutante de la Municipalidad Provincial de Lamas, en cumplimiento de lo establecido en el D.S. Nº 002-2018-PCM, ha realizado la Inspección Técnica de Seguridad en Edificaciones al Establecimiento Objeto de Inspección:
          </p>

          {/* ── NOMBRE COMERCIAL ── */}
          <p style={{ fontWeight: 'bold', fontSize: '20px', textAlign: 'center', margin: '0 0 10px 0', textTransform: 'uppercase' }}>
            "{itse.nombre_comercial || '-'}"
          </p>

          {/* ── UBICACIÓN ── */}
          <p style={{ fontSize: '16px', margin: '0 0 0px 0', lineHeight: '1.5', fontWeight: 'bold' }}>
            Ubicado en :&nbsp;&nbsp;&nbsp;&nbsp;{itse.direccion || '-'}
          </p>
          <p style={{ fontSize: '12px', margin: '0 0 8px 0', lineHeight: '1.5', fontWeight: 'bold' }}>
            Distrito de Pinto Recodo - Provincia Lamas - Departamento San Martín
          </p>

          {/* ── SOLICITADO POR ── */}
          <p style={{ fontSize: '16px', margin: '8px 0 8px 0', lineHeight: '1.5', fontWeight: 'bold' }}>
            Solicitado por:&nbsp;&nbsp;&nbsp;&nbsp;{itse.titular_nombre || itse.conductor_nombre || '-'}
          </p>

          {/* ── CERTIFICA ── */}
          <p style={{ fontSize: '13px', textAlign: 'justify', margin: '0 0 8px 0', lineHeight: '1.6' }}>
            El que suscribe <strong><em>CERTIFICA</em></strong> que el Establecimiento Objeto de Inspección antes señalado{' '}
            <strong><em>CUMPLE</em></strong>{' '}
            CON LAS CONDICIONES DE SEGURIDAD.
          </p>

          {/* ── CAPACIDAD ── */}
          <p style={{ fontSize: '16px', margin: '0 0 6px 0', lineHeight: '1.5' }}>
            <strong>Capacidad Máxima de la Edificación: ({itse.capacidad_aforo ?? '-'}) personas</strong>
          </p>

          {/* ── GIRO ── */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '6px', alignItems: 'baseline' }}>
            <p style={{ fontSize: '16px', margin: 0, flexShrink: 0 }}><strong>Giro o actividad:</strong></p>
            <p style={{ fontSize: '14px', margin: 0, fontWeight: 'bold', lineHeight: '1.5' }}>
              {girosTexto || '-'}
            </p>
          </div>

          {/* ── EXPEDIENTE ── */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '4px', alignItems: 'baseline', fontWeight: 'bold' }}>
            <p style={{ fontSize: '16px', margin: 0, minWidth: '100px' }}>Expediente Nº :</p>
            <p style={{ fontSize: '16px', margin: 0 }}>{expedienteNum}</p>
          </div>

          {/* ── RESOLUCIÓN ── */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '6px', alignItems: 'baseline', fontWeight: 'bold' }}>
            <p style={{ fontSize: '16px', margin: 0, minWidth: '100px' }}>Resolución N° :</p>
            <p style={{ fontSize: '16px', margin: 0, fontWeight: 'bold' }}>{itse.resolucion_numero || '-'}</p>
          </div>

          {/* ── VIGENCIA ── */}
          <p style={{ fontSize: '16px', margin: '0 0 4px 0', fontWeight: 'bold', textTransform: 'uppercase' }}>
            VIGENCIA: {vigencia}*
          </p>

          {/* ── LUGAR Y FECHA ── */}
          <p style={{ fontSize: '16px', textAlign: 'right', margin: '0 0 10px 0', fontWeight: 'bold' }}>
            LAMAS, {formatFechaLarga(itse.fecha_expedicion)}
          </p>

          {/* ── FECHAS ── */}
          <div style={{ marginBottom: '6px' }}>
            <div style={{ display: 'flex', gap: '6px', marginBottom: '2px' }}>
              <p style={{ fontSize: '14px', margin: 0, fontWeight: 'bold', minWidth: '300px' }}>FECHA DE EXPEDICIÓN</p>
              <p style={{ fontSize: '14px', margin: 0 }}>: {formatFecha(itse.fecha_expedicion)}</p>
            </div>
            <div style={{ display: 'flex', gap: '6px', marginBottom: '2px' }}>
              <p style={{ fontSize: '14px', margin: 0, fontWeight: 'bold', minWidth: '300px' }}>FECHA DE SOLICITUD DE RENOVACIÓN</p>
              <p style={{ fontSize: '14px', margin: 0 }}>: {formatFecha(itse.fecha_solicitud_renovacion)}</p>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <p style={{ fontSize: '14px', margin: 0, fontWeight: 'bold', minWidth: '300px' }}>FECHA DE CADUCIDAD</p>
              <p style={{ fontSize: '14px', margin: 0 }}>: {formatFecha(itse.fecha_caducidad)}</p>
            </div>
          </div>

          {/* Espaciador */}
          <div style={{ flex: 1 }} />

          {/* ── PIE: NOTA + QR ── */}
          <div style={{ borderTop: '1px solid #000', paddingTop: '6px', display: 'flex', gap: '10px' }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: '8px', margin: '0 0 4px 0', lineHeight: '1.4' }}>
                *El presente Certificado de ITSE no constituye autorización alguna para el funcionamiento del Establecimiento Objeto de Inspección o para el inicio de la actividad
              </p>
              <p style={{ fontWeight: 'bold', fontSize: '8px', margin: '0 0 3px 0' }}>NOTA:</p>
              {NOTAS.map((texto, i) => (
                <div key={i} style={{ display: 'flex', gap: '4px', marginBottom: '1px' }}>
                  <span style={{ fontSize: '7.5px', flexShrink: 0 }}>-</span>
                  <p style={{ margin: 0, fontSize: '7.5px', lineHeight: '1.3', textTransform: 'uppercase' }}>{texto}</p>
                </div>
              ))}
            </div>
            {qrUrl && (
              <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <QRCode value={qrUrl} size={68} level="M" />
                <p style={{ fontSize: '7px', margin: '3px 0 0 0', textAlign: 'center', color: '#555' }}>
                  Verificar documento
                </p>
              </div>
            )}
          </div>

        </div>{/* fin borde interior */}
        </div>{/* fin hoja A4 */}
      </div>{/* fin fondo gris */}
    </>
  )
}

export default ItseImprimirPage