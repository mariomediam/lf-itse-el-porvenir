import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { QRCode } from 'react-qr-code'
import { itseApi } from '@api/itseApi'
import { configPublicaApi } from '@api/configPublicaApi'

const getAnio = (fechaStr) => {
  if (!fechaStr) return '-'
  return new Date(fechaStr).getUTCFullYear()
}

const formatFecha = (fechaStr) => {
  if (!fechaStr) return '-'
  const d = new Date(fechaStr)
  return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
}

const calcularVigencia = (fechaInicio, fechaFin) => {
  if (!fechaInicio || !fechaFin) return '-'
  const inicio = new Date(fechaInicio)
  const fin = new Date(fechaFin)
  const meses = (fin.getUTCFullYear() - inicio.getUTCFullYear()) * 12
    + (fin.getUTCMonth() - inicio.getUTCMonth())
  if (meses >= 12) {
    const anios = Math.round(meses / 12)
    return `${anios} ${anios === 1 ? 'AÑO' : 'AÑOS'}`
  }
  return `${meses} ${meses === 1 ? 'MES' : 'MESES'}`
}

const UNIDADES = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
const ESPECIALES = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE']
const DECENAS_PREFIX = ['', '', 'VEINTI', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
const CENTENAS = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS']

function numeroALetras(n) {
  if (n == null || isNaN(n)) return ''
  n = Math.floor(Math.abs(n))
  if (n === 0) return 'CERO'
  if (n === 100) return 'CIEN'
  let resultado = ''
  if (n >= 1000) {
    const miles = Math.floor(n / 1000)
    resultado += miles === 1 ? 'MIL' : `${numeroALetras(miles)} MIL`
    n %= 1000
    if (n > 0) resultado += ' '
  }
  if (n >= 100) {
    resultado += CENTENAS[Math.floor(n / 100)]
    n %= 100
    if (n > 0) resultado += ' '
  }
  if (n >= 10 && n <= 15) {
    resultado += ESPECIALES[n - 10]
  } else if (n >= 16 && n <= 19) {
    resultado += `DIECI${UNIDADES[n - 10]}`
  } else if (n >= 20 && n <= 29 && n !== 20) {
    resultado += `VEINTI${UNIDADES[n - 20]}`
  } else if (n === 20) {
    resultado += 'VEINTE'
  } else if (n >= 30) {
    resultado += DECENAS_PREFIX[Math.floor(n / 10)]
    const u = n % 10
    if (u > 0) resultado += ` Y ${UNIDADES[u]}`
  } else if (n >= 1) {
    resultado += UNIDADES[n]
  }
  return resultado
}

const NOTAS = [
  'DE ACUERDO A LO ESTABLECIDO EN EL REGLAMENTO DE INSPECCIONES TÉCNICAS DE SEGURIDAD EN EDIFICACIONES APROBADO POR DECRETO SUPREMO N° 002-2018 PCM, EL PRESENTE CERTIFICADO DEBERÁ SER FIRMADO POR EL RESPONSABLE DEL ÓRGANO EJECUTANTE.',
  'ESTE CERTIFICADO DEBERÁ COLOCARSE EN UN LUGAR VISIBLE DENTRO DEL ESTABLECIMIENTO OBJETO DE INSPECCIÓN.',
  'CUALQUIER TACHA O ENMENDADURA INVALIDA EL PRESENTE CERTIFICADO.',
]

const ItseImprimirPage = () => {
  const { id } = useParams()
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

  const anioExpedicion = getAnio(itse.fecha_expedicion)
  const girosTexto = giros.map((g) => g.nombre).join(', ').toUpperCase()
  const vigencia = calcularVigencia(itse.fecha_expedicion, itse.fecha_caducidad)
  const aforo = itse.capacidad_aforo ?? 0
  const aforoLetras = numeroALetras(aforo)
  const numExp = itse.numero_expediente
    ? `E-${itse.numero_expediente}-${getAnio(itse.fecha_recepcion)}`
    : '-'

  const celdasEstilo = { padding: '7px 4px', fontSize: '13px', verticalAlign: 'top' }
  const labelEstilo = { ...celdasEstilo, fontWeight: 'bold', whiteSpace: 'nowrap' }
  const colonEstilo = { ...celdasEstilo, width: '10px', textAlign: 'center' }
  const valorEstilo = { ...celdasEstilo, fontWeight: 'bold' }

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
          Vista previa — ITSE N° {itse.numero_itse}-{anioExpedicion}
        </span>
      </div>

      {/* Fondo gris */}
      <div className="fondo-gris-itse" style={{ backgroundColor: '#d1d5db', minHeight: '100vh', paddingTop: '32px', paddingBottom: '32px' }}>

        {/* Hoja A4 */}
        <div className="hoja-a4-itse" style={{
          width: '210mm',
          height: '297mm',
          margin: '0 auto',
          backgroundColor: '#fff',
          boxSizing: 'border-box',
          fontFamily: 'Arial, sans-serif',
          color: '#000',
          position: 'relative',
          overflow: 'hidden',
          padding: '12mm 16mm 12mm 16mm',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
        }}>

          {/* Marca de agua de fondo */}
          <img
            src="/images/escudo-muni.png"
            alt=""
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              opacity: 0.06,
              width: '75%',
              pointerEvents: 'none',
              zIndex: 0,
            }}
            onError={(e) => { e.target.style.display = 'none' }}
          />

          {/* Contenido sobre la marca de agua */}
          <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', flex: 1 }}>

            {/* ── ENCABEZADO: Logo muni + Título + Logo CENEPRED ── */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
              <img
                src="/images/escudo-muni.png"
                alt="Escudo Municipalidad"
                style={{ height: '95px', width: 'auto', flexShrink: 0 }}
                onError={(e) => { e.target.style.display = 'none' }}
              />
              <p style={{
                fontWeight: 'bold',
                fontSize: '15px',
                margin: '8px 0 0 0',
                lineHeight: '1.35',
                textTransform: 'uppercase',
                textAlign: 'center',
                flex: 1,
              }}>
                CERTIFICADO DE INSPECCIÓN TÉCNICA DE SEGURIDAD EN EDIFICACIONES PARA
                ESTABLECIMIENTOS OBJETO DE INSPECCIÓN CLASIFICADOS CON NIVEL DE RIESGO{' '}
                {(itse.nivel_riesgo_nombre || '').toUpperCase()}{' '}
                SEGÚN LA MATRIZ DE RIESGOS
              </p>
              <img
                src="/images/escudo-cenepred.png"
                alt="CENEPRED"
                style={{ height: '90px', width: 'auto', flexShrink: 0 }}
                onError={(e) => { e.target.style.display = 'none' }}
              />
            </div>

            {/* ── N° ITSE ── */}
            <p style={{
              fontWeight: '900',
              fontSize: '22px',
              textAlign: 'center',
              margin: '4px 0 10px 0',              
            }}>
              N° {itse.numero_itse}-{anioExpedicion}
            </p>

            {/* ── PÁRRAFO INTRODUCTORIO ── */}
            <p style={{ fontSize: '13.7px', textAlign: 'justify', margin: '0 0 8px 0', lineHeight: '1.3' }}>
              El Órgano Ejecutante de la Municipalidad Distrital de El Porvenir, en cumplimiento
              de lo establecido en el D.S. N.º 002-2018-PCM, ha realizado la Inspección Técnica de
              Seguridad en Edificaciones al Establecimiento Objeto de Inspección:
            </p>

            {/* ── NOMBRE COMERCIAL ── */}
            <p style={{
              fontWeight: '900',
              fontSize: '22px',
              textAlign: 'center',
              margin: '4px 0 12px 0',
              textTransform: 'uppercase',
              lineHeight: '1.3',
            }}>
              {itse.nombre_comercial || '-'}
            </p>

            {/* ── TABLA DE DATOS ── */}
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '0' }}>
              <tbody>
                <tr>
                  <td style={labelEstilo}>DIRECCION</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>{(itse.direccion || '').toUpperCase()}</td>
                </tr>
                <tr>
                  <td style={labelEstilo}>Distrito</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>EL PORVENIR</td>
                </tr>
                <tr>
                  <td style={labelEstilo}>Provincia</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>TRUJILLO</td>
                </tr>
                <tr>
                  <td style={labelEstilo}>Departamento</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>LA LIBERTAD</td>
                </tr>
                <tr>
                  <td style={labelEstilo}>TITULAR</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>{(itse.titular_nombre || '').toUpperCase()}</td>
                </tr>
                <tr>
                  <td style={labelEstilo}>AREA</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>
                    {itse.area != null ? <>{Number(itse.area).toFixed(2)} m<sup>2</sup></> : '-'}
                  </td>
                </tr>

                {/* Fila combinada: Certificación */}
                <tr>
                  <td colSpan={3} style={{ padding: '8px 4px', fontSize: '13px', lineHeight: '1.5' }}>
                    <p>
                    El que suscribe <strong>CERTIFICA</strong> que el Establecimiento Objeto de
                    Inspección antes señalado <strong>CUMPLE CON LAS CONDICIONES DE SEGURIDAD</strong>.
                    </p>
                    <p style={{ marginTop: '12px' }}>
                    Capacidad Máxima de la Edificación:{' '}
                    <strong>{aforo} ({aforoLetras}) personas.</strong>
                    </p>
                  </td>
                </tr>

                {/* Giro o actividad */}
                <tr>
                  <td style={labelEstilo}>Giro o actividad</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>{girosTexto || '-'}.</td>
                </tr>
                {/* Expediente y Resolución */}
                <tr>
                  <td style={labelEstilo}>Expediente Nº</td>
                  <td style={colonEstilo}>:</td>
                  <td style={{ ...valorEstilo, display: 'flex', justifyContent: 'space-between' }}>
                    <span>{numExp}</span>
                    <span style={{ marginRight: '50px' }}>Resolución: {itse.resolucion_numero || '-'}</span>
                  </td>
                </tr>
                {/* Vigencia */}
                <tr>
                  <td style={labelEstilo}>VIGENCIA</td>
                  <td style={colonEstilo}>:</td>
                  <td style={valorEstilo}>{vigencia}</td>
                </tr>
              </tbody>
            </table>

            {/* ── FECHAS ── */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px', marginBottom: '10px' }}>
              <div style={{ fontSize: '13px', lineHeight: '2' }}>
                <div style={{ display: 'flex' }}>
                  <span style={{ minWidth: '290px' }}>FECHA DE EXPEDICIÓN</span>
                  <span>: <strong>{formatFecha(itse.fecha_expedicion)}</strong></span>
                </div>
                <div style={{ display: 'flex' }}>
                  <span style={{ minWidth: '290px' }}>FECHA DE SOLICITUD DE RENOVACIÓN</span>
                  <span>: <strong>{formatFecha(itse.fecha_solicitud_renovacion)}</strong></span>
                </div>
                <div style={{ display: 'flex' }}>
                  <span style={{ minWidth: '290px' }}>FECHA DE CADUCIDAD</span>
                  <span>: <strong>{formatFecha(itse.fecha_caducidad)}</strong></span>
                </div>
              </div>
            </div>

            {/* Espaciador */}
            <div style={{ flex: 1 }} />

            {/* ── QR ── */}
            {qrUrl && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', marginBottom: '8px' }}>
                <QRCode value={qrUrl} size={68} level="M" bgColor="transparent" />
                <p style={{ fontSize: '7px', margin: '3px 0 0 0', color: '#555' }}>
                  Verificar documento
                </p>
              </div>
            )}

            {/* ── PIE DE PÁGINA ── */}
            <div style={{ paddingTop: '5px' }}>
              <p style={{ fontSize: '8px', margin: '0 0 4px 0', lineHeight: '1.3', fontStyle: 'italic' }}>
                *El presente Certificado de ITSE no constituye autorización alguna para el
                funcionamiento del Establecimiento Objeto de Inspección o para el inicio de la actividad
              </p>
              <p style={{ fontWeight: 'bold', fontSize: '8px', margin: '0 0 2px 0', textDecoration: 'underline' }}>NOTA:</p>
              {NOTAS.map((texto, i) => (
                <div key={i} style={{ display: 'flex', gap: '3px', marginBottom: '1px' }}>
                  <span style={{ fontSize: '9px', flexShrink: 0 }}>-</span>
                  <p style={{ margin: 0, fontSize: '8px', lineHeight: '1.3', textTransform: 'uppercase' }}>{texto}</p>
                </div>
              ))}
            </div>

          </div>{/* fin contenido */}
        </div>{/* fin hoja A4 */}
      </div>{/* fin fondo gris */}
    </>
  )
}

export default ItseImprimirPage
