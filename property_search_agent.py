#!/usr/bin/env python3
"""
Property Search MCP Agent - Real estate property search and scraping
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import uuid
import re
from dataclasses import dataclass

import httpx
from anthropic import AsyncAnthropic
import asyncpg
from pydantic import BaseModel
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyCriteria:
    """Property search criteria from realconnect.online"""
    location: str
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None  # house, condo, townhouse, etc.
    square_feet_min: Optional[int] = None
    square_feet_max: Optional[int] = None
    lot_size_min: Optional[float] = None
    keywords: Optional[List[str]] = None

@dataclass
class Property:
    """Property data model"""
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: int
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int]
    lot_size: Optional[float]
    property_type: str
    listing_url: str
    image_urls: List[str]
    description: str
    listing_date: Optional[str]
    source: str  # zillow, realtor, etc.
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None

class PropertySearchResult(BaseModel):
    """Search result container"""
    criteria: Dict
    properties: List[Dict]
    total_found: int
    search_timestamp: str
    sources_searched: List[str]

class RealEstateScraper:
    """Base class for real estate site scrapers"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    async def search_properties(self, criteria: PropertyCriteria) -> List[Property]:
        """Override in subclasses"""
        raise NotImplementedError

class ZillowScraper(RealEstateScraper):
    """Zillow property scraper"""
    
    BASE_URL = "https://www.zillow.com"
    
    async def search_properties(self, criteria: PropertyCriteria) -> List[Property]:
        """Search Zillow for properties matching criteria"""
        try:
            # Build search URL
            search_url = self._build_search_url(criteria)
            
            # Make request
            response = await self.session.get(search_url)
            response.raise_for_status()
            
            # Parse results
            properties = self._parse_search_results(response.text, criteria)
            return properties[:20]  # Limit to 20 results
            
        except Exception as e:
            logger.error(f"Zillow search error: {str(e)}")
            return []
    
    def _build_search_url(self, criteria: PropertyCriteria) -> str:
        """Build Zillow search URL from criteria"""
        base = f"{self.BASE_URL}/homes/"
        location = criteria.location.replace(' ', '-').replace(',', '')
        url = f"{base}{location}_rb/"
        
        params = []
        if criteria.min_price:
            params.append(f"pricem_min={criteria.min_price}")
        if criteria.max_price:
            params.append(f"pricem_max={criteria.max_price}")
        if criteria.bedrooms:
            params.append(f"beds_min={criteria.bedrooms}")
        if criteria.bathrooms:
            params.append(f"baths_min={criteria.bathrooms}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def _parse_search_results(self, html: str, criteria: PropertyCriteria) -> List[Property]:
        """Parse Zillow search results HTML"""
        properties = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find property cards (this is a simplified approach)
        property_cards = soup.find_all('div', {'data-test': 'property-card'})
        
        for card in property_cards[:20]:  # Limit results
            try:
                property_data = self._extract_property_data(card)
                if property_data:
                    properties.append(property_data)
            except Exception as e:
                logger.warning(f"Error parsing Zillow property: {str(e)}")
                continue
        
        return properties
    
    def _extract_property_data(self, card) -> Optional[Property]:
        """Extract property data from a Zillow card element"""
        try:
            # This is a simplified extraction - would need to be updated based on actual HTML structure
            address_elem = card.find('address')
            price_elem = card.find('span', {'data-test': 'property-card-price'})
            details_elem = card.find('ul', {'data-test': 'property-card-details'})
            link_elem = card.find('a', {'data-test': 'property-card-link'})
            
            if not all([address_elem, price_elem, link_elem]):
                return None
            
            # Extract basic info
            address = address_elem.get_text().strip()
            price_text = price_elem.get_text().strip()
            price = int(re.sub(r'[^\d]', '', price_text)) if price_text else 0
            
            # Extract details
            bedrooms = bathrooms = square_feet = None
            if details_elem:
                details_text = details_elem.get_text()
                bed_match = re.search(r'(\d+)\s*bed', details_text)
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', details_text)
                sqft_match = re.search(r'([\d,]+)\s*sqft', details_text)
                
                if bed_match:
                    bedrooms = int(bed_match.group(1))
                if bath_match:
                    bathrooms = float(bath_match.group(1))
                if sqft_match:
                    square_feet = int(sqft_match.group(1).replace(',', ''))
            
            # Build property object
            return Property(
                id=f"zillow_{uuid.uuid4().hex[:8]}",
                address=address,
                city="",  # Would extract from address
                state="",  # Would extract from address
                zip_code="",  # Would extract from address
                price=price,
                bedrooms=bedrooms or 0,
                bathrooms=bathrooms or 0,
                square_feet=square_feet,
                lot_size=None,
                property_type="house",  # Would extract from data
                listing_url=f"{self.BASE_URL}{link_elem.get('href')}",
                image_urls=[],  # Would extract from image elements
                description="",  # Would extract from detail page
                listing_date=None,
                source="zillow"
            )
            
        except Exception as e:
            logger.warning(f"Error extracting Zillow property data: {str(e)}")
            return None

class RealtorScraper(RealEstateScraper):
    """Realtor.com property scraper"""
    
    BASE_URL = "https://www.realtor.com"
    
    async def search_properties(self, criteria: PropertyCriteria) -> List[Property]:
        """Search Realtor.com for properties matching criteria"""
        try:
            search_url = self._build_search_url(criteria)
            response = await self.session.get(search_url)
            response.raise_for_status()
            
            properties = self._parse_search_results(response.text, criteria)
            return properties[:20]
            
        except Exception as e:
            logger.error(f"Realtor.com search error: {str(e)}")
            return []
    
    def _build_search_url(self, criteria: PropertyCriteria) -> str:
        """Build Realtor.com search URL"""
        location = criteria.location.replace(' ', '%20')
        url = f"{self.BASE_URL}/realestateandhomes-search/{location}"
        
        params = []
        if criteria.min_price:
            params.append(f"price-min={criteria.min_price}")
        if criteria.max_price:
            params.append(f"price-max={criteria.max_price}")
        if criteria.bedrooms:
            params.append(f"beds-min={criteria.bedrooms}")
        if criteria.bathrooms:
            params.append(f"baths-min={criteria.bathrooms}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def _parse_search_results(self, html: str, criteria: PropertyCriteria) -> List[Property]:
        """Parse Realtor.com search results"""
        # Similar implementation to Zillow but adapted for Realtor.com structure
        properties = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find property listings (simplified approach)
        property_cards = soup.find_all('div', class_=re.compile(r'property|listing'))
        
        for card in property_cards[:20]:
            try:
                property_data = self._extract_realtor_property(card)
                if property_data:
                    properties.append(property_data)
            except Exception:
                continue
        
        return properties
    
    def _extract_realtor_property(self, card) -> Optional[Property]:
        """Extract property data from Realtor.com card"""
        # Simplified extraction - would need actual HTML structure analysis
        try:
            return Property(
                id=f"realtor_{uuid.uuid4().hex[:8]}",
                address="Sample Address",
                city="Sample City",
                state="CA",
                zip_code="12345",
                price=500000,
                bedrooms=3,
                bathrooms=2.0,
                square_feet=1500,
                lot_size=0.25,
                property_type="house",
                listing_url=f"{self.BASE_URL}/sample",
                image_urls=[],
                description="Sample property from Realtor.com",
                listing_date=None,
                source="realtor"
            )
        except Exception:
            return None

class PropertySearchAgent:
    """Main property search agent"""
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.db_url = os.getenv('DATABASE_URL', '')
        
        # Initialize scrapers
        self.scrapers = {
            'zillow': ZillowScraper(),
            'realtor': RealtorScraper(),
        }
        
        # RealConnect API endpoints
        self.realconnect_base = "https://realconnect.online"
    
    async def get_buyer_criteria(self) -> Optional[PropertyCriteria]:
        """Fetch buyer criteria from realconnect.online/buyer"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.realconnect_base}/buyer")
                if response.status_code == 200:
                    data = response.json()
                    return PropertyCriteria(
                        location=data.get('location', ''),
                        min_price=data.get('min_price'),
                        max_price=data.get('max_price'),
                        bedrooms=data.get('bedrooms'),
                        bathrooms=data.get('bathrooms'),
                        property_type=data.get('property_type'),
                        square_feet_min=data.get('square_feet_min'),
                        square_feet_max=data.get('square_feet_max'),
                        keywords=data.get('keywords', [])
                    )
        except Exception as e:
            logger.error(f"Error fetching buyer criteria: {str(e)}")
        return None
    
    async def get_seller_criteria(self) -> Optional[PropertyCriteria]:
        """Fetch seller criteria from realconnect.online/seller"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.realconnect_base}/seller")
                if response.status_code == 200:
                    data = response.json()
                    return PropertyCriteria(
                        location=data.get('location', ''),
                        min_price=data.get('min_price'),
                        max_price=data.get('max_price'),
                        bedrooms=data.get('bedrooms'),
                        bathrooms=data.get('bathrooms'),
                        property_type=data.get('property_type'),
                        square_feet_min=data.get('square_feet_min'),
                        square_feet_max=data.get('square_feet_max'),
                        keywords=data.get('keywords', [])
                    )
        except Exception as e:
            logger.error(f"Error fetching seller criteria: {str(e)}")
        return None
    
    async def search_properties(self, criteria: PropertyCriteria) -> PropertySearchResult:
        """Search all real estate sites for properties matching criteria"""
        all_properties = []
        sources_searched = []
        
        # Search all scrapers in parallel
        tasks = []
        for source_name, scraper in self.scrapers.items():
            tasks.append(self._search_with_scraper(source_name, scraper, criteria))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for source_name, result in zip(self.scrapers.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error searching {source_name}: {str(result)}")
                continue
            
            all_properties.extend(result)
            sources_searched.append(source_name)
        
        # Remove duplicates and sort by price
        unique_properties = self._deduplicate_properties(all_properties)
        unique_properties.sort(key=lambda p: p.price)
        
        # Convert to dict format
        properties_dict = [self._property_to_dict(p) for p in unique_properties]
        
        return PropertySearchResult(
            criteria=self._criteria_to_dict(criteria),
            properties=properties_dict,
            total_found=len(properties_dict),
            search_timestamp=datetime.now().isoformat(),
            sources_searched=sources_searched
        )
    
    async def _search_with_scraper(self, source_name: str, scraper: RealEstateScraper, criteria: PropertyCriteria) -> List[Property]:
        """Search with a single scraper"""
        try:
            return await scraper.search_properties(criteria)
        except Exception as e:
            logger.error(f"Error searching {source_name}: {str(e)}")
            return []
    
    def _deduplicate_properties(self, properties: List[Property]) -> List[Property]:
        """Remove duplicate properties based on address similarity"""
        unique = []
        seen_addresses = set()
        
        for prop in properties:
            # Simple deduplication by normalized address
            normalized_addr = re.sub(r'[^\w\s]', '', prop.address.lower()).strip()
            if normalized_addr not in seen_addresses:
                unique.append(prop)
                seen_addresses.add(normalized_addr)
        
        return unique
    
    def _property_to_dict(self, prop: Property) -> Dict:
        """Convert Property to dictionary"""
        return {
            'id': prop.id,
            'address': prop.address,
            'city': prop.city,
            'state': prop.state,
            'zip_code': prop.zip_code,
            'price': prop.price,
            'bedrooms': prop.bedrooms,
            'bathrooms': prop.bathrooms,
            'square_feet': prop.square_feet,
            'lot_size': prop.lot_size,
            'property_type': prop.property_type,
            'listing_url': prop.listing_url,
            'image_urls': prop.image_urls,
            'description': prop.description,
            'listing_date': prop.listing_date,
            'source': prop.source,
            'agent_name': prop.agent_name,
            'agent_phone': prop.agent_phone
        }
    
    def _criteria_to_dict(self, criteria: PropertyCriteria) -> Dict:
        """Convert PropertyCriteria to dictionary"""
        return {
            'location': criteria.location,
            'min_price': criteria.min_price,
            'max_price': criteria.max_price,
            'bedrooms': criteria.bedrooms,
            'bathrooms': criteria.bathrooms,
            'property_type': criteria.property_type,
            'square_feet_min': criteria.square_feet_min,
            'square_feet_max': criteria.square_feet_max,
            'lot_size_min': criteria.lot_size_min,
            'keywords': criteria.keywords
        }
    
    async def analyze_properties_with_ai(self, search_result: PropertySearchResult) -> Dict:
        """Use AI to analyze and rank properties"""
        try:
            context = {
                'criteria': search_result.criteria,
                'properties': search_result.properties[:10],  # Limit for token usage
                'total_found': search_result.total_found
            }
            
            prompt = f"""You are a real estate expert analyzing property search results.
            
            Search Criteria: {json.dumps(search_result.criteria, indent=2)}
            
            Properties Found: {json.dumps(search_result.properties[:5], indent=2)}
            
            Please provide:
            1. Analysis of how well these properties match the criteria
            2. Top 3 property recommendations with reasons
            3. Market insights based on the results
            4. Suggestions for refining the search criteria
            
            Respond in JSON format with analysis, recommendations, and insights."""
            
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=2000
            )
            
            analysis_text = response.content[0].text
            
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                analysis = {'analysis': analysis_text, 'recommendations': [], 'insights': ''}
            
            return {
                'ai_analysis': analysis,
                'search_result': search_result.dict(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                'error': str(e),
                'search_result': search_result.dict(),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_buyer_search(self) -> Dict:
        """Run property search for buyer criteria"""
        criteria = await self.get_buyer_criteria()
        if not criteria:
            return {'error': 'Could not fetch buyer criteria'}
        
        search_result = await self.search_properties(criteria)
        return await self.analyze_properties_with_ai(search_result)
    
    async def run_seller_search(self) -> Dict:
        """Run property search for seller criteria (market analysis)"""
        criteria = await self.get_seller_criteria()
        if not criteria:
            return {'error': 'Could not fetch seller criteria'}
        
        search_result = await self.search_properties(criteria)
        return await self.analyze_properties_with_ai(search_result)

async def main():
    """Test the property search agent"""
    agent = PropertySearchAgent()
    
    # Test with sample criteria
    test_criteria = PropertyCriteria(
        location="San Francisco, CA",
        min_price=500000,
        max_price=1000000,
        bedrooms=2,
        bathrooms=2,
        property_type="condo"
    )
    
    print("Searching properties...")
    result = await agent.search_properties(test_criteria)
    
    print(f"Found {result.total_found} properties from sources: {result.sources_searched}")
    
    # Analyze with AI
    analysis = await agent.analyze_properties_with_ai(result)
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    asyncio.run(main())