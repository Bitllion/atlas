"""API contracts for the generic workflow engine."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class WorkflowDefinitionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = None
    definition: dict[str, Any]
    version: int = Field(default=1, ge=1)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_graph(self):
        nodes = self.definition.get("nodes")
        edges = self.definition.get("edges")
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("definition.nodes 必须是非空数组")
        if not isinstance(edges, list):
            raise ValueError("definition.edges 必须是数组")
        ids: list[str] = []
        for node in nodes:
            if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]:
                raise ValueError("每个节点必须包含非空 id")
            if node.get("type") not in {"approval", "end", "terminal"}:
                raise ValueError("节点 type 仅支持 approval/end/terminal")
            if node["type"] == "approval" and not (node.get("assignee_role") or node.get("assignee_user_id") or node.get("user_id")):
                raise ValueError("审批节点必须配置 assignee_role 或 user_id")
            ids.append(node["id"])
        if len(ids) != len(set(ids)):
            raise ValueError("节点 id 不可重复")
        known = set(ids)
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("边必须是对象")
            source, target = edge.get("source", edge.get("from")), edge.get("target", edge.get("to"))
            if source not in known or target not in known:
                raise ValueError("边的 source/target 必须引用已有节点")
        return self


class WorkflowInstanceStart(BaseModel):
    definition_code: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: UUID
    business_key: str | None = Field(default=None, max_length=255)


class WorkflowTaskAction(BaseModel):
    comment: str | None = None
