import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '../api/client.js'

export const useVersioningStore = defineStore('versioning', () => {
  const versionList = ref({ wip: false, versions: [] })
  const selectedVersion = ref('wip')
  const versionData = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchVersionList(productSn) {
    try {
      const { data } = await client.get(`/products/${productSn}/versioning`)
      versionList.value = data
    } catch {
      versionList.value = { wip: false, versions: [] }
    }
  }

  async function selectVersion(productSn, version) {
    selectedVersion.value = version
    versionData.value = null
    error.value = null
    loading.value = true
    try {
      const { data } = await client.get(`/products/${productSn}/versioning/${version}`)
      versionData.value = data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to load version data'
    } finally {
      loading.value = false
    }
  }

  async function reset(productSn) {
    await client.post(`/products/${productSn}/versioning/wip/reset`)
    await selectVersion(productSn, 'wip')
    await fetchVersionList(productSn)
  }

  function clear() {
    versionList.value = { wip: false, versions: [] }
    selectedVersion.value = 'wip'
    versionData.value = null
    error.value = null
  }

  return { versionList, selectedVersion, versionData, loading, error, fetchVersionList, selectVersion, reset, clear }
})
