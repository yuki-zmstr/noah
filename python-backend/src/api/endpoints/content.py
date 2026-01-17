"""Content management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database import get_db
from src.models.content import ContentItem, PurchaseLink
from src.schemas.content import (
    ContentItemCreate,
    ContentItemResponse,
    PurchaseLinkCreate,
    PurchaseLinkResponse
)

router = APIRouter()


@router.post("/", response_model=ContentItemResponse)
async def create_content_item(
    content: ContentItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new content item."""
    # Check if content already exists
    existing_content = db.query(ContentItem).filter(
        ContentItem.id == content.id
    ).first()

    if existing_content:
        raise HTTPException(
            status_code=400, detail="Content item already exists")

    # Create new content item
    db_content = ContentItem(
        id=content.id,
        title=content.title,
        content=content.content,
        language=content.language,
        content_metadata=content.metadata.dict(),
        analysis=content.analysis.dict() if content.analysis else None
    )

    db.add(db_content)
    db.commit()
    db.refresh(db_content)

    return db_content


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
    links = db.query(PurchaseLink).filter(
        PurchaseLink.content_id == content_id
    ).all()

    return links
