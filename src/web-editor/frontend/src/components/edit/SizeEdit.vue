<template>
  <div class="edit-panel">
    <h2>Size: {{ node.display_name }}</h2>
    <div class="field-group">
      <label>Shortname <input :value="node.shortname" readonly class="readonly" /></label>
      <label>Display Name <input v-model="form.display_name" @blur="save" /></label>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { useTreeStore } from '../../stores/tree.js'
import client from '../../api/client.js'

const props = defineProps({ node: Object, productSn: String, sizeSn: String })
const store = useTreeStore()
const form = reactive({ display_name: props.node.display_name })
watch(() => props.node, (n) => Object.assign(form, { display_name: n.display_name }))

async function save() {
  await client.put(`/products/${props.productSn}/sizes/${props.sizeSn}`, form)
  await store.fetchTree()
}
</script>

<style scoped>
.edit-panel { max-width: 600px; }
h2 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }
.field-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.readonly { background: #f9fafb; color: #6b7280; }
</style>
