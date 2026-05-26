<template>
  <div class="edit-panel">
    <h2>Flavour: {{ node.display_name }}</h2>
    <div class="field-group">
      <label>Shortname <input :value="node.shortname" readonly class="readonly" /></label>
      <label>Display Name <input v-model="form.display_name" @blur="save" /></label>
      <label>Image Type
        <select v-model="form.image_type" @change="onTypeChange">
          <option value="">None</option>
          <option value="file">File</option>
          <option value="mermaid">Mermaid</option>
        </select>
      </label>

      <!-- file mode -->
      <template v-if="form.image_type === 'file'">
        <div class="upload-area">
          <label class="upload-label">Upload image (.png, .svg)</label>
          <input type="file" accept=".png,.svg" @change="upload" />
          <span v-if="uploadMsg" :class="uploadMsg.ok ? 'msg-ok' : 'msg-err'">{{ uploadMsg.text }}</span>
        </div>
        <div v-if="node.image_value" class="image-preview">
          <img :src="`/api/files/image/${productSn}/${sizeSn}/${flavourSn}?t=${cacheBust}`" alt="Preview" />
        </div>
      </template>

      <!-- mermaid mode -->
      <template v-else-if="form.image_type === 'mermaid'">
        <div class="mermaid-editor">
          <div class="mermaid-header">
            <span class="field-label">Mermaid diagram</span>
            <button class="btn-preview" @click="togglePreview">{{ previewMode ? 'Edit' : 'Preview' }}</button>
          </div>
          <textarea v-if="!previewMode" v-model="mermaidContent" @blur="saveMermaid" rows="8" class="mermaid-textarea" placeholder="graph TD&#10;  A --> B" />
          <div v-else class="mermaid-preview" v-html="mermaidSvg" />
          <span v-if="mermaidErr" class="msg-err">{{ mermaidErr }}</span>
          <span v-if="mermaidSaving" class="msg-saving">Saving…</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import mermaid from 'mermaid'
import { useTreeStore } from '../../stores/tree.js'
import client from '../../api/client.js'

mermaid.initialize({ startOnLoad: false, theme: 'default' })

const props = defineProps({ node: Object, productSn: String, sizeSn: String, flavourSn: String })
const store = useTreeStore()

const form = reactive({ display_name: props.node.display_name, image_type: props.node.image_type || '' })
const uploadMsg = ref(null)
const cacheBust = ref(Date.now())

const mermaidContent = ref('')
const previewMode = ref(false)
const mermaidSvg = ref('')
const mermaidErr = ref('')
const mermaidSaving = ref(false)

watch(() => props.node, async (n) => {
  Object.assign(form, { display_name: n.display_name, image_type: n.image_type || '' })
  mermaidContent.value = ''
  previewMode.value = false
  mermaidErr.value = ''
  if (n.image_type === 'mermaid') await loadMermaidContent()
})

onMounted(async () => {
  if (form.image_type === 'mermaid') await loadMermaidContent()
})

async function save(imageValue) {
  await client.put(`/products/${props.productSn}/sizes/${props.sizeSn}/flavours/${props.flavourSn}`, {
    display_name: form.display_name,
    image_type: form.image_type || null,
    image_value: imageValue !== undefined ? imageValue : (props.node.image_value || null),
  })
  await store.fetchTree()
}

async function onTypeChange() {
  const imageValue = form.image_type ? (props.node.image_value || null) : null
  await save(imageValue)
  uploadMsg.value = null
  mermaidContent.value = ''
  previewMode.value = false
  mermaidErr.value = ''
  if (form.image_type === 'mermaid') await loadMermaidContent()
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
    cacheBust.value = Date.now()
    await store.fetchTree()
  } catch (err) {
    uploadMsg.value = { ok: false, text: err.response?.data?.detail || 'Upload failed' }
  }
}

async function loadMermaidContent() {
  try {
    const { data } = await client.get(`/files/content/${props.productSn}/${props.sizeSn}/${props.flavourSn}`)
    mermaidContent.value = data.content
  } catch {
    mermaidContent.value = ''
  }
}

async function saveMermaid() {
  if (!mermaidContent.value.trim()) return
  mermaidSaving.value = true
  try {
    const blob = new Blob([mermaidContent.value], { type: 'text/plain' })
    const file = new File([blob], 'diagram.mmd', { type: 'text/plain' })
    const fd = new FormData()
    fd.append('file', file)
    await client.post(`/files/upload/${props.productSn}/${props.sizeSn}/${props.flavourSn}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await store.fetchTree()
  } finally {
    mermaidSaving.value = false
  }
}

async function togglePreview() {
  if (!previewMode.value) {
    try {
      mermaidErr.value = ''
      const id = `mermaid-${Date.now()}`
      const { svg } = await mermaid.render(id, mermaidContent.value)
      mermaidSvg.value = svg
    } catch (e) {
      mermaidErr.value = `Render error: ${e.message}`
      return
    }
  }
  previewMode.value = !previewMode.value
}
</script>

<style scoped>
.edit-panel { max-width: 600px; }
h2 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }
.field-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input, select { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.readonly { background: #f9fafb; color: #6b7280; }
.upload-area { display: flex; flex-direction: column; gap: 6px; }
.upload-label { font-size: 13px; font-weight: 500; color: #374151; }
.msg-ok { color: #16a34a; font-size: 12px; }
.msg-err { color: #dc2626; font-size: 12px; }
.msg-saving { color: #6b7280; font-size: 12px; }
.image-preview { border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; background: #f9fafb; }
.image-preview img { max-width: 100%; max-height: 300px; object-fit: contain; display: block; }
.mermaid-editor { display: flex; flex-direction: column; gap: 6px; }
.mermaid-header { display: flex; align-items: center; justify-content: space-between; }
.field-label { font-size: 13px; font-weight: 500; color: #374151; }
.btn-preview { padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: white; cursor: pointer; font-size: 12px; }
.mermaid-textarea { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 13px; resize: vertical; }
.mermaid-preview { padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; overflow-x: auto; }
</style>
