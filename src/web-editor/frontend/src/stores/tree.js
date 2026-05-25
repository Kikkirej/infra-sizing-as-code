import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '../api/client.js'

export const useTreeStore = defineStore('tree', () => {
  const treeData = ref(null)
  const selectedNode = ref(null)
  const selectedDetail = ref(null)

  async function fetchTree() {
    const { data } = await client.get('/tree')
    treeData.value = data
  }

  function selectNode(node) {
    selectedNode.value = node
    selectedDetail.value = null
  }

  function clearSelection() {
    selectedNode.value = null
    selectedDetail.value = null
  }

  function setDetail(detail) {
    selectedDetail.value = detail
  }

  function updateNodeChange(shortname, change) {
    if (treeData.value?.products?.[shortname]) {
      treeData.value.products[shortname].change = change
    }
  }

  return { treeData, selectedNode, selectedDetail, fetchTree, selectNode, clearSelection, setDetail, updateNodeChange }
})
