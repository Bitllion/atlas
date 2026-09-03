import type { InventoryLocation } from '../types'

const key = 'atlas-inventory-locations'
export function savedLocations(): InventoryLocation[] {
  try { return JSON.parse(localStorage.getItem(key) || '[]') as InventoryLocation[] } catch { return [] }
}
export function rememberLocation(location: InventoryLocation) {
  const items = savedLocations().filter((item) => item.id !== location.id)
  localStorage.setItem(key, JSON.stringify([location, ...items]))
}
export function savedOperator(): string { return localStorage.getItem('atlas-operator-id') || '' }
export function rememberOperator(id: string) { localStorage.setItem('atlas-operator-id', id) }
