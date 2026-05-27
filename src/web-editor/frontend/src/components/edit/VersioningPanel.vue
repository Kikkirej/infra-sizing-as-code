<template>
  <div class="edit-panel">
    <div class="edit-header">
      <h2>Version History: {{ productSn }}</h2>
    </div>

    <!-- Version selector -->
    <div class="version-selector-row">
      <label class="selector-label">Version
        <select v-model="selectedVer" @change="onVersionChange" class="version-select">
          <option v-if="store.versionList.wip" value="wip">WIP</option>
          <option v-for="v in store.versionList.versions" :key="v" :value="v">{{ v }}</option>
        </select>
      </label>
      <span v-if="isReadonly" class="readonly-badge">Read-only</span>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="state-msg">Loading…</div>

    <!-- Malformed WIP error -->
    <div v-else-if="isMalformed" class="error-banner">
      <p>{{ store.error }}</p>
      <button class="btn-reset-wip" @click="resetWip">Reset to empty WIP</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!store.versionData" class="state-msg">No version data available.</div>

    <template v-else>
      <!-- version_name field -->
      <div class="field-group">
        <label>Version Name
          <input
            :value="versionNameInput"
            :readonly="isReadonly"
            :class="{ readonly: isReadonly, 'input-error': versionNameError }"
            @input="versionNameInput = $event.target.value"
            @blur="saveVersionName"
            placeholder="e.g. 1.0.0"
          />
          <span v-if="versionNameError" class="field-error">{{ versionNameError }}</span>
        </label>
      </div>

      <!-- Entries table -->
      <div class="entries-section">
        <div class="entries-header">
          <span class="section-title">Entries ({{ store.versionData.entries.length }})</span>
          <button v-if="!isReadonly" class="btn-add-entry" @click="openAddForm">+ Add Entry</button>
        </div>

        <div v-if="store.versionData.entries.length === 0" class="state-msg small">No entries yet.</div>

        <table v-else class="entries-table">
          <thead>
            <tr>
              <th>Author</th>
              <th>Date</th>
              <th>Notes</th>
              <th v-if="!isReadonly"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, idx) in store.versionData.entries" :key="idx">
              <td>{{ entry.author }}</td>
              <td>{{ entry.date }}</td>
              <td>{{ entry.notes || '' }}</td>
              <td v-if="!isReadonly" class="row-actions">
                <button class="btn-edit" @click="openEditForm(idx, entry)">Edit</button>
                <button class="btn-delete" @click="deleteEntry(idx)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Entry form (add/edit) -->
      <div v-if="showForm" class="entry-form">
        <div class="form-title">{{ editingIdx === null ? 'Add Entry' : 'Edit Entry' }}</div>
        <label>Author
          <input v-model="formAuthor" @blur="validateAuthorField" placeholder="Surname, Firstname" />
          <span v-if="formAuthorError" class="field-error">{{ formAuthorError }}</span>
        </label>
        <label>Date
          <input v-model="formDate" type="date" />
        </label>
        <label>Notes
          <textarea v-model="formNotes" rows="2" placeholder="Optional notes…" />
        </label>
        <div class="form-actions">
          <button class="btn-save" :disabled="!!formAuthorError || !formAuthor || !formDate" @click="saveEntry">Save</button>
          <button class="btn-cancel" @click="closeForm">Cancel</button>
          <span v-if="formError" class="field-error">{{ formError }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useVersioningStore } from '../../stores/versioning.js'
import client from '../../api/client.js'

const props = defineProps({ productSn: String })
const store = useVersioningStore()

const selectedVer = ref('wip')
const versionNameInput = ref('')
const versionNameError = ref('')

const showForm = ref(false)
const editingIdx = ref(null)
const formAuthor = ref('')
const formDate = ref('')
const formNotes = ref('')
const formAuthorError = ref('')
const formError = ref('')

const AUTHOR_TOKEN = /^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$/
const VERSION_NAME_RE = /^[A-Za-z0-9._-]+$/

const isReadonly = computed(() => store.versionData?.readonly === true)
const isMalformed = computed(() => !store.loading && store.error && !store.versionData)

watch(() => store.versionData, (d) => {
  if (d) versionNameInput.value = d.version_name ?? ''
})

async function onVersionChange() {
  await store.selectVersion(props.productSn, selectedVer.value)
  closeForm()
}

async function resetWip() {
  await store.reset(props.productSn)
  selectedVer.value = 'wip'
}

function validateAuthorField() {
  const tokens = formAuthor.value.split(/;\s*/).filter(t => t.trim())
  const invalid = tokens.filter(t => !AUTHOR_TOKEN.test(t.trim()))
  formAuthorError.value = invalid.length
    ? `Invalid token(s): ${invalid.map(t => `"${t.trim()}"`).join(', ')} — expected "Surname, Firstname"`
    : ''
}

async function saveVersionName() {
  const val = versionNameInput.value.trim()
  if (!val) { versionNameError.value = ''; return }
  if (!VERSION_NAME_RE.test(val)) {
    versionNameError.value = 'Only letters, digits, dots, hyphens, underscores allowed'
    return
  }
  versionNameError.value = ''
  try {
    await client.patch(`/products/${props.productSn}/versioning/wip`, { version_name: val })
    await store.selectVersion(props.productSn, 'wip')
  } catch (err) {
    versionNameError.value = err.response?.data?.detail || 'Save failed'
  }
}

function openAddForm() {
  editingIdx.value = null
  formAuthor.value = ''
  formDate.value = new Date().toISOString().slice(0, 10)
  formNotes.value = ''
  formAuthorError.value = ''
  formError.value = ''
  showForm.value = true
}

function openEditForm(idx, entry) {
  editingIdx.value = idx
  formAuthor.value = entry.author
  formDate.value = entry.date
  formNotes.value = entry.notes || ''
  formAuthorError.value = ''
  formError.value = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingIdx.value = null
}

async function saveEntry() {
  validateAuthorField()
  if (formAuthorError.value) return
  formError.value = ''
  const payload = { author: formAuthor.value, date: formDate.value, notes: formNotes.value || null }
  try {
    if (editingIdx.value === null) {
      await client.post(`/products/${props.productSn}/versioning/wip/entries`, payload)
    } else {
      await client.put(`/products/${props.productSn}/versioning/wip/entries/${editingIdx.value}`, payload)
    }
    await store.selectVersion(props.productSn, 'wip')
    closeForm()
  } catch (err) {
    formError.value = err.response?.data?.detail
      ? (typeof err.response.data.detail === 'string' ? err.response.data.detail : JSON.stringify(err.response.data.detail))
      : 'Save failed'
  }
}

async function deleteEntry(idx) {
  if (!confirm('Delete this entry?')) return
  try {
    await client.delete(`/products/${props.productSn}/versioning/wip/entries/${idx}`)
    await store.selectVersion(props.productSn, 'wip')
  } catch (err) {
    alert(err.response?.data?.detail || 'Delete failed')
  }
}

onMounted(async () => {
  await store.fetchVersionList(props.productSn)
  if (store.versionList.wip) {
    selectedVer.value = 'wip'
    await store.selectVersion(props.productSn, 'wip')
  } else if (store.versionList.versions.length) {
    selectedVer.value = store.versionList.versions[0]
    await store.selectVersion(props.productSn, selectedVer.value)
  }
})
</script>

<style scoped>
.edit-panel { max-width: 700px; padding-bottom: 24px; }
.edit-header { margin-bottom: 16px; }
h2 { font-size: 18px; font-weight: 600; }

.version-selector-row { display: flex; align-items: flex-end; gap: 12px; margin-bottom: 16px; }
.selector-label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; }
.version-select { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; min-width: 140px; }
.readonly-badge { padding: 3px 8px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 11px; color: #64748b; }

.field-group { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input, textarea { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
input.readonly { background: #f9fafb; color: #6b7280; }
input.input-error, textarea.input-error { border-color: #fca5a5; }
.field-error { font-size: 12px; color: #dc2626; margin-top: 2px; }

.entries-section { margin-top: 4px; }
.entries-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.section-title { font-size: 13px; font-weight: 600; color: #374151; }
.btn-add-entry { padding: 4px 10px; background: #dcfce7; color: #16a34a; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }

.entries-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.entries-table th { text-align: left; padding: 6px 8px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #374151; }
.entries-table td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
.row-actions { white-space: nowrap; width: 80px; }
.btn-edit { padding: 2px 8px; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer; font-size: 11px; background: white; margin-right: 4px; }
.btn-delete { padding: 2px 6px; background: #fee2e2; color: #dc2626; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; }

.entry-form { margin-top: 16px; padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; gap: 12px; }
.form-title { font-size: 14px; font-weight: 600; color: #374151; }
.form-actions { display: flex; align-items: center; gap: 8px; }
.btn-save { padding: 6px 16px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-save:disabled { background: #93c5fd; cursor: not-allowed; }
.btn-cancel { padding: 6px 12px; background: white; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 13px; }

.state-msg { color: #94a3b8; font-size: 13px; padding: 12px 0; }
.state-msg.small { padding: 8px 0; }
.error-banner { padding: 12px; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; color: #dc2626; font-size: 13px; }
.error-banner p { margin: 0 0 8px; }
.btn-reset-wip { padding: 5px 12px; background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; border-radius: 4px; cursor: pointer; font-size: 12px; }
</style>
