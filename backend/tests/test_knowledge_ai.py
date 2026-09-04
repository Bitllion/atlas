"""Tests for knowledge AI service."""

from unittest.mock import Mock, patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models import Organization, Role, User, UserRole
from app.models.knowledge import KnowledgeArticle
from app.services.knowledge_ai import search_articles


@pytest.fixture(scope="module")
def test_user():
    """Create test user for the module."""
    marker = uuid4().hex
    with SessionLocal() as db:
        organization = Organization(name=f"knowledge-ai-test-org-{marker}", org_type="INTERNAL")
        db.add(organization)
        db.flush()
        user = User(
            username=f"knowledge-ai-user-{marker}",
            email=f"{marker}@example.test",
            password_hash="test",
            organization_id=organization.id
        )
        db.add(user)
        db.flush()
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        db.add(UserRole(user_id=user.id, role_id=admin_role.id, granted_by=user.id))
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture(scope="module")
def user_headers(test_user):
    """Return auth headers for test user."""
    return {"X-User-Id": str(test_user.id)}


@pytest.fixture(scope="module")
def sample_articles(test_user):
    """Create sample published articles for testing."""
    with SessionLocal() as db:
        articles = [
            KnowledgeArticle(
                id=uuid4(),
                title="GPU 更换 SOP",
                content="本文档详细说明了 GPU 更换流程。首先需要关闭服务器电源,然后拆卸旧 GPU 卡,安装新 GPU 卡,最后验证硬件识别。",
                type="SOP",
                status="PUBLISHED",
                tags=["GPU", "硬件", "维修"],
                author_id=test_user.id,
                version=1,
                is_latest=True
            ),
            KnowledgeArticle(
                id=uuid4(),
                title="B300 Firmware 升级指南",
                content="B300 GPU 的 Firmware 升级需要特定工具。升级前请备份配置,升级后需要重启系统验证。",
                type="SOP",
                status="PUBLISHED",
                tags=["B300", "Firmware", "升级"],
                author_id=test_user.id,
                version=1,
                is_latest=True
            ),
            KnowledgeArticle(
                id=uuid4(),
                title="服务器验收流程",
                content="新服务器到货后需要完成硬件检查、操作系统安装、性能测试等步骤。",
                type="BEST_PRACTICE",
                status="PUBLISHED",
                tags=["服务器", "验收"],
                author_id=test_user.id,
                version=1,
                is_latest=True
            ),
            KnowledgeArticle(
                id=uuid4(),
                title="草稿文档",
                content="这是草稿状态的文档,不应该被检索到。",
                type="FAQ",
                status="DRAFT",
                tags=["测试"],
                author_id=test_user.id,
                version=1,
                is_latest=True
            )
        ]
        db.add_all(articles)
        db.commit()
        article_ids = [a.id for a in articles]

    yield article_ids

    # Cleanup
    with SessionLocal() as db:
        for aid in article_ids:
            article = db.get(KnowledgeArticle, aid)
            if article:
                db.delete(article)
        db.commit()


def test_search_articles_by_title(sample_articles):
    """Test search matches title with highest score."""
    with SessionLocal() as db:
        results = search_articles(db, "GPU", limit=5)

    assert len(results) > 0
    # "GPU 更换 SOP" should rank first (title match + tag match + content match)
    assert "GPU" in results[0]["title"]
    assert results[0]["score"] >= 3  # At least title match


def test_search_articles_by_tag(sample_articles):
    """Test search matches tags."""
    with SessionLocal() as db:
        results = search_articles(db, "Firmware", limit=5)

    assert len(results) > 0
    found_firmware = any("Firmware" in r["title"] for r in results)
    assert found_firmware


def test_search_articles_by_content(sample_articles):
    """Test search matches content."""
    with SessionLocal() as db:
        results = search_articles(db, "备份", limit=5)

    assert len(results) > 0
    found = any("B300" in r["title"] for r in results)
    assert found


def test_search_articles_multi_keyword(sample_articles):
    """Test multi-keyword search (space-separated)."""
    with SessionLocal() as db:
        results = search_articles(db, "GPU 升级", limit=5)

    # Should match both "GPU 更换 SOP" and "B300 Firmware 升级指南"
    assert len(results) >= 2


def test_search_articles_excludes_draft(sample_articles):
    """Test that draft articles are not included in search results."""
    with SessionLocal() as db:
        results = search_articles(db, "草稿", limit=5)

    # Should not find the draft article
    assert all("草稿" not in r["title"] for r in results)


def test_search_articles_score_ordering(sample_articles):
    """Test that results are ordered by score (title > tags > content)."""
    with SessionLocal() as db:
        results = search_articles(db, "GPU", limit=5)

    # Verify descending score order
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_articles_empty_query(sample_articles):
    """Test empty query returns empty results."""
    with SessionLocal() as db:
        results = search_articles(db, "", limit=5)
        assert len(results) == 0

        results = search_articles(db, "   ", limit=5)
        assert len(results) == 0


def test_search_articles_limit(sample_articles):
    """Test limit parameter."""
    with SessionLocal() as db:
        results = search_articles(db, "服务器", limit=2)
    assert len(results) <= 2


def test_search_articles_summary_generation(sample_articles):
    """Test that summary is generated correctly."""
    with SessionLocal() as db:
        results = search_articles(db, "GPU", limit=5)

    assert len(results) > 0
    assert "summary" in results[0]
    assert len(results[0]["summary"]) <= 203  # 200 chars + "..."


def test_ask_endpoint_without_llm_config(client, sample_articles, user_headers):
    """Test /ask endpoint returns configured=false when LLM not configured."""
    response = client.post(
        "/api/v1/knowledge/ask",
        json={"question": "如何更换 GPU?"},
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["answer"] is None
    assert "sources" in data
    assert len(data["sources"]) > 0
    # Should find GPU-related article
    assert any("GPU" in s["title"] for s in data["sources"])


def test_ask_endpoint_with_llm_config(client, sample_articles, user_headers, monkeypatch):
    """Test /ask endpoint with LLM configured."""
    # Mock settings at the module level where it's imported
    mock_settings = Mock()
    mock_settings.llm_base_url = "https://api.example.com"
    mock_settings.llm_api_key = "test-key"
    mock_settings.llm_model = "gpt-3.5-turbo"

    # Mock httpx.post
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "根据[来源1],GPU 更换需要先关闭服务器电源。"
            }
        }]
    }
    mock_response.raise_for_status = Mock()

    with patch("app.api.v1.knowledge.httpx.post", return_value=mock_response) as mock_post:
        # Patch the settings in the ask_question function's scope
        with patch("app.config.settings.settings", mock_settings):
            response = client.post(
                "/api/v1/knowledge/ask",
                json={"question": "如何更换 GPU?"},
                headers=user_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["answer"] is not None
        assert "来源" in data["answer"]
        assert len(data["sources"]) > 0

        # Verify httpx.post was called with correct parameters
        assert mock_post.called
        call_args = mock_post.call_args
        assert "Authorization" in call_args.kwargs["headers"]
        assert "Bearer test-key" == call_args.kwargs["headers"]["Authorization"]
        assert call_args.kwargs["json"]["model"] == "gpt-3.5-turbo"
        assert "如何更换 GPU?" in call_args.kwargs["json"]["messages"][0]["content"]


def test_ask_endpoint_llm_failure_fallback(client, sample_articles, user_headers, monkeypatch):
    """Test /ask endpoint falls back to sources-only when LLM fails."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.llm_base_url = "https://api.example.com"
    mock_settings.llm_api_key = "test-key"
    mock_settings.llm_model = "gpt-3.5-turbo"

    # Mock httpx.post to raise exception
    with patch("app.api.v1.knowledge.httpx.post", side_effect=httpx.TimeoutException("Timeout")):
        with patch("app.config.settings.settings", mock_settings):
            response = client.post(
                "/api/v1/knowledge/ask",
                json={"question": "如何更换 GPU?"},
                headers=user_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True  # Config exists but LLM failed
        assert data["answer"] is None  # Fallback to sources only
        assert len(data["sources"]) > 0


def test_ask_endpoint_prompt_contains_search_results(client, sample_articles, user_headers, monkeypatch):
    """Test that LLM prompt contains search results."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.llm_base_url = "https://api.example.com"
    mock_settings.llm_api_key = "test-key"
    mock_settings.llm_model = "gpt-3.5-turbo"

    # Mock httpx.post
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": "测试回答"
            }
        }]
    }
    mock_response.raise_for_status = Mock()

    with patch("app.api.v1.knowledge.httpx.post", return_value=mock_response) as mock_post:
        with patch("app.config.settings.settings", mock_settings):
            response = client.post(
                "/api/v1/knowledge/ask",
                json={"question": "GPU"},
                headers=user_headers
            )

        assert response.status_code == 200

        # Verify prompt contains search results
        call_args = mock_post.call_args
        prompt = call_args.kwargs["json"]["messages"][0]["content"]
        assert "GPU 更换 SOP" in prompt or "来源" in prompt
        assert "GPU" in prompt

