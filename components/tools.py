from langchain_tavily import TavilySearch
from langchain.tools import Tool
from typing import List, Dict, Any, Optional
import re
import time
import os
from bot_instructions import tool_bot_prompt
from config.index import TAVILY_API_KEY

# Initialize Tavily search wrapper
def initialize_tavily_search():
    """Initialize Tavily search with proper API key handling"""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY environment variable is required")
    
    return TavilySearch(
        tavily_api_key=TAVILY_API_KEY,
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True
    )

# Initialize search wrapper with error handling
try:
    search = initialize_tavily_search()
    search_available = True
except Exception as e:
    print(f"Warning: Tavily search not available: {e}")
    search_available = False
    search = None

# Enhanced search tool with Tavily integration
def tavily_search_function(query: str) -> str:
    """Enhanced search function using Tavily"""
    if not search_available or not search:
        return f"Search unavailable. Please ensure TAVILY_API_KEY is set. Query was: {query}"
    
    try:
        # Use Tavily's advanced search capabilities
        results = search.run(query)
        
        # If results is a string, return it directly
        if isinstance(results, str):
            return results
        
        # If results is a list or dict, process it
        if isinstance(results, list):
            # Join multiple results
            return "\n\n".join([str(result) for result in results])
        elif isinstance(results, dict):
            # Extract relevant information from dict
            if 'answer' in results:
                return results['answer']
            elif 'content' in results:
                return results['content']
            else:
                return str(results)
        
        return str(results)
        
    except Exception as e:
        return f"Search error for query '{query}': {str(e)}"

search_tool = Tool(
    name="Tavily_Web_Research",
    func=tavily_search_function,
    description=tool_bot_prompt,
)

class ResearchBot:
    """
    Advanced research assistant for debate bots using Tavily Search
    """
    
    def __init__(self, search_tool: Tool):
        self.search_tool = search_tool
        self.research_cache: Dict[str, str] = {}  # Simple cache to avoid duplicate searches
    
    def conduct_research(self, topic: str, perspective: str, specific_queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Conduct comprehensive research for a debate topic using Tavily
        
        Args:
            topic: The main debate topic
            perspective: "PRO" or "CON" 
            specific_queries: Optional list of specific search queries
            
        Returns:
            Dict containing research results and insights
        """
        
        # Generate search queries based on topic and perspective
        if not specific_queries:
            specific_queries = self._generate_search_queries(topic, perspective)
        
        research_results: Dict[str, Any] = {
            "topic": topic,
            "perspective": perspective,
            "findings": [],
            "statistics": [],
            "expert_opinions": [],
            "case_studies": [],
            "current_events": [],
            "summary": ""
        }
        
        # Conduct searches with rate limiting
        for query in specific_queries[:4]:  # Limit to 4 searches for comprehensive coverage
            try:
                # Check cache first
                cache_key = f"{query}_{perspective}"
                if cache_key in self.research_cache:
                    result = self.research_cache[cache_key]
                else:
                    result = self.search_tool.run(query)
                    self.research_cache[cache_key] = result
                    time.sleep(0.5)  # Rate limiting for Tavily
                
                # Process and categorize results
                processed_result = self._process_search_result(query, result)
                research_results["findings"].append(processed_result)
                
                # Extract specific types of information
                if any(keyword in query.lower() for keyword in ['statistic', 'data', 'number', 'percent', 'study']):
                    research_results["statistics"].append(processed_result)
                elif any(keyword in query.lower() for keyword in ['expert', 'opinion', 'research', 'analysis']):
                    research_results["expert_opinions"].append(processed_result)
                elif any(keyword in query.lower() for keyword in ['case', 'example', 'instance', 'real']):
                    research_results["case_studies"].append(processed_result)
                elif any(keyword in query.lower() for keyword in ['news', '2024', '2025', 'recent', 'latest']):
                    research_results["current_events"].append(processed_result)
                    
            except Exception as e:
                print(f"Research error for query '{query}': {e}")
                continue
        
        # Generate research summary
        research_results["summary"] = self._generate_research_summary(research_results)
        
        return research_results
    
    def _generate_search_queries(self, topic: str, perspective: str) -> List[str]:
        """Generate targeted search queries based on topic and perspective"""
        
        # Extract key terms from topic
        topic_lower = topic.lower()
        
        # Base queries that work for most topics
        base_queries = []
        
        if perspective == "PRO":
            base_queries = [
                f"{topic} benefits statistics 2024 2025",
                f"{topic} positive impact research study",
                f"{topic} success stories case studies",
                f"{topic} expert support analysis",
                f"{topic} economic advantages data"
            ]
        else:  # CON
            base_queries = [
                f"{topic} risks problems statistics 2024 2025", 
                f"{topic} negative impact research study",
                f"{topic} failures case studies",
                f"{topic} expert criticism analysis",
                f"{topic} costs disadvantages data"
            ]
        
        # Add topic-specific queries with current focus
        if any(keyword in topic_lower for keyword in ['ai', 'artificial intelligence', 'machine learning']):
            if perspective == "PRO":
                base_queries.extend([
                    "AI productivity economic benefits 2024 study",
                    "artificial intelligence job creation research 2024"
                ])
            else:
                base_queries.extend([
                    "AI job displacement statistics 2024 study",
                    "artificial intelligence bias ethics problems 2024"
                ])
                
        elif any(keyword in topic_lower for keyword in ['climate', 'environment', 'renewable']):
            if perspective == "PRO":
                base_queries.extend([
                    "renewable energy economic benefits 2024 data",
                    "green technology investment returns 2024"
                ])
            else:
                base_queries.extend([
                    "renewable energy costs challenges 2024 study",
                    "green transition economic burden 2024"
                ])
                
        elif any(keyword in topic_lower for keyword in ['health', 'medical', 'healthcare']):
            if perspective == "PRO":
                base_queries.extend([
                    "digital health technology benefits 2024 study",
                    "telemedicine effectiveness research 2024"
                ])
            else:
                base_queries.extend([
                    "digital health privacy risks 2024 study",
                    "telemedicine limitations problems 2024"
                ])
        
        # Add current events and recent data
        base_queries.append(f"{topic} latest news developments 2024 2025")
        
        return base_queries[:5]  # Return top 5 most relevant queries
    
    def _process_search_result(self, query: str, result: str) -> Dict[str, Any]:
        """Process and clean search results from Tavily"""
        
        # Clean up the result text
        cleaned_result = re.sub(r'\s+', ' ', result).strip()
        
        # Extract key information
        processed = {
            "query": query,
            "content": cleaned_result[:800] + "..." if len(cleaned_result) > 800 else cleaned_result,
            "key_points": self._extract_key_points(cleaned_result),
            "source_type": self._identify_source_type(cleaned_result),
            "recency": self._extract_recency_indicators(cleaned_result)
        }
        
        return processed
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from search results"""
        
        key_points: List[str] = []
        
        # Look for statistics (numbers with %)
        stats = re.findall(r'\d+(?:\.\d+)?%', text)
        if stats:
            key_points.extend([f"Statistic: {stat}" for stat in stats[:3]])
        
        # Look for years (recent data)
        years = re.findall(r'20(2[0-5]|1[89])', text)
        if years:
            recent_years = [year for year in set(years) if int(year) >= 2022]
            if recent_years:
                key_points.append(f"Recent data from: {', '.join(recent_years)}")
        
        # Look for dollar amounts
        money = re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|trillion|thousand))?', text, re.IGNORECASE)
        if money:
            key_points.extend([f"Financial figure: {amount}" for amount in money[:2]])
        
        # Look for growth/change indicators
        growth = re.findall(r'(?:increase|decrease|growth|decline|rise|fall)(?:d|s)?\s+(?:of|by)?\s*\d+(?:\.\d+)?%?', text, re.IGNORECASE)
        if growth:
            key_points.extend([f"Trend: {trend}" for trend in growth[:2]])
        
        return key_points[:4]  # Return top 4 key points
    
    def _extract_recency_indicators(self, text: str) -> List[str]:
        """Extract indicators of how recent the information is"""
        
        recency_indicators = []
        
        # Look for recent time references
        recent_terms = re.findall(r'(?:recent|latest|new|current|this year|2024|2025|last month|past year)', text, re.IGNORECASE)
        if recent_terms:
            recency_indicators.extend(list(set(recent_terms))[:3])
        
        return recency_indicators
    
    def _identify_source_type(self, text: str) -> str:
        """Identify the type of source from the content"""
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['study', 'research', 'journal', 'paper', 'university']):
            return "Academic/Research"
        elif any(keyword in text_lower for keyword in ['government', 'gov', 'agency', 'department', 'federal']):
            return "Government"
        elif any(keyword in text_lower for keyword in ['news', 'report', 'article', 'reuters', 'bloomberg', 'cnn']):
            return "News/Media"
        elif any(keyword in text_lower for keyword in ['company', 'corporate', 'business', 'industry']):
            return "Corporate"
        elif any(keyword in text_lower for keyword in ['expert', 'analyst', 'economist', 'researcher']):
            return "Expert Opinion"
        else:
            return "General"
    
    def _generate_research_summary(self, research_results: Dict[str, Any]) -> str:
        """Generate a summary of research findings"""
        
        findings_count = len(research_results["findings"])
        stats_count = len(research_results["statistics"])
        
        summary = f"Comprehensive research completed: {findings_count} high-quality sources analyzed via Tavily advanced search"
        
        if stats_count > 0:
            summary += f", {stats_count} statistical references with current data"
        
        if research_results["expert_opinions"]:
            summary += f", {len(research_results['expert_opinions'])} expert analysis sources"
        
        if research_results["current_events"]:
            summary += f", {len(research_results['current_events'])} recent developments tracked"
        
        summary += f". {research_results['perspective']} perspective supported with real-time evidence and authoritative sources."
        
        return summary

# Initialize the research bot
research_bot = ResearchBot(search_tool)

# Enhanced research function for easy integration
def enhanced_research(topic: str, perspective: str, specific_focus: Optional[str] = None) -> str:
    """
    Simplified research function for bot integration with Tavily
    
    Args:
        topic: Main debate topic
        perspective: "PRO" or "CON"
        specific_focus: Optional specific aspect to research
        
    Returns:
        Formatted research summary for use in arguments
    """
    
    try:
        # Generate targeted queries
        queries: List[str] = []
        if specific_focus:
            queries.append(f"{topic} {specific_focus} {perspective.lower()} 2024 2025")
            queries.append(f"{topic} {specific_focus} latest research study")
        
        # Conduct research
        results = research_bot.conduct_research(topic, perspective, queries)
        
        # Format for bot consumption
        formatted_output = f"CURRENT RESEARCH FINDINGS ({perspective} perspective) - Powered by Tavily:\n\n"
        
        # Include top 3 findings for comprehensive coverage
        for i, finding in enumerate(results["findings"][:3], 1):
            formatted_output += f"{i}. Query: {finding['query']}\n"
            formatted_output += f"   Latest Information: {finding['content'][:300]}...\n"
            
            # Safely handle key_points
            key_points = finding.get('key_points', [])
            if key_points and isinstance(key_points, list):
                formatted_output += f"   Key Data Points: {'; '.join(key_points)}\n"
            
            formatted_output += f"   Source Type: {finding['source_type']}\n"
            
            # Add recency indicators
            recency = finding.get('recency', [])
            if recency:
                formatted_output += f"   Recency: {', '.join(recency)}\n"
            
            formatted_output += "\n"
        
        # Add summary
        formatted_output += f"RESEARCH SUMMARY: {results['summary']}\n\n"
        formatted_output += "INSTRUCTION: Integrate this current, verified information into your argument. "
        formatted_output += "Use specific statistics, expert opinions, and recent developments to strengthen your position."
        
        return formatted_output
        
    except Exception as e:
        # Return fallback message if research fails
        return f"Research system temporarily unavailable for {perspective} perspective on '{topic}'. Error: {str(e)}. Proceeding with general knowledge - ensure TAVILY_API_KEY is properly configured."