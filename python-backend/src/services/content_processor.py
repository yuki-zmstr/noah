"""Multilingual content processing and analysis service."""

import logging
import re
import locale
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum

import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
import MeCab
import torch

from src.schemas.content import ContentAnalysis, ContentMetadata

logger = logging.getLogger(__name__)


class SupportedLocale(Enum):
    """Supported locales for content processing."""
    ENGLISH_US = "en_US.UTF-8"
    ENGLISH_GB = "en_GB.UTF-8"
    JAPANESE = "ja_JP.UTF-8"


class ContentProcessor:
    """Multilingual content processor for English and Japanese text analysis."""

    def __init__(self):
        """Initialize the content processor with required models and tools."""
        self._setup_locales()
        self._initialize_nltk()
        self._initialize_spacy()
        self._initialize_mecab()
        self._initialize_sentence_transformer()

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

            # Japanese doesn't have NLTK stopwords, we'll define basic ones
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

    def _initialize_spacy(self):
        """Initialize spaCy models with locale-aware loading."""
        self.nlp_models = {}

        # English models
        english_models = ["en_core_web_sm", "en_core_web_md", "en_core_web_lg"]
        for model_name in english_models:
            try:
                self.nlp_models['english'] = spacy.load(model_name)
                self.nlp_models['en'] = self.nlp_models['english']
                logger.info(f"Loaded English spaCy model: {model_name}")
                break
            except OSError:
                continue

        if 'english' not in self.nlp_models:
            logger.warning(
                "No English spaCy model found. Install with: python -m spacy download en_core_web_sm")
            self.nlp_models['english'] = None
            self.nlp_models['en'] = None

        # Japanese models
        japanese_models = ["ja_core_news_sm",
                           "ja_core_news_md", "ja_core_news_lg"]
        for model_name in japanese_models:
            try:
                self.nlp_models['japanese'] = spacy.load(model_name)
                self.nlp_models['ja'] = self.nlp_models['japanese']
                logger.info(f"Loaded Japanese spaCy model: {model_name}")
                break
            except OSError:
                continue

        if 'japanese' not in self.nlp_models:
            logger.warning(
                "No Japanese spaCy model found. Install with: python -m spacy download ja_core_news_sm")
            self.nlp_models['japanese'] = None
            self.nlp_models['ja'] = None

    def _initialize_mecab(self):
        """Initialize MeCab for Japanese text analysis with locale support."""
        try:
            # Set Japanese locale for MeCab initialization
            self._set_locale_for_language("japanese")

            # Initialize MeCab with different output formats
            self.mecab_wakati = MeCab.Tagger("-Owakati")  # Word segmentation
            self.mecab_chasen = MeCab.Tagger("-Ochasen")  # Detailed analysis
            self.mecab_features = MeCab.Tagger()  # Full feature analysis

            logger.info("MeCab initialized successfully")

            # Restore original locale
            self._restore_original_locale()

        except Exception as e:
            logger.error(f"Failed to initialize MeCab: {e}")
            self.mecab_wakati = None
            self.mecab_chasen = None
            self.mecab_features = None

    def _initialize_sentence_transformer(self):
        """Initialize sentence transformer for embeddings."""
        try:
            # Use a multilingual model that supports both English and Japanese
            self.sentence_model = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformer: {e}")
            self.sentence_model = None

    def analyze_content(self, content: str, language: str, metadata: ContentMetadata) -> ContentAnalysis:
        """
        Analyze content for topics, complexity, reading level, and generate embeddings.

        Args:
            content: The text content to analyze
            language: Language of the content ("english", "en", "japanese", "ja")
            metadata: Content metadata

        Returns:
            ContentAnalysis object with analysis results
        """
        # Normalize language identifier
        lang_key = self._normalize_language_key(language)
        logger.info(f"Analyzing {lang_key} content: {metadata.title[:50]}...")

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
        """Analyze English content using NLTK and spaCy."""
        # Basic text statistics
        sentences = sent_tokenize(content)
        words = word_tokenize(content.lower())
        word_count = len([w for w in words if w.isalpha()])
        sentence_count = len(sentences)

        # Calculate readability metrics
        reading_level = self._calculate_english_readability(
            content, word_count, sentence_count)

        # Extract topics and key phrases
        topics = self._extract_english_topics(content)
        key_phrases = self._extract_english_key_phrases(content)

        # Calculate complexity metrics
        complexity = self._calculate_english_complexity(
            content, words, sentences)

        # Generate embedding
        embedding = self._generate_embedding(content)

        return ContentAnalysis(
            topics=topics,
            reading_level=reading_level,
            complexity=complexity,
            embedding=embedding,
            key_phrases=key_phrases
        )

    def _analyze_japanese_content(self, content: str, metadata: ContentMetadata) -> ContentAnalysis:
        """Analyze Japanese content using MeCab and spaCy."""
        # Basic text statistics using MeCab
        if self.mecab_wakati:
            words = self.mecab_wakati.parse(content).strip().split()
            word_count = len(words)
        else:
            # Fallback: rough word count
            word_count = len(content.replace(' ', ''))

        sentences = self._split_japanese_sentences(content)
        sentence_count = len(sentences)

        # Calculate Japanese-specific readability metrics
        reading_level = self._calculate_japanese_readability(
            content, word_count, sentence_count)

        # Extract topics and key phrases
        topics = self._extract_japanese_topics(content)
        key_phrases = self._extract_japanese_key_phrases(content)

        # Calculate complexity metrics
        complexity = self._calculate_japanese_complexity(content, sentences)

        # Generate embedding
        embedding = self._generate_embedding(content)

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

    def _extract_english_topics(self, content: str) -> List[Dict]:
        """Extract topics from English content using spaCy."""
        topics = []

        if self.nlp_models.get("english"):
            doc = self.nlp_models["english"](content)

            # Extract named entities as topics
            entities = {}
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "WORK_OF_ART"]:
                    entities[ent.text] = entities.get(ent.text, 0) + 1

            # Convert to topic format
            for entity, count in sorted(entities.items(), key=lambda x: x[1], reverse=True)[:10]:
                topics.append({
                    "topic": entity,
                    "confidence": min(count / 10, 1.0),
                    "type": "entity"
                })

        # Fallback: extract common nouns
        if not topics:
            words = word_tokenize(content.lower())
            nouns = [word for word in words if word.isalpha(
            ) and word not in self.english_stopwords]
            word_freq = {}
            for word in nouns:
                word_freq[word] = word_freq.get(word, 0) + 1

            for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
                topics.append({
                    "topic": word,
                    "confidence": min(count / 20, 1.0),
                    "type": "keyword"
                })

        return topics

    def _extract_japanese_topics(self, content: str) -> List[Dict]:
        """Extract topics from Japanese content using MeCab and spaCy."""
        topics = []

        if self.nlp_models.get("japanese"):
            doc = self.nlp_models["japanese"](content)

            # Extract named entities
            entities = {}
            for ent in doc.ents:
                entities[ent.text] = entities.get(ent.text, 0) + 1

            for entity, count in sorted(entities.items(), key=lambda x: x[1], reverse=True)[:10]:
                topics.append({
                    "topic": entity,
                    "confidence": min(count / 5, 1.0),
                    "type": "entity"
                })

        # Use MeCab for noun extraction
        if self.mecab_wakati and not topics:
            parsed = self.mecab_wakati.parse(content)
            # This is a simplified approach - in practice, you'd parse the MeCab output properly
            words = parsed.strip().split()
            word_freq = {}
            for word in words:
                if len(word) > 1:  # Filter out single characters
                    word_freq[word] = word_freq.get(word, 0) + 1

            for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
                topics.append({
                    "topic": word,
                    "confidence": min(count / 10, 1.0),
                    "type": "keyword"
                })

        return topics

    def _extract_english_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases from English content."""
        key_phrases = []

        if self.nlp_models.get("english"):
            doc = self.nlp_models["english"](content)

            # Extract noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) >= 2 and len(chunk.text) <= 50:
                    key_phrases.append(chunk.text.strip())

        # Fallback: extract common bigrams and trigrams
        if not key_phrases:
            words = word_tokenize(content.lower())
            stopwords_set = self.stopwords.get("english", set())
            words = [w for w in words if w.isalpha() and w not in stopwords_set]

            # Simple bigram extraction
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                if len(phrase) <= 30:
                    key_phrases.append(phrase)

        # Return unique phrases, limit to 10
        return list(set(key_phrases))[:10]

    def _extract_japanese_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases from Japanese content."""
        key_phrases = []

        if self.nlp_models.get("japanese"):
            doc = self.nlp_models["japanese"](content)

            # Extract noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text) >= 2 and len(chunk.text) <= 20:
                    key_phrases.append(chunk.text.strip())

        # Fallback: extract compound words using simple heuristics
        if not key_phrases and self.mecab_wakati:
            # This is simplified - proper implementation would parse MeCab output
            sentences = self._split_japanese_sentences(content)
            for sentence in sentences[:3]:  # Analyze first few sentences
                if len(sentence) >= 4:
                    # Take first 10 characters as phrase
                    key_phrases.append(sentence[:10])

        return list(set(key_phrases))[:10]

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

    def _generate_embedding(self, content: str) -> List[float]:
        """Generate sentence embedding for content similarity."""
        if not self.sentence_model:
            return [0.0] * 384  # Return zero vector if model not available

        try:
            # Truncate content if too long (model has token limits)
            truncated_content = content[:1000] if len(
                content) > 1000 else content
            embedding = self.sentence_model.encode(truncated_content)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 384

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
