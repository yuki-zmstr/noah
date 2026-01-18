"""Lightweight content processing service using OpenAI embeddings."""

import logging
import re
import locale
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import openai
from openai import OpenAI

from src.schemas.content import ContentAnalysis, ContentMetadata
from src.config import settings

logger = logging.getLogger(__name__)


class SupportedLocale(Enum):
    """Supported locales for content processing."""
    ENGLISH_US = "en_US.UTF-8"
    ENGLISH_GB = "en_GB.UTF-8"
    JAPANESE = "ja_JP.UTF-8"


class ContentProcessor:
    """Lightweight content processor using OpenAI embeddings."""

    def __init__(self):
        """Initialize the content processor with OpenAI client."""
        self._setup_locales()
        self._initialize_nltk()
        self._initialize_openai()

    def _setup_locales(self):
        """Set up locale support for different languages."""
        self.locale_mapping = {
            "english": SupportedLocale.ENGLISH_US.value,
            "en": SupportedLocale.ENGLISH_US.value,
            "en_US": SupportedLocale.ENGLISH_US.value,
            "en_GB": SupportedLocale.ENGLISH_GB.value,
            "japanese": SupportedLocale.JAPANESE.value,
            "ja": SupportedLocale.JAPANESE.value,
            "ja_JP": SupportedLocale.JAPANESE.value
        }

        # Store current locale to restore later
        self.original_locale = locale.getlocale()

        # Test locale availability
        self.available_locales = {}
        for lang, loc in self.locale_mapping.items():
            try:
                locale.setlocale(locale.LC_ALL, loc)
                self.available_locales[lang] = loc
                logger.info(f"Locale {loc} available for {lang}")
            except locale.Error:
                logger.warning(
                    f"Locale {loc} not available for {lang}, using fallback")
                # Fallback to C locale
                self.available_locales[lang] = "C"

        # Restore original locale
        try:
            locale.setlocale(locale.LC_ALL, self.original_locale)
        except (locale.Error, TypeError):
            locale.setlocale(locale.LC_ALL, "C")

    def _set_locale_for_language(self, language: str) -> str:
        """Set appropriate locale for the given language."""
        lang_key = language.lower()
        target_locale = self.available_locales.get(lang_key, "C")

        try:
            current_locale = locale.setlocale(locale.LC_ALL, target_locale)
            logger.debug(
                f"Set locale to {current_locale} for language {language}")
            return current_locale
        except locale.Error as e:
            logger.warning(f"Failed to set locale {target_locale}: {e}")
            locale.setlocale(locale.LC_ALL, "C")
            return "C"

    def _restore_original_locale(self):
        """Restore the original locale."""
        try:
            locale.setlocale(locale.LC_ALL, self.original_locale)
        except (locale.Error, TypeError):
            locale.setlocale(locale.LC_ALL, "C")

    def _initialize_nltk(self):
        """Initialize NLTK resources with locale support."""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)

            # Initialize stopwords for supported languages
            self.stopwords = {}
            try:
                self.stopwords['english'] = set(stopwords.words('english'))
                self.stopwords['en'] = self.stopwords['english']
            except Exception as e:
                logger.warning(f"Failed to load English stopwords: {e}")
                self.stopwords['english'] = set()
                self.stopwords['en'] = set()

            # Japanese stopwords
            self.stopwords['japanese'] = {
                'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ', 'ある', 'いる',
                'も', 'する', 'から', 'な', 'こと', 'として', 'い', 'や', 'れる', 'など', 'なっ', 'ない',
                'この', 'ため', 'その', 'あっ', 'よう', 'また', 'もの', 'という', 'あり', 'まで', 'られ',
                'なる', 'へ', 'か', 'だ', 'これ', 'によって', 'により', 'おり', 'より', 'による', 'ず',
                'なり', 'られる', 'において', 'ば', 'なかっ', 'なく', 'しかし', 'について', 'せ', 'だっ',
                'その後', 'できる', 'それ'
            }
            self.stopwords['ja'] = self.stopwords['japanese']

        except Exception as e:
            logger.error(f"Failed to initialize NLTK: {e}")
            self.stopwords = {'english': set(), 'en': set(),
                              'japanese': set(), 'ja': set()}

    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None

    def analyze_content(self, content: str, language: str, metadata: ContentMetadata, title: str = "Unknown") -> ContentAnalysis:
        """
        Analyze content for topics, complexity, reading level, and generate embeddings.

        Args:
            content: The text content to analyze
            language: Language of the content ("english", "en", "japanese", "ja")
            metadata: Content metadata
            title: Title of the content for logging purposes

        Returns:
            ContentAnalysis object with analysis results
        """
        # Normalize language identifier
        lang_key = self._normalize_language_key(language)
        logger.info(f"Analyzing {lang_key} content: {title[:50]}...")

        # Set appropriate locale for processing
        original_locale = self._set_locale_for_language(lang_key)

        try:
            if lang_key in ["english", "en"]:
                result = self._analyze_english_content(content, metadata)
            elif lang_key in ["japanese", "ja"]:
                result = self._analyze_japanese_content(content, metadata)
            else:
                raise ValueError(f"Unsupported language: {language}")
        finally:
            # Always restore original locale
            self._restore_original_locale()

        return result

    def _normalize_language_key(self, language: str) -> str:
        """Normalize language identifier to supported format."""
        lang_lower = language.lower()
        if lang_lower in ["english", "en", "en_us", "en_gb"]:
            return "english"
        elif lang_lower in ["japanese", "ja", "ja_jp"]:
            return "japanese"
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _analyze_english_content(self, content: str, metadata: ContentMetadata) -> ContentAnalysis:
        """Analyze English content using NLTK and simple heuristics."""
        # Basic text statistics
        sentences = sent_tokenize(content)
        words = word_tokenize(content.lower())
        word_count = len([w for w in words if w.isalpha()])
        sentence_count = len(sentences)

        # Calculate readability metrics
        reading_level = self._calculate_english_readability(
            content, word_count, sentence_count)

        # Extract topics and key phrases using simple methods
        topics = self._extract_english_topics_simple(content, words)
        key_phrases = self._extract_english_key_phrases_simple(content, words)

        # Calculate complexity metrics
        complexity = self._calculate_english_complexity(
            content, words, sentences)

        # Generate embedding using OpenAI
        embedding = self._generate_openai_embedding(content)

        return ContentAnalysis(
            topics=topics,
            reading_level=reading_level,
            complexity=complexity,
            embedding=embedding,
            key_phrases=key_phrases
        )

    def _analyze_japanese_content(self, content: str, metadata: ContentMetadata) -> ContentAnalysis:
        """Analyze Japanese content using simple heuristics."""
        # Basic text statistics
        sentences = self._split_japanese_sentences(content)
        sentence_count = len(sentences)
        # Character count for Japanese
        word_count = len(content.replace(' ', ''))

        # Calculate Japanese-specific readability metrics
        reading_level = self._calculate_japanese_readability(
            content, word_count, sentence_count)

        # Extract topics and key phrases using simple methods
        topics = self._extract_japanese_topics_simple(content)
        key_phrases = self._extract_japanese_key_phrases_simple(content)

        # Calculate complexity metrics
        complexity = self._calculate_japanese_complexity(content, sentences)

        # Generate embedding using OpenAI
        embedding = self._generate_openai_embedding(content)

        return ContentAnalysis(
            topics=topics,
            reading_level=reading_level,
            complexity=complexity,
            embedding=embedding,
            key_phrases=key_phrases
        )

    def _calculate_english_readability(self, content: str, word_count: int, sentence_count: int) -> Dict:
        """Calculate English readability metrics."""
        if sentence_count == 0 or word_count == 0:
            return {"flesch_kincaid": 0, "smog": 0, "coleman_liau": 0, "level": "beginner"}

        # Flesch-Kincaid Grade Level
        syllable_count = self._count_syllables_english(content)
        fk_grade = 0.39 * (word_count / sentence_count) + \
            11.8 * (syllable_count / word_count) - 15.59

        # SMOG Index (simplified)
        complex_words = self._count_complex_words_english(content)
        smog = 1.043 * ((complex_words * 30 / sentence_count) ** 0.5) + 3.1291

        # Coleman-Liau Index
        letters = len([c for c in content if c.isalpha()])
        coleman_liau = 0.0588 * (letters / word_count * 100) - \
            0.296 * (sentence_count / word_count * 100) - 15.8

        # Determine reading level
        avg_grade = (fk_grade + smog + coleman_liau) / 3
        if avg_grade <= 6:
            level = "beginner"
        elif avg_grade <= 9:
            level = "intermediate"
        elif avg_grade <= 13:
            level = "advanced"
        else:
            level = "expert"

        return {
            "flesch_kincaid": round(fk_grade, 2),
            "smog": round(smog, 2),
            "coleman_liau": round(coleman_liau, 2),
            "average_grade": round(avg_grade, 2),
            "level": level
        }

    def _calculate_japanese_readability(self, content: str, word_count: int, sentence_count: int) -> Dict:
        """Calculate Japanese readability metrics based on kanji density and complexity."""
        # Count kanji characters
        kanji_count = len([c for c in content if '\u4e00' <= c <= '\u9faf'])
        hiragana_count = len([c for c in content if '\u3040' <= c <= '\u309f'])
        katakana_count = len([c for c in content if '\u30a0' <= c <= '\u30ff'])

        total_chars = len(content.replace(' ', '').replace('\n', ''))
        if total_chars == 0:
            return {"kanji_density": 0, "avg_sentence_length": 0, "level": "beginner"}

        # Calculate metrics
        kanji_density = kanji_count / total_chars
        avg_sentence_length = total_chars / max(sentence_count, 1)

        # Determine reading level based on kanji density and sentence length
        if kanji_density <= 0.2 and avg_sentence_length <= 20:
            level = "beginner"
        elif kanji_density <= 0.4 and avg_sentence_length <= 35:
            level = "intermediate"
        elif kanji_density <= 0.6 and avg_sentence_length <= 50:
            level = "advanced"
        else:
            level = "expert"

        return {
            "kanji_density": round(kanji_density, 3),
            "kanji_count": kanji_count,
            "hiragana_count": hiragana_count,
            "katakana_count": katakana_count,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "level": level
        }

    def _extract_english_topics_simple(self, content: str, words: List[str]) -> List[Dict]:
        """Extract topics from English content using simple frequency analysis."""
        topics = []

        # Filter out stopwords and get word frequencies
        stopwords_set = self.stopwords.get('english', set())
        content_words = [word for word in words if word.isalpha()
                         and len(word) > 3 and word not in stopwords_set]

        # Count word frequencies
        word_freq = {}
        for word in content_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Get top words as topics
        for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
            confidence = min(count / len(content_words), 1.0)
            if confidence > 0.01:  # Only include words that appear meaningfully
                topics.append({
                    "topic": word.title(),
                    "confidence": round(confidence, 3),
                    "type": "keyword"
                })

        return topics

    def _extract_japanese_topics_simple(self, content: str) -> List[Dict]:
        """Extract topics from Japanese content using character patterns."""
        topics = []

        # Extract potential compound words (sequences of kanji/katakana)
        kanji_words = re.findall(r'[\u4e00-\u9faf]{2,}', content)
        katakana_words = re.findall(r'[\u30a0-\u30ff]{2,}', content)

        # Count frequencies
        word_freq = {}
        for word in kanji_words + katakana_words:
            if len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top words as topics
        for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
            confidence = min(count / 10, 1.0)
            topics.append({
                "topic": word,
                "confidence": round(confidence, 3),
                "type": "keyword"
            })

        return topics

    def _extract_english_key_phrases_simple(self, content: str, words: List[str]) -> List[str]:
        """Extract key phrases using simple bigram analysis."""
        key_phrases = []
        stopwords_set = self.stopwords.get("english", set())

        # Filter meaningful words
        meaningful_words = [w for w in words if w.isalpha()
                            and len(w) > 2 and w not in stopwords_set]

        # Extract bigrams
        bigrams = {}
        for i in range(len(meaningful_words) - 1):
            bigram = f"{meaningful_words[i]} {meaningful_words[i+1]}"
            bigrams[bigram] = bigrams.get(bigram, 0) + 1

        # Get top bigrams
        for phrase, count in sorted(bigrams.items(), key=lambda x: x[1], reverse=True)[:10]:
            if count > 1:  # Only phrases that appear multiple times
                key_phrases.append(phrase.title())

        return key_phrases

    def _extract_japanese_key_phrases_simple(self, content: str) -> List[str]:
        """Extract key phrases from Japanese content using pattern matching."""
        key_phrases = []

        # Extract sequences of kanji + hiragana (common phrase pattern)
        phrases = re.findall(
            r'[\u4e00-\u9faf][\u3040-\u309f]{1,3}[\u4e00-\u9faf]', content)

        # Extract longer kanji sequences
        long_phrases = re.findall(r'[\u4e00-\u9faf]{3,6}', content)

        # Combine and deduplicate
        all_phrases = list(set(phrases + long_phrases))

        # Return top phrases by length (longer = more specific)
        key_phrases = sorted(all_phrases, key=len, reverse=True)[:10]

        return key_phrases

    def _generate_openai_embedding(self, content: str) -> List[float]:
        """Generate embedding using OpenAI's text-embedding-3-small model."""
        if not self.openai_client:
            logger.warning(
                "OpenAI client not available, returning zero vector")
            return [0.0] * 1536  # text-embedding-3-small dimension

        try:
            # Truncate content to stay within token limits (~8000 tokens max)
            truncated_content = content[:6000] if len(
                content) > 6000 else content

            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=truncated_content,
                encoding_format="float"
            )

            embedding = response.data[0].embedding
            logger.debug(
                f"Generated OpenAI embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate OpenAI embedding: {e}")
            return [0.0] * 1536

    def _calculate_english_complexity(self, content: str, words: List[str], sentences: List[str]) -> Dict:
        """Calculate complexity metrics for English content."""
        if not words or not sentences:
            return {"lexical_diversity": 0, "avg_word_length": 0, "complex_word_ratio": 0}

        # Lexical diversity (Type-Token Ratio)
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words)

        # Average word length
        alpha_words = [w for w in words if w.isalpha()]
        avg_word_length = sum(len(w)
                              for w in alpha_words) / max(len(alpha_words), 1)

        # Complex word ratio (words with 3+ syllables)
        complex_words = self._count_complex_words_english(content)
        complex_word_ratio = complex_words / max(len(alpha_words), 1)

        return {
            "lexical_diversity": round(lexical_diversity, 3),
            "avg_word_length": round(avg_word_length, 2),
            "complex_word_ratio": round(complex_word_ratio, 3)
        }

    def _calculate_japanese_complexity(self, content: str, sentences: List[str]) -> Dict:
        """Calculate complexity metrics for Japanese content."""
        if not sentences:
            return {"character_variety": 0, "avg_sentence_length": 0, "punctuation_density": 0}

        # Character variety (mix of hiragana, katakana, kanji)
        has_hiragana = any('\u3040' <= c <= '\u309f' for c in content)
        has_katakana = any('\u30a0' <= c <= '\u30ff' for c in content)
        has_kanji = any('\u4e00' <= c <= '\u9faf' for c in content)
        character_variety = sum([has_hiragana, has_katakana, has_kanji]) / 3

        # Average sentence length
        total_chars = sum(len(s.replace(' ', '')) for s in sentences)
        avg_sentence_length = total_chars / len(sentences)

        # Punctuation density
        punctuation_chars = len([c for c in content if c in '。、！？；：'])
        total_chars = len(content.replace(' ', '').replace('\n', ''))
        punctuation_density = punctuation_chars / max(total_chars, 1)

        return {
            "character_variety": round(character_variety, 3),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "punctuation_density": round(punctuation_density, 3)
        }

    def _count_syllables_english(self, text: str) -> int:
        """Count syllables in English text (simplified approach)."""
        words = word_tokenize(text.lower())
        syllable_count = 0

        for word in words:
            if word.isalpha():
                # Simple syllable counting heuristic
                vowels = 'aeiouy'
                word_syllables = 0
                prev_was_vowel = False

                for char in word:
                    if char in vowels:
                        if not prev_was_vowel:
                            word_syllables += 1
                        prev_was_vowel = True
                    else:
                        prev_was_vowel = False

                # Handle silent 'e'
                if word.endswith('e') and word_syllables > 1:
                    word_syllables -= 1

                # Ensure at least 1 syllable per word
                syllable_count += max(word_syllables, 1)

        return syllable_count

    def _count_complex_words_english(self, text: str) -> int:
        """Count complex words (3+ syllables) in English text."""
        words = word_tokenize(text.lower())
        complex_count = 0

        for word in words:
            if word.isalpha() and len(word) > 6:  # Simplified: assume longer words are complex
                complex_count += 1

        return complex_count

    def _split_japanese_sentences(self, text: str) -> List[str]:
        """Split Japanese text into sentences."""
        # Simple sentence splitting based on Japanese punctuation
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()]


# Global instance
content_processor = ContentProcessor()
