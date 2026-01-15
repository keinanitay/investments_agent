import os
import json
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to cost-effective model
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)  # For custom endpoints or local models

client = None
if OPENAI_API_KEY:
    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    client = AsyncOpenAI(**client_kwargs)
else:
    logger.warning("OPENAI_API_KEY not set. Response generation will use fallback mode.")


def build_system_prompt() -> str:
    """Builds the system prompt that defines the AI assistant's role and capabilities."""
    return """You are a helpful financial assistant specializing in the Tel Aviv Stock Exchange (TASE) and Israeli market analysis.

IMPORTANT: This bot is ONLY for investment-related questions. If a user asks about anything outside of investments, stocks, financial markets, or TASE-related topics, you must politely decline to answer and redirect them to ask investment-related questions instead.

Your role is to:
- Provide accurate and helpful information about TASE stocks, indices, and market trends
- Analyze financial data and provide insights
- Answer questions about investments, market conditions, and financial instruments
- Use markdown formatting for better readability (tables, lists, bold text, etc.)
- When discussing specific stocks or companies, provide structured information when relevant

Guidelines:
- Be concise but informative
- Use markdown tables for structured data (metrics, comparisons, etc.)
- Provide sources when referencing specific data
- If you don't have specific real-time data, acknowledge this and provide general guidance
- Format responses professionally with proper markdown syntax
- If asked about non-investment topics (e.g., general knowledge, other subjects), politely decline and remind the user that you are an investment assistant"""


async def generate_chat_title(user_message: str) -> str:
    """
    Generates a concise, descriptive title for a chat session based on the user's first message.
    
    Args:
        user_message: The first user message in the chat
    
    Returns:
        A short title (max 60 characters) describing the chat topic
    """
    # If no OpenAI client is configured, generate a simple title from the message
    if not client:
        # Fallback: use first 50 characters of the message or a default
        title = user_message[:50].strip()
        if len(title) < 10:
            title = "New Chat"
        return title
    
    try:
        # Use LLM to generate a concise title
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates concise, descriptive titles for investment-related chat conversations. Generate a short title (maximum 60 characters) that summarizes the main topic or question from the user's message. Return ONLY the title, no additional text."
                },
                {
                    "role": "user",
                    "content": f"Generate a title for this investment-related question: {user_message}"
                }
            ],
            temperature=0.7,
            max_tokens=30,
        )
        
        title = response.choices[0].message.content.strip()
        
        # Clean up the title (remove quotes if present, limit length)
        title = title.strip('"\'')
        if len(title) > 60:
            title = title[:57] + "..."
        
        # Ensure we have a valid title
        if not title or len(title) < 3:
            title = user_message[:50].strip() if len(user_message) > 3 else "New Chat"
        
        return title
        
    except Exception as e:
        logger.error(f"Error generating chat title: {str(e)}", exc_info=True)
        # Fallback to a simple title derived from the message
        title = user_message[:50].strip()
        if len(title) < 10:
            title = "New Chat"
        return title


def format_chat_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Formats chat history from database format to OpenAI API format.
    Converts ChatMessage objects to the format expected by OpenAI.
    """
    formatted = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        # Skip empty messages
        if not content:
            continue
            
        formatted.append({
            "role": role,
            "content": content
        })
    
    return formatted


async def generate_response(
    user_message: str,
    chat_history: List[Dict[str, Any]],
    user_context: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generates a contextual AI response based on the user's message and chat history.
    
    Args:
        user_message: The current user message
        chat_history: List of previous messages in the conversation
        user_context: Optional user-specific context (risk level, preferences, etc.)
    
    Returns:
        Tuple of (response_text, metadata_dict)
    """
    # If no OpenAI client is configured, return a fallback response
    if not client:
        logger.warning("OpenAI client not configured. Using fallback response.")
        return _generate_fallback_response(user_message, chat_history), {
            "type": "text",
            "sources": [],
            "execution_time": 0.0
        }
    
    try:
        # Format chat history for API
        formatted_messages = format_chat_history(chat_history)
        
        # Log history usage for debugging
        history_count = len(formatted_messages)
        logger.info(f"Using chat history: {history_count} previous messages in context")
        
        # Add the current user message
        formatted_messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Build system prompt with optional user context
        system_prompt = build_system_prompt()
        if user_context:
            risk_level = user_context.get("risk_level", "")
            if risk_level:
                system_prompt += f"\n\nUser Context: The user's risk level is {risk_level}. Consider this when providing investment advice."
        
        # Prepare messages for API call
        api_messages = [
            {"role": "system", "content": system_prompt}
        ] + formatted_messages
        
        # Call OpenAI API
        import time
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=api_messages,
            temperature=0.7,
            max_tokens=1000,
        )
        
        execution_time = time.time() - start_time
        
        # Extract response text
        ai_response_text = response.choices[0].message.content
        
        # Build metadata
        metadata = {
            "type": "text",
            "sources": [{"name": "TASE Bot AI"}],
            "execution_time": execution_time,
            "model": OPENAI_MODEL,
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
        }
        
        # Try to detect if response contains structured data that could be displayed as a chart
        # This is a simple heuristic - you can enhance this based on your needs
        if "|" in ai_response_text and "---" in ai_response_text:
            # Response contains markdown table, might want to add chart metadata
            metadata["has_table"] = True
        
        return ai_response_text, metadata
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        # Return a helpful error message
        error_response = (
            "I apologize, but I encountered an error while generating a response. "
            "Please try again in a moment. If the issue persists, please contact support."
        )
        return error_response, {
            "type": "error",
            "sources": [],
            "execution_time": 0.0,
            "error": str(e)
        }


def _generate_fallback_response(user_message: str, chat_history: List[Dict[str, Any]]) -> str:
    """
    Fallback response generator when OpenAI API is not available.
    Provides basic contextual responses based on keywords.
    """
    message_lower = user_message.lower()
    
    # Investment-related keywords
    investment_keywords = [
        "bank", "leumi", "hapoalim", "discount", "stock", "share", "equity", 
        "tase", "investment", "portfolio", "market", "financial", "trading",
        "dividend", "yield", "index", "bond", "security", "asset", "fund"
    ]
    
    # Check if message is investment-related
    is_investment_related = any(word in message_lower for word in investment_keywords)
    
    if not is_investment_related:
        return (
            "I'm sorry, but I'm an investment assistant specializing in TASE and Israeli market analysis. "
            "I can only help with investment-related questions.\n\n"
            "Please ask me about:\n"
            "- TASE stocks and companies\n"
            "- Market trends and analysis\n"
            "- Investment advice\n"
            "- Financial instruments\n"
            "- Portfolio management"
        )
    
    # Simple keyword-based responses for investment topics
    if any(word in message_lower for word in ["bank", "leumi", "hapoalim", "discount"]):
        return (
            "I'd be happy to help you with information about Israeli banks. "
            "However, I'm currently operating in fallback mode. "
            "To get detailed, AI-powered analysis, please configure the OPENAI_API_KEY environment variable.\n\n"
            "For real-time TASE data, visit: [TASE Website](https://www.tase.co.il)"
        )
    elif any(word in message_lower for word in ["stock", "share", "equity", "tase"]):
        return (
            "I can help you with TASE stock information. "
            "Currently, I'm operating in limited mode. "
            "Please configure OPENAI_API_KEY for full AI-powered responses.\n\n"
            "You can find official TASE data at: [TASE](https://www.tase.co.il)"
        )
    else:
        return (
            "Thank you for your message. I'm a TASE financial assistant. "
            "Currently operating in fallback mode. "
            "To enable full AI-powered responses, please configure the OPENAI_API_KEY environment variable.\n\n"
            "I can help you with:\n"
            "- Stock analysis\n"
            "- Market trends\n"
            "- Investment advice\n"
            "- TASE data queries"
        )
