<template>
  <div class="edit-panel">
    <h2>Flavour: {{ node.display_name }}</h2>
    <div class="field-group">
      <label>Shortname <input :value="node.shortname" readonly class="readonly" /></label>
      <label>Display Name <input v-model="form.display_name" @blur="save" /></label>
      <label>Image Type
        <select v-model="form.image_type" @change="save">
          <option value="">None</option>
          <option value="file">file</option>
          <option value="mermaid">mermaid</option>
        </select>
      </label>
      <label v-if="form.image_type">Image File <input :value="node.image_value || ''" readonly class="readonly" /></label>

      <div class="upload-area">
        <label class="upload-label">Upload image / diagram</label>
        <input type="file" accept=".png,.svg,.mmd" @change="upload" />
        <span v-if="uploadMsg" :class="uploadMsg.ok ? 'msg-ok' : 'msg-err'">{{ uploadMsg.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useTreeStore } from '../../stores/tree.js'
import client from '../../api/client.js'

const props = defineProps({ node: Object, productSn: String, sizeSn: String, flavourSn: String })
const store = useTreeStore()
const uploadMsg = ref(null)
const form = reactive({ display_name: props.node.display_name, image_type: props.node.image_type || '' })
watch(() => props.node, (n) => Object.assign(form, { display_name: n.display_name, image_type: n.image_type || '' }))

async function save() {
  await client.put(`/products/${props.productSn}/sizes/${props.sizeSn}/flavours/${props.flavourSn}`, {
    display_name: form.display_name,
    image_type: form.image_type || null,
    image_value: props.node.image_value || null,
  })
  await store.fetchTree()
}

async function upload(e) {
  const file = e.target.files[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    await client.post(`/files/upload/${props.productSn}/${props.sizeSn}/${props.flavourSn}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    uploadMsg.value = { ok: true, text: `Uploaded: ${file.name}` }
    await store.fetchTree()
  } catch (err) {
    uploadMsg.value = { ok: false, text: err.response?.data?.detail || 'Upload failed' }
  }
}
</script>

<style scoped>
.edit-panel { max-width: 600px; }
h2 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }
.field-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input, select { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.readonly { background: #f9fafb; color: #6b7280; }
.upload-area { display: flex; flex-direction: column; gap: 6px; border-top: 1px solid #e2e8f0; padding-top: 12px; }
.upload-label { font-size: 13px; font-weight: 500; color: #374151; }
.msg-ok { color: #16a34a; font-size: 12px; }
.msg-err { color: #dc2626; font-size: 12px; }
</style>
