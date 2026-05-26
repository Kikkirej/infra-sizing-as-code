<template>
  <span class="tv-input">
    <select v-model="local.type" @change="emit('update:modelValue', local)">
      <option value="static">static</option>
      <option value="dynamic">dynamic</option>
    </select>
    <input v-if="local.type === 'static'" type="number" v-model.number="local.value" @input="emit('update:modelValue', local)" />
    <input v-else type="text" v-model="local.formula" @input="emit('update:modelValue', local)" placeholder="formula" />
    <select v-model="local.unit" @change="emit('update:modelValue', local)" :class="{ invalid: local.invalid }">
      <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
    </select>
    <span v-if="local.invalid" class="invalid-badge" title="Unit no longer in registry">⚠ invalid unit</span>
  </span>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { useUnitsStore } from '../../stores/units.js'
import { storeToRefs } from 'pinia'

const props = defineProps({ modelValue: Object })
const emit = defineEmits(['update:modelValue'])

const unitsStore = useUnitsStore()
const { units } = storeToRefs(unitsStore)

const local = reactive({ type: 'static', unit: '', value: 0, formula: '', invalid: false, ...props.modelValue })
watch(() => props.modelValue, (v) => Object.assign(local, v), { deep: true })
</script>

<style scoped>
.tv-input { display: inline-flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.tv-input input[type="number"] { width: 80px; }
.tv-input input[type="text"] { width: 120px; }
.invalid { border-color: #ef4444; }
.invalid-badge { color: #ef4444; font-size: 11px; }
</style>
