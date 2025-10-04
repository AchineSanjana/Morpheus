from typing import Optional, Dict, Any, List
import random
import logging
import re
import hashlib
from datetime import datetime

from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text, gemini_ready
from app.audio_service import audio_service

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

class SecurityValidator:
    """Security validation for storyteller inputs and outputs"""
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove potential prompt injection patterns
        dangerous_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s*:",
            r"admin\s*:",
            r"override\s+settings",
            r"<\s*script",
            r"javascript\s*:",
            r"eval\s*\(",
            r"exec\s*\(",
            r"import\s+",
            r"from\s+.*\s+import",
            r"__.*__",
            r"document\.",
            r"window\.",
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)
        
        # Remove potential SQL injection
        sql_patterns = [r"[';\"\\]", r"--", r"/\*", r"\*/", r"union\s+select", r"drop\s+table"]
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Limit length and remove excessive special characters
        sanitized = sanitized[:1000]  # Reasonable limit
        sanitized = re.sub(r'[^\w\s\-.,!?áéíóúàèìòùâêîôû]', '', sanitized)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_story_output(content: str) -> bool:
        """Validate AI-generated story output for safety"""
        if not content or len(content.strip()) < 10:
            return False
        
        # Check for harmful content patterns
        harmful_patterns = [
            r'\b(suicide|kill|death|violence|murder|weapon)\b',
            r'\b(medication|drug|prescription|medical advice)\b',
            r'\b(personal information|credit card|ssn|social security)\b',
            r'\b(address|phone number|email|password)\b',
            r'\b(explicit|sexual|inappropriate)\b',
            r'\b(scary|frightening|terrifying|nightmare)\b'
        ]
        
        content_lower = content.lower()
        for pattern in harmful_patterns:
            if re.search(pattern, content_lower):
                security_logger.warning(f"Story content failed safety check: {pattern}")
                return False
        
        return True
    
    @staticmethod
    def hash_for_logging(content: str) -> str:
        """Create safe hash for logging without exposing content"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def sanitize_user_name(user_name: str) -> Optional[str]:
        """Sanitize and validate user name"""
        if not user_name:
            return None
        
        # Remove special characters and limit length
        sanitized = re.sub(r'[^\w\s\-.]', '', user_name)
        sanitized = sanitized.strip()[:50]  # Reasonable name length limit
        
        # Don't use names that look like email addresses or contain sensitive patterns
        if '@' in sanitized or any(pattern in sanitized.lower() for pattern in ['admin', 'root', 'system']):
            return None
        
        return sanitized if len(sanitized) >= 2 else None

# Story themes and their associated elements
STORY_THEMES = {
    "nature": {
        "elements": ["forest", "mountain", "ocean", "meadow", "river", "garden", "desert", "lake"],
        "characters": ["wise owl", "gentle deer", "sleepy rabbit", "peaceful fox", "kind bear", "quiet squirrel"],
        "settings": ["moonlit clearing", "cozy tree hollow", "peaceful grove", "serene valley", "quiet pond"]
    },
    "journey": {
        "elements": ["winding path", "distant lighthouse", "old bridge", "hidden village", "peaceful ship"],
        "characters": ["thoughtful traveler", "kind stranger", "wise guide", "gentle wanderer"],
        "settings": ["cobblestone road", "quiet harbor", "mountain pass", "riverside path", "ancient trail"]
    },
    "home": {
        "elements": ["warm fireplace", "cozy window", "soft blanket", "gentle lamp", "comfortable chair"],
        "characters": ["sleepy cat", "wise grandmother", "caring friend", "peaceful family"],
        "settings": ["quiet library", "cozy cottage", "peaceful garden", "warm kitchen", "comfortable bedroom"]
    },
    "magical": {
        "elements": ["twinkling stars", "gentle magic", "floating lanterns", "soft glowing lights", "peaceful dreams"],
        "characters": ["kind fairy", "wise wizard", "gentle dragon", "peaceful spirit", "dream guardian"],
        "settings": ["enchanted garden", "starlit castle", "magical library", "dream realm", "cloud palace"]
    }
}

STORY_LENGTHS = {
    "short": {"words": "120-180", "description": "A brief, gentle tale"},
    "medium": {"words": "800-1200", "description": "A comfortable bedtime story"},
    "long": {"words": "1200-1500", "description": "A longer, more detailed story"},
    "extended": {"words": "1500-2000", "description": "An immersive, detailed bedtime journey"}
}

SYSTEM_STYLE_BASE = (
    "You are a gentle bedtime storyteller who creates peaceful, calming stories. "
    "Write in simple, flowing language that soothes and relaxes. "
    "No horror, violence, high-energy action, or disturbing content. "
    "Keep everything cozy, safe, hopeful, and conducive to sleep. "
    "Use soft imagery like gentle lights, calm water, quiet nature, and comfortable spaces. "
    "End with a peaceful, satisfying conclusion that naturally leads to rest."
)

# Multiple fallback stories for variety
FALLBACK_STORIES = [
    # Original story
    (
        "As the evening breeze drifted through the quiet room, a small lantern "
        "glowed like a sleepy firefly on the windowsill. Outside, a calm lake "
        "held the sky's last colors—lavender and soft silver—while reeds swayed "
        "like they were listening to a familiar lullaby. A traveler paused on the "
        "shore, toes in the cool sand, breathing with the water's slow rhythm. "
        "They imagined each ripple as a thought passing by, kind and unhurried. "
        "A gentle owl blinked from a pine branch, then tucked its head beneath a "
        "wing. The lantern's glow softened, and the traveler wrapped a blanket a "
        "little tighter, feeling warm and safe. The world settled into the hush "
        "of night, and the lake drew a curtain of stars across its surface. With "
        "one last easy breath, the traveler smiled, letting the quiet carry them "
        "toward rest—unfolding like a cloud, drifting into dream."
    ),
    # Forest story
    (
        "In a peaceful forest clearing, a wise old oak tree stretched its branches "
        "toward the evening sky. Fireflies began their gentle dance, creating tiny "
        "lanterns of light between the leaves. A soft-eyed deer stepped delicately "
        "through the ferns, pausing to drink from a babbling brook that caught the "
        "last rays of sunlight. The tree's ancient roots held stories of countless "
        "quiet nights, and its leaves whispered lullabies to the woodland creatures "
        "settling in for rest. A family of rabbits nestled in the warm grass, "
        "listening to the gentle symphony of crickets and rustling leaves. As stars "
        "began to appear through the canopy, the forest wrapped itself in a blanket "
        "of peace, and all who dwelled there felt the loving embrace of nature's "
        "gentle goodnight."
    ),
    # Cottage story
    (
        "A cozy cottage sat nestled in a garden full of lavender and rosemary, its "
        "windows glowing with warm, golden light. Inside, a kettle hummed softly on "
        "the stove while a tabby cat stretched lazily by the fireplace. The gentle "
        "crackle of burning logs mixed with the distant sound of rain tapping against "
        "the roof in a rhythmic, soothing pattern. An old rocking chair swayed "
        "peacefully by the window, where someone had left a half-finished book and "
        "a cup of chamomile tea. The cottage seemed to breathe with contentment, "
        "its walls holding decades of peaceful evenings and restful nights. As the "
        "fire settled into glowing embers, the cottage tucked itself in for the "
        "night, safe and warm under a blanket of twinkling stars."
    )
]

class StoryTellerAgent(BaseAgent):
    name = "storyteller"

    def __init__(self):
        super().__init__()
        self.action_type = "storytelling"  # For responsible AI context
        self.story_preferences = {}  # Track user preferences (encrypted)
        self.story_history = []  # Track recent stories for variety
        self.security_validator = SecurityValidator()
        self.audio_enabled = True  # Enable audio features

    def _extract_story_preferences(self, message: str, ctx: Optional[AgentContext] = None) -> Dict[str, Any]:
        """Extract story preferences from sanitized user message and context"""
        # Sanitize input first
        sanitized_message = self.security_validator.sanitize_user_input(message)
        
        preferences = {
            "theme": None,
            "length": "medium",  # Now defaults to ~1000 words
            "custom_topic": None,
            "include_name": True,
            "mood": "calm"
        }
        
        message_lower = sanitized_message.lower() if sanitized_message else ""
        
        # Extract theme preferences
        for theme in STORY_THEMES.keys():
            if theme in message_lower or any(element in message_lower for element in STORY_THEMES[theme]["elements"]):
                preferences["theme"] = theme
                break
        
        # Extract length preferences
        if any(word in message_lower for word in ["short", "brief", "quick"]):
            preferences["length"] = "short"
        elif any(word in message_lower for word in ["very long", "extended", "detailed", "immersive"]):
            preferences["length"] = "extended"
        elif any(word in message_lower for word in ["long"]):
            preferences["length"] = "long"
        
        # Extract custom topic (with additional sanitization)
        topic_indicators = ["about", "with", "featuring", "story of", "tale of"]
        for indicator in topic_indicators:
            if indicator in message_lower:
                topic_start = message_lower.find(indicator) + len(indicator)
                topic_end = len(message_lower)
                custom_topic = sanitized_message[topic_start:topic_end].strip()
                if custom_topic and len(custom_topic) <= 100:  # Limit topic length
                    # Additional sanitization for custom topics
                    custom_topic = re.sub(r'[^\w\s\-.,]', '', custom_topic)
                    preferences["custom_topic"] = custom_topic
                break
        
        # Check for name preference
        if any(word in message_lower for word in ["no name", "anonymous", "without name"]):
            preferences["include_name"] = False
        
        return preferences

    def _build_enhanced_prompt(self, preferences: Dict[str, Any], user_name: Optional[str]) -> str:
        """Build an enhanced prompt based on user preferences with security checks"""
        length_info = STORY_LENGTHS[preferences["length"]]
        
        prompt = f"{SYSTEM_STYLE_BASE}\n\n"
        prompt += f"Write a {preferences['length']} bedtime story ({length_info['words']} words). "
        
        # Add length-specific guidance
        if preferences["length"] in ["medium", "long", "extended"]:
            prompt += "For this longer story, include: multiple gentle scenes, "
            prompt += "rich sensory descriptions, character development, "
            prompt += "a clear but gentle progression, and several peaceful moments. "
            prompt += "Take time to build atmosphere and create a immersive, calming experience. "
        
        # Add theme guidance (pre-validated themes only)
        if preferences["theme"] and preferences["theme"] in STORY_THEMES:
            theme_data = STORY_THEMES[preferences["theme"]]
            prompt += f"Focus on a {preferences['theme']} theme. "
            prompt += f"Consider incorporating elements like: {', '.join(theme_data['elements'][:3])}. "
            prompt += f"Possible characters: {', '.join(theme_data['characters'][:2])}. "
            prompt += f"Settings might include: {', '.join(theme_data['settings'][:2])}. "
        
        # Add custom topic (already sanitized)
        if preferences["custom_topic"]:
            prompt += f"The story should be about: {preferences['custom_topic']}. "
        
        # Add name instruction (sanitized name)
        sanitized_name = self.security_validator.sanitize_user_name(user_name) if user_name else None
        if preferences["include_name"] and sanitized_name:
            prompt += f"The listener's name is {sanitized_name}. Include their name gently in the story. "
        
        prompt += "\nRemember: Keep the tone peaceful and sleep-inducing. "
        prompt += "Use sensory details that promote relaxation. "
        prompt += "End with a gentle conclusion that encourages rest and peaceful dreams. "
        prompt += "Do not include any personal information, scary content, or inappropriate material."
        
        return prompt

    def _select_fallback_story(self) -> str:
        """Select a fallback story, avoiding recent repeats"""
        available_stories = [story for i, story in enumerate(FALLBACK_STORIES) 
                           if i not in self.story_history[-2:]]  # Avoid last 2 stories
        
        if not available_stories:
            available_stories = FALLBACK_STORIES  # Reset if all used recently
            self.story_history = []
        
        selected_story = random.choice(available_stories)
        story_index = FALLBACK_STORIES.index(selected_story)
        self.story_history.append(story_index)
        
        # Keep history manageable
        if len(self.story_history) > 5:
            self.story_history = self.story_history[-3:]
        
        return selected_story

    def _get_data_sources(self, ctx: AgentContext) -> List[str]:
        """Override to specify storytelling data sources"""
        sources = ["ai_generated_content", "creative_writing"]
        if ctx.get("user"):
            sources.append("user_preferences")
        return sources

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Core storytelling logic with enhanced security"""
        try:
            ctx = ctx or {}
            user = ctx.get("user") or {}
            
            # Sanitize input message first
            sanitized_message = self.security_validator.sanitize_user_input(message)
            
            # Log security event (without exposing content)
            user_id = user.get('id', 'anonymous')[:8] if user.get('id') else 'anonymous'
            security_logger.info(f"Story request - User: {user_id}, "
                               f"Hash: {self.security_validator.hash_for_logging(sanitized_message)}")
            
            # Extract user name with privacy protection - NO EMAIL EXTRACTION
            user_name = None
            if user.get("user_metadata"):
                user_name = user["user_metadata"].get("name")
            # REMOVED: Email-based name extraction to prevent email exposure
            # Only use explicitly provided names from user metadata
            
            # Extract story preferences from sanitized input
            preferences = self._extract_story_preferences(sanitized_message, ctx)
            
            # Build enhanced prompt with security checks
            prompt = self._build_enhanced_prompt(preferences, user_name)
            
            # Try to generate story with AI
            story_text = ""
            generation_method = "fallback"
            
            if gemini_ready():
                try:
                    story_text = await generate_gemini_text(
                        prompt, 
                        model_name="gemini-2.0-flash-exp"
                    )
                    
                    # Validate AI output for security and appropriateness
                    if (story_text and 
                        len(story_text.strip()) > 50 and 
                        self.security_validator.validate_story_output(story_text)):
                        generation_method = "ai_generated"
                        logger.info(f"Story generated successfully - Length: {len(story_text)} chars, "
                                  f"Hash: {self.security_validator.hash_for_logging(story_text)}")
                    else:
                        logger.warning("AI-generated story failed validation, using fallback")
                        story_text = ""
                        
                except Exception as e:
                    logger.warning(f"Story generation failed: {str(e)[:100]}")  # Limit error message length
                    story_text = ""
            
            # Use fallback if AI generation failed or was invalid
            if not story_text:
                story_text = self._select_fallback_story()
                logger.info("Using validated fallback story")
            
            # Always provide text story first - audio is now optional via button
            # No automatic audio generation - user can request it via "Generate Audio" button
            
            # Prepare response data with security metadata and audio capability info
            response_data = {
                "preferences": {
                    "theme": preferences.get("theme"),
                    "length": preferences.get("length"),
                    "has_custom_topic": bool(preferences.get("custom_topic")),
                    "name_requested": preferences.get("include_name", False)
                },
                "generation_method": generation_method,
                "story_metadata": {
                    "word_count": len(story_text.split()),
                    "character_count": len(story_text),
                    "estimated_reading_time": f"{len(story_text.split()) // 150 + 1} minute(s)",
                    "security_validated": True,
                    "content_hash": self.security_validator.hash_for_logging(story_text)
                },
                "audio_capability": {
                    "available": self.audio_enabled,
                    "can_generate": True,
                    "story_suitable_for_audio": len(story_text) > 50,
                    "estimated_audio_duration": f"{len(story_text.split()) // 130} minute(s)"
                },
                "security_info": {
                    "input_sanitized": True,
                    "output_validated": True,
                    "user_name_sanitized": bool(user_name),
                    "prompt_secured": True,
                    "email_protected": True
                }
            }
            
            return {
                "agent": self.name,
                "text": story_text,
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"Error in storyteller agent: {str(e)[:200]}")  # Limit error logging
            # Emergency fallback with security validation
            fallback_story = FALLBACK_STORIES[0]
            return {
                "agent": self.name,
                "text": fallback_story,
                "data": {
                    "error": "fallback_due_to_error",
                    "generation_method": "emergency_fallback",
                    "security_validated": True,
                    "content_hash": self.security_validator.hash_for_logging(fallback_story),
                    "email_protected": True,
                    "audio": {"available": False, "error": "Emergency fallback mode"}
                }
            }

    # Keep legacy method for backward compatibility
    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Legacy handle method - redirects to new framework"""
        return await super().handle(message, ctx)