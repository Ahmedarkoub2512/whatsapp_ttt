import os
import logging
import asyncio
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger("src.processor")

MODEL_NAME = "llama3.1:8b"

# Initialize Ollama LLM
llm = OllamaLLM(
    model=MODEL_NAME,
    temperature=0.2,
    max_tokens=300,
    streaming=False # Set to False for now as the current architecture expects a full response
)

class MessageProcessor:
    async def run(self, messages: list) -> str:
        try:
            loop = asyncio.get_running_loop()
            
            # Convert messages to the format expected by OllamaLLM or just pass the prompt
            # OllamaLLM expects a string prompt usually, but can handle messages if using ChatOllama
            # However, the user provided code uses OllamaLLM which is for text completion usually, 
            # but let's see how they used it.
            # User code: prompt = RESPONSE_PROMPT.format(...) -> llm.stream(prompt)
            # So it expects a string prompt.
            
            # The current ai_agent.py constructs a list of messages. 
            # I should probably change ai_agent.py to construct a string prompt, 
            # OR I can handle the conversion here.
            # For now, I will assume the input `messages` is a list of dicts and I'll convert it to a string prompt here
            # or better yet, I will update ai_agent.py to send a string prompt.
            
            # BUT, to keep this file robust, let's handle the input.
            # If messages is a list, we'll concatenate the content.
            
            prompt = ""
            if isinstance(messages, list):
                for msg in messages:
                    prompt += f"{msg['content']}\n\n"
            else:
                prompt = str(messages)

            # Run in executor to keep it async
            response = await loop.run_in_executor(
                None,
                lambda: llm.invoke(prompt)
            )

            result = str(response).strip()
            logger.info(f"✅ LLM Response: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Processor error: {e}")
            return "⚠️ An error occurred while processing the request."
