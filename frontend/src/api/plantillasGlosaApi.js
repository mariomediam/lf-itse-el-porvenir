import api from './axios'

export const plantillasGlosaApi = {
  listar: (params = {}) =>
    api.get('/api/lf-itse/plantillas-glosa-licencia/', { params }),

  obtener: (id) =>
    api.get(`/api/lf-itse/plantillas-glosa-licencia/${id}/`),

  crear: (data) =>
    api.post('/api/lf-itse/plantillas-glosa-licencia/', data),

  actualizar: (id, data) =>
    api.put(`/api/lf-itse/plantillas-glosa-licencia/${id}/`, data),

  eliminar: (id) =>
    api.delete(`/api/lf-itse/plantillas-glosa-licencia/${id}/`),
}
