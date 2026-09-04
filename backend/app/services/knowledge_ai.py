"""Knowledge AI search and answer service."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeArticle


def search_articles(db: Session, query: str, limit: int = 5) -> list[dict]:
    """Search published articles by keyword matching with scoring.

    Scoring:
    - Title match: +3
    - Tag match: +2
    - Content match: +1

    Supports multi-keyword search (space-separated, any match).
    """
    if not query or not query.strip():
        return []

    # Get all published articles
    articles = db.scalars(
        select(KnowledgeArticle).where(
            KnowledgeArticle.status == "PUBLISHED",
            KnowledgeArticle.deleted_at.is_(None),
            KnowledgeArticle.is_latest.is_(True)
        )
    ).all()

    # Normalize query: remove punctuation and split by whitespace
    import re
    # Remove common punctuation
    normalized_query = re.sub(r'[?!,;。?!,;、]', ' ', query)
    # Split by whitespace and filter empty
    keywords = [kw.strip().lower() for kw in normalized_query.split() if kw.strip()]
    if not keywords:
        return []

    # Score each article
    scored_articles = []
    for article in articles:
        score = 0
        title_lower = article.title.lower()
        content_lower = article.content.lower()
        tags_lower = [tag.lower() for tag in (article.tags or [])]

        for keyword in keywords:
            # Title match: +3
            if keyword in title_lower:
                score += 3

            # Tag match: +2
            if any(keyword in tag for tag in tags_lower):
                score += 2

            # Content match: +1
            if keyword in content_lower:
                score += 1

        if score > 0:
            # Generate summary (first 200 chars)
            summary = article.content[:200]
            if len(article.content) > 200:
                summary += "..."

            scored_articles.append({
                "id": str(article.id),
                "title": article.title,
                "type": article.type,
                "summary": summary,
                "content": article.content,
                "score": score
            })

    # Sort by score descending and return top N
    scored_articles.sort(key=lambda x: x["score"], reverse=True)
    return scored_articles[:limit]
