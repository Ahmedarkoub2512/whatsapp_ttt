import logging
from typing import Dict, Any
from src.knowledge_base import KnowledgeBase, get_formatted_context
from src.processor import MessageProcessor

logger = logging.getLogger("src.ai_agent")

RESPONSE_PROMPT = """
You are an assistant for international students in UK universities. Use only the following information to answer:

Available Information:
{context}

User Question:
{question}

Instructions:
- Answer in ENGLISH only
- Be concise and practical (2-3 sentences maximum)
- Focus on UK grading system, university resources, study skills, and student support
- If the answer is not in the information, say: "I don't have specific information about this in the student guides"
- Provide actionable advice for international students

Answer:
"""

class AIAgent:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.processor = MessageProcessor()
        self.history = [] # Keep history if needed, but the current prompt is single-turn
        logger.info("✅ AI Agent Initialized")

    async def generate_response(self, query: str) -> Dict[str, Any]:
        # Get context from ChromaDB based on the query
        context = get_formatted_context(query, self.kb)

        if not context:
             # Fallback if no context found, though the prompt handles it too.
             # But let's stick to the prompt logic.
             pass

        prompt = RESPONSE_PROMPT.format(context=context, question=query)

        # We pass the prompt as a single message or just the string.
        # The processor now handles string input or list.
        # Let's pass it as a string to be safe and simple.
        
        answer = await self.processor.run(prompt)
        
        # Optionally update history if we want to support multi-turn in future
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": answer})

        return {"text": answer}
