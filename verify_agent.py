import asyncio
import logging
from src.ai_agent import AIAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("🔹 Initializing AI Agent...")
    try:
        agent = AIAgent()
        
        query = "What is the UK grading system?"
        print(f"\n❓ Query: {query}")
        
        response = await agent.generate_response(query)
        print(f"\n🤖 Response: {response['text']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
