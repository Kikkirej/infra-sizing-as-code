<template>
  <div class="tree-panel-inner" @keyup.esc="store.clearSelection()">
    <div v-if="!store.treeData" class="tree-loading">Loading…</div>

    <div v-else-if="!hasProducts" class="tree-empty">
      <p>No products defined yet.</p>
      <button class="btn-add-first" @click="addProduct">+ Add first product</button>
    </div>

    <div v-else class="tree-root">
      <!-- Global files -->
      <div class="tree-section-label">Global</div>
      <div class="tree-node adoc-node global-node"
        :class="[adocClass(store.treeData.globals?.prefix_change), { 'is-selected': store.selectedNode?.path === 'infra/prefix.adoc' }]"
        @click="selectAdoc('infra/prefix.adoc', 'prefix')">
        <span class="node-label">prefix.adoc</span>
      </div>
      <div class="tree-node adoc-node global-node"
        :class="[adocClass(store.treeData.globals?.suffix_change), { 'is-selected': store.selectedNode?.path === 'infra/suffix.adoc' }]"
        @click="selectAdoc('infra/suffix.adoc', 'suffix')">
        <span class="node-label">suffix.adoc</span>
      </div>
      <div class="tree-node theme-node global-node"
        :class="[adocClass(store.treeData.globals?.theme_change), { 'is-selected': store.selectedNode?.type === 'theme' }]"
        @click="store.selectNode({ type: 'theme' })">
        <span class="node-label">theme.yml</span>
      </div>

      <div class="tree-section-label">Products <button class="btn-add-product" @click="addProduct">+</button></div>
      <div
        v-for="(product, sn) in store.treeData.products"
        :key="sn"
        class="tree-node-group"
      >
        <div
          class="tree-node product-node"
          :class="nodeClass(product)"
          @click="select('product', product, sn)"
        >
          <span class="node-toggle" @click.stop="toggleExpand(sn)">{{ expanded[sn] ? '▾' : '▸' }}</span>
          <span class="node-label" :class="{ deleted: product.change === 'DELETED' }">{{ product.display_name }}</span>
          <span v-if="product.change === 'ERROR'" class="badge error" :title="product.error">⚠</span>
          <span v-else-if="isDirty(product)" class="badge modified">●</span>
          <button class="btn-inline-add" title="Add size" @click.stop="addSize(sn)">+</button>
        </div>

        <template v-if="expanded[sn]">
          <!-- Adoc nodes -->
          <div class="tree-node adoc-node" :class="adocClass(product.prefix_change)" @click="selectAdoc(`infra/${sn}/prefix.adoc`, 'prefix')">
            <span class="node-label">prefix.adoc</span>
          </div>
          <div class="tree-node adoc-node" :class="adocClass(product.suffix_change)" @click="selectAdoc(`infra/${sn}/suffix.adoc`, 'suffix')">
            <span class="node-label">suffix.adoc</span>
          </div>
          <!-- Versions node -->
          <div class="tree-node versions-node"
            :class="{ 'is-selected': store.selectedNode?.type === 'versions' && store.selectedNode?.product === sn }"
            @click="store.selectNode({ type: 'versions', product: sn })">
            <span class="node-label">Versions</span>
          </div>

          <!-- Sizes -->
          <div v-for="(size, ssn) in product.sizes" :key="ssn" class="tree-node-group indent-1">
            <div class="tree-node size-node" :class="nodeClass(size)" @click="select('size', size, sn, ssn)">
              <span class="node-toggle" @click.stop="toggleExpand(sn+'/'+ssn)">{{ expanded[sn+'/'+ssn] ? '▾' : '▸' }}</span>
              <span class="node-label" :class="{ deleted: size.change === 'DELETED' }">{{ size.display_name }}</span>
              <span v-if="isDirty(size)" class="badge modified">●</span>
              <button class="btn-inline-add" title="Add flavour" @click.stop="addFlavour(sn, ssn)">+</button>
              <button class="btn-inline-del" title="Delete size" @click.stop="deleteNode('size', sn, ssn)">✕</button>
            </div>

            <template v-if="expanded[sn+'/'+ssn]">
              <div class="tree-node adoc-node indent-2" :class="adocClass(size.prefix_change)"
                @click="selectAdoc(`infra/${sn}/${ssn}/prefix.adoc`, 'prefix')">
                <span class="node-label">prefix.adoc</span>
              </div>
              <div class="tree-node adoc-node indent-2" :class="adocClass(size.suffix_change)"
                @click="selectAdoc(`infra/${sn}/${ssn}/suffix.adoc`, 'suffix')">
                <span class="node-label">suffix.adoc</span>
              </div>

              <div v-for="(flavour, fsn) in size.flavours" :key="fsn" class="tree-node-group indent-2">
                <div class="tree-node flavour-node" :class="nodeClass(flavour)" @click="select('flavour', flavour, sn, ssn, fsn)">
                  <span class="node-toggle" @click.stop="toggleExpand(sn+'/'+ssn+'/'+fsn)">{{ expanded[sn+'/'+ssn+'/'+fsn] ? '▾' : '▸' }}</span>
                  <span class="node-label" :class="{ deleted: flavour.change === 'DELETED' }">{{ flavour.display_name }}</span>
                  <span v-if="isDirty(flavour)" class="badge modified">●</span>
                  <button class="btn-inline-add" title="Add server" @click.stop="addServer(sn, ssn, fsn)">+</button>
                  <button class="btn-inline-del" title="Delete flavour" @click.stop="deleteNode('flavour', sn, ssn, fsn)">✕</button>
                </div>

                <template v-if="expanded[sn+'/'+ssn+'/'+fsn]">
                  <!-- Adoc nodes for flavour -->
                  <div class="tree-node adoc-node indent-3" :class="adocClass(flavour.prefix_change)"
                    @click="selectAdoc(`infra/${sn}/${ssn}/${fsn}/prefix.adoc`, 'prefix')">
                    <span class="node-label">prefix.adoc</span>
                  </div>
                  <div class="tree-node adoc-node indent-3" :class="adocClass(flavour.suffix_change)"
                    @click="selectAdoc(`infra/${sn}/${ssn}/${fsn}/suffix.adoc`, 'suffix')">
                    <span class="node-label">suffix.adoc</span>
                  </div>

                  <!-- Servers -->
                  <div
                    v-for="(server, idx) in flavour.servers"
                    :key="idx"
                    class="tree-node server-node indent-3"
                    :class="nodeClass(server)"
                    @click="select('server', server, sn, ssn, fsn, idx)"
                  >
                    <span class="node-label" :class="{ deleted: server.change === 'DELETED' }">{{ server.system || '(unnamed)' }}</span>
                    <span v-if="isDirty(server)" class="badge modified">●</span>
                    <button class="btn-inline-del" title="Delete server" @click.stop="deleteNode('server', sn, ssn, fsn, idx)">✕</button>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTreeStore } from '../stores/tree.js'
import client from '../api/client.js'

const store = useTreeStore()
const expanded = ref({})

const hasProducts = computed(() => store.treeData && Object.keys(store.treeData.products || {}).length > 0)

function toggleExpand(key) {
  expanded.value[key] = !expanded.value[key]
}

function nodeClass(node) {
  return {
    'is-modified': node.change === 'MODIFIED',
    'is-added': node.change === 'ADDED',
    'is-deleted': node.change === 'DELETED',
    'is-error': node.change === 'ERROR',
    'is-selected': store.selectedNode?.data === node,
  }
}

function adocClass(change) {
  return { 'is-modified': change === 'MODIFIED', 'is-added': change === 'ADDED' }
}

function isDirty(node) {
  return ['MODIFIED', 'ADDED'].includes(node.change)
}

function select(type, data, product, size, flavour, serverIdx) {
  store.selectNode({ type, data, product, size, flavour, serverIdx })
}

function selectAdoc(path, fileType) {
  store.selectNode({ type: 'adoc', path, fileType })
}

async function addProduct() {
  const shortname = prompt('Product shortname:')
  const displayName = prompt('Display name:')
  if (!shortname || !displayName) return
  await client.post('/products', { shortname, display_name: displayName })
  await store.fetchTree()
}

async function addSize(productSn) {
  const shortname = prompt('Size shortname:')
  const displayName = prompt('Display name:')
  if (!shortname || !displayName) return
  try {
    await client.post(`/products/${productSn}/sizes`, { shortname, display_name: displayName })
    await store.fetchTree()
    expanded.value[productSn] = true
  } catch (e) {
    alert(e.response?.data?.detail || 'Error adding size')
  }
}

async function addFlavour(productSn, sizeSn) {
  const shortname = prompt('Flavour shortname:')
  const displayName = prompt('Display name:')
  if (!shortname || !displayName) return
  try {
    await client.post(`/products/${productSn}/sizes/${sizeSn}/flavours`, { shortname, display_name: displayName })
    await store.fetchTree()
    expanded.value[`${productSn}/${sizeSn}`] = true
  } catch (e) {
    alert(e.response?.data?.detail || 'Error adding flavour')
  }
}

async function addServer(productSn, sizeSn, flavourSn) {
  const system = prompt('Server system name:')
  if (!system) return
  const defaultServer = {
    system, count: 1,
    cpu: { type: 'static', value: 1, unit: 'vCPU' },
    cpu_clocking: '2.0 GHz',
    memory: { type: 'static', value: 8, unit: 'GB' },
    disk: [{ size: { type: 'static', value: 50, unit: 'GB' }, performance: 'SSD', comment: 'OS' }],
    network: [], software: [], comment: '',
  }
  await client.post(`/products/${productSn}/sizes/${sizeSn}/flavours/${flavourSn}/servers`, defaultServer)
  await store.fetchTree()
  expanded.value[`${productSn}/${sizeSn}/${flavourSn}`] = true
}

async function deleteNode(type, product, size, flavour, serverIdx) {
  if (!confirm('Delete this item? It will remain visible until committed.')) return
  try {
    if (type === 'size') await client.delete(`/products/${product}/sizes/${size}`)
    if (type === 'flavour') await client.delete(`/products/${product}/sizes/${size}/flavours/${flavour}`)
    if (type === 'server') await client.delete(`/products/${product}/sizes/${size}/flavours/${flavour}/servers/${serverIdx}`)
    await store.fetchTree()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error deleting')
  }
}

onMounted(() => store.fetchTree())
</script>

<style scoped>
.tree-panel-inner { padding: 8px 0; }
.tree-loading, .tree-empty { padding: 16px; color: #64748b; font-size: 13px; }
.btn-add-first { display: block; margin-top: 12px; padding: 8px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; }

.tree-node {
  display: flex; align-items: center; gap: 4px;
  padding: 4px 8px; cursor: pointer; border-radius: 4px;
  font-size: 13px; position: relative;
}
.tree-node:hover { background: #f1f5f9; }
.tree-node.is-selected { background: #dbeafe; }
.tree-node.is-modified .node-label { color: #2563eb; }
.tree-node.is-added .node-label { color: #16a34a; }
.tree-node.is-deleted { opacity: 0.6; }
.node-label.deleted { text-decoration: line-through; color: #ef4444; }
.tree-node.is-error .node-label { color: #dc2626; }

.indent-1 { padding-left: 16px; }
.indent-2 { padding-left: 32px; }
.indent-3 { padding-left: 48px; }

.node-toggle { font-size: 10px; color: #94a3b8; width: 12px; flex-shrink: 0; }
.badge { font-size: 11px; margin-left: 4px; }
.badge.modified { color: #3b82f6; }
.badge.error { color: #dc2626; cursor: help; }

.btn-inline-add, .btn-inline-del {
  display: none; margin-left: auto; padding: 1px 5px; border: none;
  border-radius: 3px; cursor: pointer; font-size: 11px;
}
.btn-inline-add { background: #dcfce7; color: #16a34a; }
.btn-inline-del { background: #fee2e2; color: #dc2626; }
.tree-node:hover .btn-inline-add,
.tree-node:hover .btn-inline-del { display: inline-flex; }

.adoc-node { color: #6366f1; font-size: 12px; }
.theme-node { color: #0891b2; font-size: 12px; }
.versions-node { color: #059669; font-size: 12px; }
.global-node { padding-left: 12px; }
.tree-section-label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; padding: 8px 8px 2px; display: flex; align-items: center; justify-content: space-between; }
.btn-add-product { background: none; border: none; color: #94a3b8; font-size: 14px; cursor: pointer; line-height: 1; padding: 0 2px; }
.btn-add-product:hover { color: #3b82f6; }
</style>
