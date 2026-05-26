import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTreeStore } from '../stores/tree.js'

describe('tree store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initialises with no selection', () => {
    const store = useTreeStore()
    expect(store.selectedNode).toBeNull()
  })

  it('selectNode sets the selected node', () => {
    const store = useTreeStore()
    const node = { type: 'product', shortname: 'test' }
    store.selectNode(node)
    expect(store.selectedNode).toEqual(node)
  })
})
