<template>
  <div class="edit-panel">
    <div class="edit-header">
      <h2>Product: {{ node.display_name }}</h2>
      <button v-if="node.change !== 'ADDED'" class="btn-reset" @click="reset">Reset Product</button>
    </div>
    <div v-if="node.error" class="error-banner">{{ node.error }}</div>
    <div v-else class="field-group">
      <label>Shortname <input :value="node.shortname" readonly class="readonly" /></label>
      <label>Display Name <input v-model="displayName" @blur="save" /></label>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTreeStore } from '../../stores/tree.js'
import client from '../../api/client.js'

const props = defineProps({ node: Object, productSn: String })
const store = useTreeStore()
const displayName = ref(props.node.display_name)

watch(() => props.node, (n) => { displayName.value = n.display_name }, { deep: true })

async function save() {
  await client.put(`/products/${props.productSn}`, { display_name: displayName.value })
  await store.fetchTree()
}

async function reset() {
  if (!confirm('Reset all changes for this product?')) return
  await client.post(`/products/${props.productSn}/reset`)
  await store.fetchTree()
  store.clearSelection()
}
</script>

<style scoped>
.edit-panel { max-width: 600px; }
.edit-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
h2 { font-size: 18px; font-weight: 600; }
.btn-reset { padding: 6px 12px; background: #fee2e2; color: #dc2626; border: none; border-radius: 6px; cursor: pointer; }
.error-banner { padding: 12px; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; color: #dc2626; }
.field-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.readonly { background: #f9fafb; color: #6b7280; }
</style>
