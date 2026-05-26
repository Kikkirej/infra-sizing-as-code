import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '../api/client.js'

export const useUnitsStore = defineStore('units', () => {
  const units = ref([])

  async function fetchUnits() {
    const { data } = await client.get('/units')
    units.value = data.units
  }

  async function addUnit(unit) {
    await client.post('/units', { unit })
    await fetchUnits()
  }

  async function removeUnit(unit) {
    const { data } = await client.delete(`/units/${encodeURIComponent(unit)}`)
    await fetchUnits()
    return data
  }

  return { units, fetchUnits, addUnit, removeUnit }
})
