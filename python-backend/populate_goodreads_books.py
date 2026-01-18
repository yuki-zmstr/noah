#!/usr/bin/env python3
"""
Script to populate the database with top 10 books from Goodreads 2025 popular books.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import uuid
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database import get_db
from src.models.content import ContentItem
from src.schemas.content import ContentAnalysis, ContentMetadata
from src.services.content_processor import content_processor

# Top 10 books from Goodreads 2025 popular books
GOODREADS_BOOKS = [
    {
        "title": "Onyx Storm",
        "author": "Rebecca Yarros",
        "description": "After nearly eighteen months at Basgiath War College, Violet Sorrengail knows there's no more time for lessons. No more time for uncertainty. Because the battle has truly begun, and with enemies closing in from outside their walls and within their ranks, it's impossible to know who to trust. Now Violet must journey beyond the failing Aretian wards to seek allies from unfamiliar lands to stand with Navarre.",
        "genre": "Fantasy Romance",
        "series": "Fourth Wing",
        "estimated_pages": 650,
        "language": "english"
    },
    {
        "title": "Sunrise on the Reaping",
        "author": "Suzanne Collins",
        "description": "The phenomenal fifth book in the Hunger Games series! When you've been set up to lose everything you love, what is there left to fight for? As the day dawns on the fiftieth annual Hunger Games, fear grips the districts of Panem. This year, in honor of the Quarter Quell, twice as many tributes will be taken from their homes.",
        "genre": "Dystopian Fiction",
        "series": "The Hunger Games",
        "estimated_pages": 400,
        "language": "english"
    },
    {
        "title": "People We Meet on Vacation",
        "author": "Emily Henry",
        "description": "Two writers compete for the chance to tell the larger-than-life story of a woman with more than a couple of plot twists up her sleeve. Alice Scott is an eternal optimist still dreaming of her big writing break. Hayden Anderson is a Pulitzer-prize winning human thundercloud. And they're both on balmy Little Crescent Island for the same reason.",
        "genre": "Contemporary Romance",
        "series": None,
        "estimated_pages": 350,
        "language": "english"
    },
    {
        "title": "Atmosphere",
        "author": "Taylor Jenkins Reid",
        "description": "Joan Goodwin has been obsessed with the stars for as long as she can remember. Selected from a pool of thousands of applicants in the summer of 1980, Joan begins training at Houston's Johnson Space Center, alongside an exceptional group of fellow candidates. Fast-paced, thrilling, and emotional, Atmosphere is Taylor Jenkins Reid at her best.",
        "genre": "Historical Fiction",
        "series": None,
        "estimated_pages": 420,
        "language": "english"
    },
    {
        "title": "The Locked Door",
        "author": "Freida McFadden",
        "description": "A brand new psychological thriller from #1 New York Times bestselling author Freida McFadden! Tegan is eight months pregnant, alone, and desperately wants to put her crumbling life in the rearview mirror. Stranded in rural Maine with a dead car and broken ankle, Tegan worries she's made a terrible mistake.",
        "genre": "Psychological Thriller",
        "series": None,
        "estimated_pages": 300,
        "language": "english"
    },
    {
        "title": "The Winners",
        "author": "Fredrik Backman",
        "description": "#1 New York Times bestselling author Fredrik Backman returns with an unforgettably funny, deeply moving tale of four teenagers whose friendship creates a bond so powerful that it changes a complete stranger's life twenty-five years later. Most people don't even notice them—three tiny figures sitting at the end of a long pier.",
        "genre": "Literary Fiction",
        "series": "Beartown",
        "estimated_pages": 480,
        "language": "english"
    },
    {
        "title": "The Roommate",
        "author": "Freida McFadden",
        "description": "There's no place like home… Blake Porter is riding high, until he's not. Fired abruptly from his job and unable to make mortgage payments, he's desperate to make ends meet. Enter Whitney. Beautiful, charming, down-to-earth, and looking for a room to rent. But something isn't quite right.",
        "genre": "Psychological Thriller",
        "series": None,
        "estimated_pages": 280,
        "language": "english"
    },
    {
        "title": "Broken Country",
        "author": "Fiona McFarlane",
        "description": "Beth and her gentle, kind husband Frank are happily married, but their relationship relies on the past staying buried. A sweeping love story with the pace and twists of a thriller, Broken Country is a novel of simmering passion, impossible choices, and explosive consequences.",
        "genre": "Literary Thriller",
        "series": None,
        "estimated_pages": 380,
        "language": "english"
    },
    {
        "title": "Love, Theoretically",
        "author": "Ali Hazelwood",
        "description": "A competitive diver and an ace swimmer jump into forbidden waters in this steamy college romance. Scarlett Vandermeer is swimming upstream. A Junior at Stanford and a student-athlete who specializes in platform diving, Scarlett prefers to keep her head down, concentrating on getting into med school.",
        "genre": "Contemporary Romance",
        "series": None,
        "estimated_pages": 320,
        "language": "english"
    },
    {
        "title": "Wild Dark Shore",
        "author": "Charlotte McConaghy",
        "description": "A family on a remote island. A mysterious woman washed ashore. A rising storm on the horizon. Dominic Salt and his three children are caretakers of Shearwater, a tiny island not far from Antarctica. A novel of breathtaking twists, dizzying beauty, and ferocious love.",
        "genre": "Literary Fiction",
        "series": None,
        "estimated_pages": 360,
        "language": "english"
    }
]

def calculate_reading_time(pages: int) -> int:
    """Calculate estimated reading time in minutes based on page count."""
    # Average reading speed: 250 words per minute
    # Average words per page: 250-300
    words_per_page = 275
    words_per_minute = 250
    
    total_words = pages * words_per_page
    reading_time_minutes = total_words / words_per_minute
    
    return int(reading_time_minutes)

def create_sample_content(title: str, description: str, pages: int) -> str:
    """Create sample content for analysis based on description and genre."""
    # Create a more substantial sample for better analysis
    sample_content = f"""
    {title}
    
    {description}
    
    This compelling narrative explores themes of human connection, resilience, and the power of storytelling. 
    The author masterfully weaves together character development and plot progression, creating an engaging 
    reading experience that resonates with readers across different backgrounds.
    
    The story delves into complex relationships and emotional journeys, offering insights into the human 
    condition while maintaining an accessible writing style. Through vivid descriptions and authentic 
    dialogue, the narrative brings characters to life and immerses readers in the world created by the author.
    
    With its blend of compelling storytelling and thoughtful exploration of universal themes, this work 
    stands as a testament to the enduring power of literature to both entertain and enlighten readers.
    """
    
    return sample_content.strip()

def get_topics_from_genre(genre: str) -> list:
    """Map genre to relevant topics for content analysis."""
    genre_topic_mapping = {
        "Fantasy Romance": ["fantasy", "romance", "magic", "relationships"],
        "Dystopian Fiction": ["dystopia", "society", "politics", "survival"],
        "Contemporary Romance": ["romance", "relationships", "contemporary", "love"],
        "Historical Fiction": ["history", "historical", "period", "culture"],
        "Psychological Thriller": ["psychology", "thriller", "suspense", "mystery"],
        "Literary Fiction": ["literary", "character_study", "human_nature", "society"],
        "Literary Thriller": ["literary", "thriller", "suspense", "character_study"]
    }
    
    topics = genre_topic_mapping.get(genre, ["fiction", "literature"])
    return [{"topic": topic, "confidence": 0.8} for topic in topics]

def create_content_analysis(book_data: dict, content: str) -> dict:
    """Create content analysis for a book."""
    pages = book_data["estimated_pages"]
    reading_time = calculate_reading_time(pages)
    
    # Estimate reading level based on genre and description complexity
    genre = book_data["genre"]
    description_length = len(book_data["description"])
    
    # Base reading level calculation
    if "Romance" in genre or "Contemporary" in genre:
        base_level = 7.5
    elif "Literary" in genre:
        base_level = 9.5
    elif "Thriller" in genre or "Fantasy" in genre:
        base_level = 8.0
    elif "Historical" in genre:
        base_level = 8.5
    else:
        base_level = 8.0
    
    # Adjust based on description complexity
    if description_length > 400:
        base_level += 0.5
    elif description_length < 200:
        base_level -= 0.5
    
    analysis = {
        "topics": get_topics_from_genre(genre),
        "reading_level": {
            "flesch_kincaid": round(base_level, 1),
            "estimated_grade": int(base_level)
        },
        "complexity": {
            "overall": min(0.9, max(0.3, (base_level - 6) / 6)),
            "vocabulary": min(0.9, max(0.3, (base_level - 5) / 8)),
            "sentence_structure": min(0.9, max(0.3, (base_level - 6) / 7))
        },
        "key_phrases": [
            book_data["title"].lower(),
            book_data["author"].lower(),
            genre.lower()
        ],
        "sentiment": {
            "overall": 0.6,
            "emotional_intensity": 0.7 if "Romance" in genre or "Thriller" in genre else 0.5
        },
        "embedding": [0.1] * 1536  # Placeholder embedding vector
    }
    
    return analysis

def create_content_metadata(book_data: dict) -> dict:
    """Create content metadata for a book."""
    reading_time = calculate_reading_time(book_data["estimated_pages"])
    
    metadata = {
        "author": book_data["author"],
        "genre": book_data["genre"],
        "series": book_data.get("series"),
        "estimated_reading_time": reading_time,
        "page_count": book_data["estimated_pages"],
        "content_type": "book",
        "publication_year": 2025,
        "source": "goodreads_popular_2025",
        "tags": [
            book_data["genre"].lower().replace(" ", "_"),
            "popular_2025",
            "goodreads"
        ],
        "difficulty_level": "intermediate",
        "target_audience": "adult"
    }
    
    return metadata

def populate_books():
    """Populate the database with Goodreads books."""
    print("Starting to populate database with Goodreads 2025 popular books...")
    
    try:
        db = next(get_db())
        
        # Check if books already exist
        existing_count = db.query(ContentItem).count()
        print(f"Current content items in database: {existing_count}")
        
        added_count = 0
        
        for i, book_data in enumerate(GOODREADS_BOOKS, 1):
            print(f"\nProcessing book {i}/10: {book_data['title']}")
            
            # Generate unique ID
            content_id = f"goodreads_2025_{i:02d}_{book_data['title'].lower().replace(' ', '_').replace(',', '')}"
            
            # Check if book already exists
            existing_book = db.query(ContentItem).filter(ContentItem.id == content_id).first()
            if existing_book:
                print(f"  ✓ Book already exists: {book_data['title']}")
                continue
            
            # Create sample content for analysis
            sample_content = create_sample_content(
                book_data["title"], 
                book_data["description"], 
                book_data["estimated_pages"]
            )
            
            # Create analysis and metadata
            analysis = create_content_analysis(book_data, sample_content)
            metadata = create_content_metadata(book_data)
            
            # Create ContentItem
            content_item = ContentItem(
                id=content_id,
                title=book_data["title"],
                content=sample_content,
                language=book_data["language"],
                content_metadata=metadata,
                analysis=analysis,
                adaptations=[],  # No adaptations for now
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(content_item)
            added_count += 1
            print(f"  ✓ Added: {book_data['title']} by {book_data['author']}")
        
        # Commit all changes
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"Successfully added {added_count} new books to the database!")
        print(f"Total content items now: {existing_count + added_count}")
        print(f"{'='*60}")
        
        # Display summary
        print("\nAdded books:")
        for i, book_data in enumerate(GOODREADS_BOOKS, 1):
            print(f"{i:2d}. {book_data['title']} - {book_data['author']} ({book_data['genre']})")
        
        print(f"\nBooks are now available for the recommendation engine!")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    populate_books()