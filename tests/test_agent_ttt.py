import asyncio
import logging
from src.ai_agent import AIAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tests.test_agent")

async def test_agent():
    try:
        agent = AIAgent()
        query = "عندك جمبري؟"
        logger.info(f"Testing query: {query}")
        
        response = await agent.generate_response(query)
        
        logger.info(f"Response: {response}")
        
        if "text" in response and "audio" not in response:
             logger.info("✅ Agent returned text only as expected")
        elif "audio" in response:
             logger.error("❌ Agent returned audio field (unexpected)")
        else:
             logger.error("❌ Agent response format incorrect")

    except Exception as e:
        logger.error(f"❌ Error testing agent: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
