"""Purchase link generation service for books and content."""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.services.amazon_api import amazon_api_service, AmazonProduct, AmazonAPIError
from src.models.content import PurchaseLink, ContentItem
from src.schemas.content import PurchaseLinkCreate, PurchaseLinkResponse
from src.database import get_db

logger = logging.getLogger(__name__)


class PurchaseLinkGenerator:
    """Service for generating purchase links for books and content."""

    def __init__(self):
        self.amazon_service = amazon_api_service

    async def generate_purchase_links(
        self,
        content_id: str,
        title: str,
        author: Optional[str] = None,
        isbn: Optional[str] = None
    ) -> List[PurchaseLinkResponse]:
        """Generate all available purchase links for a book."""
        links = []

        try:
            # Try Amazon API first
            amazon_links = await self._generate_amazon_links(title, author, isbn)
            links.extend(amazon_links)

        except AmazonAPIError as e:
            logger.warning(f"Amazon API failed for '{title}': {e}")

        # Always add web search fallback
        web_search_links = self._generate_web_search_links(title, author)
        links.extend(web_search_links)

        # Add library search links
        library_links = self._generate_library_search_links(
            title, author, isbn)
        links.extend(library_links)

        # Store links in database
        stored_links = await self._store_purchase_links(content_id, links)

        return stored_links

    async def _generate_amazon_links(
        self,
        title: str,
        author: Optional[str] = None,
        isbn: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate Amazon purchase links."""
        links = []

        try:
            # Try ISBN lookup first if available
            if isbn:
                product = await self.amazon_service.lookup_by_isbn(isbn)
                if product:
                    link = self._create_amazon_link_dict(product)
                    links.append(link)
                    return links

            # Fall back to title/author search
            products = await self.amazon_service.get_multiple_formats(title, author)

            for product in products:
                link = self._create_amazon_link_dict(product)
                links.append(link)

        except Exception as e:
            logger.error(f"Failed to generate Amazon links: {e}")
            raise AmazonAPIError(f"Amazon link generation failed: {e}")

        return links

    def _create_amazon_link_dict(self, product: AmazonProduct) -> Dict[str, Any]:
        """Create purchase link dictionary from Amazon product."""
        format_display = {
            'physical': 'Paperback/Hardcover',
            'digital': 'Kindle Edition',
            'audiobook': 'Audible Audiobook'
        }

        display_text = f"Buy on Amazon ({format_display.get(product.format, product.format)})"
        if product.price:
            display_text += f" - {product.price}"

        return {
            'link_id': str(uuid.uuid4()),
            'link_type': 'amazon',
            'url': product.url,
            'display_text': display_text,
            'format': product.format,
            'price': product.price,
            'availability': product.availability
        }

    def _generate_web_search_links(
        self,
        title: str,
        author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate web search links for book purchasing."""
        links = []

        # Build search query
        query = f'"{title}"'
        if author:
            query += f' "{author}"'
        query += " buy book"

        # Google search
        google_url = f"https://www.google.com/search?q={self._encode_query(query)}"
        links.append({
            'link_id': str(uuid.uuid4()),
            'link_type': 'web_search',
            'url': google_url,
            'display_text': 'Search Google for purchase options',
            'format': None,
            'price': None,
            'availability': 'unknown'
        })

        # Bing search
        bing_url = f"https://www.bing.com/search?q={self._encode_query(query)}"
        links.append({
            'link_id': str(uuid.uuid4()),
            'link_type': 'web_search',
            'url': bing_url,
            'display_text': 'Search Bing for purchase options',
            'format': None,
            'price': None,
            'availability': 'unknown'
        })

        # Barnes & Noble search
        bn_query = f'"{title}"'
        if author:
            bn_query += f' {author}'
        bn_url = f"https://www.barnesandnoble.com/s/{self._encode_query(bn_query)}"
        links.append({
            'link_id': str(uuid.uuid4()),
            'link_type': 'alternative_retailer',
            'url': bn_url,
            'display_text': 'Search Barnes & Noble',
            'format': None,
            'price': None,
            'availability': 'unknown'
        })

        return links

    def _generate_library_search_links(
        self,
        title: str,
        author: Optional[str] = None,
        isbn: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate library catalog search links."""
        links = []

        # Build search query
        query = f'"{title}"'
        if author:
            query += f' "{author}"'

        # WorldCat (global library catalog)
        worldcat_url = f"https://www.worldcat.org/search?q={self._encode_query(query)}&qt=results_page"
        links.append({
            'link_id': str(uuid.uuid4()),
            'link_type': 'library',
            'url': worldcat_url,
            'display_text': 'Find in libraries (WorldCat)',
            'format': None,
            'price': 'Free (library)',
            'availability': 'unknown'
        })

        # Open Library
        openlibrary_url = f"https://openlibrary.org/search?q={self._encode_query(query)}"
        links.append({
            'link_id': str(uuid.uuid4()),
            'link_type': 'library',
            'url': openlibrary_url,
            'display_text': 'Search Open Library',
            'format': 'digital',
            'price': 'Free',
            'availability': 'unknown'
        })

        return links

    def _encode_query(self, query: str) -> str:
        """URL encode search query."""
        import urllib.parse
        return urllib.parse.quote_plus(query)

    async def _store_purchase_links(
        self,
        content_id: str,
        links: List[Dict[str, Any]]
    ) -> List[PurchaseLinkResponse]:
        """Store purchase links in database."""
        stored_links = []

        # Get database session
        db = next(get_db())

        try:
            # Remove existing links for this content
            db.query(PurchaseLink).filter(
                PurchaseLink.content_id == content_id
            ).delete()

            # Create new links
            for link_data in links:
                db_link = PurchaseLink(
                    link_id=link_data['link_id'],
                    content_id=content_id,
                    link_type=link_data['link_type'],
                    url=link_data['url'],
                    display_text=link_data['display_text'],
                    format=link_data['format'],
                    price=link_data['price'],
                    availability=link_data['availability']
                )

                db.add(db_link)
                db.flush()  # Get the ID without committing

                # Convert to response model
                response = PurchaseLinkResponse(
                    link_id=db_link.link_id,
                    content_id=db_link.content_id,
                    link_type=db_link.link_type,
                    url=db_link.url,
                    display_text=db_link.display_text,
                    format=db_link.format,
                    price=db_link.price,
                    availability=db_link.availability,
                    generated_at=db_link.generated_at or datetime.now(
                        timezone.utc)
                )
                stored_links.append(response)

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store purchase links: {e}")
            raise
        finally:
            db.close()

        return stored_links

    async def refresh_amazon_links(self, content_id: str) -> List[PurchaseLinkResponse]:
        """Refresh Amazon links for existing content."""
        db = next(get_db())

        try:
            # Get content item
            content = db.query(ContentItem).filter(
                ContentItem.id == content_id
            ).first()

            if not content:
                raise ValueError(f"Content item {content_id} not found")

            # Extract metadata
            metadata = content.content_metadata or {}
            title = content.title
            author = metadata.get('author')

            # Get existing Amazon links to check for ISBN/ASIN
            existing_links = db.query(PurchaseLink).filter(
                PurchaseLink.content_id == content_id,
                PurchaseLink.link_type == 'amazon'
            ).all()

            isbn = None
            # Try to extract ISBN from existing data or metadata
            if 'isbn' in metadata:
                isbn = metadata['isbn']

            # Generate new Amazon links
            amazon_links = await self._generate_amazon_links(title, author, isbn)

            # Remove old Amazon links
            db.query(PurchaseLink).filter(
                PurchaseLink.content_id == content_id,
                PurchaseLink.link_type == 'amazon'
            ).delete()

            # Store new Amazon links
            stored_links = []
            for link_data in amazon_links:
                db_link = PurchaseLink(
                    link_id=link_data['link_id'],
                    content_id=content_id,
                    link_type=link_data['link_type'],
                    url=link_data['url'],
                    display_text=link_data['display_text'],
                    format=link_data['format'],
                    price=link_data['price'],
                    availability=link_data['availability']
                )

                db.add(db_link)
                db.flush()

                response = PurchaseLinkResponse(
                    link_id=db_link.link_id,
                    content_id=db_link.content_id,
                    link_type=db_link.link_type,
                    url=db_link.url,
                    display_text=db_link.display_text,
                    format=db_link.format,
                    price=db_link.price,
                    availability=db_link.availability,
                    generated_at=db_link.generated_at or datetime.now(
                        timezone.utc)
                )
                stored_links.append(response)

            db.commit()
            return stored_links

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to refresh Amazon links: {e}")
            raise
        finally:
            db.close()

    async def get_purchase_links(self, content_id: str) -> List[PurchaseLinkResponse]:
        """Get all purchase links for content."""
        db = next(get_db())

        try:
            links = db.query(PurchaseLink).filter(
                PurchaseLink.content_id == content_id
            ).all()

            return [
                PurchaseLinkResponse(
                    link_id=link.link_id,
                    content_id=link.content_id,
                    link_type=link.link_type,
                    url=link.url,
                    display_text=link.display_text,
                    format=link.format,
                    price=link.price,
                    availability=link.availability,
                    generated_at=link.generated_at
                )
                for link in links
            ]

        finally:
            db.close()


# Global service instance
purchase_link_generator = PurchaseLinkGenerator()
