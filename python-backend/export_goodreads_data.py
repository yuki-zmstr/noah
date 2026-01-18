#!/usr/bin/env python3
"""
Export Goodreads books data from local database to SQL format for production.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database import get_db
from src.models.content import ContentItem

def escape_sql_string(text):
    """Escape single quotes in SQL strings."""
    if text is None:
        return 'NULL'
    return "'" + str(text).replace("'", "''") + "'"

def format_json_for_sql(json_data):
    """Format JSON data for SQL insertion."""
    if json_data is None:
        return 'NULL'
    return "'" + json.dumps(json_data).replace("'", "''") + "'"

def export_goodreads_books():
    """Export Goodreads books to SQL format."""
    print("Exporting Goodreads books from local database...")
    
    db = next(get_db())
    
    try:
        # Get all Goodreads books
        books = db.query(ContentItem).filter(
            ContentItem.id.like('goodreads_2025_%')
        ).order_by(ContentItem.id).all()
        
        if not books:
            print("No Goodreads books found in database!")
            return
        
        print(f"Found {len(books)} Goodreads books to export")
        
        # Generate SQL
        sql_statements = []
        sql_statements.append("-- SQL script to insert Goodreads 2025 popular books into production database")
        sql_statements.append("-- Generated from local database export")
        sql_statements.append("")
        sql_statements.append("INSERT INTO content_items (id, title, content, language, content_metadata, analysis, adaptations, created_at, updated_at) VALUES")
        
        values = []
        for book in books:
            value_parts = [
                escape_sql_string(book.id),
                escape_sql_string(book.title),
                escape_sql_string(book.content),
                escape_sql_string(book.language),
                format_json_for_sql(book.content_metadata),
                format_json_for_sql(book.analysis),
                format_json_for_sql(book.adaptations),
                "NOW()",
                "NOW()"
            ]
            values.append(f"({', '.join(value_parts)})")
        
        sql_statements.append(',\n'.join(values))
        sql_statements.append("")
        sql_statements.append("ON CONFLICT (id) DO NOTHING;")
        sql_statements.append("")
        
        # Add verification queries
        sql_statements.extend([
            "-- Verify the insertion",
            "SELECT",
            "    id,",
            "    title,",
            "    content_metadata->>'author' as author,",
            "    content_metadata->>'genre' as genre,",
            "    content_metadata->>'estimated_reading_time' as reading_time_minutes,",
            "    created_at",
            "FROM content_items",
            "WHERE id LIKE 'goodreads_2025_%'",
            "ORDER BY id;",
            "",
            "-- Summary query",
            "SELECT",
            "    COUNT(*) as total_books,",
            "    COUNT(DISTINCT content_metadata->>'author') as unique_authors,",
            "    COUNT(DISTINCT content_metadata->>'genre') as unique_genres",
            "FROM content_items",
            "WHERE id LIKE 'goodreads_2025_%';"
        ])
        
        # Write to file
        output_file = "goodreads_books_export.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_statements))
        
        print(f"✅ SQL export completed: {output_file}")
        print(f"📚 Exported {len(books)} books:")
        
        for book in books:
            author = book.content_metadata.get('author', 'Unknown') if book.content_metadata else 'Unknown'
            genre = book.content_metadata.get('genre', 'Unknown') if book.content_metadata else 'Unknown'
            print(f"   - {book.title} by {author} ({genre})")
        
        print(f"\n🚀 To use in production:")
        print(f"   1. Copy {output_file} to your production server")
        print(f"   2. Connect to your production PostgreSQL database")
        print(f"   3. Run: \\i {output_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    export_goodreads_books()