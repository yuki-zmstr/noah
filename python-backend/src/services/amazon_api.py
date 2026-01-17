"""Amazon Product Advertising API integration service."""

import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import xml.etree.ElementTree as ET
import httpx
import logging
from dataclasses import dataclass

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AmazonProduct:
    """Amazon product information."""
    asin: str
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    url: str = ""
    price: Optional[str] = None
    availability: str = "unknown"
    format: str = "physical"  # physical, digital, audiobook
    image_url: Optional[str] = None
    description: Optional[str] = None


class AmazonAPIError(Exception):
    """Amazon API specific errors."""
    pass


class AmazonAPIService:
    """Service for Amazon Product Advertising API integration."""

    def __init__(self):
        self.access_key = settings.amazon_access_key
        self.secret_key = settings.amazon_secret_key
        self.associate_tag = settings.amazon_associate_tag
        self.endpoint = "webservices.amazon.com"
        self.uri = "/onca/xml"
        self.service = "AWSECommerceService"
        self.version = "2013-08-01"

    def _generate_signature(self, params: Dict[str, str]) -> str:
        """Generate AWS signature for API request."""
        # Sort parameters
        sorted_params = sorted(params.items())

        # Create canonical query string
        canonical_query = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}"
                                   for k, v in sorted_params])

        # Create string to sign
        string_to_sign = f"GET\n{self.endpoint}\n{self.uri}\n{canonical_query}"

        # Generate signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    def _build_request_url(self, operation: str, **kwargs) -> str:
        """Build complete Amazon API request URL."""
        # Base parameters
        params = {
            'Service': self.service,
            'Version': self.version,
            'Operation': operation,
            'AWSAccessKeyId': self.access_key,
            'AssociateTag': self.associate_tag,
            'Timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        }

        # Add operation-specific parameters
        params.update(kwargs)

        # Generate signature
        signature = self._generate_signature(params)
        params['Signature'] = signature

        # Build URL
        query_string = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}"
                                for k, v in sorted(params.items())])

        return f"https://{self.endpoint}{self.uri}?{query_string}"

    async def search_books_by_title(self, title: str, author: Optional[str] = None) -> List[AmazonProduct]:
        """Search for books by title and optionally author."""
        try:
            # Build search keywords
            keywords = title
            if author:
                keywords = f"{title} {author}"

            # Build request URL
            url = self._build_request_url(
                operation="ItemSearch",
                SearchIndex="Books",
                Keywords=keywords,
                ResponseGroup="ItemAttributes,Offers,Images"
            )

            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()

            # Parse XML response
            return self._parse_search_response(response.text)

        except httpx.HTTPError as e:
            logger.error(f"Amazon API HTTP error: {e}")
            raise AmazonAPIError(f"Failed to search Amazon: {e}")
        except Exception as e:
            logger.error(f"Amazon API search error: {e}")
            raise AmazonAPIError(f"Amazon search failed: {e}")

    async def lookup_by_isbn(self, isbn: str) -> Optional[AmazonProduct]:
        """Look up book by ISBN."""
        try:
            # Clean ISBN (remove hyphens, spaces)
            clean_isbn = isbn.replace("-", "").replace(" ", "")

            # Build request URL
            url = self._build_request_url(
                operation="ItemLookup",
                ItemId=clean_isbn,
                IdType="ISBN",
                SearchIndex="Books",
                ResponseGroup="ItemAttributes,Offers,Images"
            )

            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()

            # Parse XML response
            products = self._parse_lookup_response(response.text)
            return products[0] if products else None

        except httpx.HTTPError as e:
            logger.error(f"Amazon API HTTP error for ISBN {isbn}: {e}")
            raise AmazonAPIError(f"Failed to lookup ISBN: {e}")
        except Exception as e:
            logger.error(f"Amazon API ISBN lookup error: {e}")
            raise AmazonAPIError(f"ISBN lookup failed: {e}")

    async def lookup_by_asin(self, asin: str) -> Optional[AmazonProduct]:
        """Look up product by ASIN."""
        try:
            # Build request URL
            url = self._build_request_url(
                operation="ItemLookup",
                ItemId=asin,
                ResponseGroup="ItemAttributes,Offers,Images"
            )

            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()

            # Parse XML response
            products = self._parse_lookup_response(response.text)
            return products[0] if products else None

        except httpx.HTTPError as e:
            logger.error(f"Amazon API HTTP error for ASIN {asin}: {e}")
            raise AmazonAPIError(f"Failed to lookup ASIN: {e}")
        except Exception as e:
            logger.error(f"Amazon API ASIN lookup error: {e}")
            raise AmazonAPIError(f"ASIN lookup failed: {e}")

    def _parse_search_response(self, xml_response: str) -> List[AmazonProduct]:
        """Parse Amazon ItemSearch XML response."""
        try:
            root = ET.fromstring(xml_response)

            # Check for errors
            error_elem = root.find(
                './/{http://webservices.amazon.com/AWSECommerceService/2013-08-01}Error')
            if error_elem is not None:
                error_code = error_elem.find(
                    './/{http://webservices.amazon.com/AWSECommerceService/2013-08-01}Code')
                error_message = error_elem.find(
                    './/{http://webservices.amazon.com/AWSECommerceService/2013-08-01}Message')
                raise AmazonAPIError(
                    f"Amazon API Error: {error_code.text if error_code is not None else 'Unknown'} - {error_message.text if error_message is not None else 'No message'}")

            products = []
            items = root.findall(
                './/{http://webservices.amazon.com/AWSECommerceService/2013-08-01}Item')

            for item in items:
                product = self._parse_item_element(item)
                if product:
                    products.append(product)

            return products

        except ET.ParseError as e:
            logger.error(f"Failed to parse Amazon XML response: {e}")
            raise AmazonAPIError(f"Invalid XML response from Amazon: {e}")

    def _parse_lookup_response(self, xml_response: str) -> List[AmazonProduct]:
        """Parse Amazon ItemLookup XML response."""
        return self._parse_search_response(xml_response)  # Same parsing logic

    def _parse_item_element(self, item_elem) -> Optional[AmazonProduct]:
        """Parse individual item element from Amazon response."""
        try:
            ns = '{http://webservices.amazon.com/AWSECommerceService/2013-08-01}'

            # Extract ASIN
            asin_elem = item_elem.find(f'.//{ns}ASIN')
            if asin_elem is None:
                return None
            asin = asin_elem.text

            # Extract attributes
            attrs = item_elem.find(f'.//{ns}ItemAttributes')
            if attrs is None:
                return None

            # Title
            title_elem = attrs.find(f'.//{ns}Title')
            title = title_elem.text if title_elem is not None else "Unknown Title"

            # Author
            author_elem = attrs.find(f'.//{ns}Author')
            author = author_elem.text if author_elem is not None else None

            # ISBN
            isbn_elem = attrs.find(f'.//{ns}ISBN')
            isbn = isbn_elem.text if isbn_elem is not None else None

            # Format/Binding
            binding_elem = attrs.find(f'.//{ns}Binding')
            binding = binding_elem.text if binding_elem is not None else "Unknown"

            # Map binding to our format
            format_mapping = {
                'Paperback': 'physical',
                'Hardcover': 'physical',
                'Kindle Edition': 'digital',
                'Audible Audiobook': 'audiobook',
                'Audio CD': 'audiobook',
                'MP3 CD': 'audiobook'
            }
            format_type = format_mapping.get(binding, 'physical')

            # Price
            price = None
            offers = item_elem.find(f'.//{ns}Offers')
            if offers is not None:
                offer = offers.find(f'.//{ns}Offer')
                if offer is not None:
                    listing_price = offer.find(
                        f'.//{ns}OfferListing/{ns}Price/{ns}FormattedPrice')
                    if listing_price is not None:
                        price = listing_price.text

            # Availability
            availability = "unknown"
            if offers is not None:
                availability_elem = offers.find(
                    f'.//{ns}Offer/{ns}OfferListing/{ns}Availability')
                if availability_elem is not None:
                    availability_text = availability_elem.text.lower()
                    if "in stock" in availability_text:
                        availability = "available"
                    elif "out of stock" in availability_text:
                        availability = "out_of_stock"
                    elif "pre-order" in availability_text:
                        availability = "pre_order"

            # Detail page URL
            url_elem = item_elem.find(f'.//{ns}DetailPageURL')
            url = url_elem.text if url_elem is not None else ""

            # Add associate tag to URL if not present
            if url and self.associate_tag and self.associate_tag not in url:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}tag={self.associate_tag}"

            # Image URL
            image_url = None
            images = item_elem.find(f'.//{ns}MediumImage')
            if images is not None:
                image_url_elem = images.find(f'.//{ns}URL')
                if image_url_elem is not None:
                    image_url = image_url_elem.text

            return AmazonProduct(
                asin=asin,
                title=title,
                author=author,
                isbn=isbn,
                url=url,
                price=price,
                availability=availability,
                format=format_type,
                image_url=image_url
            )

        except Exception as e:
            logger.error(f"Failed to parse Amazon item: {e}")
            return None

    def generate_affiliate_link(self, asin: str, format_type: str = "physical") -> str:
        """Generate Amazon affiliate link for a product."""
        base_url = f"https://www.amazon.com/dp/{asin}"

        # Add associate tag
        if self.associate_tag:
            base_url = f"{base_url}?tag={self.associate_tag}"

        return base_url

    async def get_multiple_formats(self, title: str, author: Optional[str] = None) -> List[AmazonProduct]:
        """Get all available formats for a book (physical, digital, audiobook)."""
        try:
            # Search for all formats
            products = await self.search_books_by_title(title, author)

            # Group by format and deduplicate
            format_products = {}
            for product in products:
                if product.format not in format_products:
                    format_products[product.format] = product
                elif product.price and not format_products[product.format].price:
                    # Prefer products with price information
                    format_products[product.format] = product

            return list(format_products.values())

        except Exception as e:
            logger.error(f"Failed to get multiple formats: {e}")
            return []


# Global service instance
amazon_api_service = AmazonAPIService()
