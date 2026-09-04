<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { IconDelete, IconPlus } from "@arco-design/web-vue/es/icon";
import { assetApi } from "../api/assets";
import { rememberOperator, savedOperator } from "../api/inventory";
import { objectApi } from "../api/objects";
import type {
  ObjectType,
  PurchaseItem,
  PurchaseRequest,
  WorkflowInstance,
} from "../types";
const requests = ref<PurchaseRequest[]>([]),
  types = ref<ObjectType[]>([]),
  loading = ref(false),
  submitting = ref(false),
  createVisible = ref(false),
  reviewVisible = ref(false),
  reviewAction = ref<"approve" | "reject">("approve"),
  reviewing = ref<PurchaseRequest | null>(null),
  rejectReason = ref(""),
  operatorId = ref(savedOperator()),
  workflowInstances = ref<Record<string, WorkflowInstance>>({});
type PurchaseFormItem = Omit<
  PurchaseItem,
  "model" | "unit_budget" | "vendor"
> & { model: string; unit_budget?: number; vendor: string };
const emptyItem = (): PurchaseFormItem => ({
  object_type_id: "",
  quantity: 1,
  model: "",
  unit_budget: undefined,
  vendor: "",
});
const form = ref({
  title: "",
  preferred_vendor: "",
  estimated_cost: undefined as number | undefined,
  justification: "",
});
const items = ref<PurchaseFormItem[]>([emptyItem()]);
const typeMap = computed(() =>
  Object.fromEntries(
    types.value.map((item) => [item.id, item.display_name || item.name]),
  ),
);
const statusName: Record<string, string> = {
  DRAFT: "草稿",
  PENDING: "待审批",
  APPROVED: "已批准",
  REJECTED: "已驳回",
  CANCELLED: "已取消",
};
const statusColor = (value: string) =>
  ({
    DRAFT: "gray",
    PENDING: "orange",
    APPROVED: "green",
    REJECTED: "red",
    CANCELLED: "gray",
  })[value] || "gray";
function addItem() {
  items.value.push(emptyItem());
}
function itemSummary(parts: PurchaseItem[]) {
  return parts
    .map((part) => `${typeMap.value[part.object_type_id] || "未知类型"} × ${part.quantity}`)
    .join("；");
}
function removeItem(index: number) {
  if (items.value.length > 1) items.value.splice(index, 1);
}
async function load() {
  loading.value = true;
  try {
    requests.value = (await assetApi.purchases()).data.items;
    workflowInstances.value = {};
    await Promise.all(
      requests.value.map(async (request) => {
        try {
          const { data } = await assetApi.getPurchaseWorkflow(request.id);
          if (data) workflowInstances.value[request.id] = data;
        } catch {
          /* 没有工作流实例 */
        }
      }),
    );
  } finally {
    loading.value = false;
  }
}
async function create() {
  if (
    !operatorId.value ||
    !form.value.title ||
    items.value.some((item) => !item.object_type_id || item.quantity < 1)
  )
    return;
  submitting.value = true;
  try {
    rememberOperator(operatorId.value);
    await assetApi.createPurchase({
      ...form.value,
      requester_id: operatorId.value,
      currency: "CNY",
      items: items.value.map((item) => ({
        ...item,
        model: item.model || null,
        vendor: item.vendor || form.value.preferred_vendor || null,
        unit_budget: item.unit_budget || null,
      })),
    });
    form.value = {
      title: "",
      preferred_vendor: "",
      estimated_cost: undefined,
      justification: "",
    };
    items.value = [emptyItem()];
    createVisible.value = false;
    await load();
  } finally {
    submitting.value = false;
  }
}
function openReview(item: PurchaseRequest, kind: "approve" | "reject") {
  reviewing.value = item;
  reviewAction.value = kind;
  rejectReason.value = "";
  reviewVisible.value = true;
}
async function submitReview() {
  if (
    !reviewing.value ||
    !operatorId.value ||
    (reviewAction.value === "reject" && !rejectReason.value.trim())
  )
    return;
  submitting.value = true;
  try {
    rememberOperator(operatorId.value);
    if (reviewAction.value === "approve")
      await assetApi.approvePurchase(reviewing.value.id, operatorId.value);
    else
      await assetApi.rejectPurchase(
        reviewing.value.id,
        operatorId.value,
        rejectReason.value.trim(),
      );
    reviewVisible.value = false;
    await load();
  } finally {
    submitting.value = false;
  }
}
function workflowStatus(id: string) {
  const instance = workflowInstances.value[id];
  return instance?.status === "RUNNING"
    ? `审批中${instance.current_node_id ? ` · ${instance.current_node_id}` : ""}`
    : null;
}
function hasActiveWorkflow(id: string) {
  return workflowInstances.value[id]?.status === "RUNNING";
}
onMounted(async () => {
  types.value = (await objectApi.types()).data.items;
  await load();
});
</script>
<template>
  <section class="page arco-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">采购管理</p>
        <h1>采购申请</h1>
        <p class="muted">按基础设施对象类型提交采购清单并完成审批</p>
      </div>
      <a-button type="primary" @click="createVisible = true"
        ><template #icon><IconPlus /></template>新建申请</a-button
      >
    </header>
    <a-card class="arco-table-card" :bordered="false"
      ><a-table
        :data="requests"
        :loading="loading"
        :pagination="false"
        row-key="id"
        :scroll="{ x: 1400 }"
        ><template #columns
          ><a-table-column
            title="申请编号"
            data-index="request_number"
            :width="170"
          /><a-table-column
            title="标题"
            data-index="title"
            :width="210"
          /><a-table-column title="设备清单" :width="260"
            ><template #cell="{ record }">{{
              itemSummary(record.items)
            }}</template></a-table-column
          ><a-table-column title="供应商" :width="140"
            ><template #cell="{ record }">{{
              record.preferred_vendor || "—"
            }}</template></a-table-column
          ><a-table-column title="预算" :width="150"
            ><template #cell="{ record }">{{
              record.estimated_cost == null
                ? "—"
                : `${record.currency || "CNY"} ${record.estimated_cost}`
            }}</template></a-table-column
          ><a-table-column title="状态" :width="100"
            ><template #cell="{ record }"
              ><a-tag :color="statusColor(record.status)" bordered>{{
                statusName[record.status] || record.status
              }}</a-tag></template
            ></a-table-column
          ><a-table-column title="审批状态" :width="200"
            ><template #cell="{ record }"
              ><a-tag v-if="workflowStatus(record.id)" color="orange">{{
                workflowStatus(record.id)
              }}</a-tag
              ><span v-else>—</span></template
            ></a-table-column
          ><a-table-column title="创建时间" :width="180"
            ><template #cell="{ record }">{{
              new Date(record.created_at).toLocaleString("zh-CN")
            }}</template></a-table-column
          ><a-table-column title="操作" fixed="right" :width="140"
            ><template #cell="{ record }"
              ><a-space
                v-if="
                  record.status === 'PENDING' && !hasActiveWorkflow(record.id)
                "
                ><a-button
                  type="text"
                  size="small"
                  @click="openReview(record, 'approve')"
                  >批准</a-button
                ><a-button
                  type="text"
                  status="danger"
                  size="small"
                  @click="openReview(record, 'reject')"
                  >驳回</a-button
                ></a-space
              ><span v-else>—</span></template
            ></a-table-column
          ></template
        ><template #empty><a-empty description="暂无采购申请" /></template
      ></a-table>
      <div class="arco-pagination">
        <span>共 {{ requests.length }} 条</span>
      </div></a-card
    >
    <a-modal
      v-model:visible="createVisible"
      title="新建采购申请"
      width="900px"
      :ok-loading="submitting"
      ok-text="提交申请"
      cancel-text="取消"
      @ok="create"
      ><a-form :model="form" layout="vertical"
        ><div class="modal-form-grid">
          <a-form-item label="申请标题" required
            ><a-input
              v-model="form.title"
              placeholder="例如：采购 10 台 GB300 服务器" /></a-form-item
          ><a-form-item label="首选供应商"
            ><a-input v-model="form.preferred_vendor" /></a-form-item
          ><a-form-item label="预算总额（CNY）"
            ><a-input-number
              v-model="form.estimated_cost"
              :min="0"
              hide-button /></a-form-item
          ><a-form-item label="操作用户 ID" required
            ><a-input v-model="operatorId" placeholder="申请人的用户 UUID"
          /></a-form-item>
        </div>
        <a-form-item label="申请说明"
          ><a-textarea
            v-model="form.justification"
            :auto-size="{ minRows: 2, maxRows: 4 }"
        /></a-form-item>
        <div class="purchase-items-title">
          <strong>采购明细</strong
          ><a-button type="text" @click="addItem"
            ><template #icon><IconPlus /></template>添加明细</a-button
          >
        </div>
        <div
          v-for="(item, index) in items"
          :key="index"
          class="arco-purchase-item"
        >
          <a-form-item label="对象类型" required
            ><a-select v-model="item.object_type_id" placeholder="请选择"
              ><a-option
                v-for="type in types"
                :key="type.id"
                :value="type.id"
                >{{ type.display_name || type.name }}</a-option
              ></a-select
            ></a-form-item
          ><a-form-item label="型号"
            ><a-input v-model="item.model" /></a-form-item
          ><a-form-item label="数量" required
            ><a-input-number v-model="item.quantity" :min="1" /></a-form-item
          ><a-form-item label="单价预算"
            ><a-input-number
              v-model="item.unit_budget"
              :min="0"
              hide-button /></a-form-item
          ><a-button
            type="text"
            status="danger"
            :disabled="items.length === 1"
            @click="removeItem(index)"
            ><template #icon><IconDelete /></template
          ></a-button></div></a-form
    ></a-modal>
    <a-modal
      v-model:visible="reviewVisible"
      :title="reviewAction === 'approve' ? '批准采购申请' : '驳回采购申请'"
      :ok-loading="submitting"
      :ok-button-props="{
        disabled:
          !operatorId || (reviewAction === 'reject' && !rejectReason.trim()),
      }"
      :ok-text="reviewAction === 'approve' ? '确认批准' : '确认驳回'"
      cancel-text="取消"
      @ok="submitReview"
      ><a-alert :type="reviewAction === 'approve' ? 'info' : 'warning'"
        >{{ reviewing?.request_number }} · {{ reviewing?.title }}</a-alert
      ><a-form :model="{}" layout="vertical"
        ><a-form-item label="操作用户 ID" required
          ><a-input v-model="operatorId" /></a-form-item
        ><a-form-item v-if="reviewAction === 'reject'" label="驳回原因" required
          ><a-textarea
            v-model="rejectReason"
            :auto-size="{ minRows: 3, maxRows: 5 }" /></a-form-item></a-form
    ></a-modal>
  </section>
</template>
