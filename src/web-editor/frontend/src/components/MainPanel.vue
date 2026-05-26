<template>
  <div class="main-panel-inner">
    <OverviewPanel v-if="!node" />
    <ProductEdit v-else-if="node.type === 'product'" :node="node.data" :productSn="node.product" />
    <SizeEdit v-else-if="node.type === 'size'" :node="node.data" :productSn="node.product" :sizeSn="node.size" />
    <FlavourEdit v-else-if="node.type === 'flavour'" :node="node.data" :productSn="node.product" :sizeSn="node.size" :flavourSn="node.flavour" />
    <ServerEdit v-else-if="node.type === 'server'" :node="node.data" :productSn="node.product" :sizeSn="node.size" :flavourSn="node.flavour" :serverIdx="node.serverIdx" />
    <AdocEditor v-else-if="node.type === 'adoc'" :path="node.path" />
    <ThemeEditor v-else-if="node.type === 'theme'" />
    <div v-else class="unknown">Unknown node type: {{ node.type }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useTreeStore } from '../stores/tree.js'
import { useUnitsStore } from '../stores/units.js'
import OverviewPanel from './OverviewPanel.vue'
import ProductEdit from './edit/ProductEdit.vue'
import SizeEdit from './edit/SizeEdit.vue'
import FlavourEdit from './edit/FlavourEdit.vue'
import ServerEdit from './edit/ServerEdit.vue'
import AdocEditor from './edit/AdocEditor.vue'
import ThemeEditor from './edit/ThemeEditor.vue'

const store = useTreeStore()
const unitsStore = useUnitsStore()
const node = computed(() => store.selectedNode)

onMounted(() => unitsStore.fetchUnits())
</script>

<style scoped>
.main-panel-inner { height: 100%; }
.unknown { color: #dc2626; }
</style>
