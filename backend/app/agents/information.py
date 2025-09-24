from typing import Optional, Dict, List, Any, TypedDict
import os
import json
import re
import httpx
from . import BaseAgent, AgentContext, AgentResponse

# JSON schema for IR responses
class IRJson(TypedDict):
    answer: str
    bullets: List[str]
    citations: List[Dict[str, str]]
    safety_flag: bool
    disclaimer: str

# Curated KB (authoritative sources only). Expand as needed.
KB: Dict[str, Dict[str, Any]] = {
    "caffeine": {
        "answer": (
            "Yes. Caffeine can delay sleep, shorten total sleep time, and lighten sleep. "
            "Avoid caffeine for at least 6 hours before bedtime; 8–10 hours if you’re sensitive."
        ),
        "bullets": [
            "Stop coffee/tea/energy drinks 6–8 hours before bed; try 8–10 hours if sleep is fragile.",
            "Use decaf or herbal tea after lunch.",
            "Aim for ≤400 mg caffeine/day (less if pregnant or insomnia-prone).",
            "Watch hidden sources: soda, chocolate, pre-workouts, some cold/pain meds.",
        ],
        "citations": [
            {
                "title": "How You Can Sleep Better (sleep hygiene)",
                "url": "https://www.cdc.gov/sleep/about/sleep-hygiene.html",
                "publisher": "CDC",
            },
            {
                "title": "Caffeine and Sleep",
                "url": "https://sleepeducation.org/sleep-hygiene-caffeine-and-sleep/",
                "publisher": "American Academy of Sleep Medicine (AASM)",
            },
            {
                "title": "Spilling the Beans: How Much Caffeine is Too Much?",
                "url": "https://www.fda.gov/consumers/consumer-updates/spilling-beans-how-much-caffeine-too-much",
                "publisher": "U.S. Food and Drug Administration (FDA)",
            },
        ],
        "disclaimer": "General guidance, not medical advice.",
    },
    "screens": {
        "answer": (
            "Bright screens and engaging content near bedtime can delay sleep onset. "
            "Aim for 60–90 minutes of screen-free wind-down under dim light."
        ),
        "bullets": [
            "Start a 60–90 minute wind-down with lights dimmed.",
            "Use night-shift modes if you must use screens; lower brightness.",
            "Swap to relaxing, non-screen activities (reading paper, gentle stretches).",
        ],
        "citations": [
            {
                "title": "Healthy Sleep: Tips",
                "url": "https://sleepeducation.org/healthy-sleep/healthy-sleep-habits/",
                "publisher": "American Academy of Sleep Medicine (AASM)",
            },
            {
                "title": "Circadian Rhythms Fact Sheet",
                "url": "https://www.nigms.nih.gov/education/fact-sheets/Pages/circadian-rhythms.aspx",
                "publisher": "NIH (NIGMS)",
            },
        ],
        "disclaimer": "General guidance, not medical advice.",
    },
    "schedule": {
        "answer": (
            "A regular schedule strengthens your body clock. Keep a consistent wake time; "
            "shift by 15–30 minutes every few days if you need to move your schedule."
        ),
        "bullets": [
            "Prioritize a fixed wake time daily; let bedtime follow when sleepy.",
            "If adjusting, move wake time by 15–30 minutes every 2–3 days.",
            "Get morning light exposure for 10–30 minutes to reinforce timing.",
        ],
        "citations": [
            {
                "title": "How You Can Sleep Better (sleep hygiene)",
                "url": "https://www.cdc.gov/sleep/about/sleep-hygiene.html",
                "publisher": "CDC",
            },
            {
                "title": "Circadian Rhythms Fact Sheet",
                "url": "https://www.nigms.nih.gov/education/fact-sheets/Pages/circadian-rhythms.aspx",
                "publisher": "NIH (NIGMS)",
            },
        ],
        "disclaimer": "General guidance, not medical advice.",
    },
    "naps": {
        "answer": (
            "Short midday naps (10–20 minutes) can boost alertness. Avoid late-day naps if they make night sleep harder."
        ),
        "bullets": [
            "Keep naps ~10–20 minutes; set an alarm.",
            "Finish naps by mid-afternoon if nighttime sleep is sensitive.",
        ],
        "citations": [
            {
                "title": "Healthy Sleep: Napping",
                "url": "https://sleepeducation.org/healthy-sleep/healthy-sleep-habits/",
                "publisher": "American Academy of Sleep Medicine (AASM)",
            }
        ],
        "disclaimer": "General guidance, not medical advice.",
    },
}

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "caffeine": ["caff", "coffee", "espresso", "tea", "latte", "energy drink"],
    "screens": ["screen", "phone", "device", "tablet", "blue light", "tv", "youtube", "tiktok", "instagram"],
    "schedule": ["schedule", "bedtime", "wake", "wake-up", "regular", "weekend"],
    "naps": ["nap", "napping", "siesta"],
}

RED_FLAG_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"insomnia\s*(for|>).*?(3\s*months|three\s*months|90\s*days)", re.I),
    re.compile(r"snor(e|ing).*?(loud|chok|stop\s*breath|apnea)", re.I),
    re.compile(r"(sleepy.*?drive|fall\s+asleep\s+(at|while)\s+(the\s+)?wheel)", re.I),
    re.compile(r"suicid|harm myself|kill myself", re.I),
]


def _match_topic(message: str) -> Optional[str]:
    t = message.lower()
    for topic, keys in TOPIC_KEYWORDS.items():
        if any(k in t for k in keys):
            return topic
    return None


def _detect_red_flags(message: str) -> bool:
    t = message.lower()
    return any(p.search(t) for p in RED_FLAG_PATTERNS)


def _kb_response(topic: str) -> IRJson:
    card = KB.get(topic)
    if not card:
        return {
            "answer": "I don’t have enough evidence to answer that.",
            "bullets": [],
            "citations": [],
            "safety_flag": False,
            "disclaimer": "",
        }
    return {
        "answer": card["answer"],
        "bullets": card["bullets"],
        "citations": card["citations"],
        "safety_flag": False,
        "disclaimer": card.get("disclaimer", ""),
    }


def _insufficient() -> IRJson:
    return {
        "answer": "I don’t have enough evidence to answer that.",
        "bullets": [],
        "citations": [],
        "safety_flag": False,
        "disclaimer": "",
    }


def _strip_code_fences(text: str) -> str:
    s = text.strip()
    # Remove triple backtick fences with or without language
    if s.startswith("```"):
        # remove first line of backticks (and optional language tag)
        s = s.split("\n", 1)[-1]
    if s.endswith("```"):
        s = s.rsplit("\n", 1)[0] if "\n" in s else s[:-3]
    # Remove inline single backticks if the whole content is fenced that way
    if s.startswith("`") and s.endswith("`") and len(s) >= 2:
        s = s[1:-1]
    return s.strip()


def _extract_first_json(text: str) -> Optional[str]:
    # Find first JSON object by brace matching
    s = text
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return s[start:i+1]
    return None


async def _call_gemini(prompt: str) -> Optional[IRJson]:
    """Optional Gemini fallback. Uses GOOGLE_API_KEY or GEMINI_API_KEY. Returns parsed IRJson or None."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    system_instruction = (
        "Role: You are an evidence-based librarian for sleep health. "
        "Rules: Use only authoritative sources (CDC, NIH, WHO, AASM, FDA, Cochrane, USPSTF). "
        "Return strict JSON with keys: answer (<=120 words), bullets (array of strings), "
        "citations (array of {title,url,publisher}), safety_flag (boolean), disclaimer (string or empty). "
        "Never invent URLs or statistics. If unsure, set answer to 'I don’t have enough evidence to answer that.' "
        "and leave bullets/citations empty. Keep tone practical and non-alarmist."
    )

    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": system_instruction + "\n\nQuestion: " + prompt}]}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.post(url, params={"key": api_key}, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None

    # Collect potential text outputs from all candidates/parts
    texts: List[str] = []
    try:
        for cand in data.get("candidates", []) or []:
            content = cand.get("content", {}) or {}
            for part in content.get("parts", []) or []:
                t = part.get("text", "")
                if isinstance(t, str) and t.strip():
                    texts.append(t.strip())
    except Exception:
        return None

    for raw in texts:
        stripped = _strip_code_fences(raw)
        json_str = _extract_first_json(stripped)
        if not json_str:
            continue
        try:
            parsed = json.loads(json_str)
        except Exception:
            continue
        # Validate and normalize
        if not isinstance(parsed, dict):
            continue
        required = ["answer", "bullets", "citations", "safety_flag", "disclaimer"]
        if any(k not in parsed for k in required):
            continue
        # Normalize bullets
        bullets = parsed.get("bullets", [])
        if not isinstance(bullets, list):
            bullets = []
        else:
            bullets = [b for b in bullets if isinstance(b, str)]
        # Normalize citations
        citations_in = parsed.get("citations", [])
        citations: List[Dict[str, str]] = []
        if isinstance(citations_in, list):
            for c in citations_in:
                if isinstance(c, dict):
                    title = c.get("title") if isinstance(c.get("title"), str) else None
                    url_field = c.get("url") if isinstance(c.get("url"), str) else None
                    publisher = c.get("publisher") if isinstance(c.get("publisher"), str) else None
                    if title and url_field and publisher:
                        citations.append({"title": title, "url": url_field, "publisher": publisher})
        answer = parsed.get("answer")
        if not isinstance(answer, str):
            answer = "I don’t have enough evidence to answer that."
            bullets = []
            citations = []
        # Constrain answer length (≤800 chars)
        if len(answer) > 800:
            answer = answer[:800]
        safety_flag = bool(parsed.get("safety_flag", False))
        disclaimer = parsed.get("disclaimer") if isinstance(parsed.get("disclaimer"), str) else ""
        return {
            "answer": answer,
            "bullets": bullets,
            "citations": citations,
            "safety_flag": safety_flag,
            "disclaimer": disclaimer,
        }

    return None


class InformationAgent(BaseAgent):
    """
    Evidence-based librarian: returns strict JSON (as string) in AgentResponse.text.
    Prefers curated KB; optional Gemini fallback if not covered.
    """
    name = "information"

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        # Safety routing
        safety = _detect_red_flags(message or "")
        if safety:
            result: IRJson = {
                "answer": (
                    "Your message suggests a safety concern. Please use the Safety Agent for urgent guidance and clinical routing."
                ),
                "bullets": [
                    "Avoid driving or hazardous activities if very sleepy.",
                    "Seek medical care promptly for symptoms like choking at night or suicidal thoughts.",
                ],
                "citations": [],
                "safety_flag": True,
                "disclaimer": "This is general safety information, not medical advice.",
            }
            return {"agent": self.name, "text": json.dumps(result), "data": result}  # type: ignore

        # Topic match and KB-first answer
        topic = _match_topic(message or "")
        if topic and topic in KB:
            result = _kb_response(topic)
            return {"agent": self.name, "text": json.dumps(result), "data": result}  # type: ignore

        # Gemini fallback if available
        gem = await _call_gemini(message or "")
        if gem:
            return {"agent": self.name, "text": json.dumps(gem), "data": gem}  # type: ignore

        # Insufficient evidence default per specification
        result = _insufficient()
        return {"agent": self.name, "text": json.dumps(result), "data": result}  # type: ignore
