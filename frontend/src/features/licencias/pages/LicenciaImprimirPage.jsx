import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { QRCode } from 'react-qr-code'
import { licenciasApi } from '@api/licenciasApi'
import { personasApi } from '@api/personasApi'
import { configPublicaApi } from '@api/configPublicaApi'

const CODIGO_DNI = '01'
const CODIGO_CE  = '04'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

const getAnio = (fechaStr) => {
  if (!fechaStr) return ''
  return new Date(fechaStr).getUTCFullYear()
}

const formatFechaLarga = (fechaStr) => {
  if (!fechaStr) return ''
  const d = new Date(fechaStr)
  const dia = String(d.getUTCDate()).padStart(2, '0')
  const mes = MESES[d.getUTCMonth()]
  const anio = d.getUTCFullYear()
  return `${dia} de ${mes} del ${anio}`
}

const formatFechaCorta = (fechaStr) => {
  if (!fechaStr) return ''
  const d = new Date(fechaStr)
  return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
}

const LicenciaImprimirPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [licencia, setLicencia] = useState(null)
  const [giros, setGiros] = useState([])
  const [docTitular, setDocTitular] = useState(null)
  const [qrUrl, setQrUrl] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const cargar = async () => {
      try {
        setCargando(true)
        const [licRes, girosRes, configRes] = await Promise.all([
          licenciasApi.buscar('ID', id),
          licenciasApi.getGiros(id),
          configPublicaApi.getConfig().catch(() => ({ data: {} })),
        ])

        const lic = licRes.data[0]
        if (!lic) { setError('Licencia no encontrada.'); return }

        setLicencia(lic)
        setGiros(girosRes.data)

        const cfg = configRes.data
        if (cfg.qr_verificacion_habilitado && cfg.qr_url_verificar_licencia && lic.uuid) {
          const base = cfg.qr_url_verificar_licencia.replace(/\/+$/, '')
          setQrUrl(`${base}/${lic.uuid}`)
        }

        if (lic.titular_id) {
          try {
            const docRes = await personasApi.getDocumentos(lic.titular_id)
            const docs = docRes.data
            const docDni = docs.find((d) => d.tipos_documento_identidad_codigo === CODIGO_DNI)
            const docCe = docs.find((d) => d.tipos_documento_identidad_codigo === CODIGO_CE)
            setDocTitular(docDni || docCe || null)
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

  const numLic = `${String(licencia.numero_licencia).padStart(4, '0')}-${getAnio(licencia.fecha_emision)}`
  const numExp = `${String(licencia.numero_expediente ?? '').padStart(1, '0')}-${getAnio(licencia.fecha_recepcion)}`
  const girosTexto = giros.map((g) => g.nombre).join(', ').toUpperCase()

  const vencimiento = licencia.es_vigencia_indeterminada
    ? 'INDEFINIDA'
    : licencia.fecha_inicio_vigencia && licencia.fecha_fin_vigencia
      ? `${formatFechaCorta(licencia.fecha_inicio_vigencia)} - ${formatFechaCorta(licencia.fecha_fin_vigencia)}`
      : '-'

  const docTitularTexto = docTitular
    ? `${docTitular.tipos_documento_identidad_nombre || 'DNI'} N°${docTitular.numero_documento}`
    : ''

  return (
    <>
      <style>{`
        @media print {
          @page { size: 240mm 160mm; margin: 0; }
          html, body { margin: 0; padding: 0; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
          .fondo-gris { background: none !important; padding: 0 !important; }
          .hoja { margin: 0 !important; box-shadow: none !important; }
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
          Vista previa — LIC. N° {numLic}
        </span>
      </div>

      {/* Fondo gris */}
      <div className="fondo-gris" style={{ backgroundColor: '#d1d5db', minHeight: '100vh', paddingTop: '32px', paddingBottom: '32px' }}>

        {/* Hoja 240mm x 160mm */}
        <div className="hoja" style={{
          width: '240mm',
          height: '160mm',
          margin: '0 auto',
          backgroundColor: '#fff',
          boxSizing: 'border-box',
          fontFamily: 'Arial, sans-serif',
          color: '#4a2000',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        }}>

          {/* ── ENCABEZADO ── */}
          <div style={{ padding: '8mm 12mm 0 12mm' }}>

            {/* Fila superior: Número de licencia (izq) + Expediente y Vencimiento (der) */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>

              {/* Número de licencia */}
              <div style={{
                border: '3.5px solid #4a2000',
                padding: '2mm 5mm',
                fontSize: '20px',
                fontWeight: 'bold',
                marginTop: '18mm',
                marginLeft: '52mm',
              }}>
                {numLic}
              </div>

              {/* Expediente + Vencimiento */}
              <div style={{ textAlign: 'right' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '2mm', marginBottom: '3mm' }}>
                  
                  <span style={{
                    // border: '1px solid #4a2000',
                    padding: '1.5mm 4mm',
                    fontSize: '18px',
                    fontWeight: 'bold',
                    minWidth: '25mm',
                    textAlign: 'center',
                    marginTop: '14mm',
                    marginRight: '33mm',
                  }}>
                    {numExp}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '3mm' }}>
                  
                  <span style={{
                    // border: '1px solid #4a2000',
                    padding: '1.5mm 4mm',
                    fontSize: '18px',
                    fontWeight: 'bold',
                    minWidth: '25mm',
                    textAlign: 'center',
                    marginTop: '0mm',
                    marginRight: '23mm',
                  }}>
                    {vencimiento}
                  </span>
                </div>
              </div>
            </div>

            {/* ── TÍTULO ── */}
            <h1 style={{
              textAlign: 'center',
              fontSize: '18px',
              fontWeight: 'bold',
              margin: '2mm 0 0 0',
              letterSpacing: '0.5px',
            }}>
              CERTIFICADO DE LICENCIA DE FUNCIONAMIENTO
            </h1>
            <p style={{
              textAlign: 'center',
              fontSize: '8.5px',
              margin: '0 0 3mm 0',
            }}>
              Ley Orgánica de Municipalidades N° 27972, Ley Marco de Licencia de Funcionamiento N° 28976.
            </p>

            {/* ── CAMPOS ── */}
            <div style={{ fontSize: '12px', lineHeight: '1.8', paddingLeft: '9mm', paddingRight: '9mm' }}>

              {/* OTORGADO A */}
              <div style={{ display: 'flex', gap: '2mm', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap', width: '34mm', flexShrink: 0 }}>OTORGADO A</span>
                <span style={{ whiteSpace: 'nowrap' }}>:</span>
                <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', minWidth: 0 }}>
                  {(licencia.titular_nombre || '').toUpperCase()}
                  {docTitularTexto && (
                    <span style={{ marginLeft: '12px' }}>{docTitularTexto}</span>
                  )}
                  {licencia.titular_ruc && (
                    <span style={{ marginLeft: '12px' }}>RUC N°{licencia.titular_ruc}</span>
                  )}
                </span>
              </div>

              {/* GIRO O ACTIVIDAD */}
              <div style={{ display: 'flex', gap: '2mm', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap', width: '34mm', flexShrink: 0 }}>GIRO O ACTIVIDAD</span>
                <span style={{ whiteSpace: 'nowrap' }}>:</span>
                <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', minWidth: 0 }}>{licencia.actividad || '-'}</span>
              </div>

              {/* NOMBRE COMERCIAL */}
              <div style={{ display: 'flex', gap: '2mm', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap', width: '34mm', flexShrink: 0 }}>NOMBRE COMERCIAL</span>
                <span style={{ whiteSpace: 'nowrap' }}>:</span>
                <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', minWidth: 0 }}>{(licencia.nombre_comercial || '').toUpperCase()}</span>
              </div>

              {/* DIRECCIÓN */}
              <div style={{ display: 'flex', gap: '2mm', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap', width: '34mm', flexShrink: 0 }}>DIRECCIÓN</span>
                <span style={{ whiteSpace: 'nowrap' }}>:</span>
                <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', minWidth: 0 }}>{(licencia.direccion || '').toUpperCase()}</span>
              </div>

              {/* ÁREA COMERCIAL + CÓDIGO CATASTRAL */}
              <div style={{ display: 'flex', gap: '2mm', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap', width: '34mm', flexShrink: 0 }}>ÁREA COMERCIAL</span>
                <span style={{ whiteSpace: 'nowrap' }}>:</span>
                <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', minWidth: 0 }}>
                  {licencia.area != null ? `${Number(licencia.area).toFixed(0)} m²` : '-'}
                </span>
                <div style={{ display: 'flex', alignItems: 'flex-end', flexShrink: 0, width: '75mm' }}>
                  <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>CÓDIGO CATASTRAL:</span>
                  <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', marginLeft: '2mm', minWidth: 0, textAlign: 'center' }}>
                    {licencia.zonificacion_codigo || '-'}
                  </span>
                </div>
              </div>

              {/* TIPO DE ANUNCIO + MEDIDA */}
              <div style={{ display: 'flex', gap: '2mm', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap', width: '34mm', flexShrink: 0 }}>TIPO DE ANUNCIO</span>
                <span style={{ whiteSpace: 'nowrap' }}>:</span>
                <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', minWidth: 0 }}>{licencia.tipo_letrero_nombre || '-'}</span>
                <div style={{ display: 'flex', alignItems: 'flex-end', flexShrink: 0, width: '75mm' }}>
                  <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>MEDIDA:</span>
                  <span style={{ fontWeight: 'bold', flex: 1, borderBottom: '1px solid #4a2000', marginLeft: '2mm', minWidth: 0, textAlign: 'center' }}>
                    {licencia.medidas || '-'}
                  </span>
                </div>
              </div>
            </div>

            {/* ── GLOSA ── */}
            {licencia.glosa && (
              <p style={{
                fontSize: '12.5px',
                lineHeight: '1.4',
                margin: '3mm 0 0 9mm',
                whiteSpace: 'pre-wrap',
              }}>
                {licencia.glosa}
              </p>
            )}

            {/* ── FECHA ── */}
            <p style={{
              fontSize: '12.5px',
              textAlign: 'right',
              margin: '1mm 12mm 0 0',
              fontWeight: 'bold',
            }}>
              El Porvenir, {formatFechaLarga(licencia.fecha_emision)}
            </p>
          </div>

          {/* ── QR (inferior izquierdo) ── */}
          {qrUrl && (
            <div style={{
              position: 'absolute',
              bottom: '25mm',
              left: '10mm',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginLeft: '17mm',
            }}>
              <QRCode value={qrUrl} size={52} level="M" bgColor="transparent" />
              <p style={{ fontSize: '6px', margin: '2px 0 0 0', color: '#4a2000' }}>
                Verificar documento
              </p>
            </div>
          )}

        </div>{/* fin hoja */}
      </div>{/* fin fondo gris */}
    </>
  )
}

export default LicenciaImprimirPage
