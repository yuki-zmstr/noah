"""Content management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel

from src.database import get_db
from src.models.content import ContentItem, PurchaseLink
from src.schemas.content import (
    ContentItemCreate,
    ContentItemResponse,
    PurchaseLinkCreate,
    PurchaseLinkResponse,
    ContentAnalysis
)
from src.services.content_service import content_service
from src.services.purchase_link_generator import purchase_link_generator

router = APIRouter()


# Request/Response models for new endpoints
class TextAnalysisRequest(BaseModel):
    text: str
    language: str  # "english" or "japanese"


@router.post("/", response_model=ContentItemResponse)
async def create_content_item(
    content: ContentItemCreate,
    db: Session = Depends(get_db)
):
    """Create and process a new content item."""
    # Use content service to process and store content
    try:
        return await content_service.process_and_store_content(content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process content: {str(e)}")


@router.post("/analyze", response_model=ContentAnalysis)
async def analyze_text_sample(request: TextAnalysisRequest):
    """Analyze a text sample without storing it."""
    try:
        return content_service.analyze_text_sample(request.text, request.language)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze text: {str(e)}")


@router.get("/{content_id}/analysis", response_model=ContentAnalysis)
async def get_content_analysis(content_id: str):
    """Get content analysis for a specific content item."""
    analysis = await content_service.get_content_analysis(content_id)
    if not analysis:
        raise HTTPException(
            status_code=404, detail="Content analysis not found")
    return analysis


@router.get("/search/similar")
async def search_similar_content(
    query: str,
    language: str,
    limit: int = 10
):
    """Search for content similar to the query text."""
    try:
        results = await content_service.search_content_by_similarity(query, language, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/filter/reading-level")
async def get_content_by_reading_level(
    language: str,
    reading_level: str,
    limit: int = 10
):
    """Get content filtered by reading level."""
    try:
        results = await content_service.get_content_by_reading_level(language, reading_level, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to filter content: {str(e)}")


@router.get("/topics")
async def get_content_topics(language: str):
    """Get all unique topics from content analysis."""
    try:
        topics = await content_service.get_content_topics(language)
        return {"topics": topics}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get topics: {str(e)}")


@router.get("/{content_id}", response_model=ContentItemResponse)
async def get_content_item(
    content_id: str,
    db: Session = Depends(get_db)
):
    """Get content item by ID."""
    content = db.query(ContentItem).filter(
        ContentItem.id == content_id).first()

    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")

    return content


@router.get("/", response_model=List[ContentItemResponse])
async def list_content_items(
    language: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List content items with optional filtering."""
    query = db.query(ContentItem)

    if language:
        query = query.filter(ContentItem.language == language)

    content_items = query.offset(offset).limit(limit).all()
    return content_items


@router.post("/{content_id}/purchase-links", response_model=PurchaseLinkResponse)
async def create_purchase_link(
    content_id: str,
    purchase_link: PurchaseLinkCreate,
    db: Session = Depends(get_db)
):
    """Create a purchase link for content."""
    # Verify content exists
    content = db.query(ContentItem).filter(
        ContentItem.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")

    # Create purchase link
    db_link = PurchaseLink(
        link_id=purchase_link.link_id,
        content_id=content_id,
        link_type=purchase_link.link_type,
        url=purchase_link.url,
        display_text=purchase_link.display_text,
        format=purchase_link.format,
        price=purchase_link.price,
        availability=purchase_link.availability
    )

    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    return db_link


@router.get("/{content_id}/purchase-links", response_model=List[PurchaseLinkResponse])
async def get_purchase_links(
    content_id: str,
    db: Session = Depends(get_db)
):
    """Get all purchase links for content."""
    try:
        links = await purchase_link_generator.get_purchase_links(content_id)
        return links
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get purchase links: {str(e)}")


@router.post("/{content_id}/generate-purchase-links", response_model=List[PurchaseLinkResponse])
async def generate_purchase_links(
    content_id: str,
    db: Session = Depends(get_db)
):
    """Generate purchase links for content using Amazon API and web search."""
    # Verify content exists
    content = db.query(ContentItem).filter(
        ContentItem.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")

    try:
        # Extract metadata for link generation
        metadata = content.content_metadata or {}
        title = content.title
        author = metadata.get('author')
        isbn = metadata.get('isbn')

        # Generate purchase links
        links = await purchase_link_generator.generate_purchase_links(
            content_id=content_id,
            title=title,
            author=author,
            isbn=isbn
        )

        return links

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate purchase links: {str(e)}")


@router.post("/{content_id}/refresh-amazon-links", response_model=List[PurchaseLinkResponse])
async def refresh_amazon_links(
    content_id: str,
    db: Session = Depends(get_db)
):
    """Refresh Amazon purchase links for content."""
    # Verify content exists
    content = db.query(ContentItem).filter(
        ContentItem.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content item not found")

    try:
        links = await purchase_link_generator.refresh_amazon_links(content_id)
        return links

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh Amazon links: {str(e)}")
