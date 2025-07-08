from langchain_community.chat_models import ChatOpenAI
from typing import TypedDict, List, Dict, Any, Annotated, Union, NotRequired, Optional
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
import os
from bot_instructions import topic_bot_prompt, pro_bot_prompt, con_bot_prompt, judge_bot_prompt
from components.tools import enhanced_research


MODEL = "gpt-4o-mini"

llm = ChatOpenAI(model=MODEL, temperature=0.7)

# Helper function to safely get content from message objects or dicts
def get_content(message) -> str:
    """Safely extract content from either a message object or dictionary"""
    if hasattr(message, 'content'):
        return message.content
    elif isinstance(message, dict) and 'content' in message:
        return message['content']
    else:
        return str(message)

# State Definition with optional fields
class DebateRound(TypedDict):
    pro: str
    con: str
    round_number: int

class State(TypedDict):
    topic: Annotated[List[Dict[str, str]], add_messages]
    rounds: List[DebateRound]
    judge: Annotated[List[Dict[str, str]], add_messages]
    prompt: Annotated[List[Dict[str, str]], add_messages]
    current_round: int
    winner: Union[str, None]
    pro_argument: NotRequired[Annotated[List[Dict[str, str]], add_messages]] 
    con_argument: NotRequired[Annotated[List[Dict[str, str]], add_messages]] 

# Partial state update types for better type safety
class TopicUpdate(TypedDict):
    topic: List[Dict[str, str]]
    rounds: List[DebateRound]
    current_round: int
    winner: Union[str, None]

class ProUpdate(TypedDict):
    pro_argument: List[Dict[str, str]]
    current_round: int

class ConUpdate(TypedDict):
    con_argument: List[Dict[str, str]]

class JudgeUpdate(TypedDict):
    judge: List[Dict[str, str]]
    winner: Union[str, None]

class RoundsUpdate(TypedDict):
    rounds: List[DebateRound]

# Bot Functions with research integration
def get_debate_history(state: State) -> str:
    """Compiles the debate history for context"""
    history = []
    for i, round_data in enumerate(state["rounds"]):
        history.append(f"\nROUND {i+1}:")
        history.append(f"PRO: {round_data['pro']}")
        history.append(f"CON: {round_data['con']}")
    return "\n".join(history)

def topic_generation_bot(state: State) -> TopicUpdate:
    """Generate debate topic with research integration for current relevance"""
    user_input = get_content(state["prompt"][-1])
    
    # Conduct research on the user's topic to get current context
    try:
        # Use both PRO and CON research to get balanced current information
        research_data_pro = enhanced_research(user_input, "PRO", "current trends developments")
        research_data_con = enhanced_research(user_input, "CON", "recent challenges issues")
        
        # Combine research data for comprehensive context
        combined_research = f"""
CURRENT POSITIVE DEVELOPMENTS:
{research_data_pro}

CURRENT CHALLENGES/CONCERNS:
{research_data_con}

INSTRUCTION: Use this research to create a highly relevant, current debate topic that reflects recent developments, trends, and issues.
"""
    except Exception as e:
        combined_research = f"Research unavailable for topic generation. Proceeding with general knowledge. Error: {str(e)}"
    
    # Generate topic with research integration
    response = llm.invoke([
        {"role": "system", "content": topic_bot_prompt.format(research_data=combined_research)},
        {"role": "user", "content": f"User Topic Request: {user_input}\n\nCreate a debate topic that incorporates the latest developments and current context from the research data."}
    ])
    
    return TopicUpdate(
        topic=[{"role": "assistant", "content": str(response.content)}],
        rounds=[],
        current_round=0,
        winner=None
    )

def pro_debater_bot(state: State) -> ProUpdate:
    """Generate PRO argument with research integration"""
    topic = get_content(state["topic"][-1])
    current_round = state["current_round"] + 1
    history = get_debate_history(state)
    
    # Conduct research for PRO perspective
    try:
        research_data = enhanced_research(topic, "PRO", f"round {current_round} benefits")
    except Exception as e:
        research_data = f"Research unavailable for this round. Proceeding with general knowledge. Error: {str(e)}"
    
    # Generate argument with research integration
    response = llm.invoke([
        {"role": "system", "content": pro_bot_prompt.format(
            current_round=current_round,
            history=history,
            research_data=research_data
        )},
        {"role": "user", "content": f"Debate Topic: {topic}\n\nUse the research data provided to strengthen your PRO argument with current facts, statistics, and evidence."}
    ])
    
    return ProUpdate(
        pro_argument=[{"role": "assistant", "content": str(response.content)}],
        current_round=current_round
    )

def con_debater_bot(state: State) -> ConUpdate:
    """Generate CON argument with research integration"""
    topic = get_content(state["topic"][-1])
    current_round = state["current_round"]
    history = get_debate_history(state)
    
    # Conduct research for CON perspective
    try:
        research_data = enhanced_research(topic, "CON", f"round {current_round} risks")
    except Exception as e:
        research_data = f"Research unavailable for this round. Proceeding with general knowledge. Error: {str(e)}"
    
    # Generate argument with research integration
    response = llm.invoke([
        {"role": "system", "content": con_bot_prompt.format(
            current_round=current_round,
            history=history,
            research_data=research_data
        )},
        {"role": "user", "content": f"Debate Topic: {topic}\n\nUse the research data provided to strengthen your CON argument with current facts, statistics, and counterevidence."}
    ])
    
    return ConUpdate(
        con_argument=[{"role": "assistant", "content": str(response.content)}]
    )

def judge_bot(state: State) -> JudgeUpdate:
    """Generate final judgment - evaluates research-backed arguments"""
    topic = get_content(state["topic"][-1])
    history = get_debate_history(state)
    
    response = llm.invoke([
        {"role": "system", "content": judge_bot_prompt},
        {"role": "user", "content": f"Debate Topic: {topic}"},
        {"role": "user", "content": f"Complete Debate Transcript:\n{history}\n\nEvaluate this debate focusing on the quality of evidence, research integration, logical reasoning, and overall argument strength. Both sides had access to current research data."}
    ])
    
    content = str(response.content)
    # Updated to prevent draws - if no clear winner found, default to PRO
    if "WINNER: PRO" in content.upper():
        winner = "PRO"
    elif "WINNER: CON" in content.upper():
        winner = "CON"
    else:
        # Fallback logic: analyze content for stronger indicators
        pro_indicators = content.upper().count("PRO") + content.upper().count("STRONGER") if "PRO" in content.upper() else 0
        con_indicators = content.upper().count("CON") + content.upper().count("STRONGER") if "CON" in content.upper() else 0
        winner = "CON" if con_indicators > pro_indicators else "PRO"
    
    return JudgeUpdate(
        judge=[{"role": "assistant", "content": content}],
        winner=winner
    )
    
def update_rounds(state: State) -> Union[RoundsUpdate, Dict[str, Any]]:
    """Update rounds after both sides have spoken"""
    pro_arg: Optional[List[Dict[str, str]]] = state.get("pro_argument")
    con_arg: Optional[List[Dict[str, str]]] = state.get("con_argument")
    
    if pro_arg and con_arg and len(pro_arg) > 0 and len(con_arg) > 0:
        new_round: DebateRound = {
            "pro": get_content(pro_arg[-1]),
            "con": get_content(con_arg[-1]),
            "round_number": state["current_round"]
        }
        rounds = state["rounds"].copy()
        rounds.append(new_round)
        
        return RoundsUpdate(rounds=rounds)
    
    return {}

def should_continue_debate(state: State) -> str:
    """Conditional function to determine next step"""
    current_round = state["current_round"]
    if current_round < 3:  # Continue for 3 rounds
        return "pro_debater"
    else:
        return "judge"

# Graph Construction
def build_debate_flow():
    builder = StateGraph(State)
    
    # Add nodes
    builder.add_node("topic_generator", topic_generation_bot)
    builder.add_node("pro_debater", pro_debater_bot)
    builder.add_node("con_debater", con_debater_bot)
    builder.add_node("update_rounds", update_rounds)
    builder.add_node("judge", judge_bot)
    
    # Set initial flow
    builder.set_entry_point("topic_generator")
    
    # Connect nodes with conditional logic
    builder.add_edge("topic_generator", "pro_debater")
    builder.add_edge("pro_debater", "con_debater")
    builder.add_edge("con_debater", "update_rounds")
    
    # Use conditional edge to control debate rounds
    builder.add_conditional_edges(
        "update_rounds",
        should_continue_debate,
        {
            "pro_debater": "pro_debater",
            "judge": "judge"
        }
    )
    
    # End at judge
    builder.set_finish_point("judge")
    
    return builder.compile()

debate_flow = build_debate_flow()