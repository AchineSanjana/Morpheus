from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text
from app.schemas import InfoResponse, AgentResponseModel

class InformationAgent(BaseAgent):
    """
    Uses an LLM to answer general knowledge questions about sleep.
    """
    name = "information"

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        prompt = f"""
        You are a helpful sleep science explainer. Your goal is to answer the user's question clearly and concisely, based on general knowledge about sleep science.

        - Keep your answer focused on the user's question.
        - Use formatting like bullet points or bold text to make the information easy to digest.
        - At the end of your response, ALWAYS include the disclaimer: "_This is for informational purposes and is not medical advice._"

        User's question: "{message}"

        Your answer:
        """

        response_text = await generate_gemini_text(prompt)

        if not response_text:
            response_text = "I'm sorry, I couldn't retrieve information on that topic at the moment. Please try asking in a different way."

        # Validate response
        info = InfoResponse(topic="general_inquiry", text=response_text)
        resp = AgentResponseModel(agent=self.name, text=info.text, data={"topic": info.topic})
        return resp.dict()

