from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text, gemini_ready

SYSTEM_STYLE = (
    "You are a gentle bedtime storyteller. "
    "Write in simple, calming language suitable for winding down. "
    "Aim for ~180–300 words. "
    "No horror, no high-adrenaline action, no disturbing content. "
    "Keep it cozy, safe, hopeful. End softly."
)

FALLBACK_STORY = (
    "As the evening breeze drifted through the quiet room, a small lantern "
    "glowed like a sleepy firefly on the windowsill. Outside, a calm lake "
    "held the sky's last colors—lavender and soft silver—while reeds swayed "
    "like they were listening to a familiar lullaby. A traveler paused on the "
    "shore, toes in the cool sand, breathing with the water’s slow rhythm. "
    "They imagined each ripple as a thought passing by, kind and unhurried. "
    "A gentle owl blinked from a pine branch, then tucked its head beneath a "
    "wing. The lantern’s glow softened, and the traveler wrapped a blanket a "
    "little tighter, feeling warm and safe. The world settled into the hush "
    "of night, and the lake drew a curtain of stars across its surface. With "
    "one last easy breath, the traveler smiled, letting the quiet carry them "
    "toward rest—unfolding like a cloud, drifting into dream."
)

class StoryTellerAgent(BaseAgent):
    name = "storyteller"

    def _build_prompt(self, topic: Optional[str], user_name: Optional[str]) -> str:
        topic_part = f" Topic or vibe: {topic.strip()}." if topic else ""
        name_part = f" The listener's name is {user_name}. Work it in gently once." if user_name else ""
        return (
            f"{SYSTEM_STYLE}\n"
            "Write a short bedtime story that helps a person relax for sleep."
            f"{topic_part}{name_part}\n"
            "Keep sentences smooth and imagery soft (nature, warm light, calm water, "
            "quiet rooms). Avoid screens and caffeine references. No lists—just a single, "
            "flowing story. British or American spelling is fine. End with a gentle closing line."
        )

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        user = ctx.get("user") or {}
        user_name = (user.get("user_metadata") or {}).get("name") or user.get("email")

        # Allow users to steer the theme with a simple phrasing like:
        # "tell me a bedtime story about a lighthouse" → topic = "a lighthouse"
        # Otherwise we pass the raw message as a hint.
        topic_hint = ""
        m = (message or "").strip().lower()
        if m.startswith("story ") or m.startswith("tell ") or m.startswith("bedtime"):
            topic_hint = message
        elif len(m) > 0:
            topic_hint = message

        prompt = self._build_prompt(topic_hint, user_name)

        text = ""
        if gemini_ready():
            try:
                # generate_gemini_text is async; await it and pass the correct keyword name
                text = await generate_gemini_text(prompt, model_name="gemini-1.5-flash")
            except Exception:
                text = ""  # fall through to fallback

        if not text:
            text = FALLBACK_STORY

        return {
            "agent": self.name,
            "text": text,
            "data": {"topic": topic_hint or None}
        }