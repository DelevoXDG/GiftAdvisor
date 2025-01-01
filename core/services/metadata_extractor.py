import requests
from bs4 import BeautifulSoup
from price_parser import Price
from urllib.parse import urlparse
from typing import Dict
import json

class MetadataExtractor:
    """Service for extracting metadata from product URLs."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def extract(self, url: str) -> Dict:
        """Extract metadata from a given URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try different methods to get the data
            metadata = {
                'url': url,
                'domain': urlparse(url).netloc,
            }
            
            # Try to find structured data
            structured_data = self._extract_structured_data(soup)
            if structured_data:
                metadata.update(structured_data)
            
            # Try Open Graph tags
            metadata.update(self._extract_from_og_tags(soup))
            
            # Try standard meta tags and HTML elements
            metadata.update(self._extract_from_meta_tags(soup))
            
            # Clean up and validate the data
            return self._clean_metadata(metadata)
            
        except Exception as e:
            # Log the error in production
            print(f"Error extracting metadata from {url}: {str(e)}")
            return {'url': url, 'error': str(e)}

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from JSON-LD structured data."""
        metadata = {}
        
        # Look for JSON-LD data
        json_ld_tags = soup.find_all('script', type='application/ld+json')
        for tag in json_ld_tags:
            try:
                data = json.loads(tag.string)
                if isinstance(data, list):
                    data = data[0]
                
                if data.get('@type') == 'Product':
                    if 'name' in data:
                        metadata['title'] = data['name']
                    if 'description' in data:
                        metadata['description'] = data['description']
                    if 'image' in data:
                        metadata['image_url'] = data['image'][0] if isinstance(data['image'], list) else data['image']
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, list):
                            offers = offers[0]
                        if 'price' in offers:
                            metadata['price'] = offers['price']
                    break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return metadata

    def _extract_from_og_tags(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from OpenGraph tags."""
        metadata = {}
        
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata['title'] = og_title.get('content')
        
        og_description = soup.find('meta', property='og:description')
        if og_description:
            metadata['description'] = og_description.get('content')
        
        og_image = soup.find('meta', property='og:image')
        if og_image:
            metadata['image_url'] = og_image.get('content')
        
        og_price = soup.find('meta', property='product:price:amount')
        if og_price:
            metadata['price'] = og_price.get('content')
        
        return metadata

    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from standard meta tags and HTML elements."""
        metadata = {}
        
        # Try to find title
        if not metadata.get('title'):
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.string
        
        # Try to find description
        if not metadata.get('description'):
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content')
        
        # Try to find price (common patterns)
        if not metadata.get('price'):
            # Look for elements with price-related classes or IDs
            price_selectors = [
                '[class*="price"]:not([class*="range"])',
                '[id*="price"]:not([id*="range"])',
                '.product-price',
                '.price-current',
                '.sale-price',
            ]
            
            for selector in price_selectors:
                price_elements = soup.select(selector)
                for element in price_elements:
                    price = Price.fromstring(element.text)
                    if price.amount is not None:
                        metadata['price'] = str(price.amount)
                        break
                if 'price' in metadata:
                    break
        
        return metadata

    def _clean_metadata(self, metadata: Dict) -> Dict:
        """Clean and validate extracted metadata."""
        cleaned = {}
        
        # Clean title
        if 'title' in metadata:
            cleaned['title'] = self._clean_text(metadata['title'])
        
        # Clean description
        if 'description' in metadata:
            cleaned['description'] = self._clean_text(metadata['description'])
        
        # Clean price
        if 'price' in metadata:
            try:
                price = Price.fromstring(str(metadata['price']))
                if price.amount is not None:
                    cleaned['price'] = float(price.amount)
            except (ValueError, TypeError):
                pass
        
        # Clean image URL
        if 'image_url' in metadata:
            cleaned['image_url'] = metadata['image_url']
        
        # Always include the original URL and domain
        cleaned['url'] = metadata['url']
        cleaned['domain'] = metadata['domain']
        
        return cleaned

    def _clean_text(self, text: str) -> str:
        """Clean text fields."""
        if not text:
            return ""
        return ' '.join(text.split()) 