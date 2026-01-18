#!/usr/bin/env python3
"""
Script to populate the database with top books from Japanese bookstore rankings (2026年1月第1週).
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

# Top books from each category across Japanese bookstores (2026年1月第1週)
JAPANESE_TOP_BOOKS = [
    # Business/Management
    {
        "title": "社長がつまずくすべての疑問に答える本",
        "title_english": "The Book That Answers All Questions CEOs Stumble On",
        "author": "田中修治",
        "author_english": "Tanaka Shuji",
        "publisher": "KADOKAWA",
        "description": "経営者が直面する様々な課題と疑問に対する実践的な解決策を提供する経営指南書。リーダーシップ、組織運営、戦略立案など、CEOが日々直面する問題への具体的なアドバイスを収録。",
        "description_english": "A practical management guide providing solutions to various challenges and questions faced by business leaders. Contains specific advice on leadership, organizational management, strategic planning, and daily problems encountered by CEOs.",
        "genre": "Business Management",
        "category": "ビジネス（経営）",
        "estimated_pages": 280,
        "language": "japanese"
    },
    # Self-Development
    {
        "title": "ニュー・エリート論",
        "title_english": "New Elite Theory",
        "author": "布留川勝",
        "author_english": "Furukawa Masaru",
        "publisher": "PHP研究所",
        "description": "現代社会における新しいエリート像を提示し、従来の成功モデルを超えた人材育成論を展開。変化する時代に求められるリーダーシップと能力開発について論じる。",
        "description_english": "Presents a new image of elites in modern society and develops human resource development theory that goes beyond conventional success models. Discusses leadership and capability development required in changing times.",
        "genre": "Self-Development",
        "category": "ビジネス（自己啓発）",
        "estimated_pages": 240,
        "language": "japanese"
    },
    # Economics/Finance
    {
        "title": "今さら聞けない投資の超基本",
        "title_english": "Investment Super Basics You Can't Ask About Now",
        "author": "泉美智子・奥村彰太郎",
        "author_english": "Izumi Michiko, Okumura Shotaro",
        "publisher": "朝日新聞出版",
        "description": "投資初心者向けの基礎知識から実践的な投資戦略まで、わかりやすく解説した投資入門書。株式、債券、投資信託など様々な投資商品について基本から学べる。",
        "description_english": "An investment primer that clearly explains everything from basic knowledge for investment beginners to practical investment strategies. Learn the basics of various investment products including stocks, bonds, and mutual funds.",
        "genre": "Finance",
        "category": "経済・金融",
        "estimated_pages": 220,
        "language": "japanese"
    },
    # Non-fiction
    {
        "title": "「偶然」はどのようにあなたをつくるのか",
        "title_english": "How 'Coincidence' Shapes You",
        "author": "ブライアン・クラース",
        "author_english": "Brian Klaas",
        "publisher": "東洋経済新報社",
        "description": "偶然の出来事が人生に与える影響について科学的に分析し、運命と偶然の関係性を探る。カオス理論や複雑系科学の視点から、人生における偶然の意味を考察する。",
        "description_english": "Scientifically analyzes the impact of chance events on life and explores the relationship between fate and coincidence. Examines the meaning of chance in life from the perspective of chaos theory and complexity science.",
        "genre": "Science",
        "category": "ノンフィクション",
        "estimated_pages": 320,
        "language": "japanese"
    },
    # Literature/Fiction
    {
        "title": "成瀬は都を駆け抜ける",
        "title_english": "Naruse Runs Through the Capital",
        "author": "宮島未奈",
        "author_english": "Miyajima Mina",
        "publisher": "新潮社",
        "description": "現代を生きる若者の心情を繊細に描いた青春小説。主人公成瀬の成長と葛藤を通して、現代社会の中で自分らしく生きることの意味を問いかける作品。",
        "description_english": "A coming-of-age novel that delicately depicts the emotions of young people living in modern times. Through the growth and struggles of protagonist Naruse, the work questions the meaning of living authentically in contemporary society.",
        "genre": "Contemporary Fiction",
        "category": "文芸",
        "estimated_pages": 280,
        "language": "japanese"
    },
    # New Books (Shinsho)
    {
        "title": "世界秩序が変わるとき",
        "title_english": "When World Order Changes",
        "author": "齋藤ジン",
        "author_english": "Saito Jin",
        "publisher": "文藝春秋",
        "description": "国際政治の変動期における世界秩序の変化を分析し、日本の立ち位置と今後の戦略について考察する。地政学的な視点から現代の国際情勢を読み解く。",
        "description_english": "Analyzes changes in world order during periods of international political upheaval and examines Japan's position and future strategies. Interprets contemporary international situations from a geopolitical perspective.",
        "genre": "International Relations",
        "category": "新書",
        "estimated_pages": 200,
        "language": "japanese"
    },
    # Paperback (Bunko)
    {
        "title": "BUTTER",
        "title_english": "BUTTER",
        "author": "柚木麻子",
        "author_english": "Yuzuki Asako",
        "publisher": "新潮社",
        "description": "殺人事件を起こした女性を取材する女性記者の物語。食と欲望、女性の生き方をテーマに、現代社会の闇と光を描いた話題作。",
        "description_english": "The story of a female journalist interviewing a woman who committed murder. A topical work that depicts the darkness and light of modern society, themed around food, desire, and women's ways of living.",
        "genre": "Literary Fiction",
        "category": "文庫",
        "estimated_pages": 350,
        "language": "japanese"
    },
    # Additional top books from other stores
    {
        "title": "成長戦略型M&Aの新常識",
        "title_english": "New Common Sense of Growth Strategy M&A",
        "author": "竹内直樹",
        "author_english": "Takeuchi Naoki",
        "publisher": "日本経済新聞出版",
        "description": "企業成長戦略としてのM&Aの新しいアプローチを解説。従来の手法を超えた戦略的M&Aの実践方法と成功事例を紹介する。",
        "description_english": "Explains new approaches to M&A as corporate growth strategies. Introduces practical methods and success stories of strategic M&A that go beyond conventional approaches.",
        "genre": "Business Strategy",
        "category": "ビジネス・経済",
        "estimated_pages": 260,
        "language": "japanese"
    },
    {
        "title": "腎臓大復活",
        "title_english": "Great Kidney Revival",
        "author": "上月正博",
        "author_english": "Kozuki Masahiro",
        "publisher": "東洋経済新報社",
        "description": "腎臓の健康維持と機能回復に関する最新の医学知識を一般向けに解説。予防から治療まで、腎臓病に関する包括的な情報を提供。",
        "description_english": "Explains the latest medical knowledge about kidney health maintenance and function recovery for the general public. Provides comprehensive information about kidney disease from prevention to treatment.",
        "genre": "Health",
        "category": "ノンフィクション",
        "estimated_pages": 240,
        "language": "japanese"
    },
    {
        "title": "趣都",
        "title_english": "Capital of Taste",
        "author": "山口晃",
        "author_english": "Yamaguchi Akira",
        "publisher": "講談社",
        "description": "現代アートと伝統文化の融合をテーマにした芸術論。日本の美意識と現代社会の関係性を独自の視点で考察した作品。",
        "description_english": "An art theory themed around the fusion of contemporary art and traditional culture. A work that examines the relationship between Japanese aesthetics and modern society from a unique perspective.",
        "genre": "Art Theory",
        "category": "フィクション",
        "estimated_pages": 300,
        "language": "japanese"
    }
]

def calculate_reading_time(pages: int, language: str = "japanese") -> int:
    """Calculate estimated reading time in minutes based on page count and language."""
    if language == "japanese":
        # Japanese reading is typically slower due to kanji/hiragana/katakana
        # Average: 400-600 characters per minute
        chars_per_page = 600  # Typical for Japanese books
        chars_per_minute = 500
        
        total_chars = pages * chars_per_page
        reading_time_minutes = total_chars / chars_per_minute
    else:
        # English reading speed
        words_per_page = 275
        words_per_minute = 250
        
        total_words = pages * words_per_page
        reading_time_minutes = total_words / words_per_minute
    
    return int(reading_time_minutes)

def create_sample_content(book_data: dict) -> str:
    """Create sample content for analysis based on description and genre."""
    title = book_data["title"]
    description = book_data["description"]
    
    # Create bilingual sample content
    sample_content = f"""
    {title}
    {book_data.get('title_english', '')}
    
    {description}
    
    {book_data.get('description_english', '')}
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author's 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan's publishing industry and beloved by many readers.
    
    本書は{book_data['category']}分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the {book_data['genre']} field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.
    """
    
    return sample_content.strip()

def get_topics_from_genre(genre: str, category: str) -> list:
    """Map genre and category to relevant topics for content analysis."""
    genre_topic_mapping = {
        "Business Management": ["business", "management", "leadership", "strategy"],
        "Self-Development": ["self_improvement", "personal_development", "success", "motivation"],
        "Finance": ["finance", "investment", "money", "economics"],
        "Science": ["science", "research", "analysis", "theory"],
        "Contemporary Fiction": ["fiction", "contemporary", "japanese_literature", "society"],
        "International Relations": ["politics", "international", "geopolitics", "strategy"],
        "Literary Fiction": ["literature", "fiction", "japanese_culture", "society"],
        "Business Strategy": ["business", "strategy", "mergers", "corporate"],
        "Health": ["health", "medicine", "wellness", "medical"],
        "Art Theory": ["art", "culture", "aesthetics", "theory"]
    }
    
    # Add Japanese-specific topics
    base_topics = genre_topic_mapping.get(genre, ["japanese_literature", "culture"])
    japanese_topics = ["japanese", "japan", "contemporary_japan"]
    
    all_topics = base_topics + japanese_topics
    return [{"topic": topic, "confidence": 0.8} for topic in all_topics[:6]]  # Limit to 6 topics

def create_content_analysis(book_data: dict, content: str) -> dict:
    """Create content analysis for a Japanese book."""
    pages = book_data["estimated_pages"]
    reading_time = calculate_reading_time(pages, "japanese")
    
    # Estimate reading level for Japanese content
    genre = book_data["genre"]
    category = book_data["category"]
    
    # Base reading level calculation for Japanese
    if "ビジネス" in category or "経済" in category:
        base_level = 0.6  # Business books tend to be more complex
    elif "文芸" in category or "文庫" in category:
        base_level = 0.5  # Literature is moderately complex
    elif "新書" in category:
        base_level = 0.7  # New books (academic) are more complex
    elif "ノンフィクション" in category:
        base_level = 0.6  # Non-fiction is moderately complex
    else:
        base_level = 0.5
    
    # Adjust based on publisher (some publishers are known for more academic content)
    publisher = book_data["publisher"]
    if publisher in ["日本経済新聞出版", "東洋経済新報社"]:
        base_level += 0.1
    elif publisher in ["PHP研究所", "講談社"]:
        base_level += 0.05
    
    # Ensure level stays within bounds
    base_level = min(0.9, max(0.3, base_level))
    
    analysis = {
        "topics": get_topics_from_genre(genre, category),
        "reading_level": {
            "japanese_level": round(base_level, 2),
            "kanji_density": round(base_level * 0.8, 2),  # Estimate kanji density
            "estimated_jlpt_level": "N2" if base_level > 0.6 else "N3"
        },
        "complexity": {
            "overall": base_level,
            "vocabulary": min(0.9, base_level + 0.1),
            "sentence_structure": base_level,
            "cultural_context": 0.8  # High cultural context for Japanese books
        },
        "key_phrases": [
            book_data["title"],
            book_data["author"],
            genre.lower(),
            category
        ],
        "sentiment": {
            "overall": 0.6,
            "emotional_intensity": 0.6 if "文芸" in category else 0.5
        },
        "embedding": [0.1] * 1536  # Placeholder embedding vector
    }
    
    return analysis

def create_content_metadata(book_data: dict) -> dict:
    """Create content metadata for a Japanese book."""
    reading_time = calculate_reading_time(book_data["estimated_pages"], "japanese")
    
    metadata = {
        "author": book_data["author"],
        "author_english": book_data.get("author_english"),
        "title_english": book_data.get("title_english"),
        "publisher": book_data["publisher"],
        "genre": book_data["genre"],
        "category": book_data["category"],
        "estimated_reading_time": reading_time,
        "page_count": book_data["estimated_pages"],
        "content_type": "book",
        "publication_year": 2026,
        "source": "japanese_bookstore_rankings_2026_01",
        "tags": [
            book_data["genre"].lower().replace(" ", "_"),
            book_data["category"],
            "japanese_bestseller",
            "bookstore_ranking",
            "2026"
        ],
        "difficulty_level": "intermediate" if book_data["category"] in ["新書", "ビジネス"] else "beginner_intermediate",
        "target_audience": "adult",
        "cultural_context": "japanese",
        "ranking_position": 1,  # All these are #1 in their categories
        "ranking_source": "japanese_bookstores"
    }
    
    return metadata

def populate_japanese_books():
    """Populate the database with top Japanese books."""
    print("Starting to populate database with Japanese bookstore top books (2026年1月第1週)...")
    
    try:
        db = next(get_db())
        
        # Check if books already exist
        existing_count = db.query(ContentItem).count()
        print(f"Current content items in database: {existing_count}")
        
        added_count = 0
        
        for i, book_data in enumerate(JAPANESE_TOP_BOOKS, 1):
            print(f"\nProcessing book {i}/{len(JAPANESE_TOP_BOOKS)}: {book_data['title']}")
            
            # Generate unique ID
            title_clean = re.sub(r'[^\w\s-]', '', book_data['title']).replace(' ', '_')
            content_id = f"jp_bestseller_2026_{i:02d}_{title_clean[:30]}"
            
            # Check if book already exists
            existing_book = db.query(ContentItem).filter(ContentItem.id == content_id).first()
            if existing_book:
                print(f"  ✓ Book already exists: {book_data['title']}")
                continue
            
            # Create sample content for analysis
            sample_content = create_sample_content(book_data)
            
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
            print(f"  ✓ Added: {book_data['title']} by {book_data['author']} ({book_data['category']})")
        
        # Commit all changes
        db.commit()
        
        print(f"\n{'='*80}")
        print(f"Successfully added {added_count} new Japanese books to the database!")
        print(f"Total content items now: {existing_count + added_count}")
        print(f"{'='*80}")
        
        # Display summary by category
        print("\nAdded books by category:")
        categories = {}
        for book_data in JAPANESE_TOP_BOOKS:
            category = book_data['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(book_data)
        
        for category, books in categories.items():
            print(f"\n{category}:")
            for book in books:
                print(f"  • {book['title']} - {book['author']} ({book['publisher']})")
        
        print(f"\nJapanese books are now available for the recommendation engine!")
        print("These books represent the top sellers across major Japanese bookstores.")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    populate_japanese_books()