"""Content adaptation engine for multilingual reading level adjustment."""

import logging
import re
import locale
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import wordnet
import MeCab

logger = logging.getLogger(__name__)


class SupportedLocale(Enum):
    """Supported locales for content adaptation."""
    ENGLISH_US = "en_US.UTF-8"
    ENGLISH_GB = "en_GB.UTF-8"
    JAPANESE = "ja_JP.UTF-8"


@dataclass
class AdaptationResult:
    """Result of content adaptation."""
    adapted_content: str
    original_content: str
    adaptations_made: List[Dict]
    reading_level_change: Dict
    cultural_context_preserved: bool


class ContentAdapter:
    """Multilingual content adaptation engine."""

    def __init__(self):
        """Initialize the content adapter with language models and resources."""
        self._setup_locales()
        self._initialize_models()
        self._load_word_frequency_data()

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
        lang_key = self._normalize_language_key(language)
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

    def _normalize_language_key(self, language: str) -> str:
        """Normalize language identifier to supported format."""
        lang_lower = language.lower()
        if lang_lower in ["english", "en", "en_us", "en_gb"]:
            return "english"
        elif lang_lower in ["japanese", "ja", "ja_jp"]:
            return "japanese"
        else:
            raise ValueError(f"Unsupported language: {language}")

    def _initialize_models(self):
        """Initialize spaCy and MeCab models with locale support."""
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
            logger.warning("No English spaCy model found")
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
            logger.warning("No Japanese spaCy model found")
            self.nlp_models['japanese'] = None
            self.nlp_models['ja'] = None

        # Initialize MeCab for Japanese
        try:
            self._set_locale_for_language("japanese")
            self.mecab_wakati = MeCab.Tagger("-Owakati")
            self.mecab_chasen = MeCab.Tagger("-Ochasen")
            self._restore_original_locale()
            logger.info("MeCab initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MeCab: {e}")
            self.mecab_wakati = None
            self.mecab_chasen = None

    def _load_word_frequency_data(self):
        """Load word frequency databases for vocabulary simplification."""
        # English word frequency (simplified - in practice, load from external resource)
        self.english_simple_words = {
            'utilize': 'use', 'demonstrate': 'show', 'facilitate': 'help',
            'commence': 'start', 'terminate': 'end', 'acquire': 'get',
            'construct': 'build', 'implement': 'do', 'establish': 'set up',
            'accomplish': 'do', 'participate': 'take part', 'investigate': 'look into',
            'approximately': 'about', 'subsequently': 'then', 'furthermore': 'also',
            'nevertheless': 'but', 'consequently': 'so', 'therefore': 'so',
            'however': 'but', 'although': 'though', 'because': 'since'
        }

        # Japanese word simplification (basic examples)
        self.japanese_simple_words = {
            '実施': '行う',  # implement -> do
            '検討': '考える',  # consider -> think
            '確認': '見る',  # confirm -> see
            '提供': '与える',  # provide -> give
            '活用': '使う',  # utilize -> use
            '対応': '答える',  # respond -> answer
            '改善': '良くする',  # improve -> make better
            '効果': '結果',  # effect -> result
        }

    def adapt_content(self, content: str, language: str, target_level: str,
                      current_level: str, preserve_meaning: bool = True) -> AdaptationResult:
        """
        Adapt content to target reading level while preserving meaning.

        Args:
            content: Original content to adapt
            language: Language of content ("english", "en", "japanese", "ja")
            target_level: Target reading level ("beginner", "intermediate", "advanced", "expert")
            current_level: Current assessed reading level
            preserve_meaning: Whether to prioritize meaning preservation

        Returns:
            AdaptationResult with adapted content and metadata
        """
        # Normalize language identifier
        lang_key = self._normalize_language_key(language)
        logger.info(
            f"Adapting {lang_key} content from {current_level} to {target_level}")

        if self._should_adapt(current_level, target_level):
            # Set appropriate locale for processing
            self._set_locale_for_language(lang_key)

            try:
                if lang_key in ["english", "en"]:
                    result = self._adapt_english_content(
                        content, target_level, current_level, preserve_meaning)
                elif lang_key in ["japanese", "ja"]:
                    result = self._adapt_japanese_content(
                        content, target_level, current_level, preserve_meaning)
                else:
                    raise ValueError(f"Unsupported language: {language}")
            finally:
                # Always restore original locale
                self._restore_original_locale()

            return result
        else:
            # No adaptation needed
            return AdaptationResult(
                adapted_content=content,
                original_content=content,
                adaptations_made=[],
                reading_level_change={"from": current_level,
                                      "to": current_level, "adapted": False},
                cultural_context_preserved=True
            )

    def _should_adapt(self, current_level: str, target_level: str) -> bool:
        """Determine if content adaptation is needed."""
        level_hierarchy = ["beginner", "intermediate", "advanced", "expert"]

        try:
            current_idx = level_hierarchy.index(current_level)
            target_idx = level_hierarchy.index(target_level)
            return current_idx > target_idx  # Only adapt if current is higher than target
        except ValueError:
            return False

    def _adapt_english_content(self, content: str, target_level: str,
                               current_level: str, preserve_meaning: bool) -> AdaptationResult:
        """Adapt English content to target reading level."""
        adaptations_made = []
        adapted_content = content

        # Step 1: Vocabulary simplification
        adapted_content, vocab_adaptations = self._simplify_english_vocabulary(
            adapted_content, target_level)
        adaptations_made.extend(vocab_adaptations)

        # Step 2: Sentence structure simplification
        adapted_content, structure_adaptations = self._simplify_english_sentences(
            adapted_content, target_level)
        adaptations_made.extend(structure_adaptations)

        # Step 3: Remove or explain complex concepts if needed
        if target_level == "beginner":
            adapted_content, concept_adaptations = self._simplify_english_concepts(
                adapted_content)
            adaptations_made.extend(concept_adaptations)

        return AdaptationResult(
            adapted_content=adapted_content,
            original_content=content,
            adaptations_made=adaptations_made,
            reading_level_change={"from": current_level,
                                  "to": target_level, "adapted": True},
            cultural_context_preserved=preserve_meaning
        )

    def _adapt_japanese_content(self, content: str, target_level: str,
                                current_level: str, preserve_meaning: bool) -> AdaptationResult:
        """Adapt Japanese content to target reading level while preserving cultural context."""
        adaptations_made = []
        adapted_content = content

        # Step 1: Kanji simplification (replace complex kanji with hiragana or simpler kanji)
        adapted_content, kanji_adaptations = self._simplify_japanese_kanji(
            adapted_content, target_level)
        adaptations_made.extend(kanji_adaptations)

        # Step 2: Vocabulary simplification
        adapted_content, vocab_adaptations = self._simplify_japanese_vocabulary(
            adapted_content, target_level)
        adaptations_made.extend(vocab_adaptations)

        # Step 3: Sentence structure simplification
        adapted_content, structure_adaptations = self._simplify_japanese_sentences(
            adapted_content, target_level)
        adaptations_made.extend(structure_adaptations)

        # Step 4: Cultural context preservation check
        cultural_preserved = self._check_japanese_cultural_context(
            content, adapted_content)

        return AdaptationResult(
            adapted_content=adapted_content,
            original_content=content,
            adaptations_made=adaptations_made,
            reading_level_change={"from": current_level,
                                  "to": target_level, "adapted": True},
            cultural_context_preserved=cultural_preserved
        )

    def _simplify_english_vocabulary(self, content: str, target_level: str) -> Tuple[str, List[Dict]]:
        """Simplify English vocabulary using word frequency databases."""
        adaptations = []
        adapted_content = content

        # Replace complex words with simpler alternatives
        for complex_word, simple_word in self.english_simple_words.items():
            if complex_word in adapted_content.lower():
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(complex_word) + r'\b'
                matches = re.findall(pattern, adapted_content, re.IGNORECASE)

                if matches:
                    adapted_content = re.sub(
                        pattern, simple_word, adapted_content, flags=re.IGNORECASE)
                    adaptations.append({
                        "type": "vocabulary_simplification",
                        "original": complex_word,
                        "replacement": simple_word,
                        "count": len(matches)
                    })

        # Additional simplifications based on target level
        if target_level == "beginner":
            # Replace more advanced words
            advanced_replacements = {
                'significant': 'important', 'numerous': 'many', 'various': 'different',
                'essential': 'needed', 'particular': 'special', 'individual': 'person',
                'specific': 'exact', 'general': 'common', 'available': 'ready'
            }

            for advanced, simple in advanced_replacements.items():
                pattern = r'\b' + re.escape(advanced) + r'\b'
                if re.search(pattern, adapted_content, re.IGNORECASE):
                    adapted_content = re.sub(
                        pattern, simple, adapted_content, flags=re.IGNORECASE)
                    adaptations.append({
                        "type": "beginner_vocabulary_simplification",
                        "original": advanced,
                        "replacement": simple,
                        "count": 1
                    })

        return adapted_content, adaptations

    def _simplify_english_sentences(self, content: str, target_level: str) -> Tuple[str, List[Dict]]:
        """Simplify English sentence structure."""
        adaptations = []
        sentences = sent_tokenize(content)
        adapted_sentences = []

        for sentence in sentences:
            adapted_sentence = sentence

            # Break down complex sentences
            if len(sentence.split()) > 20 and target_level in ["beginner", "intermediate"]:
                # Simple approach: split on conjunctions
                conjunctions = [', and ', ', but ', ', or ',
                                ', so ', '; however, ', '; therefore, ']

                for conj in conjunctions:
                    if conj in adapted_sentence:
                        parts = adapted_sentence.split(conj, 1)
                        if len(parts) == 2:
                            adapted_sentence = f"{parts[0].strip()}. {parts[1].strip()}"
                            adaptations.append({
                                "type": "sentence_splitting",
                                "original": sentence,
                                "method": f"split_on_{conj.strip()}",
                                "count": 1
                            })
                            break

            # Simplify passive voice to active voice (basic approach)
            if target_level == "beginner":
                # Simple passive voice detection and conversion
                passive_patterns = [
                    (r'was (\w+ed) by', r'X \1'),  # "was done by" -> "X did"
                    (r'were (\w+ed) by', r'X \1'),  # "were done by" -> "X did"
                    (r'is (\w+ed) by', r'X \1'),   # "is done by" -> "X does"
                    (r'are (\w+ed) by', r'X \1'),  # "are done by" -> "X do"
                ]

                for pattern, replacement in passive_patterns:
                    if re.search(pattern, adapted_sentence):
                        adapted_sentence = re.sub(
                            pattern, replacement, adapted_sentence)
                        adaptations.append({
                            "type": "passive_to_active",
                            "original": sentence,
                            "pattern": pattern,
                            "count": 1
                        })
                        break

            adapted_sentences.append(adapted_sentence)

        return ' '.join(adapted_sentences), adaptations

    def _simplify_english_concepts(self, content: str) -> Tuple[str, List[Dict]]:
        """Simplify complex concepts for beginner level."""
        adaptations = []
        adapted_content = content

        # Add simple explanations for technical terms
        technical_terms = {
            'algorithm': 'algorithm (a set of rules for solving problems)',
            'database': 'database (a place to store information)',
            'network': 'network (computers connected together)',
            'software': 'software (computer programs)',
            'hardware': 'hardware (computer parts you can touch)'
        }

        for term, explanation in technical_terms.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, adapted_content, re.IGNORECASE):
                adapted_content = re.sub(
                    pattern, explanation, adapted_content, flags=re.IGNORECASE)
                adaptations.append({
                    "type": "concept_explanation",
                    "original": term,
                    "replacement": explanation,
                    "count": 1
                })

        return adapted_content, adaptations

    def _simplify_japanese_kanji(self, content: str, target_level: str) -> Tuple[str, List[Dict]]:
        """Simplify Japanese kanji based on target reading level."""
        adaptations = []
        adapted_content = content

        # Basic kanji to hiragana conversions for beginners
        if target_level == "beginner":
            kanji_to_hiragana = {
                '私': 'わたし',  # I/me
                '今日': 'きょう',  # today
                '明日': 'あした',  # tomorrow
                '昨日': 'きのう',  # yesterday
                '時間': 'じかん',  # time
                '場所': 'ばしょ',  # place
                '人': 'ひと',    # person
                '本': 'ほん',    # book
                '水': 'みず',    # water
                '食べ物': 'たべもの'  # food
            }

            for kanji, hiragana in kanji_to_hiragana.items():
                if kanji in adapted_content:
                    adapted_content = adapted_content.replace(kanji, hiragana)
                    adaptations.append({
                        "type": "kanji_to_hiragana",
                        "original": kanji,
                        "replacement": hiragana,
                        "count": adapted_content.count(hiragana)
                    })

        return adapted_content, adaptations

    def _simplify_japanese_vocabulary(self, content: str, target_level: str) -> Tuple[str, List[Dict]]:
        """Simplify Japanese vocabulary."""
        adaptations = []
        adapted_content = content

        # Replace complex words with simpler alternatives
        for complex_word, simple_word in self.japanese_simple_words.items():
            if complex_word in adapted_content:
                adapted_content = adapted_content.replace(
                    complex_word, simple_word)
                adaptations.append({
                    "type": "vocabulary_simplification",
                    "original": complex_word,
                    "replacement": simple_word,
                    "count": 1
                })

        return adapted_content, adaptations

    def _simplify_japanese_sentences(self, content: str, target_level: str) -> Tuple[str, List[Dict]]:
        """Simplify Japanese sentence structure."""
        adaptations = []
        sentences = self._split_japanese_sentences(content)
        adapted_sentences = []

        for sentence in sentences:
            adapted_sentence = sentence

            # Break down long sentences
            if len(sentence) > 30 and target_level in ["beginner", "intermediate"]:
                # Split on certain particles and conjunctions
                split_points = ['が、', 'けれど、', 'しかし、', 'そして、', 'また、']

                for split_point in split_points:
                    if split_point in adapted_sentence:
                        parts = adapted_sentence.split(split_point, 1)
                        if len(parts) == 2:
                            adapted_sentence = f"{parts[0].strip()}。{parts[1].strip()}"
                            adaptations.append({
                                "type": "sentence_splitting",
                                "original": sentence,
                                "method": f"split_on_{split_point}",
                                "count": 1
                            })
                            break

            adapted_sentences.append(adapted_sentence)

        return ''.join(adapted_sentences), adaptations

    def _check_japanese_cultural_context(self, original: str, adapted: str) -> bool:
        """Check if cultural context is preserved in Japanese adaptation."""
        # Simple check for cultural elements
        cultural_elements = [
            '敬語',  # keigo (honorific language)
            'さん', 'さま', 'くん', 'ちゃん',  # honorific suffixes
            '季節', '春', '夏', '秋', '冬',  # seasons
            '祭り', '神社', '寺',  # festivals, shrines, temples
            'お正月', 'お盆',  # traditional holidays
        ]

        original_cultural_count = sum(
            1 for element in cultural_elements if element in original)
        adapted_cultural_count = sum(
            1 for element in cultural_elements if element in adapted)

        # Consider cultural context preserved if we retain at least 80% of cultural elements
        if original_cultural_count == 0:
            return True

        preservation_ratio = adapted_cultural_count / original_cultural_count
        return preservation_ratio >= 0.8

    def _split_japanese_sentences(self, text: str) -> List[str]:
        """Split Japanese text into sentences."""
        sentences = re.split(r'[。！？]', text)
        return [s.strip() + '。' for s in sentences if s.strip()]


# Global instance
content_adapter = ContentAdapter()
