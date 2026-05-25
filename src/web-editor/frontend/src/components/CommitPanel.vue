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

      <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
      <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

      <div class="actions">
        <button
          class="btn-commit"
          :disabled="!changes.length || !message.trim() || detachedHead || loading"
          @click="commit"
        >
          {{ loading ? 'Committing…' : 'Commit & Push' }}
        </button>
        <button v-if="pushFailed" class="btn-retry" @click="retryPush" :disabled="loading">
          Retry Push
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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

async function load() {
  const [statusRes, changesRes] = await Promise.all([
    client.get('/git/status'),
    client.get('/git/changes'),
  ])
  detachedHead.value = statusRes.data.is_detached
  changes.value = changesRes.data.changes
}

async function commit() {
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const { data } = await client.post('/git/commit', { message: message.value })
    successMsg.value = `Committed ${data.commit_sha}${data.pushed ? ' and pushed.' : ' (push skipped — no remote).'}`
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
.actions { display: flex; gap: 8px; padding: 16px 20px; border-top: 1px solid #e2e8f0; }
.btn-commit { padding: 8px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; }
.btn-commit:disabled { background: #93c5fd; cursor: not-allowed; }
.btn-retry { padding: 8px 16px; background: #fef3c7; color: #d97706; border: 1px solid #fcd34d; border-radius: 6px; cursor: pointer; }
</style>
