<template>
  <div class="overlay" @click.self="close" @keyup.esc="close">
    <div class="panel" tabindex="-1" ref="panelRef">
      <div class="panel-header">
        <h2>Commit Changes</h2>
        <button class="btn-close" @click="close">✕</button>
      </div>

      <div v-if="detachedHead" class="error-banner">
        Repository is in detached HEAD state. Run <code>git checkout &lt;branch&gt;</code> before committing.
      </div>

      <div class="changes-section">
        <div class="section-title">Pending changes ({{ changes.length }})</div>
        <div v-if="!changes.length" class="no-changes">Nothing to commit.</div>
        <ul v-else class="changes-list">
          <li v-for="c in changes" :key="c">{{ c }}</li>
        </ul>
      </div>

      <div class="message-section">
        <label>Commit message
          <textarea v-model="message" rows="3" placeholder="Describe your changes…" />
        </label>
      </div>

      <!-- Version notes per changed product -->
      <div v-if="changedProducts.length" class="version-notes-section">
        <div class="section-title">Version notes (optional)</div>
        <div v-for="sn in changedProducts" :key="sn" class="version-note-product">
          <button class="note-toggle" @click="toggleNote(sn)">
            {{ expandedNotes[sn] ? '▾' : '▸' }} Add version note for <strong>{{ sn }}</strong>
          </button>
          <div v-if="expandedNotes[sn]" class="note-fields">
            <label>Author
              <input v-model="noteFields[sn].author" placeholder="Surname, Firstname" @blur="validateNote(sn)" />
              <span v-if="noteErrors[sn]" class="field-error">{{ noteErrors[sn] }}</span>
            </label>
            <label>Date
              <input v-model="noteFields[sn].date" type="date" />
            </label>
            <label>Notes
              <textarea v-model="noteFields[sn].notes" rows="2" placeholder="Optional notes…" />
            </label>
          </div>
        </div>
      </div>

      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
      <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

      <div class="actions">
        <button
          class="btn-commit"
          :disabled="!changes.length || !message.trim() || detachedHead || loading || hasNoteErrors"
          @click="commit(true)"
        >
          {{ loading ? 'Committing…' : 'Commit & Push' }}
        </button>
        <button
          class="btn-commit-only"
          :disabled="!changes.length || !message.trim() || detachedHead || loading || hasNoteErrors"
          @click="commit(false)"
        >
          {{ loading ? 'Committing…' : 'Commit Only' }}
        </button>
        <button v-if="pushFailed" class="btn-retry" @click="retryPush" :disabled="loading">
          Retry Push
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTreeStore } from '../stores/tree.js'
import client from '../api/client.js'

const emit = defineEmits(['close'])
const store = useTreeStore()

const changes = ref([])
const message = ref('')
const loading = ref(false)
const detachedHead = ref(false)
const pushFailed = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const panelRef = ref(null)

const expandedNotes = ref({})
const noteFields = ref({})
const noteErrors = ref({})

const AUTHOR_TOKEN = /^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$/

const changedProducts = computed(() => {
  const sns = new Set()
  for (const c of changes.value) {
    if (c.includes(' / ')) {
      sns.add(c.split(' / ')[0].trim())
    } else if (c.startsWith('infra/')) {
      const parts = c.replace('infra/', '').split('/')
      if (parts[0]) sns.add(parts[0])
    } else {
      // plain shortname entry (no path, no slash)
      if (!c.includes('/') && !c.includes('.')) sns.add(c)
    }
  }
  return [...sns]
})

const hasNoteErrors = computed(() => Object.values(noteErrors.value).some(e => !!e))

function toggleNote(sn) {
  expandedNotes.value[sn] = !expandedNotes.value[sn]
  if (expandedNotes.value[sn] && !noteFields.value[sn]) {
    noteFields.value[sn] = { author: '', date: new Date().toISOString().slice(0, 10), notes: '' }
    noteErrors.value[sn] = ''
  }
}

function validateNote(sn) {
  const author = noteFields.value[sn]?.author || ''
  if (!author) { noteErrors.value[sn] = ''; return }
  const tokens = author.split(/;\s*/).filter(t => t.trim())
  const invalid = tokens.filter(t => !AUTHOR_TOKEN.test(t.trim()))
  noteErrors.value[sn] = invalid.length
    ? `Invalid: ${invalid.map(t => `"${t.trim()}"`).join(', ')}`
    : ''
}

function buildVersionNotes() {
  const notes = []
  for (const sn of changedProducts.value) {
    if (!expandedNotes.value[sn]) continue
    const f = noteFields.value[sn]
    if (!f || !f.author || !f.date) continue
    notes.push({ product_shortname: sn, author: f.author, date: f.date, notes: f.notes || null })
  }
  return notes
}

async function load() {
  const [statusRes, changesRes] = await Promise.all([
    client.get('/git/status'),
    client.get('/git/changes'),
  ])
  detachedHead.value = statusRes.data.is_detached
  changes.value = changesRes.data.changes
}

async function commit(push = true) {
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const version_notes = buildVersionNotes()
    const { data } = await client.post('/git/commit', { message: message.value, push, version_notes })
    successMsg.value = `Committed ${data.commit_sha}${data.pushed ? ' and pushed.' : push ? ' (push skipped — no remote).' : ' (not pushed).'}`
    pushFailed.value = false
    await store.fetchTree()
    await load()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'object' && detail?.push_failed) {
      pushFailed.value = true
      errorMsg.value = detail.message
      await store.fetchTree()
      await load()
    } else {
      errorMsg.value = typeof detail === 'string' ? detail : JSON.stringify(detail)
    }
  } finally {
    loading.value = false
  }
}

async function retryPush() {
  loading.value = true
  errorMsg.value = ''
  try {
    await client.post('/git/push')
    successMsg.value = 'Push succeeded.'
    pushFailed.value = false
  } catch (err) {
    errorMsg.value = err.response?.data?.detail?.message || 'Push failed'
  } finally {
    loading.value = false
  }
}

function close() {
  emit('close')
}

onMounted(async () => {
  await load()
  panelRef.value?.focus()
})
</script>

<style scoped>
.overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.panel {
  background: white; border-radius: 12px; width: 560px; max-height: 80vh;
  display: flex; flex-direction: column; overflow: hidden; outline: none;
}
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #e2e8f0; }
h2 { font-size: 16px; font-weight: 600; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 16px; color: #64748b; }
.changes-section { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; flex: 1; overflow-y: auto; }
.section-title { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; }
.no-changes { color: #94a3b8; font-size: 13px; }
.changes-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.changes-list li { font-size: 13px; font-family: monospace; color: #374151; }
.message-section { padding: 16px 20px; }
label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; font-weight: 500; }
textarea { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; resize: vertical; }
.error-banner { margin: 0 20px; padding: 10px 14px; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; color: #dc2626; font-size: 13px; }
.success-banner { margin: 0 20px; padding: 10px 14px; background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; color: #16a34a; font-size: 13px; }
.version-notes-section { padding: 12px 20px; border-bottom: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 8px; }
.version-note-product { display: flex; flex-direction: column; gap: 6px; }
.note-toggle { background: none; border: none; cursor: pointer; font-size: 13px; color: #374151; text-align: left; padding: 2px 0; }
.note-toggle:hover { color: #3b82f6; }
.note-fields { display: flex; flex-direction: column; gap: 8px; padding: 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
.note-fields input, .note-fields textarea { padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.note-fields textarea { resize: vertical; }
.field-error { font-size: 12px; color: #dc2626; }
.actions { display: flex; gap: 8px; padding: 16px 20px; border-top: 1px solid #e2e8f0; }
.btn-commit { padding: 8px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; }
.btn-commit:disabled { background: #93c5fd; cursor: not-allowed; }
.btn-commit-only { padding: 8px 20px; background: white; color: #3b82f6; border: 1px solid #3b82f6; border-radius: 6px; cursor: pointer; font-weight: 500; }
.btn-commit-only:disabled { color: #93c5fd; border-color: #93c5fd; cursor: not-allowed; }
.btn-retry { padding: 8px 16px; background: #fef3c7; color: #d97706; border: 1px solid #fcd34d; border-radius: 6px; cursor: pointer; }
</style>
