<template>
  <div class="edit-panel">
    <h2>Server: {{ form.system || '(unnamed)' }}</h2>
    <div class="field-group">
      <label>System Name <input v-model="form.system" @blur="save" /></label>
      <label>Count <input type="number" v-model.number="form.count" min="1" @blur="save" /></label>
      <label>CPU <TypedValueInput v-model="form.cpu" @update:modelValue="save" /></label>
      <label>CPU Clocking <input v-model="form.cpu_clocking" @blur="save" /></label>
      <label>Memory <TypedValueInput v-model="form.memory" @update:modelValue="save" /></label>

      <div class="section-header">Disk Partitions</div>
      <div v-for="(part, i) in form.disk" :key="i" class="partition-row">
        <TypedValueInput v-model="part.size" @update:modelValue="save" />
        <input v-model="part.performance" placeholder="Performance" @blur="save" />
        <input v-model="part.comment" placeholder="Comment" @blur="save" />
        <button @click="removeDisk(i)">✕</button>
      </div>
      <button class="btn-add-disk" @click="addDisk">+ Add partition</button>

      <label>Network (one per line)
        <textarea v-model="networkText" @blur="save" rows="2" />
      </label>
      <label>Software (one per line)
        <textarea v-model="softwareText" @blur="save" rows="2" />
      </label>
      <label>Comment <textarea v-model="form.comment" @blur="save" rows="2" /></label>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { useTreeStore } from '../../stores/tree.js'
import { useUnitsStore } from '../../stores/units.js'
import TypedValueInput from './TypedValueInput.vue'
import client from '../../api/client.js'

const props = defineProps({ node: Object, productSn: String, sizeSn: String, flavourSn: String, serverIdx: Number })
const store = useTreeStore()
const unitsStore = useUnitsStore()

function clone(v) { return JSON.parse(JSON.stringify(v)) }

const form = reactive(clone(props.node))
const networkText = ref((props.node.network || []).join('\n'))
const softwareText = ref((props.node.software || []).join('\n'))

watch(() => props.node, (n) => {
  Object.assign(form, clone(n))
  networkText.value = (n.network || []).join('\n')
  softwareText.value = (n.software || []).join('\n')
})

async function save() {
  form.network = networkText.value.split('\n').map(s => s.trim()).filter(Boolean)
  form.software = softwareText.value.split('\n').map(s => s.trim()).filter(Boolean)
  await client.put(
    `/products/${props.productSn}/sizes/${props.sizeSn}/flavours/${props.flavourSn}/servers/${props.serverIdx}`,
    form
  )
  await store.fetchTree()
}

function addDisk() {
  form.disk.push({ size: { type: 'static', value: 50, unit: unitsStore.units[0] || 'GB' }, performance: 'SSD', comment: '' })
}

function removeDisk(i) {
  form.disk.splice(i, 1)
  save()
}
</script>

<style scoped>
.edit-panel { max-width: 700px; }
h2 { font-size: 18px; font-weight: 600; margin-bottom: 20px; }
.field-group { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 500; color: #374151; }
input, textarea, select { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.section-header { font-weight: 600; font-size: 13px; color: #374151; border-top: 1px solid #e2e8f0; padding-top: 12px; }
.partition-row { display: flex; gap: 8px; align-items: center; }
.partition-row input { flex: 1; }
.partition-row button { padding: 4px 8px; background: #fee2e2; color: #dc2626; border: none; border-radius: 4px; cursor: pointer; }
.btn-add-disk { padding: 6px 12px; background: #dcfce7; color: #16a34a; border: none; border-radius: 6px; cursor: pointer; }
</style>
