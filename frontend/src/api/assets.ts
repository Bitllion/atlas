import { apiClient } from './client'
import type { Asset, AssetDetail, InventoryLocation, InventoryLocationPayload, Items, LifecycleEvent, Page, PurchaseItem, PurchaseRequest } from '../types'

export interface PurchasePayload { title: string; items: PurchaseItem[]; estimated_cost?: number; currency: string; justification?: string; preferred_vendor?: string; requester_id: string }

export const assetApi = {
  list: (params: { status?: string; page: number; page_size: number }) => apiClient.get<Page<Asset>>('/assets', { params }),
  get: (id: string) => apiClient.get<AssetDetail>(`/assets/${id}`),
  lifecycle: (id: string) => apiClient.get<{ asset_id: string; items: LifecycleEvent[] }>(`/assets/${id}/lifecycle`),
  stock: (id: string, inventoryLocationId: string, operatorId: string, version: number) => apiClient.put<Asset>(`/assets/${id}/stock`, { inventory_location_id: inventoryLocationId, operator_id: operatorId, version }),
  deploy: (id: string, locationId: string, operatorId: string, version: number) => apiClient.put<Asset>(`/assets/${id}/deploy`, { location_id: locationId, deployed_by: operatorId, version }),
  purchases: () => apiClient.get<Items<PurchaseRequest>>('/purchase-requests'),
  createPurchase: (payload: PurchasePayload) => apiClient.post<PurchaseRequest>('/purchase-requests', payload),
  approvePurchase: (id: string, userId: string) => apiClient.post<PurchaseRequest>(`/purchase-requests/${id}/approve`, { approved_by: userId }),
  rejectPurchase: (id: string, userId: string, reason: string) => apiClient.post<PurchaseRequest>(`/purchase-requests/${id}/reject`, { rejected_by: userId, rejection_reason: reason }),
  createLocation: (payload: InventoryLocationPayload) => apiClient.post<InventoryLocation>('/inventory-locations', payload),
}
