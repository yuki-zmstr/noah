"""Integration tests for Amazon API functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app
from src.services.amazon_api import AmazonProduct


class TestAmazonIntegration:
    """Test Amazon API integration through FastAPI endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    @pytest.mark.asyncio
    @patch('src.services.purchase_link_generator.get_db')
    @patch('src.services.purchase_link_generator.purchase_link_generator.amazon_service')
    def test_generate_purchase_links_endpoint(self, mock_amazon_service, mock_get_db):
        """Test the generate purchase links API endpoint."""
        # Mock database
        mock_db = AsyncMock()
        mock_content = AsyncMock()
        mock_content.id = "test-content-1"
        mock_content.title = "Test Book"
        mock_content.content_metadata = {"author": "Test Author"}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_content
        mock_get_db.return_value = iter([mock_db])

        # Mock Amazon API
        mock_products = [
            AmazonProduct(
                asin="B001234567",
                title="Test Book",
                author="Test Author",
                url="https://amazon.com/dp/B001234567?tag=testtag",
                price="$19.99",
                availability="available",
                format="physical"
            )
        ]
        mock_amazon_service.get_multiple_formats = AsyncMock(
            return_value=mock_products)

        # Make API request
        response = self.client.post(
            "/api/v1/content/test-content-1/generate-purchase-links")

        assert response.status_code == 200
        data = response.json()

        # Should have multiple link types
        assert len(data) >= 5  # Amazon + web search + library links

        # Check Amazon link
        amazon_links = [link for link in data if link['link_type'] == 'amazon']
        assert len(amazon_links) >= 1
        assert amazon_links[0]['url'] == "https://amazon.com/dp/B001234567?tag=testtag"
        assert amazon_links[0]['price'] == "$19.99"

        # Check web search links
        web_links = [
            link for link in data if link['link_type'] == 'web_search']
        assert len(web_links) >= 2  # Google and Bing

        # Check library links
        library_links = [
            link for link in data if link['link_type'] == 'library']
        assert len(library_links) >= 2  # WorldCat and Open Library

    @patch('src.services.purchase_link_generator.get_db')
    def test_generate_purchase_links_content_not_found(self, mock_get_db):
        """Test generate purchase links with non-existent content."""
        # Mock database - content not found
        mock_db = AsyncMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = iter([mock_db])

        response = self.client.post(
            "/api/v1/content/nonexistent/generate-purchase-links")

        assert response.status_code == 404
        assert "Content item not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch('src.services.purchase_link_generator.get_db')
    @patch('src.services.purchase_link_generator.purchase_link_generator.amazon_service')
    def test_refresh_amazon_links_endpoint(self, mock_amazon_service, mock_get_db):
        """Test the refresh Amazon links API endpoint."""
        # Mock database
        mock_db = AsyncMock()
        mock_content = AsyncMock()
        mock_content.id = "test-content-1"
        mock_content.title = "Test Book"
        mock_content.content_metadata = {"author": "Test Author"}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_content
        mock_get_db.return_value = iter([mock_db])

        # Mock Amazon API
        mock_products = [
            AmazonProduct(
                asin="B001234567",
                title="Test Book",
                url="https://amazon.com/dp/B001234567",
                format="digital",
                price="$9.99"
            )
        ]
        mock_amazon_service.get_multiple_formats = AsyncMock(
            return_value=mock_products)

        # Make API request
        response = self.client.post(
            "/api/content/test-content-1/refresh-amazon-links")

        assert response.status_code == 200
        data = response.json()

        # Should have Amazon links only
        assert len(data) >= 1
        assert all(link['link_type'] == 'amazon' for link in data)

    @patch('src.services.purchase_link_generator.get_db')
    def test_get_purchase_links_endpoint(self, mock_get_db):
        """Test the get purchase links API endpoint."""
        # Mock database with existing links
        mock_db = AsyncMock()
        mock_link = AsyncMock()
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

        # Make API request
        response = self.client.get(
            "/api/content/test-content-1/purchase-links")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]['link_id'] == "test-link-1"
        assert data[0]['link_type'] == "amazon"

    def test_api_routes_exist(self):
        """Test that all expected API routes exist."""
        # Test that the routes are properly registered
        routes = [route.path for route in app.routes]

        # Check that content routes exist (they should be under /api/content)
        content_routes = [route for route in routes if '/content' in route]
        assert len(content_routes) > 0
