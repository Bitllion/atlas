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
