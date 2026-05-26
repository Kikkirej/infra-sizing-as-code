<template>
  <div class="edit-panel">
    <div class="edit-header">
      <h2>Product: {{ node.display_name }}</h2>
      <div class="header-actions">
        <button v-if="node.change !== 'ADDED'" class="btn-release" @click="openRelease">Release…</button>
        <button v-if="node.change !== 'ADDED'" class="btn-reset" @click="reset">Reset Product</button>
      </div>
    </div>
    <div v-if="node.error" class="error-banner">{{ node.error }}</div>
    <div v-else class="field-group">
      <label>Shortname <input :value="node.shortname" readonly class="readonly" /></label>
      <label>Display Name <input v-model="displayName" @blur="save" /></label>
    </div>

    <!-- Release modal -->
    <div v-if="showRelease" class="modal-overlay" @click.self="closeRelease">
      <div class="modal">
        <div class="modal-header">
          <h3>Release {{ productSn }}</h3>
          <button class="btn-close" @click="closeRelease">✕</button>
        </div>
        <div class="modal-body">
          <label>New WIP version name (after release)
            <input v-model="newVersionName" placeholder="e.g. 1.1.0" @input="validateNewVersion" />
            <span v-if="newVersionError" class="field-error">{{ newVersionError }}</span>
          </label>
        </div>
        <div v-if="releaseError" class="error-banner modal-error">{{ releaseError }}</div>
        <div v-if="releaseSuccess" class="success-banner">
          <div>Released <strong>{{ releaseResult.version_name }}</strong></div>
          <div>Tag: {{ releaseResult.tag }}</div>
          <div>Commit: {{ releaseResult.commit_sha }}</div>
          <div>PDF: {{ releaseResult.pdf_generated ? 'Generated' : 'Skipped (asciidoctor unavailable)' }}</div>
          <div>New WIP: {{ releaseResult.new_wip_version_name }}</div>
        </div>
        <div class="modal-actions">
          <button
            v-if="!releaseSuccess"
            class="btn-confirm"
            :disabled="!newVersionName || !!newVersionError || releaseLoading"
            @click="doRelease"
          >{{ releaseLoading ? 'Releasing…' : 'Confirm Release' }}</button>
          <button class="btn-cancel" @click="closeRelease">{{ releaseSuccess ? 'Close' : 'Cancel' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTreeStore } from '../../stores/tree.js'
import { useVersioningStore } from '../../stores/versioning.js'
import client from '../../api/client.js'

const props = defineProps({ node: Object, productSn: String })
const store = useTreeStore()
const versioningStore = useVersioningStore()
const displayName = ref(props.node.display_name)

const showRelease = ref(false)
const newVersionName = ref('')
const newVersionError = ref('')
const releaseLoading = ref(false)
const releaseError = ref('')
const releaseSuccess = ref(false)
const releaseResult = ref(null)

const VERSION_NAME_RE = /^[A-Za-z0-9._-]+$/

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

function validateNewVersion() {
  const val = newVersionName.value.trim()
  if (!val) { newVersionError.value = ''; return }
  newVersionError.value = VERSION_NAME_RE.test(val) ? '' : 'Only letters, digits, dots, hyphens, underscores allowed'
}

function openRelease() {
  newVersionName.value = ''
  newVersionError.value = ''
  releaseError.value = ''
  releaseSuccess.value = false
  releaseResult.value = null
  showRelease.value = true
}

function closeRelease() {
  showRelease.value = false
  if (releaseSuccess.value) {
    store.fetchTree()
    versioningStore.fetchVersionList(props.productSn)
  }
}

async function doRelease() {
  validateNewVersion()
  if (newVersionError.value) return
  releaseLoading.value = true
  releaseError.value = ''
  try {
    const { data } = await client.post(`/products/${props.productSn}/release`, {
      new_version_name: newVersionName.value.trim(),
    })
    releaseResult.value = data
    releaseSuccess.value = true
  } catch (err) {
    const detail = err.response?.data?.detail
    releaseError.value = typeof detail === 'string' ? detail : JSON.stringify(detail)
  } finally {
    releaseLoading.value = false
  }
}
</script>

<style scoped>
.edit-panel { max-width: 600px; }
.edit-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
h2 { font-size: 18px; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }
.btn-reset { padding: 6px 12px; background: #fee2e2; color: #dc2626; border: none; border-radius: 6px; cursor: pointer; }
.btn-release { padding: 6px 12px; background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; border-radius: 6px; cursor: pointer; font-weight: 500; }
.error-banner { padding: 12px; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; color: #dc2626; }
.success-banner { margin: 0 20px 12px; padding: 12px; background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; color: #16a34a; font-size: 13px; display: flex; flex-direction: column; gap: 4px; }
.field-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.readonly { background: #f9fafb; color: #6b7280; }
.field-error { font-size: 12px; color: #dc2626; margin-top: 2px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { background: white; border-radius: 12px; width: 440px; display: flex; flex-direction: column; overflow: hidden; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #e2e8f0; }
h3 { font-size: 15px; font-weight: 600; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 16px; color: #64748b; }
.modal-body { padding: 16px 20px; }
.modal-error { margin: 0 20px 12px; }
.modal-actions { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid #e2e8f0; }
.btn-confirm { padding: 7px 18px; background: #059669; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 13px; }
.btn-confirm:disabled { background: #6ee7b7; cursor: not-allowed; }
.btn-cancel { padding: 7px 14px; background: white; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 13px; }
</style>
