"""Tests for purchase link generator service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.purchase_link_generator import PurchaseLinkGenerator
from src.services.amazon_api import AmazonProduct, AmazonAPIError


class TestPurchaseLinkGenerator:
    """Test purchase link generator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = PurchaseLinkGenerator()

    def test_create_amazon_link_dict(self):
        """Test creating Amazon link dictionary from product."""
        product = AmazonProduct(
            asin="B001234567",
            title="Test Book",
            author="Test Author",
            url="https://amazon.com/dp/B001234567?tag=testtag",
            price="$19.99",
            availability="available",
            format="physical"
        )

        link_dict = self.generator._create_amazon_link_dict(product)

        assert link_dict['link_type'] == 'amazon'
        assert link_dict['url'] == product.url
        assert "$19.99" in link_dict['display_text']
        assert "Paperback/Hardcover" in link_dict['display_text']
        assert link_dict['format'] == 'physical'
        assert link_dict['price'] == '$19.99'
        assert link_dict['availability'] == 'available'

    def test_create_amazon_link_dict_digital(self):
        """Test creating Amazon link for digital format."""
        product = AmazonProduct(
            asin="B001234567",
            title="Test Book",
            url="https://amazon.com/dp/B001234567",
            format="digital"
        )

        link_dict = self.generator._create_amazon_link_dict(product)

        assert "Kindle Edition" in link_dict['display_text']
        assert link_dict['format'] == 'digital'

    def test_generate_web_search_links(self):
        """Test generating web search links."""
        links = self.generator._generate_web_search_links(
            "Test Book", "Test Author")

        assert len(links) >= 3  # Google, Bing, Barnes & Noble

        # Check Google link
        google_link = next(l for l in links if 'google.com' in l['url'])
        assert google_link['link_type'] == 'web_search'
        assert 'Test%2BBook' in google_link['url'] or 'Test+Book' in google_link['url']

        # Check Bing link
        bing_link = next(l for l in links if 'bing.com' in l['url'])
        assert bing_link['link_type'] == 'web_search'

        # Check Barnes & Noble link
        bn_link = next(l for l in links if 'barnesandnoble.com' in l['url'])
        assert bn_link['link_type'] == 'alternative_retailer'

    def test_generate_library_search_links(self):
        """Test generating library search links."""
        links = self.generator._generate_library_search_links(
            "Test Book", "Test Author", "1234567890"
        )

        assert len(links) >= 2  # WorldCat, Open Library

        # Check WorldCat link
        worldcat_link = next(l for l in links if 'worldcat.org' in l['url'])
        assert worldcat_link['link_type'] == 'library'
        assert worldcat_link['price'] == 'Free (library)'

        # Check Open Library link
        openlibrary_link = next(
            l for l in links if 'openlibrary.org' in l['url'])
        assert openlibrary_link['link_type'] == 'library'
        assert openlibrary_link['price'] == 'Free'

    def test_encode_query(self):
        """Test URL encoding of search queries."""
        query = 'Test Book "Author Name"'
        encoded = self.generator._encode_query(query)

        assert ' ' not in encoded
        assert '"' not in encoded
        assert 'Test' in encoded

    @pytest.mark.asyncio
    async def test_generate_amazon_links_success(self):
        """Test successful Amazon link generation."""
        mock_products = [
            AmazonProduct(
                asin="B001234567",
                title="Test Book",
                url="https://amazon.com/dp/B001234567",
                format="physical",
                price="$19.99"
            ),
            AmazonProduct(
                asin="B001234568",
                title="Test Book",
                url="https://amazon.com/dp/B001234568",
                format="digital",
                price="$9.99"
            )
        ]

        with patch.object(self.generator.amazon_service, 'get_multiple_formats',
                          new_callable=AsyncMock) as mock_get_formats:
            mock_get_formats.return_value = mock_products

            links = await self.generator._generate_amazon_links("Test Book", "Test Author")

            assert len(links) == 2
            assert links[0]['link_type'] == 'amazon'
            assert links[1]['link_type'] == 'amazon'
            assert links[0]['format'] == 'physical'
            assert links[1]['format'] == 'digital'

    @pytest.mark.asyncio
    async def test_generate_amazon_links_with_isbn(self):
        """Test Amazon link generation with ISBN lookup."""
        mock_product = AmazonProduct(
            asin="B001234567",
            title="Test Book",
            url="https://amazon.com/dp/B001234567",
            format="physical"
        )

        with patch.object(self.generator.amazon_service, 'lookup_by_isbn',
                          new_callable=AsyncMock) as mock_lookup:
            mock_lookup.return_value = mock_product

            links = await self.generator._generate_amazon_links(
                "Test Book", "Test Author", "1234567890"
            )

            assert len(links) == 1
            assert links[0]['link_type'] == 'amazon'
            mock_lookup.assert_called_once_with("1234567890")

    @pytest.mark.asyncio
    async def test_generate_amazon_links_api_error(self):
        """Test Amazon link generation with API error."""
        with patch.object(self.generator.amazon_service, 'get_multiple_formats',
                          new_callable=AsyncMock) as mock_get_formats:
            mock_get_formats.side_effect = AmazonAPIError("API Error")

            with pytest.raises(AmazonAPIError):
                await self.generator._generate_amazon_links("Test Book")

    @pytest.mark.asyncio
    @patch('src.services.purchase_link_generator.get_db')
    async def test_generate_purchase_links_success(self, mock_get_db):
        """Test successful purchase link generation."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        # Mock Amazon API success
        mock_products = [
            AmazonProduct(
                asin="B001234567",
                title="Test Book",
                url="https://amazon.com/dp/B001234567",
                format="physical"
            )
        ]

        with patch.object(self.generator.amazon_service, 'get_multiple_formats',
                          new_callable=AsyncMock) as mock_get_formats:
            mock_get_formats.return_value = mock_products

            links = await self.generator.generate_purchase_links(
                content_id="test-content-1",
                title="Test Book",
                author="Test Author"
            )

            # Should have Amazon links + web search + library links
            assert len(links) >= 5

            # Check that we have different link types
            link_types = [link.link_type for link in links]
            assert 'amazon' in link_types
            assert 'web_search' in link_types
            assert 'library' in link_types

    @pytest.mark.asyncio
    @patch('src.services.purchase_link_generator.get_db')
    async def test_generate_purchase_links_amazon_failure(self, mock_get_db):
        """Test purchase link generation when Amazon API fails."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        # Mock Amazon API failure
        with patch.object(self.generator.amazon_service, 'get_multiple_formats',
                          new_callable=AsyncMock) as mock_get_formats:
            mock_get_formats.side_effect = AmazonAPIError("API Error")

            links = await self.generator.generate_purchase_links(
                content_id="test-content-1",
                title="Test Book",
                author="Test Author"
            )

            # Should still have web search and library links
            assert len(links) >= 4

            # Should not have Amazon links
            link_types = [link.link_type for link in links]
            assert 'amazon' not in link_types
            assert 'web_search' in link_types
            assert 'library' in link_types

    @pytest.mark.asyncio
    @patch('src.services.purchase_link_generator.get_db')
    async def test_get_purchase_links(self, mock_get_db):
        """Test getting existing purchase links."""
        # Mock database session and query results
        mock_db = Mock()
        mock_link = Mock()
        mock_link.link_id = "test-link-1"
        mock_link.content_id = "test-content-1"
        mock_link.link_type = "amazon"
        mock_link.url = "https://amazon.com/dp/B001234567"
        mock_link.display_text = "Buy on Amazon"
        mock_link.format = "physical"
        mock_link.price = "$19.99"
        mock_link.availability = "available"
        mock_link.generated_at = "2023-01-01T00:00:00"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_link]
        mock_get_db.return_value = iter([mock_db])

        links = await self.generator.get_purchase_links("test-content-1")

        assert len(links) == 1
        assert links[0].link_id == "test-link-1"
        assert links[0].link_type == "amazon"
