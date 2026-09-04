export type ObjectStatus = 'PLANNED' | 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE' | 'RETIRED'
export type Ownership = 'OWNED' | 'CUSTOMER_OWNED' | 'THIRD_PARTY'
export type ManagementScope = 'FULL_CONTROL' | 'HARDWARE_ONLY' | 'MAINTENANCE_ONLY' | 'NO_ACCESS'

export interface ObjectType { id: string; name: string; display_name?: string | null; category: string; description?: string | null }
export interface InfrastructureObject {
  id: string; object_type_id: string; name: string; serial_number: string | null; asset_number: string | null
  uuid: string | null; manufacturer: string | null; model: string | null; firmware_version: string | null
  hardware_generation: string | null; status: ObjectStatus; ownership: Ownership; management_scope: ManagementScope
  owner_org_id: string | null; operator_org_id: string | null; maintainer_org_id: string | null
  deployed_location_id: string | null; version: number; created_at: string; updated_at: string
}
export interface ObjectDetail extends InfrastructureObject {
  object_type: ObjectType; spec_data: Record<string, unknown>
  relationship_summary: { outgoing: number; incoming: number; total: number }
}
export interface ObjectPayload {
  object_type_id: string; name: string; serial_number?: string | null; asset_number?: string | null
  manufacturer?: string | null; model?: string | null; firmware_version?: string | null
  hardware_generation?: string | null; status: ObjectStatus; ownership: Ownership
  management_scope: ManagementScope; owner_org_id?: string | null; operator_org_id?: string | null
  maintainer_org_id?: string | null; deployed_location_id?: string | null; spec_data: Record<string, unknown>
}
export interface Relationship {
  id: string; source_object_id: string; relationship_type_id: string; target_object_id: string
  attributes: Record<string, unknown> | null; status: string; confidence: string; data_source: string
  created_at: string; updated_at: string
}
export interface RelationshipType { id: string; name: string; display_name?: string | null; is_directed: boolean }
export interface ObjectHistory {
  id: string; object_id: string; change_type: string; before_data: Record<string, unknown> | null
  after_data: Record<string, unknown> | null; source: string; operator: string | null; created_at: string
}
export interface Page<T> { total: number; page: number; page_size: number; items: T[] }
export interface Items<T> { items: T[] }
export interface ApiErrorBody { error?: string; code?: string; message?: string; detail?: string | Array<{ msg?: string }> }

export type AssetLifecycleStatus = 'REQUESTED' | 'APPROVED' | 'ORDERED' | 'PURCHASED' | 'RECEIVED' | 'STOCK' | 'IN_TRANSIT' | 'DEPLOYING' | 'DEPLOYED' | 'ACTIVE' | 'MAINTENANCE' | 'TRANSFERRED' | 'RETIRED' | 'RECOVERED'
export interface AssetObjectSummary {
  id: string; name: string; object_type_id: string; serial_number: string | null; model: string | null
  status: string; deployed_location_id: string | null
}
export interface Asset {
  id: string; object_id: string; asset_number: string; lifecycle_status: AssetLifecycleStatus
  purchase_request_id: string | null; purchase_order_id: string | null; purchase_date: string | null
  received_date: string | null; vendor: string | null; contract_number: string | null
  warranty_start_date: string | null; warranty_end_date: string | null; warranty_provider: string | null
  service_level: string | null; cost: string | number | null; currency: string | null
  owner_org_id: string | null; operator_org_id: string | null; maintainer_org_id: string | null
  inventory_location_id: string | null; version: number; created_at: string; updated_at: string
  object: AssetObjectSummary
}
export interface AssetDetail extends Asset {
  spec: Record<string, unknown>; inventory_location: InventoryLocation | null; deployment: Deployment | null
}
export interface LifecycleEvent { event_type: string; occurred_at: string; details: Record<string, unknown> }
export interface InventoryLocation {
  id: string; name: string; warehouse: string; shelf: string | null; location_code: string
  organization_id?: string | null; description?: string | null; created_at?: string
}
export interface InventoryLocationPayload { name: string; warehouse: string; shelf?: string | null; location_code: string; organization_id?: string | null; description?: string | null }
export interface Deployment { id: string; location_id: string; deployment_type: string; status: string; acceptance_status: string; deployed_by: string | null; deployed_at: string | null; notes: string | null }
export interface PurchaseItem { object_type_id: string; quantity: number; model?: string | null; unit_budget?: number | null; vendor?: string | null }
export interface PurchaseRequest {
  id: string; request_number: string; title: string; object_type_id: string; model: string | null
  quantity: number; estimated_cost: string | number | null; currency: string | null; justification: string | null
  preferred_vendor: string | null; items: PurchaseItem[]; status: string; requester_id: string
  approved_by: string | null; approved_at: string | null; rejected_by: string | null; rejected_at: string | null
  rejection_reason: string | null; created_at: string; updated_at: string
}

export interface ImportError {
  row: number
  field: string | null
  error_type: string
  message: string
}

export interface ImportPreview {
  import_id: string
  status: string
  total_count: number
  success_count: number
  failed_count: number
  errors: ImportError[]
  dry_run: boolean
}

export interface ImportJob {
  id: string
  name: string
  filename: string
  format: string
  total_rows: number
  success_count: number
  failed_count: number
  status: string
  error_summary: Record<string, unknown> | null
  created_by: string | null
  created_at: string
  updated_at: string
  version: number
}

export type WorkOrderType = 'FAULT' | 'REPAIR' | 'INSPECTION' | 'CHANGE'
export type WorkOrderPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type WorkOrderStatus = 'CREATED' | 'ASSIGNED' | 'PROCESSING' | 'WAITING' | 'SUSPENDED' | 'RESOLVED' | 'CLOSED' | 'CANCELLED' | 'REOPENED'
export interface RepairRecord {
  id: string; work_order_id: string; object_id: string; repair_type: string; description: string
  parts_used: unknown[] | null; repair_result: string; engineer_id: string; started_at: string
  completed_at: string | null; verification_notes: string | null; created_at: string; updated_at: string
}
export interface ReplacementEvent {
  id: string; repair_record_id: string | null; old_object_id: string; new_object_id: string
  replacement_reason: string; old_object_disposition: string; engineer_id: string
  replaced_at: string; notes: string | null; created_at: string
}
export interface WorkOrderTimelineEvent { type: 'STATUS' | 'REPAIR' | 'REPLACEMENT'; status?: WorkOrderStatus; record_id?: string; at: string; operator_id: string }
export interface WorkOrder {
  id: string; work_order_number: string; title: string; type: WorkOrderType; priority: WorkOrderPriority
  status: WorkOrderStatus; related_object_id: string; description: string | null; fault_record_id: string | null
  assigned_to: string | null; created_by: string; resolved_by: string | null; closed_by: string | null
  assigned_at: string | null; resolved_at: string | null; closed_at: string | null
  version: number; created_at: string; updated_at: string
}
export interface WorkOrderDetail extends WorkOrder { repairs: RepairRecord[]; replacements: ReplacementEvent[]; timeline: WorkOrderTimelineEvent[] }
