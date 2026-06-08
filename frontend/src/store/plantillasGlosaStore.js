import { create } from 'zustand'

const usePlantillasGlosaStore = create((set) => ({
  params: null,
  setParams: (params) => set({ params }),
}))

export default usePlantillasGlosaStore
