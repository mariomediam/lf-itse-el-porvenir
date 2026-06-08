import { useState, useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'
import TopBar from '@components/layout/TopBar'
import SideMenu from '@components/layout/SideMenu'
import ExpedienteHeader from '@features/expedientes/components/ExpedienteHeader'
import BuscadorPlantillaGlosa from '../components/BuscadorPlantillaGlosa'
import PlantillaGlosaCard from '../components/PlantillaGlosaCard'
import PlantillaGlosaFormModal from '../components/PlantillaGlosaFormModal'
import { dashboardApi } from '@api/dashboardApi'
import { plantillasGlosaApi } from '@api/plantillasGlosaApi'
import usePlantillasGlosaStore from '@store/plantillasGlosaStore'

export default function PlantillasGlosaPage() {
  const [sidebarOpen,  setSidebarOpen]  = useState(true)
  const [menus,        setMenus]        = useState([])
  const [todas,        setTodas]        = useState([])
  const [plantillas,   setPlantillas]   = useState([])
  const [loading,      setLoading]      = useState(false)
  const [buscado,      setBuscado]      = useState(false)
  const [modalAgregar, setModalAgregar] = useState(false)

  const { params, setParams } = usePlantillasGlosaStore()

  const paramsInicialRef = useRef(params)

  useEffect(() => {
    dashboardApi.getMenusUsuario()
      .then((res) => setMenus(res.data))
      .catch(() => toast.error('Error al cargar el menú'))
  }, [])

  const aplicarFiltroTexto = (lista, texto) => {
    if (!texto) return lista
    const q = texto.toLowerCase()
    return lista.filter(
      (p) => p.nombre.toLowerCase().includes(q),
    )
  }

  const ejecutarBusqueda = useCallback(async (p) => {
    setLoading(true)
    setBuscado(true)
    try {
      const queryParams = {}
      if (p?.esta_activo) queryParams.esta_activo = p.esta_activo
      const res = await plantillasGlosaApi.listar(queryParams)
      setTodas(res.data)
      setPlantillas(aplicarFiltroTexto(res.data, p?.texto))
    } catch (error) {
      const msg = error.response?.data?.error || 'Error al cargar las plantillas de glosa'
      toast.error(msg)
      setTodas([])
      setPlantillas([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (paramsInicialRef.current) {
      ejecutarBusqueda(paramsInicialRef.current)
    }
  }, [ejecutarBusqueda])

  const handleBuscar = (p) => {
    setParams(p)
    ejecutarBusqueda(p)
  }

  const handleActualizar = () => {
    const ultima = usePlantillasGlosaStore.getState().params
    ejecutarBusqueda(ultima ?? {})
  }

  return (
    <div className="flex flex-col h-screen bg-neutral">
      <TopBar onToggleSidebar={() => setSidebarOpen((v) => !v)} />

      <div className="flex flex-1 overflow-hidden">
        <SideMenu menus={menus} isOpen={sidebarOpen} />

        <main className="flex-1 overflow-y-auto p-6">
          <ExpedienteHeader
            titulo="Plantillas de glosa"
            subtitulo="Gestione las plantillas de glosa para licencias de funcionamiento"
            onActualizar={handleActualizar}
            onAgregar={() => setModalAgregar(true)}
            labelAgregar="Agregar plantilla"
          />

          <BuscadorPlantillaGlosa
            onBuscar={handleBuscar}
            loading={loading}
            initialParams={paramsInicialRef.current}
          />

          {loading && (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          )}

          {!loading && buscado && (
            <>
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm font-medium text-gray-700">
                  {plantillas.length}{' '}
                  {plantillas.length === 1 ? 'plantilla encontrada' : 'plantillas encontradas'}
                  {todas.length !== plantillas.length && (
                    <span className="text-gray-400 ml-1">
                      (de {todas.length} en total)
                    </span>
                  )}
                </p>
              </div>

              {plantillas.length > 0 ? (
                <div className="space-y-3">
                  {plantillas.map((p) => (
                    <PlantillaGlosaCard key={p.id} plantilla={p} onRefrescar={handleActualizar} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500 text-sm">
                  No se encontraron plantillas de glosa con los criterios indicados.
                </div>
              )}
            </>
          )}
        </main>
      </div>

      <PlantillaGlosaFormModal
        isOpen={modalAgregar}
        onClose={() => setModalAgregar(false)}
        onSuccess={() => {
          setModalAgregar(false)
          handleActualizar()
        }}
      />
    </div>
  )
}
