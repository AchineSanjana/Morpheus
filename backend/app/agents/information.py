from typing import Optional, Dict, List
from . import BaseAgent, AgentContext, AgentResponse

# Tiny curated KB. You can expand this (or replace with your own vector search later).
KB: Dict[str, Dict[str, List[str] | str]] = {
    "caffeine": {
        "bullets": [
            "Caffeine can delay sleep and reduce deep sleep.",
            "Avoid caffeine **within 6–8 hours** of bedtime; many people choose after **3 pm** cut-off.",
        ],
        "sources": [
            "CDC: Sleep and Caffeine — https://www.cdc.gov/sleep/",
            "NIH MedlinePlus: Caffeine — https://medlineplus.gov/caffeine.html",
        ],
    },
    "screens": {
        "bullets": [
            "Bright light and engaging content close to bedtime can delay sleep onset.",
            "Try **60–90 min screen-free** wind-down; dim lights, use night-shift if needed.",
        ],
        "sources": [
            "NIH: Light exposure and sleep — https://www.nih.gov/",
            "AASM (sleep experts): Sleep hygiene tips — https://sleepeducation.org/",
        ],
    },
    "schedule": {
        "bullets": [
            "A **consistent wake-up time** is the strongest anchor for circadian rhythm.",
            "Gradually shift by **15–30 min** every few nights if you need to move your schedule.",
        ],
        "sources": [
            "CDC: Healthy Sleep — https://www.cdc.gov/sleep/",
            "NIH: Circadian Rhythm — https://www.nigms.nih.gov/education/fact-sheets/Pages/circadian-rhythms.aspx",
        ],
    },
    "naps": {
        "bullets": [
            "Short naps (~10–20 min) can be refreshing; avoid late-day naps if they harm night sleep.",
        ],
        "sources": [
            "NIH: Napping — https://www.nih.gov/",
        ],
    },
}

def _match_topic(message: str) -> str:
    t = message.lower()
    if "caff" in t or "coffee" in t: return "caffeine"
    if "screen" in t or "phone" in t or "blue light" in t: return "screens"
    if "schedule" in t or "bedtime" in t or "wake" in t: return "schedule"
    if "nap" in t: return "naps"
    return "schedule"

class InformationAgent(BaseAgent):
    """
    Evidence-based librarian: short guidance + pointers to reputable sources.
    """
    name = "information"

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        topic = _match_topic(message)
        card = KB.get(topic, KB["schedule"])
        bullets = "\n".join(f"• {b}" for b in card["bullets"])  # type: ignore
        sources = "\n".join(f"- {s}" for s in card["sources"])  # type: ignore
        text = f"**{topic.title()} — key points**\n{bullets}\n\n**Sources**\n{sources}"
        return {"agent": self.name, "text": text, "data": {"topic": topic}}
