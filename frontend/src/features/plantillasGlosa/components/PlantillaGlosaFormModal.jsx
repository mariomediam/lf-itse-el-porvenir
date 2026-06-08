import { useState, useEffect } from 'react'
import { Modal, ModalHeader, ModalBody, ModalFooter } from 'flowbite-react'
import { toast } from 'sonner'
import { plantillasGlosaApi } from '@api/plantillasGlosaApi'

const inputClass =
  'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 bg-white ' +
  'focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary ' +
  'disabled:bg-gray-50 disabled:text-gray-400 placeholder:text-gray-400'

const labelClass = 'block text-xs font-medium text-gray-600 mb-1'

const estadoInicial = {
  nombre:      '',
  descripcion: '',
  esta_activo: true,
}

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

export default function PlantillaGlosaFormModal({ isOpen, onClose, onSuccess, plantilla = null }) {
  const esEdicion = !!plantilla

  const [formData,     setFormData]     = useState(estadoInicial)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    if (plantilla) {
      setFormData({
        nombre:      plantilla.nombre      ?? '',
        descripcion: plantilla.descripcion ?? '',
        esta_activo: plantilla.esta_activo ?? true,
      })
    } else {
      setFormData(estadoInicial)
    }
  }, [isOpen, plantilla])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleClose = () => {
    setFormData(estadoInicial)
    onClose()
  }

  const handleSubmit = async () => {
    if (!formData.nombre.trim()) {
      toast.error('El nombre de la plantilla es obligatorio')
      return
    }
    if (!formData.descripcion.trim()) {
      toast.error('La descripción (glosa) es obligatoria')
      return
    }

    const body = {
      nombre:      formData.nombre.trim(),
      descripcion: formData.descripcion.trim(),
      esta_activo: formData.esta_activo,
    }

    setIsSubmitting(true)
    try {
      if (esEdicion) {
        await plantillasGlosaApi.actualizar(plantilla.id, body)
      } else {
        await plantillasGlosaApi.crear(body)
      }
      toast.success(esEdicion ? 'Plantilla actualizada correctamente' : 'Plantilla creada correctamente')
      onSuccess?.()
      handleClose()
    } catch (err) {
      const data = err.response?.data
      const detail =
        data?.error ||
        data?.detail ||
        data?.non_field_errors?.[0] ||
        (typeof data === 'string' ? data : null) ||
        'Error al guardar la plantilla'
      toast.error(detail)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal show={isOpen} size="lg" onClose={handleClose}>

      <ModalHeader className="bg-white border-b border-gray-200">
        <div className="flex items-center gap-2.5">
          <span className="text-primary">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </span>
          <span className="text-base font-semibold text-gray-800">
            {esEdicion ? 'Modificar plantilla de glosa' : 'Agregar plantilla de glosa'}
          </span>
        </div>
      </ModalHeader>

      <ModalBody className="bg-white px-6 py-5 space-y-5">

        <div>
          <label className={labelClass}>
            Nombre <span className="text-danger">*</span>
          </label>
          <input
            type="text"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            placeholder="Ej: Bares - O.M. N° 0010-2019-MDEP"
            className={inputClass}
            maxLength={150}
          />
        </div>

        <div>
          <label className={labelClass}>
            Descripción (glosa) <span className="text-danger">*</span>
          </label>
          <textarea
            name="descripcion"
            value={formData.descripcion}
            onChange={handleChange}
            rows={5}
            placeholder="Ej: O.M. N° 0010-2019-MDEP: BARES: La modalidad de expendio..."
            className={`${inputClass} resize-y`}
          />
        </div>

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="esta_activo"
            name="esta_activo"
            checked={formData.esta_activo}
            onChange={handleChange}
            className="w-4 h-4 text-primary border-gray-300 rounded
                       focus:ring-2 focus:ring-primary/30 cursor-pointer"
          />
          <label htmlFor="esta_activo" className="text-sm text-gray-700 cursor-pointer select-none">
            Plantilla activa
          </label>
        </div>

      </ModalBody>

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
          {isSubmitting ? (
            <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
          ) : (
            <IconoGuardar />
          )}
          {isSubmitting ? 'Guardando...' : 'Guardar plantilla'}
        </button>
      </ModalFooter>
    </Modal>
  )
}
