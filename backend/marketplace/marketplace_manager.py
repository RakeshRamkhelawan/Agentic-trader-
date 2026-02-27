"""Strategy marketplace management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from collections import defaultdict


class ListingStatus(Enum):
    """Strategy listing statuses."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class PricingType(Enum):
    """Strategy pricing models."""
    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    PERFORMANCE_FEE = "performance_fee"


@dataclass
class StrategyListing:
    """A strategy listed on the marketplace."""
    id: str
    name: str
    description: str
    author_id: str
    author_name: str
    
    # Strategy details
    strategy_code: str
    language: str  # python, javascript, etc.
    tags: List[str] = field(default_factory=list)
    
    # Status and pricing
    status: ListingStatus = ListingStatus.DRAFT
    pricing_type: PricingType = PricingType.FREE
    price: float = 0.0  # For one-time or subscription
    performance_fee_percent: float = 0.0  # For performance-based
    
    # Stats
    downloads: int = 0
    active_users: int = 0
    total_revenue: float = 0.0
    
    # Ratings
    rating_avg: float = 0.0
    rating_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author": {
                "id": self.author_id,
                "name": self.author_name,
            },
            "language": self.language,
            "tags": self.tags,
            "status": self.status.value,
            "pricing": {
                "type": self.pricing_type.value,
                "price": self.price,
                "performance_fee": self.performance_fee_percent,
            },
            "stats": {
                "downloads": self.downloads,
                "active_users": self.active_users,
                "total_revenue": self.total_revenue,
                "rating_avg": round(self.rating_avg, 2),
                "rating_count": self.rating_count,
            },
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Review:
    """A marketplace review."""
    id: str
    listing_id: str
    user_id: str
    user_name: str
    rating: int  # 1-5
    title: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    helpful_count: int = 0


class MarketplaceManager:
    """
    Strategy marketplace for developers.
    
    Allows developers to:
    - Publish trading strategies
    - Set pricing (free, one-time, subscription, performance-based)
    - Track downloads and revenue
    - Receive ratings and reviews
    """
    
    def __init__(self):
        self._listings: Dict[str, StrategyListing] = {}
        self._reviews: Dict[str, List[Review]] = defaultdict(list)
        self._author_listings: Dict[str, List[str]] = defaultdict(list)
        self._tag_index: Dict[str, List[str]] = defaultdict(list)
    
    def create_listing(
        self,
        name: str,
        description: str,
        author_id: str,
        author_name: str,
        strategy_code: str,
        language: str,
        tags: List[str],
        pricing_type: PricingType = PricingType.FREE,
        price: float = 0.0,
    ) -> StrategyListing:
        """Create a new strategy listing."""
        import uuid
        
        listing_id = str(uuid.uuid4())
        
        listing = StrategyListing(
            id=listing_id,
            name=name,
            description=description,
            author_id=author_id,
            author_name=author_name,
            strategy_code=strategy_code,
            language=language,
            tags=tags,
            pricing_type=pricing_type,
            price=price,
        )
        
        self._listings[listing_id] = listing
        self._author_listings[author_id].append(listing_id)
        
        # Index by tags
        for tag in tags:
            self._tag_index[tag.lower()].append(listing_id)
        
        return listing
    
    def get_listing(self, listing_id: str) -> Optional[StrategyListing]:
        """Get listing by ID."""
        return self._listings.get(listing_id)
    
    def search_listings(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        pricing_type: Optional[PricingType] = None,
        min_rating: float = 0.0,
        sort_by: str = "downloads",
        limit: int = 20,
    ) -> List[StrategyListing]:
        """Search marketplace listings."""
        results = list(self._listings.values())
        
        # Filter by status (only show published)
        results = [l for l in results if l.status == ListingStatus.PUBLISHED]
        
        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                l for l in results
                if query_lower in l.name.lower()
                or query_lower in l.description.lower()
            ]
        
        # Filter by tags
        if tags:
            tag_set = set(t.lower() for t in tags)
            results = [
                l for l in results
                if tag_set & set(t.lower() for t in l.tags)
            ]
        
        # Filter by pricing
        if pricing_type:
            results = [l for l in results if l.pricing_type == pricing_type]
        
        # Filter by rating
        if min_rating > 0:
            results = [l for l in results if l.rating_avg >= min_rating]
        
        # Sort
        if sort_by == "downloads":
            results.sort(key=lambda l: l.downloads, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda l: l.rating_avg, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda l: l.created_at, reverse=True)
        elif sort_by == "revenue":
            results.sort(key=lambda l: l.total_revenue, reverse=True)
        
        return results[:limit]
    
    def publish_listing(self, listing_id: str) -> Optional[StrategyListing]:
        """Publish a listing (after review)."""
        listing = self._listings.get(listing_id)
        if listing and listing.status == ListingStatus.PENDING_REVIEW:
            listing.status = ListingStatus.PUBLISHED
            listing.published_at = datetime.utcnow()
            return listing
        return None
    
    def record_download(self, listing_id: str, user_id: str) -> bool:
        """Record a strategy download."""
        listing = self._listings.get(listing_id)
        if listing:
            listing.downloads += 1
            listing.active_users += 1
            return True
        return False
    
    def add_review(
        self,
        listing_id: str,
        user_id: str,
        user_name: str,
        rating: int,
        title: str,
        content: str,
    ) -> Optional[Review]:
        """Add a review to a listing."""
        listing = self._listings.get(listing_id)
        if not listing:
            return None
        
        import uuid
        review = Review(
            id=str(uuid.uuid4()),
            listing_id=listing_id,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            title=title,
            content=content,
        )
        
        self._reviews[listing_id].append(review)
        
        # Update listing rating
        reviews = self._reviews[listing_id]
        listing.rating_count = len(reviews)
        listing.rating_avg = sum(r.rating for r in reviews) / len(reviews)
        
        return review
    
    def get_author_stats(self, author_id: str) -> Dict[str, Any]:
        """Get marketplace stats for an author."""
        listing_ids = self._author_listings.get(author_id, [])
        listings = [self._listings[lid] for lid in listing_ids]
        
        return {
            "author_id": author_id,
            "total_listings": len(listings),
            "published_listings": len([l for l in listings if l.status == ListingStatus.PUBLISHED]),
            "total_downloads": sum(l.downloads for l in listings),
            "total_revenue": sum(l.total_revenue for l in listings),
            "average_rating": (
                sum(l.rating_avg for l in listings) / len(listings)
                if listings else 0
            ),
        }
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get overall marketplace statistics."""
        listings = list(self._listings.values())
        
        return {
            "total_listings": len(listings),
            "published_listings": len([l for l in listings if l.status == ListingStatus.PUBLISHED]),
            "total_downloads": sum(l.downloads for l in listings),
            "total_revenue": sum(l.total_revenue for l in listings),
            "total_authors": len(self._author_listings),
            "average_listing_price": (
                sum(l.price for l in listings if l.pricing_type == PricingType.ONE_TIME)
                / len([l for l in listings if l.pricing_type == PricingType.ONE_TIME])
                if any(l.pricing_type == PricingType.ONE_TIME for l in listings)
                else 0
            ),
            "top_tags": self._get_top_tags(),
        }
    
    def _get_top_tags(self, limit: int = 10) -> List[tuple]:
        """Get most popular tags."""
        tag_counts = [(tag, len(listings)) for tag, listings in self._tag_index.items()]
        tag_counts.sort(key=lambda x: x[1], reverse=True)
        return tag_counts[:limit]


# Global marketplace manager
marketplace_manager = MarketplaceManager()
