"""
Advanced Message Processor with Enhanced RAG
=============================================
Features:
- Hybrid Search (BM25 + Vector)
- Hierarchical Retrieval
- Cross-Encoder Re-ranking
- Smart context selection
"""

import logging
from typing import Optional
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

# Import the advanced retrieval system
from src.advanced_retrieval import AdvancedKnowledgeBase, get_formatted_context

load_dotenv()
logger = logging.getLogger("src.processor")

MODEL_NAME = "gemma2:2b"

# Initialize Ollama LLM
llm = OllamaLLM(
    model=MODEL_NAME,
    temperature=0.2,
    max_tokens=300,
    streaming=False
)


class MessageProcessor:
    """
    Advanced message processor with enhanced RAG capabilities
    """
    
    def __init__(self, collection_name: str = "Uk_docs"):
        logger.info("🚀 Initializing Advanced Message Processor...")
        try:
            # Initialize advanced knowledge base
            self.kb = AdvancedKnowledgeBase(collection_name=collection_name)
            logger.info("✅ Advanced RAG system initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize knowledge base: {e}")
            raise

    def _needs_knowledge_base(self, message: str) -> bool:
        """
        Determine if message requires knowledge base search
        """
        message_lower = message.lower()
        
        # Keywords that suggest need for KB
        kb_keywords = [
            'how', 'what', 'when', 'where', 'why', 'which',
            'visa', 'immigration', 'study', 'work', 'uk',
            'application', 'requirement', 'process', 'cost',
            'eligibility', 'document', 'fee', 'time'
        ]
        
        # Check if message is a question or contains keywords
        if any(keyword in message_lower for keyword in kb_keywords):
            return True
        
        # Check if it's a question
        if message.strip().endswith('?'):
            return True
        
        return False

    def _build_prompt(self, message: str, context: str) -> str:
        """
        Build enhanced prompt for LLM with context
        """
        if context:
            return f"""You are a helpful immigration assistant for the UK. Use the following information to answer the question accurately and concisely.

Context Information:
{context}

Question: {message}

Instructions:
- Answer based on the provided context
- Be specific and cite sources when possible
- If the context doesn't contain enough information, say so
- Keep your response concise and helpful
- Use bullet points for clarity when appropriate

Answer:"""
        else:
            return f"""You are a helpful immigration assistant for the UK. Answer the following question:

Question: {message}

Answer (be concise and helpful):"""

    def process_message(
        self, 
        message: str, 
        use_kb: bool = True,
        use_reranking: bool = True,
        n_results: int = 3
    ) -> str:
        """
        Process incoming message with advanced RAG
        
        Args:
            message: User message
            use_kb: Whether to use knowledge base
            use_reranking: Whether to use re-ranking (slower but more accurate)
            n_results: Number of context documents to retrieve
        """
        logger.info(f"📨 Processing message: '{message[:50]}...'")
        
        context = ""
        
        # Check if we need knowledge base
        if use_kb and self._needs_knowledge_base(message):
            logger.info("🔍 Retrieving context from knowledge base...")
            try:
                # Use advanced retrieval system
                context = get_formatted_context(
                    query=message,
                    kb=self.kb,
                    n_results=n_results
                )
                
                if context:
                    logger.info(f"✅ Retrieved context ({len(context)} chars)")
                else:
                    logger.info("⚠️ No relevant context found")
                    
            except Exception as e:
                logger.error(f"❌ Knowledge base search failed: {e}")
        else:
            logger.info("📝 Processing without knowledge base")
        
        # Build prompt
        prompt = self._build_prompt(message, context)
        
        # Generate response
        try:
            logger.info("🤖 Generating response with LLM...")
            response = llm.invoke(prompt)
            logger.info("✅ Response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            return "I apologize, but I encountered an error processing your message. Please try again."


# Singleton instance
_processor_instance: Optional[MessageProcessor] = None


def get_processor() -> MessageProcessor:
    """Get or create message processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = MessageProcessor()
    return _processor_instance


def process_user_message(message: str) -> str:
    """
    Main entry point for processing user messages
    """
    processor = get_processor()
    return processor.process_message(message)
