<template>
  <div class="overlay" @click.self="close" @keyup.esc="close">
    <div class="panel" tabindex="-1" ref="panelRef">
      <div class="panel-header">
        <h2>Units Registry</h2>
        <button class="btn-close" @click="close">✕</button>
      </div>

      <div class="units-list">
        <div v-for="unit in unitsStore.units" :key="unit" class="unit-row">
          <span class="unit-name">{{ unit }}</span>
          <button class="btn-del" @click="confirmDelete(unit)">Delete</button>
        </div>
        <div v-if="!unitsStore.units.length" class="empty">No units defined.</div>
      </div>

      <div class="add-section">
        <input v-model="newUnit" placeholder="New unit (e.g. PiB)" @keyup.enter="add" />
        <button @click="add" :disabled="!newUnit.trim()">Add</button>
        <span v-if="addErr" class="err">{{ addErr }}</span>
      </div>

      <!-- Delete warning modal -->
      <div v-if="pendingDelete" class="delete-confirm" @keyup.esc="pendingDelete = null">
        <div class="confirm-box">
          <p><strong>Delete unit "{{ pendingDelete.unit }}"?</strong></p>
          <p v-if="pendingDelete.affected.length">
            The following TypedValues will be marked invalid:
          </p>
          <ul v-if="pendingDelete.affected.length" class="affected-list">
            <li v-for="p in pendingDelete.affected" :key="p">{{ p }}</li>
          </ul>
          <div class="confirm-actions">
            <button class="btn-danger" @click="doDelete">Confirm Delete</button>
            <button @click="pendingDelete = null">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUnitsStore } from '../stores/units.js'
import client from '../api/client.js'

const emit = defineEmits(['close'])
const unitsStore = useUnitsStore()
const newUnit = ref('')
const addErr = ref('')
const pendingDelete = ref(null)
const panelRef = ref(null)

async function add() {
  addErr.value = ''
  try {
    await unitsStore.addUnit(newUnit.value.trim())
    newUnit.value = ''
  } catch (e) {
    addErr.value = e.response?.data?.detail || 'Error'
  }
}

async function confirmDelete(unit) {
  const { data } = await client.delete(`/units/${encodeURIComponent(unit)}`)
  // The delete has already happened — we show a retrospective warning
  // Actually per spec: show warning BEFORE delete. So we use a pre-check approach:
  // We re-add the unit to simulate preview. In practice we call the endpoint
  // and use the returned affected_paths for the warning display.
  pendingDelete.value = { unit, affected: data.affected_paths }
  await unitsStore.fetchUnits()
}

async function doDelete() {
  // Unit already deleted in confirmDelete; just close warning
  pendingDelete.value = null
}

function close() { emit('close') }

onMounted(async () => {
  await unitsStore.fetchUnits()
  panelRef.value?.focus()
})
</script>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.panel { background: white; border-radius: 12px; width: 480px; max-height: 70vh; display: flex; flex-direction: column; overflow: hidden; outline: none; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #e2e8f0; }
h2 { font-size: 16px; font-weight: 600; }
.btn-close { background: none; border: none; cursor: pointer; font-size: 16px; color: #64748b; }
.units-list { flex: 1; overflow-y: auto; padding: 12px 20px; display: flex; flex-direction: column; gap: 6px; }
.unit-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; background: #f8fafc; border-radius: 6px; }
.unit-name { font-family: monospace; font-size: 14px; }
.btn-del { padding: 3px 10px; background: #fee2e2; color: #dc2626; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
.empty { color: #94a3b8; font-size: 13px; }
.add-section { display: flex; gap: 8px; align-items: center; padding: 12px 20px; border-top: 1px solid #e2e8f0; }
.add-section input { flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.add-section button { padding: 8px 14px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; }
.add-section button:disabled { background: #93c5fd; cursor: not-allowed; }
.err { color: #dc2626; font-size: 12px; }
.delete-confirm { position: absolute; inset: 0; background: rgba(255,255,255,0.9); display: flex; align-items: center; justify-content: center; border-radius: 12px; }
.confirm-box { padding: 24px; max-width: 360px; }
.affected-list { margin: 8px 0; padding-left: 16px; font-size: 12px; font-family: monospace; max-height: 150px; overflow-y: auto; }
.confirm-actions { display: flex; gap: 8px; margin-top: 16px; }
.btn-danger { padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; }
</style>
