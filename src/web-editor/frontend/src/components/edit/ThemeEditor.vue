<template>
  <div class="theme-editor">
    <div class="theme-header">
      <h2>theme.yml</h2>
    </div>
    <textarea v-model="content" @blur="save" class="theme-textarea" spellcheck="false" />
    <div v-if="saveErr" class="err">{{ saveErr }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import client from '../../api/client.js'

const content = ref('')
const saveErr = ref('')

async function load() {
  const { data } = await client.get('/theme')
  content.value = data.content
}

async function save() {
  saveErr.value = ''
  try {
    await client.put('/theme', { content: content.value })
  } catch (e) {
    saveErr.value = e.response?.data?.detail || 'Save failed'
  }
}

onMounted(load)
</script>

<style scoped>
.theme-editor { display: flex; flex-direction: column; height: 100%; }
.theme-header { display: flex; align-items: center; margin-bottom: 12px; }
h2 { font-size: 14px; font-weight: 600; color: #374151; }
.theme-textarea {
  flex: 1; width: 100%; min-height: 400px;
  font-family: 'Courier New', monospace; font-size: 13px;
  padding: 12px; border: 1px solid #d1d5db; border-radius: 6px;
  resize: vertical; line-height: 1.5;
}
.err { color: #dc2626; font-size: 12px; margin-top: 6px; }
</style>
