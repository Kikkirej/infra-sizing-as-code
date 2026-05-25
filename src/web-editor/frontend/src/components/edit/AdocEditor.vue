<template>
  <div class="adoc-editor">
    <div class="adoc-header">
      <h2>{{ path }}</h2>
      <button @click="previewMode = !previewMode">{{ previewMode ? 'Edit' : 'Preview' }}</button>
    </div>
    <textarea v-if="!previewMode" v-model="content" @blur="save" class="adoc-textarea" />
    <div v-else class="adoc-preview" v-html="rendered" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Asciidoctor from 'asciidoctor'
import client from '../../api/client.js'

const props = defineProps({ path: String })
const content = ref('')
const previewMode = ref(false)
const asciidoctor = Asciidoctor()

const rendered = computed(() => asciidoctor.convert(content.value, { safe: 'safe' }))

async function load() {
  const { data } = await client.get(`/adoc/${props.path}`)
  content.value = data.content
}

async function save() {
  await client.put(`/adoc/${props.path}`, { content: content.value })
}

onMounted(load)
watch(() => props.path, load)
</script>

<style scoped>
.adoc-editor { display: flex; flex-direction: column; height: 100%; }
.adoc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
h2 { font-size: 14px; font-weight: 600; color: #374151; word-break: break-all; }
.adoc-header button { padding: 6px 14px; border: 1px solid #d1d5db; border-radius: 6px; background: white; cursor: pointer; }
.adoc-textarea { flex: 1; width: 100%; min-height: 400px; font-family: 'Courier New', monospace; font-size: 13px; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; resize: vertical; }
.adoc-preview { flex: 1; padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px; overflow-y: auto; }
</style>
