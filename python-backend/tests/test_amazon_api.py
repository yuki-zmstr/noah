"""Tests for Amazon API integration."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.amazon_api import AmazonAPIService, AmazonProduct, AmazonAPIError


class TestAmazonAPIService:
    """Test Amazon API service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = AmazonAPIService()

    def test_generate_signature(self):
        """Test AWS signature generation."""
        params = {
            'Service': 'AWSECommerceService',
            'Operation': 'ItemSearch',
            'AWSAccessKeyId': 'test_key',
            'Timestamp': '2023-01-01T00:00:00.000Z'
        }

        signature = self.service._generate_signature(params)
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_build_request_url(self):
        """Test request URL building."""
        url = self.service._build_request_url(
            operation="ItemSearch",
            SearchIndex="Books",
            Keywords="test book"
        )

        assert "webservices.amazon.com" in url
        assert "Operation=ItemSearch" in url
        assert "SearchIndex=Books" in url
        assert "Keywords=test%20book" in url or "Keywords=test+book" in url

    def test_generate_affiliate_link(self):
        """Test affiliate link generation."""
        asin = "B001234567"
        link = self.service.generate_affiliate_link(asin)

        assert f"amazon.com/dp/{asin}" in link
        assert "tag=" in link

    @pytest.mark.asyncio
    async def test_search_books_by_title_success(self):
        """Test successful book search."""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <ItemSearchResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
            <Items>
                <Item>
                    <ASIN>B001234567</ASIN>
                    <DetailPageURL>https://amazon.com/dp/B001234567</DetailPageURL>
                    <ItemAttributes>
                        <Title>Test Book</Title>
                        <Author>Test Author</Author>
                        <ISBN>1234567890</ISBN>
                        <Binding>Paperback</Binding>
                    </ItemAttributes>
                    <Offers>
                        <Offer>
                            <OfferListing>
                                <Price>
                                    <FormattedPrice>$19.99</FormattedPrice>
                                </Price>
                                <Availability>Usually ships in 24 hours</Availability>
                            </OfferListing>
                        </Offer>
                    </Offers>
                </Item>
            </Items>
        </ItemSearchResponse>'''

        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.text = mock_response
            mock_response_obj.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response_obj
            )

            products = await self.service.search_books_by_title("Test Book", "Test Author")

            assert len(products) == 1
            product = products[0]
            assert product.asin == "B001234567"
            assert product.title == "Test Book"
            assert product.author == "Test Author"
            assert product.isbn == "1234567890"
            assert product.price == "$19.99"
            assert product.format == "physical"

    @pytest.mark.asyncio
    async def test_search_books_api_error(self):
        """Test API error handling."""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <ItemSearchResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
            <Items>
                <Request>
                    <Errors>
                        <Error>
                            <Code>AWS.InvalidParameterValue</Code>
                            <Message>Invalid search index</Message>
                        </Error>
                    </Errors>
                </Request>
            </Items>
        </ItemSearchResponse>'''

        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.text = mock_response
            mock_response_obj.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response_obj
            )

            with pytest.raises(AmazonAPIError):
                await self.service.search_books_by_title("Test Book")

    @pytest.mark.asyncio
    async def test_lookup_by_isbn_success(self):
        """Test successful ISBN lookup."""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <ItemLookupResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
            <Items>
                <Item>
                    <ASIN>B001234567</ASIN>
                    <DetailPageURL>https://amazon.com/dp/B001234567</DetailPageURL>
                    <ItemAttributes>
                        <Title>Test Book</Title>
                        <Author>Test Author</Author>
                        <ISBN>1234567890</ISBN>
                        <Binding>Kindle Edition</Binding>
                    </ItemAttributes>
                </Item>
            </Items>
        </ItemLookupResponse>'''

        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.text = mock_response
            mock_response_obj.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response_obj
            )

            product = await self.service.lookup_by_isbn("1234567890")

            assert product is not None
            assert product.asin == "B001234567"
            assert product.title == "Test Book"
            assert product.format == "digital"

    @pytest.mark.asyncio
    async def test_get_multiple_formats(self):
        """Test getting multiple formats for a book."""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <ItemSearchResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
            <Items>
                <Item>
                    <ASIN>B001234567</ASIN>
                    <DetailPageURL>https://amazon.com/dp/B001234567</DetailPageURL>
                    <ItemAttributes>
                        <Title>Test Book</Title>
                        <Author>Test Author</Author>
                        <Binding>Paperback</Binding>
                    </ItemAttributes>
                </Item>
                <Item>
                    <ASIN>B001234568</ASIN>
                    <DetailPageURL>https://amazon.com/dp/B001234568</DetailPageURL>
                    <ItemAttributes>
                        <Title>Test Book</Title>
                        <Author>Test Author</Author>
                        <Binding>Kindle Edition</Binding>
                    </ItemAttributes>
                </Item>
                <Item>
                    <ASIN>B001234569</ASIN>
                    <DetailPageURL>https://amazon.com/dp/B001234569</DetailPageURL>
                    <ItemAttributes>
                        <Title>Test Book</Title>
                        <Author>Test Author</Author>
                        <Binding>Audible Audiobook</Binding>
                    </ItemAttributes>
                </Item>
            </Items>
        </ItemSearchResponse>'''

        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.text = mock_response
            mock_response_obj.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response_obj
            )

            products = await self.service.get_multiple_formats("Test Book", "Test Author")

            assert len(products) == 3
            formats = [p.format for p in products]
            assert "physical" in formats
            assert "digital" in formats
            assert "audiobook" in formats

    def test_parse_item_element_minimal(self):
        """Test parsing item with minimal data."""
        xml_content = '''<Item xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
            <ASIN>B001234567</ASIN>
            <ItemAttributes>
                <Title>Minimal Book</Title>
            </ItemAttributes>
        </Item>'''

        import xml.etree.ElementTree as ET
        item_elem = ET.fromstring(xml_content)

        product = self.service._parse_item_element(item_elem)

        assert product is not None
        assert product.asin == "B001234567"
        assert product.title == "Minimal Book"
        assert product.author is None
        assert product.isbn is None
        assert product.format == "physical"  # default

    def test_parse_item_element_invalid(self):
        """Test parsing invalid item element."""
        xml_content = '''<Item xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
            <!-- Missing ASIN -->
            <ItemAttributes>
                <Title>Invalid Book</Title>
            </ItemAttributes>
        </Item>'''

        import xml.etree.ElementTree as ET
        item_elem = ET.fromstring(xml_content)

        product = self.service._parse_item_element(item_elem)

        assert product is None
