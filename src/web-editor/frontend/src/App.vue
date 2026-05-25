<template>
  <div class="editor-layout">
    <header class="top-nav">
      <span class="app-title">Infra Sizing Editor</span>
      <div class="nav-actions">
        <button class="btn-units" @click="unitsOpen = true">Units</button>
        <button class="btn-commit" @click="commitPanelOpen = true">Commit</button>
      </div>
    </header>

    <div class="editor-body">
      <aside class="tree-panel">
        <TreePanel />
      </aside>
      <main class="main-panel">
        <MainPanel />
      </main>
    </div>

    <CommitPanel v-if="commitPanelOpen" @close="commitPanelOpen = false" />
    <UnitsRegistryPanel v-if="unitsOpen" @close="unitsOpen = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import TreePanel from './components/TreePanel.vue'
import MainPanel from './components/MainPanel.vue'
import CommitPanel from './components/CommitPanel.vue'
import UnitsRegistryPanel from './components/UnitsRegistryPanel.vue'

const commitPanelOpen = ref(false)
const unitsOpen = ref(false)
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; font-size: 14px; color: #1a1a1a; }

.editor-layout { display: flex; flex-direction: column; height: 100vh; }

.top-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; height: 48px;
  background: #1e293b; color: #f1f5f9;
  flex-shrink: 0;
}
.app-title { font-weight: 600; font-size: 15px; }
.btn-units {
  padding: 6px 14px; border-radius: 6px; border: 1px solid #475569; cursor: pointer;
  background: transparent; color: #cbd5e1; font-weight: 500; margin-right: 8px;
}
.btn-units:hover { background: #334155; }
.btn-commit {
  padding: 6px 16px; border-radius: 6px; border: none; cursor: pointer;
  background: #3b82f6; color: white; font-weight: 500;
}
.btn-commit:hover { background: #2563eb; }

.editor-body { display: flex; flex: 1; overflow: hidden; }
.tree-panel { width: 280px; border-right: 1px solid #e2e8f0; overflow-y: auto; flex-shrink: 0; }
.main-panel { flex: 1; overflow-y: auto; padding: 24px; }
</style>
