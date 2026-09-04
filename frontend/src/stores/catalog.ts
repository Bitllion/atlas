import { computed, reactive } from 'vue'
import { adminApi } from '../api/admin'
import { assetApi } from '../api/assets'
import { objectApi } from '../api/objects'
import type { InventoryLocation, ObjectType, Organization, User } from '../types'

const state = reactive({
  organizations: [] as Organization[], locations: [] as InventoryLocation[], objectTypes: [] as ObjectType[], users: [] as User[],
})
let baseLoading: Promise<void> | null = null
let usersLoading: Promise<void> | null = null

export async function loadCatalogs(force = false) {
  if (baseLoading && !force) return baseLoading
  baseLoading = Promise.all([
    adminApi.organizations({ page: 1, page_size: 200 }), assetApi.locations(), objectApi.types(),
  ]).then(([organizations, locations, objectTypes]) => {
    state.organizations = organizations.data.items
    state.locations = locations.data.items
    state.objectTypes = objectTypes.data.items
  }).finally(() => { baseLoading = null })
  return baseLoading
}

export async function loadUsers(force = false) {
  if (usersLoading && !force) return usersLoading
  usersLoading = adminApi.users({ page: 1, page_size: 200 }).then(({ data }) => { state.users = data.items }).finally(() => { usersLoading = null })
  return usersLoading
}

export function useCatalog() {
  return {
    state,
    organizationMap: computed(() => Object.fromEntries(state.organizations.map(item => [item.id, item.name]))),
    locationMap: computed(() => Object.fromEntries(state.locations.map(item => [item.id, item.name]))),
    objectTypeMap: computed(() => Object.fromEntries(state.objectTypes.map(item => [item.id, item.display_name || item.name]))),
    userMap: computed(() => Object.fromEntries(state.users.map(item => [item.id, item.full_name || item.username]))),
  }
}
