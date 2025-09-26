from typing import Optional, Dict, Any, List
import random
import logging

from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text, gemini_ready

logger = logging.getLogger(__name__)

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
    "medium": {"words": "180-300", "description": "A comfortable bedtime story"},
    "long": {"words": "300-450", "description": "A longer, more detailed story"}
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
        self.story_preferences = {}  # Track user preferences
        self.story_history = []  # Track recent stories for variety

    def _extract_story_preferences(self, message: str, ctx: Optional[AgentContext] = None) -> Dict[str, Any]:
        """Extract story preferences from user message and context"""
        preferences = {
            "theme": None,
            "length": "medium",
            "custom_topic": None,
            "include_name": True,
            "mood": "calm"
        }
        
        message_lower = message.lower() if message else ""
        
        # Extract theme preferences
        for theme in STORY_THEMES.keys():
            if theme in message_lower or any(element in message_lower for element in STORY_THEMES[theme]["elements"]):
                preferences["theme"] = theme
                break
        
        # Extract length preferences
        if any(word in message_lower for word in ["short", "brief", "quick"]):
            preferences["length"] = "short"
        elif any(word in message_lower for word in ["long", "detailed", "extended"]):
            preferences["length"] = "long"
        
        # Extract custom topic
        topic_indicators = ["about", "with", "featuring", "story of", "tale of"]
        for indicator in topic_indicators:
            if indicator in message_lower:
                topic_start = message_lower.find(indicator) + len(indicator)
                topic_end = len(message)
                custom_topic = message[topic_start:topic_end].strip()
                if custom_topic:
                    preferences["custom_topic"] = custom_topic
                break
        
        # Check for name preference
        if any(word in message_lower for word in ["no name", "anonymous", "without name"]):
            preferences["include_name"] = False
        
        return preferences

    def _build_enhanced_prompt(self, preferences: Dict[str, Any], user_name: Optional[str]) -> str:
        """Build an enhanced prompt based on user preferences"""
        length_info = STORY_LENGTHS[preferences["length"]]
        
        prompt = f"{SYSTEM_STYLE_BASE}\n\n"
        prompt += f"Write a {preferences['length']} bedtime story ({length_info['words']} words). "
        
        # Add theme guidance
        if preferences["theme"]:
            theme_data = STORY_THEMES[preferences["theme"]]
            prompt += f"Focus on a {preferences['theme']} theme. "
            prompt += f"Consider incorporating elements like: {', '.join(theme_data['elements'][:3])}. "
            prompt += f"Possible characters: {', '.join(theme_data['characters'][:2])}. "
            prompt += f"Settings might include: {', '.join(theme_data['settings'][:2])}. "
        
        # Add custom topic
        if preferences["custom_topic"]:
            prompt += f"The story should be about: {preferences['custom_topic']}. "
        
        # Add name instruction
        if preferences["include_name"] and user_name:
            prompt += f"The listener's name is {user_name}. Include their name gently in the story. "
        
        prompt += "\nRemember: Keep the tone peaceful and sleep-inducing. "
        prompt += "Use sensory details that promote relaxation. "
        prompt += "End with a gentle conclusion that encourages rest and peaceful dreams."
        
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
        """Core storytelling logic with enhancements"""
        try:
            ctx = ctx or {}
            user = ctx.get("user") or {}
            user_name = None
            
            # Extract user name from various sources
            if user.get("user_metadata"):
                user_name = user["user_metadata"].get("name")
            if not user_name and user.get("email"):
                user_name = user["email"].split("@")[0].title()  # Use email username as name
            
            # Extract story preferences
            preferences = self._extract_story_preferences(message, ctx)
            
            # Build enhanced prompt
            prompt = self._build_enhanced_prompt(preferences, user_name)
            
            # Try to generate story with AI
            story_text = ""
            generation_method = "fallback"
            
            if gemini_ready():
                try:
                    story_text = await generate_gemini_text(
                        prompt, 
                        model_name="gemini-1.5-flash-8b",
                        temperature=0.7  # Slightly creative but controlled
                    )
                    if story_text and len(story_text.strip()) > 50:  # Minimum viable story length
                        generation_method = "ai_generated"
                        logger.info(f"Generated story using AI: {len(story_text)} characters")
                    else:
                        story_text = ""
                except Exception as e:
                    logger.warning(f"Story generation failed: {e}")
                    story_text = ""
            
            # Use fallback if AI generation failed
            if not story_text:
                story_text = self._select_fallback_story()
                logger.info("Using fallback story")
            
            # Prepare response data with metadata
            response_data = {
                "preferences": preferences,
                "generation_method": generation_method,
                "story_length": len(story_text.split()),
                "theme_used": preferences.get("theme"),
                "custom_topic": preferences.get("custom_topic"),
                "user_name_included": bool(user_name and preferences.get("include_name")),
                "story_metadata": {
                    "word_count": len(story_text.split()),
                    "character_count": len(story_text),
                    "estimated_reading_time": f"{len(story_text.split()) // 150 + 1} minute(s)"
                }
            }
            
            return {
                "agent": self.name,
                "text": story_text,
                "data": response_data
            }
            
        except Exception as e:
            logger.error(f"Error in storyteller agent: {e}")
            # Emergency fallback
            return {
                "agent": self.name,
                "text": FALLBACK_STORIES[0],
                "data": {
                    "error": "fallback_due_to_error",
                    "generation_method": "emergency_fallback"
                }
            }

    # Keep legacy method for backward compatibility
    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Legacy handle method - redirects to new framework"""
        return await super().handle(message, ctx)