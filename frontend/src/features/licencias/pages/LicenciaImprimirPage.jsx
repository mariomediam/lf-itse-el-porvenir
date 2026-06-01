import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { QRCode } from 'react-qr-code'
import { licenciasApi } from '@api/licenciasApi'
import { personasApi } from '@api/personasApi'
import { configPublicaApi } from '@api/configPublicaApi'

// ── Constantes ────────────────────────────────────────────────────────────────

const CODIGO_DNI = '01'
const CODIGO_CE  = '04'

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

const NOTAS = [
  'Este Certificado debe ser exhibido en lugar visible, bajo pena de multa y/o clausura del establecimiento u oficina.',
  'No autoriza el uso de la vía pública, ni el retiro municipal.',
  'El presente certificado, queda anulado por: Cambio de nombre o razón social, transferencia, traslado, ampliación del local, cambio de giro, fallecimiento del propietario, cuando el ITSE "no cumple" o cuando lo determine la autoridad municipal.',
  'El cierre del establecimiento debe ser comunicado, previa devolución del cartón.',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

const formatFechaEnLetras = (fechaStr) => {
  if (!fechaStr) return '-'
  const d = new Date(fechaStr)
  return `${d.getUTCDate()} de ${MESES[d.getUTCMonth()]} del ${d.getUTCFullYear()}`
}

const getAnio = (fechaStr) => {
  if (!fechaStr) return '-'
  return new Date(fechaStr).getUTCFullYear()
}

const etiquetaDocumento = (doc) => {
  if (!doc) return 'DNI'
  if (doc.tipos_documento_identidad_codigo === CODIGO_DNI) return 'DNI'
  if (doc.tipos_documento_identidad_codigo === CODIGO_CE) return 'C.E.'
  return doc.tipos_documento_identidad_nombre || 'DNI'
}

// ── Página ────────────────────────────────────────────────────────────────────

const LicenciaImprimirPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()

  const [licencia, setLicencia] = useState(null)
  const [giros, setGiros] = useState([])
  const [docIdentidad, setDocIdentidad] = useState(null)
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

        if (lic.conductor_id) {
          try {
            const docRes = await personasApi.getDocumentos(lic.conductor_id)
            const docs = docRes.data
            const docDni = docs.find((d) => d.tipos_documento_identidad_codigo === CODIGO_DNI)
            const docCe = docs.find((d) => d.tipos_documento_identidad_codigo === CODIGO_CE)
            setDocIdentidad(docDni || docCe || null)
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

  const anioLicencia = getAnio(licencia.fecha_emision)
  const girosTexto = giros.map((g) => g.nombre).join(' Y ').toUpperCase()

  const ubicacionConductor = [
    licencia.conductor_direccion,
    licencia.conductor_distrito ? `distrito ${licencia.conductor_distrito}` : null,
    licencia.conductor_provincia ? `provincia ${licencia.conductor_provincia}` : null,
    licencia.conductor_departamento ? `región ${licencia.conductor_departamento}` : null,
  ].filter(Boolean).join(', ')

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <style>{`
        @media print {
          @page { size: A4; margin: 0; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
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
          Vista previa — LIC. N° {licencia.numero_licencia} - {anioLicencia}
        </span>
      </div>

      {/* Fondo gris */}
      <div style={{ backgroundColor: '#d1d5db', minHeight: '100vh', paddingTop: '32px', paddingBottom: '32px' }}>

        {/* Hoja A4 */}
        <div style={{
          width: '210mm',
          height: '297mm',
          margin: '0 auto',
          backgroundColor: '#ffffff',
          padding: '12mm 16mm',
          boxSizing: 'border-box',
          fontFamily: 'Arial, sans-serif',
          color: '#000000',
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>

          {/* Imagen de fondo (marca de agua) */}
          <img
            src="/images/fondo-lf.png"
            alt=""
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '75%',
              opacity: 0.08,
              pointerEvents: 'none',
              zIndex: 0,
            }}
            onError={(e) => { e.target.style.display = 'none' }}
          />

          {/* Contenido (sobre la marca de agua) */}
          <div style={{ position: 'relative', zIndex: 1, flex: 1, display: 'flex', flexDirection: 'column' }}>

            {/* ── ENCABEZADO ── */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
              <img
                src="/images/logo-lf.png"
                alt="Logo"
                style={{ height: '75px', width: 'auto', flexShrink: 0 }}
                onError={(e) => { e.target.style.display = 'none' }}
              />
              <p style={{
                fontWeight: 'bold',
                fontSize: '22px',
                textTransform: 'uppercase',
                margin: 0,
                lineHeight: '1.2',
              }}>
                Municipalidad Provincial de Lamas
              </p>
            </div>

            {/* ── TÍTULOS CENTRADOS ── */}
            <div style={{ textAlign: 'center', marginBottom: '8px' }}>
              <p style={{ fontWeight: 'bold', fontSize: '16px', margin: '0 0 6px 0', textTransform: 'uppercase' }}>
                Certificado de Licencia Municipal de Funcionamiento
              </p>
              <p style={{ fontWeight: 'bold', fontSize: '11px', margin: '0 0 2px 0' }}>
                LEY Nº 28976
              </p>
              <p style={{ fontWeight: 'bold', fontSize: '11px', margin: '0 0 8px 0' }}>
                ORDENANZA MUNICIPAL Nº 022-2010-MPL
              </p>
            </div>

            {/* ── INTRODUCCIÓN ── */}
            <p style={{ fontSize: '11px', textAlign: 'center', margin: '0 0 14px 0', lineHeight: '1.6' }}>
              EL SUBGERENTE DE COMERCIO, LICENCIAS Y CONTROL SANITARIO DE LA MUNICIPALIDAD PROVINCIAL DE LAMAS, QUE SUSCRIBE:
            </p>

            {/* ── CERTIFICA A ── */}
            <p style={{ fontWeight: 'bold', fontSize: '16px', textAlign: 'center', margin: '0 0 10px 0', textDecoration: 'underline' }}>
              CERTIFICA A:
            </p>

            {/* ── NOMBRE COMERCIAL ── */}
            <p style={{ fontWeight: 'bold', fontSize: '28px', textAlign: 'center', margin: '0 0 14px 0', textTransform: 'uppercase', lineHeight: '1.2' }}>
              {licencia.nombre_comercial || '-'}
            </p>

            {/* ── PÁRRAFO PRINCIPAL ── */}
            <p style={{ fontSize: '12px', textAlign: 'justify', margin: '0 0 14px 0', lineHeight: '1.7' }}>
              Con dirección en {licencia.direccion || '-'}, distrito y provincia de Lamas, región
              San Martín{licencia.titular_ruc ? `; con RUC N° ${licencia.titular_ruc}` : ''}, expedida
              con Resolución Subgerencial Nº {licencia.resolucion_numero || '-'}, registrado con el
              Código de Contribuyente Nº {licencia.numero_licencia || '-'}.
            </p>

            {/* ── PROPIETARIO / REPRESENTANTE LEGAL ── */}
            <p style={{ fontWeight: 'bold', fontSize: '12px', margin: '0 0 4px 0', textDecoration: 'underline' }}>
              Propietario o Representante Legal:
            </p>
            <p style={{ fontSize: '12px', textAlign: 'justify', margin: '0 0 14px 0', lineHeight: '1.7' }}>
              <strong>{licencia.conductor_nombre || '-'}</strong>
              {docIdentidad && (
                <> con {etiquetaDocumento(docIdentidad)} Nº {docIdentidad.numero_documento}</>
              )}
              {ubicacionConductor && <>, con domicilio en {ubicacionConductor}</>}
              .
            </p>

            {/* ── ACTIVIDAD ECONÓMICA ── */}
            <p style={{ fontWeight: 'bold', fontSize: '12px', margin: '0 0 4px 0', textDecoration: 'underline' }}>
              Actividad Económica:
            </p>
            <p style={{ fontWeight: 'bold', fontSize: '16px', margin: '0 0 14px 0', lineHeight: '1.5', textTransform: 'uppercase' }}>
              {girosTexto || '-'}
            </p>

            {/* ── HABILITACIÓN ── */}
            <p style={{ fontSize: '12px', textAlign: 'justify', margin: '0 0 16px 0', lineHeight: '1.7' }}>
              Habiendo cumplido con los requisitos reglamentarios que exige las Disposiciones Municipales
              vigentes, está legalmente habilitada a desarrollar su actividad económica.
            </p>

            {/* ── LUGAR Y FECHA ── */}
            <p style={{ fontSize: '12px', textAlign: 'right', margin: '0 0 0 0', lineHeight: '1.5' }}>
              Lamas, {formatFechaEnLetras(licencia.fecha_emision)}
            </p>

            {/* Espaciador */}
            <div style={{ flex: 1 }} />

            {/* ── NOTA + QR ── */}
            <div style={{ border: '1.5px solid #000', padding: '8px 10px', display: 'flex', gap: '10px' }}>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 'bold', fontSize: '9px', margin: '0 0 4px 0', color: '#c00', textDecoration: 'underline' }}>
                  NOTA:
                </p>
                {NOTAS.map((texto, i) => (
                  <div key={i} style={{ display: 'flex', gap: '4px', marginBottom: '2px' }}>
                    <span style={{ fontSize: '8.5px', flexShrink: 0 }}>-</span>
                    <p style={{ margin: 0, fontSize: '8.5px', lineHeight: '1.4' }}>{texto}</p>
                  </div>
                ))}
              </div>
              {qrUrl && (
                <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <QRCode value={qrUrl} size={72} level="M" />
                  <p style={{ fontSize: '7px', margin: '3px 0 0 0', textAlign: 'center', color: '#555' }}>
                    Verificar documento
                  </p>
                </div>
              )}
            </div>

          </div>{/* fin contenido */}
        </div>{/* fin hoja A4 */}
      </div>{/* fin fondo gris */}
    </>
  )
}

export default LicenciaImprimirPage
