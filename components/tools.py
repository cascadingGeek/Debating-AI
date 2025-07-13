from openai import OpenAI
import logging
from config.index import MODEL

client = OpenAI()

def openai_web_search(query: str, perspective: str = "", context: str = "") -> str:
    """
    Conduct web search using OpenAI's web_search_preview tool
    
    Args:
        query: The main search query
        perspective: Additional perspective to add to search (e.g., "PRO benefits advantages")
        context: Additional context for the search (e.g., "round 1 evidence statistics")
    
    Returns:
        Formatted research findings as a string
    """
    try:
        full_query = f"{query}"
        if perspective:
            full_query += f" {perspective}"
        if context:
            full_query += f" {context}"
        
        full_query += " 2024 2025 latest research statistics current"
        
        response = client.responses.create(
            model=MODEL,
            tools=[{"type": "web_search_preview"}],
            input=f"""Research this topic thoroughly: {full_query}

Please provide comprehensive, current information including:
- Current statistics and data points
- Recent developments and trends (2024-2025)
- Expert opinions and authoritative studies
- Real-world examples and case studies
- Evidence-based insights

Format your response as structured research findings with clear sections and specific data points."""
        )
        
        if hasattr(response, 'output_text') and response.output_text:
            return response.output_text
        elif hasattr(response, 'content'):
            return str(response.content)
        else:
            return "Research completed but no specific data retrieved."
            
    except Exception as e:
        logging.error(f"Web search error: {str(e)}")
        return f"Web search temporarily unavailable. Proceeding with available knowledge. Error: {str(e)}"

def get_simple_llm_response(messages: list) -> str:
    """
    Get a simple LLM response without web search for fallback cases
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        String response from the model
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"LLM response error: {str(e)}")
        return f"Response generation failed: {str(e)}"