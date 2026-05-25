<template>
  <div class="overview">
    <h2>Infrastructure Overview</h2>
    <p class="subtitle">Select a node in the tree to start editing, or click a product card to navigate.</p>

    <div v-if="loading" class="loading">Loading overview…</div>
    <div v-else class="cards">
      <div
        v-for="p in products"
        :key="p.shortname"
        class="card"
        :class="{ 'card-error': p.has_error }"
        @click="selectProduct(p.shortname)"
      >
        <div class="card-title">{{ p.display_name }}</div>
        <div v-if="p.has_error" class="card-error-msg">⚠ Load error</div>
        <div class="card-stats">
          <span>{{ p.size_count }} size{{ p.size_count !== 1 ? 's' : '' }}</span>
          <span>{{ p.flavour_count }} flavour{{ p.flavour_count !== 1 ? 's' : '' }}</span>
          <span>{{ p.server_count }} server{{ p.server_count !== 1 ? 's' : '' }}</span>
        </div>
      </div>

      <div v-if="!products.length" class="empty">No products defined yet.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTreeStore } from '../stores/tree.js'
import client from '../api/client.js'

const store = useTreeStore()
const products = ref([])
const loading = ref(true)

async function load() {
  const { data } = await client.get('/overview')
  products.value = data.products
  loading.value = false
}

function selectProduct(shortname) {
  if (!store.treeData?.products?.[shortname]) return
  store.selectNode({ type: 'product', data: store.treeData.products[shortname], product: shortname })
}

onMounted(load)
</script>

<style scoped>
.overview { max-width: 800px; }
h2 { font-size: 20px; font-weight: 700; margin-bottom: 6px; }
.subtitle { color: #64748b; font-size: 13px; margin-bottom: 24px; }
.loading { color: #64748b; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.card {
  padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px;
  cursor: pointer; transition: box-shadow 0.15s;
}
.card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.card-error { border-color: #fca5a5; background: #fff1f2; }
.card-title { font-weight: 600; font-size: 14px; margin-bottom: 8px; }
.card-error-msg { color: #dc2626; font-size: 12px; margin-bottom: 6px; }
.card-stats { display: flex; flex-direction: column; gap: 2px; color: #64748b; font-size: 12px; }
.empty { color: #64748b; font-size: 14px; }
</style>
