"""AI Response Generation Service using OpenAI API."""

import logging
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import openai
import asyncio

from src.config import settings

logger = logging.getLogger(__name__)


class AIResponseService:
    """Service for generating dynamic AI responses using OpenAI API."""

    def __init__(self):
        """Initialize AI response service with OpenAI."""
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        if settings.openai_api_key:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Determine if we have AI available
        self.has_ai = self.openai_client is not None
        logger.info(f"AI Response Service initialized with OpenAI: {self.has_ai}")

    def _determine_preferred_provider(self) -> str:
        """Determine which AI provider to use based on availability."""
        if self.openai_client:
            return "openai"
        else:
            return "fallback"

    async def generate_response(
        self,
        user_message: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        recommendations: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Generate a conversational response using AI."""
        try:
            # Extract language from context
            language = context.get("preferred_language", "english")
            
            # Build system prompt for Noah's personality
            system_prompt = self._build_noah_system_prompt(language)
            
            # Build context-aware user prompt
            user_prompt = self._build_contextual_prompt(
                user_message=user_message,
                intent=intent,
                context=context,
                conversation_history=conversation_history,
                recommendations=recommendations,
                user_profile=user_profile
            )
            
            # Generate response using preferred provider
            if self.has_ai and self.openai_client:
                return await self._generate_openai_response(system_prompt, user_prompt)
            else:
                return self._generate_fallback_response(user_message, intent, language)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            language = context.get("preferred_language", "english")
            return self._generate_fallback_response(user_message, intent, language)

    async def generate_streaming_response(
        self,
        user_message: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        recommendations: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming conversational response using AI."""
        try:
            # Extract language from context
            language = context.get("preferred_language", "english")
            
            # Build system prompt for Noah's personality
            system_prompt = self._build_noah_system_prompt(language)
            
            # Build context-aware user prompt
            user_prompt = self._build_contextual_prompt(
                user_message=user_message,
                intent=intent,
                context=context,
                conversation_history=conversation_history,
                recommendations=recommendations,
                user_profile=user_profile
            )
            
            # Generate streaming response using preferred provider
            if self.has_ai and self.openai_client:
                async for chunk in self._generate_openai_streaming_response(system_prompt, user_prompt):
                    yield chunk
            else:
                # Fallback to non-streaming response
                language = context.get("preferred_language", "english")
                response = self._generate_fallback_response(user_message, intent, language)
                # Simulate streaming by yielding words
                words = response.split()
                for i, word in enumerate(words):
                    yield word + (" " if i < len(words) - 1 else "")
                    await asyncio.sleep(0.05)  # Small delay for natural typing effect
                
        except Exception as e:
            logger.error(f"Error generating streaming AI response: {e}")
            # Don't yield the entire fallback response as one chunk - this could cause duplication
            # Instead, let the caller handle the error appropriately
            raise

    def _build_noah_system_prompt(self, language: str = "english") -> str:
        """Build Noah's personality and behavior system prompt."""
        if language == "japanese":
            return """あなたはノア（Noah）です。知的で熱心な読書の友達です。あなたの性格的特徴：

性格：
- 温かく、親しみやすく、本と読書に対して心から興奮している
- 知識豊富だが、決して見下したり圧倒したりしない
- すべての読書レベルと好みをサポートする
- ユーザーの好みや読書目標に好奇心を持つ
- 読書の旅路について励ましと前向きさを持つ

会話スタイル：
- 自然で会話的な言葉遣いを使う
- 好みをより良く理解するために思慮深いフォローアップ質問をする
- 心からの熱意を持って推薦を説明する
- 関連する場合は以前の会話を覚えて参照する
- 簡潔だが魅力的に - 過度に長い回答は避ける

主な責任：
1. ユーザーの好みに基づいてパーソナライズされた本の推薦を提供する
2. 「発見モード」を通じて新しいジャンルや著者を発見する手助けをする
3. フィードバックを処理して将来の推薦を改善する
4. 本、読書、文学について魅力的な会話を維持する
5. レベルに関係なくユーザーの読書の旅をサポートする

回答ガイドライン：
- 常にノアのキャラクターとして回答する
- 推薦をする際は、なぜユーザーがその本を楽しめると思うかを説明する
- 読書目標と進歩について励ます
- 特定の本の情報がない場合は、ユーザーが探しているものを説明する手助けに焦点を当てる
- 会話的な回答を保ち、過度にフォーマルやロボット的になることを避ける

覚えておいて：あなたは単に情報を提供するだけではありません - あなたはユーザーが次の素晴らしい読書を見つけることを心から気にかけるサポート的な読書の友達なのです。"""
        else:
            return """You are Noah, an intelligent and enthusiastic reading companion. Your personality traits:

PERSONALITY:
- Warm, friendly, and genuinely excited about books and reading
- Knowledgeable but never condescending or overwhelming
- Supportive of all reading levels and preferences
- Curious about user preferences and reading goals
- Encouraging and positive about the reading journey

CONVERSATION STYLE:
- Use natural, conversational language
- Ask thoughtful follow-up questions to understand preferences better
- Explain recommendations with genuine enthusiasm
- Remember and reference previous conversations when relevant
- Be concise but engaging - avoid overly long responses

CORE RESPONSIBILITIES:
1. Provide personalized book recommendations based on user preferences
2. Help users discover new genres and authors through "discovery mode"
3. Process feedback to improve future recommendations
4. Maintain engaging conversations about books, reading, and literature
5. Support users in their reading journey regardless of their level

RESPONSE GUIDELINES:
- Always respond in character as Noah
- When making recommendations, explain why you think the user might enjoy each book
- Be encouraging about reading goals and progress
- If you don't have specific book information, focus on helping the user describe what they're looking for
- Keep responses conversational and avoid being too formal or robotic

Remember: You're not just providing information - you're being a supportive reading companion who genuinely cares about helping users find their next great read."""

    def _build_contextual_prompt(
        self,
        user_message: str,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
        recommendations: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Build a contextual prompt with all relevant information."""
        prompt_parts = []
        
        # Add conversation context
        if context:
            prompt_parts.append("CURRENT CONTEXT:")
            if context.get("current_topic"):
                prompt_parts.append(f"- Current topic: {context['current_topic']}")
            if context.get("user_mood"):
                prompt_parts.append(f"- User mood: {context['user_mood']}")
            if context.get("discovery_mode_active"):
                prompt_parts.append("- Discovery mode is active (user wants to explore new genres)")
            if context.get("preferred_language"):
                prompt_parts.append(f"- Preferred language: {context['preferred_language']}")
            prompt_parts.append("")
        
        # Add user profile information
        if user_profile:
            prompt_parts.append("USER PROFILE:")
            if user_profile.get("preferences"):
                prefs = user_profile["preferences"]
                if prefs.get("topics"):
                    topics = [t.get("topic", str(t)) for t in prefs["topics"][:5]]  # Top 5 topics
                    prompt_parts.append(f"- Favorite topics: {', '.join(topics)}")
                if prefs.get("content_types"):
                    types = [t.get("type", str(t)) for t in prefs["content_types"][:3]]
                    prompt_parts.append(f"- Preferred content types: {', '.join(types)}")
            
            if user_profile.get("reading_levels"):
                levels = user_profile["reading_levels"]
                if levels.get("english"):
                    prompt_parts.append(f"- English reading level: {levels['english'].get('level', 'Unknown')}")
                if levels.get("japanese"):
                    prompt_parts.append(f"- Japanese reading level: {levels['japanese'].get('level', 'Unknown')}")
            prompt_parts.append("")
        
        # Add recent conversation history
        if conversation_history and len(conversation_history) > 0:
            prompt_parts.append("RECENT CONVERSATION:")
            for msg in conversation_history[-5:]:  # Last 5 messages
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")[:200]  # Truncate long messages
                prompt_parts.append(f"- {sender.title()}: {content}")
            prompt_parts.append("")
        
        # Add intent information
        intent_type = intent.get("intent", "general_conversation")
        confidence = intent.get("confidence", 0.0)
        prompt_parts.append(f"DETECTED INTENT: {intent_type} (confidence: {confidence:.2f})")
        
        if intent.get("entities"):
            entities = intent["entities"]
            if entities:
                prompt_parts.append("EXTRACTED ENTITIES:")
                for entity_type, values in entities.items():
                    if values:
                        prompt_parts.append(f"- {entity_type}: {', '.join(values)}")
        prompt_parts.append("")
        
        # Add recommendations if available
        if recommendations:
            prompt_parts.append("AVAILABLE RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):  # Show up to 3 recommendations
                title = rec.get("title", "Unknown Title")
                author = rec.get("author", "Unknown Author")
                description = rec.get("description", "")[:100]  # Truncate description
                prompt_parts.append(f"{i}. {title} by {author}")
                if description:
                    prompt_parts.append(f"   {description}...")
            prompt_parts.append("")
        
        # Add the user's current message
        prompt_parts.append(f"USER MESSAGE: {user_message}")
        prompt_parts.append("")
        prompt_parts.append("Please respond as Noah, keeping in mind all the context above. Be conversational, helpful, and enthusiastic about helping with reading recommendations.")
        
        return "\n".join(prompt_parts)

    async def _generate_openai_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI API."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            raise

    async def _generate_openai_streaming_response(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API."""
        try:
            stream = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error generating OpenAI streaming response: {e}")
            raise

    def _generate_fallback_response(self, user_message: str, intent: Dict[str, Any], language: str = "english") -> str:
        """Generate fallback response when AI services are unavailable."""
        intent_type = intent.get("intent", "general_conversation")
        
        if language == "japanese":
            fallback_responses = {
                "book_recommendation": "あなたの次の素晴らしい読書を見つけるお手伝いをしたいです！どのようなジャンルやトピックに興味がありますか？軽くて楽しいもの、それともより考えさせられるものをお探しですか？",
                
                "discovery_mode": "わくわくしますね - 全く新しいものを探検しましょう！あなたの普段の好みとは違う本を発見するお手伝いをします。これは私の大好きなことの一つです - 読者を驚かせる隠れた名作を見つけることです！",
                
                "feedback": "あなたの感想をシェアしていただき、ありがとうございます！あなたのフィードバックは、あなたの好みをより良く理解するのに役立ちます。好きだったことや好きではなかったことについてもっと教えてください - それは私があなたにより良い推薦をするのに本当に役立ちます。",
                
                "purchase_inquiry": "その本に興味を持っていただいているのですね！直接購入リンクを生成することはできませんが、その本についてより多くの情報を見つけたり、あなたが楽しめそうな似たような本を提案したりするお手伝いをさせていただきます。",
                
                "general_conversation": "こんにちは！私はノア、あなたの読書の友達です。素晴らしい本を発見するお手伝いができることを心から嬉しく思います！次のお気に入りの小説を探している、新しいジャンルを探求したい、または単に本について話したいなど、私はあなたのためにここにいます。今日はどのような読書のことを考えていますか？"
            }
        else:
            fallback_responses = {
                "book_recommendation": "I'd love to help you find your next great read! What genres or topics are you interested in? Are you looking for something light and fun, or perhaps something more thought-provoking?",
                
                "discovery_mode": "How exciting - let's explore something completely new! I'll help you discover books outside your usual preferences. This is one of my favorite things to do - finding hidden gems that surprise readers!",
                
                "feedback": "Thank you so much for sharing your thoughts! Your feedback helps me understand your preferences better. Tell me more about what you liked or didn't like - it really helps me make better recommendations for you.",
                
                "purchase_inquiry": "I understand you're interested in getting that book! While I can't generate purchase links directly, I'd be happy to help you find more information about it or suggest similar books you might enjoy.",
                
                "general_conversation": "Hi there! I'm Noah, your reading companion, and I'm absolutely thrilled to help you discover amazing books! Whether you're looking for your next favorite novel, want to explore a new genre, or just want to chat about books, I'm here for you. What's on your reading mind today?"
            }
        
        return fallback_responses.get(intent_type, fallback_responses["general_conversation"])

    async def generate_contextual_response_templates(
        self,
        intent_type: str,
        context: Dict[str, Any],
        user_profile: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate dynamic response templates based on context and user profile."""
        try:
            # Build a prompt for generating response templates
            template_prompt = f"""Generate 3 different response templates for a reading assistant named Noah responding to a user with intent: {intent_type}

Context: {json.dumps(context, indent=2)}
User Profile: {json.dumps(user_profile or {}, indent=2)}

Each template should:
1. Be conversational and friendly
2. Reflect Noah's enthusiastic personality about books
3. Be appropriate for the given context and user profile
4. Include placeholders like {{book_title}}, {{author}}, {{genre}} where relevant

Return as JSON with keys: template1, template2, template3"""

            if self.preferred_provider == "openai" and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates conversational templates for a reading companion AI."},
                        {"role": "user", "content": template_prompt}
                    ],
                    max_tokens=400,
                    temperature=0.8
                )
                
                # Try to parse JSON response
                try:
                    return json.loads(response.choices[0].message.content)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    pass
            
            # Fallback templates
            return self._get_fallback_templates(intent_type, context.get("preferred_language", "english"))
            
        except Exception as e:
            logger.error(f"Error generating contextual templates: {e}")
            return self._get_fallback_templates(intent_type, context.get("preferred_language", "english"))

    def _get_fallback_templates(self, intent_type: str, language: str = "english") -> Dict[str, str]:
        """Get fallback response templates."""
        if language == "japanese":
            templates = {
                "book_recommendation": {
                    "template1": "あなたの次の素晴らしい読書を見つけるお手伝いができて嬉しいです！あなたが教えてくれたことに基づいて、{author}の{book_title}を本当に楽しめると思います。{reason}",
                    "template2": "ああ、あなたにぴったりの提案があります！{author}の{book_title}は、まさにあなたが探しているもののようです。{reason}",
                    "template3": "{author}の{book_title}をお勧めします - これがあなたの次のお気に入りの本になるかもしれません！{reason}"
                },
                "discovery_mode": {
                    "template1": "冒険の時間です！全く違うものを試してみましょう - {author}の{book_title}です。あなたの普段の好みとは違いますが、{reason}",
                    "template2": "発見モードが大好きです！あなたを驚かせるかもしれないものがあります：{author}の{book_title}です。{reason}",
                    "template3": "探検の準備はできていますか？{author}の{book_title}は、あなたが普段読むものとはかなり違いますが、{reason}"
                },
                "general_conversation": {
                    "template1": "ここにいてくださって嬉しいです！あなたの読書の友達として、素晴らしい本を発見するお手伝いができることを嬉しく思います。今日はどのような読書の冒険に出かけましょうか？",
                    "template2": "こんにちは！私はノアです。人々が完璧な次の読書を見つけるお手伝いをすることが大好きです。最近、どのようなことが読書の興味を引いていますか？",
                    "template3": "いらっしゃいませ！読者を彼らが愛する本と結びつけることほど楽しいことはありません。今日は何を発見するお手伝いができますか？"
                }
            }
        else:
            templates = {
                "book_recommendation": {
                    "template1": "I'm excited to help you find your next great read! Based on what you've told me, I think you might really enjoy {book_title} by {author}. {reason}",
                    "template2": "Oh, I have the perfect suggestion for you! {book_title} by {author} sounds like exactly what you're looking for. {reason}",
                    "template3": "Let me recommend {book_title} by {author} - I think this could be your next favorite book! {reason}"
                },
                "discovery_mode": {
                    "template1": "Time for an adventure! Let's try something completely different - {book_title} by {author}. It's outside your usual preferences, but {reason}",
                    "template2": "I love discovery mode! Here's something that might surprise you: {book_title} by {author}. {reason}",
                    "template3": "Ready to explore? {book_title} by {author} is quite different from what you usually read, but {reason}"
                },
                "general_conversation": {
                    "template1": "I'm so glad you're here! As your reading companion, I'm excited to help you discover amazing books. What kind of reading adventure are we going on today?",
                    "template2": "Hello! I'm Noah, and I absolutely love helping people find their perfect next read. Tell me, what's caught your reading interest lately?",
                    "template3": "Welcome! There's nothing I enjoy more than connecting readers with books they'll love. What can I help you discover today?"
                }
            }
        
        return templates.get(intent_type, templates["general_conversation"])

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the AI response service configuration."""
        return {
            "service_name": "AI Response Service",
            "provider": "openai" if self.has_ai else "fallback",
            "openai_available": self.openai_client is not None,
            "capabilities": [
                "dynamic_response_generation",
                "streaming_responses",
                "contextual_awareness",
                "personality_consistency",
                "conversation_memory",
                "template_generation"
            ],
            "model": "gpt-4o-mini" if self.has_ai else "fallback"
        }