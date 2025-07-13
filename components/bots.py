from typing import TypedDict, List, Dict, Any, Annotated, Union, Optional, cast
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
from bot_instructions import topic_bot_prompt, pro_bot_prompt, con_bot_prompt, judge_bot_prompt
from components.tools import openai_web_search, get_simple_llm_response
import logging

def get_content(message: Union[Dict[str, Any], Any]) -> str:
    """Safely extract content from either a message object or dictionary"""
    if hasattr(message, 'content'):
        return str(message.content)
    elif isinstance(message, dict) and 'content' in message:
        return str(message['content'])
    else:
        return str(message)

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
    winner: Optional[str]
    pro_argument: Annotated[List[Dict[str, str]], add_messages]
    con_argument: Annotated[List[Dict[str, str]], add_messages]
    processing_state: str
    ready_for_next_round: bool

def get_debate_history(state: State) -> str:
    """Compiles the debate history for context"""
    history = []
    for i, round_data in enumerate(state["rounds"]):
        history.append(f"\nROUND {i+1}:")
        history.append(f"PRO: {round_data['pro']}")
        history.append(f"CON: {round_data['con']}")
    return "\n".join(history)

def topic_generation_bot(state: State) -> State:
    """Generate debate topic with OpenAI web search integration"""
    try:
        user_input = get_content(state["prompt"][-1]) if state["prompt"] else "General debate topic"
        
        research_data = openai_web_search(
            query=user_input,
            context="current trends developments challenges issues recent news"
        )
        
        messages = [
            {
                "role": "system", 
                "content": topic_bot_prompt.format(research_data=research_data)
            },
            {
                "role": "user", 
                "content": f"User Topic Request: {user_input}\n\nCreate a debate topic that incorporates the latest developments and current context from the research data."
            }
        ]
        
        response_content = get_simple_llm_response(messages)
        
        updated_state = cast(State, state.copy())
        updated_state["topic"] = [{"role": "assistant", "content": response_content}]
        updated_state["processing_state"] = "topic_ready"
        
        return updated_state
        
    except Exception as e:
        logging.error(f"Topic generation error: {str(e)}")
        updated_state = cast(State, state.copy())
        updated_state["topic"] = [{"role": "assistant", "content": f"Error generating topic: {str(e)}"}]
        updated_state["processing_state"] = "error"
        return updated_state

def pro_debater_bot(state: State) -> State:
    """Generate PRO argument with OpenAI web search integration"""
    try:
        topic = get_content(state["topic"][-1]) if state["topic"] else "Unknown topic"
        current_round = state["current_round"] + 1
        history = get_debate_history(state)
        
        research_data = openai_web_search(
            query=topic,
            perspective="PRO benefits advantages positive outcomes",
            context=f"round {current_round} evidence statistics success stories"
        )
        
        messages = [
            {
                "role": "system", 
                "content": pro_bot_prompt.format(
                    current_round=current_round,
                    history=history,
                    research_data=research_data
                )
            },
            {
                "role": "user", 
                "content": f"Debate Topic: {topic}\n\nUse the research data provided to strengthen your PRO argument with current facts, statistics, and evidence."
            }
        ]
        
        response_content = get_simple_llm_response(messages)
        
        updated_state = cast(State, state.copy())
        updated_state["pro_argument"] = [{"role": "assistant", "content": response_content}]
        updated_state["processing_state"] = "pro_ready"
        
        return updated_state
        
    except Exception as e:
        logging.error(f"PRO argument generation error: {str(e)}")
        updated_state = cast(State, state.copy())
        updated_state["pro_argument"] = [{"role": "assistant", "content": f"Error generating PRO argument: {str(e)}"}]
        updated_state["processing_state"] = "error"
        return updated_state

def con_debater_bot(state: State) -> State:
    """Generate CON argument with OpenAI web search integration"""
    try:
        topic = get_content(state["topic"][-1]) if state["topic"] else "Unknown topic"
        current_round = state["current_round"]
        history = get_debate_history(state)
        
        pro_current = ""
        if state.get("pro_argument") and len(state["pro_argument"]) > 0:
            pro_current = get_content(state["pro_argument"][-1])
        
        research_data = openai_web_search(
            query=topic,
            perspective="CON risks disadvantages negative outcomes criticism",
            context=f"round {current_round} counterevidence problems failures rebuttal to: {pro_current[:200]}"
        )
        
        messages = [
            {
                "role": "system", 
                "content": con_bot_prompt.format(
                    current_round=current_round,
                    history=history,
                    research_data=research_data
                )
            },
            {
                "role": "user", 
                "content": f"Debate Topic: {topic}\n\nPRO's Current Argument: {pro_current}\n\nUse the research data provided to strengthen your CON argument with current facts, statistics, and counterevidence."
            }
        ]
        
        response_content = get_simple_llm_response(messages)
        
        updated_state = cast(State, state.copy())
        updated_state["con_argument"] = [{"role": "assistant", "content": response_content}]
        updated_state["processing_state"] = "con_ready"
        
        return updated_state
        
    except Exception as e:
        logging.error(f"CON argument generation error: {str(e)}")
        updated_state = cast(State, state.copy())
        updated_state["con_argument"] = [{"role": "assistant", "content": f"Error generating CON argument: {str(e)}"}]
        updated_state["processing_state"] = "error"
        return updated_state

def judge_bot(state: State) -> State:
    """Generate final judgment with fact-checking via OpenAI web search"""
    try:
        topic = get_content(state["topic"][-1]) if state["topic"] else "Unknown topic"
        history = get_debate_history(state)
        
        pro_claims = []
        con_claims = []
        
        for round_data in state["rounds"]:
            pro_claims.append(round_data["pro"][:300])  
            con_claims.append(round_data["con"][:300])
        
        verification_data = openai_web_search(
            query=topic,
            context=f"fact check verify claims evidence PRO: {' '.join(pro_claims[:200])} CON: {' '.join(con_claims[:200])}"
        )
        
        messages = [
            {
                "role": "system", 
                "content": judge_bot_prompt
            },
            {
                "role": "user", 
                "content": f"Debate Topic: {topic}"
            },
            {
                "role": "user", 
                "content": f"Complete Debate Transcript:\n{history}\n\nFact-Check and Verification Data:\n{verification_data}\n\nEvaluate this debate focusing on factual accuracy, evidence quality, logical reasoning, and overall argument strength. Use the verification data to assess the credibility of claims made by both sides."
            }
        ]
        
        response_content = get_simple_llm_response(messages)
        
        winner = None
        if "WINNER: PRO" in response_content.upper():
            winner = "PRO"
        elif "WINNER: CON" in response_content.upper():
            winner = "CON"
        else:
            pro_indicators = response_content.upper().count("PRO") + response_content.upper().count("STRONGER") if "PRO" in response_content.upper() else 0
            con_indicators = response_content.upper().count("CON") + response_content.upper().count("STRONGER") if "CON" in response_content.upper() else 0
            winner = "CON" if con_indicators > pro_indicators else "PRO"
        
        updated_state = cast(State, state.copy())
        updated_state["judge"] = [{"role": "assistant", "content": response_content}]
        updated_state["winner"] = winner
        updated_state["processing_state"] = "judgment_complete"
        
        return updated_state
        
    except Exception as e:
        logging.error(f"Judge generation error: {str(e)}")
        updated_state = cast(State, state.copy())
        updated_state["judge"] = [{"role": "assistant", "content": f"Error generating judgment: {str(e)}"}]
        updated_state["winner"] = "ERROR"
        updated_state["processing_state"] = "error"
        return updated_state
    
def update_rounds(state: State) -> State:
    """Update rounds after both sides have spoken"""
    try:
        pro_arg = state.get("pro_argument", [])
        con_arg = state.get("con_argument", [])
        
        if pro_arg and con_arg and len(pro_arg) > 0 and len(con_arg) > 0:
            new_round: DebateRound = {
                "pro": get_content(pro_arg[-1]),
                "con": get_content(con_arg[-1]),
                "round_number": state["current_round"]
            }
            
            updated_state = cast(State, state.copy())
            updated_state["rounds"] = state["rounds"].copy()
            updated_state["rounds"].append(new_round)
            updated_state["ready_for_next_round"] = True
            updated_state["processing_state"] = "round_complete"
            
            return updated_state
        
        updated_state = cast(State, state.copy())
        updated_state["processing_state"] = "processing_round"
        return updated_state
        
    except Exception as e:
        logging.error(f"Round update error: {str(e)}")
        updated_state = cast(State, state.copy())
        updated_state["processing_state"] = "error"
        return updated_state

def should_continue_debate(state: State) -> str:
    """Conditional function to determine next step"""
    current_round = state["current_round"]
    if current_round < 3:  
        return "waiting_for_next_round"
    else:
        return "judge"

def build_debate_flow():
    builder = StateGraph(State)
    
    builder.add_node("topic_generator", topic_generation_bot)
    builder.add_node("pro_debater", pro_debater_bot)
    builder.add_node("con_debater", con_debater_bot)
    builder.add_node("update_rounds", update_rounds)
    builder.add_node("judge", judge_bot)
    
    builder.set_entry_point("topic_generator")
    builder.add_edge("topic_generator", "pro_debater")
    builder.add_edge("pro_debater", "con_debater")
    builder.add_edge("con_debater", "update_rounds")
    builder.set_finish_point("update_rounds")
    
    return builder.compile()

def generate_topic_only(prompt: str) -> State:
    """Generate only the topic"""
    input_state: State = {
        "topic": [],
        "rounds": [],
        "judge": [],
        "prompt": [{"role": "user", "content": prompt}],
        "current_round": 0,
        "winner": None,
        "pro_argument": [],
        "con_argument": [],
        "processing_state": "generating_topic",
        "ready_for_next_round": False
    }
    
    return topic_generation_bot(input_state)

def generate_round_arguments(state: State) -> State:
    """Generate PRO and CON arguments for current round"""
    try:
        updated_state = cast(State, state.copy())
        updated_state["current_round"] += 1
        updated_state["processing_state"] = "generating_arguments"
        
        updated_state = pro_debater_bot(updated_state)
        updated_state["processing_state"] = "pro_complete"
        
        
        updated_state = con_debater_bot(updated_state)
        updated_state["processing_state"] = "con_complete"
        
        
        updated_state = update_rounds(updated_state)
        
        return updated_state
        
    except Exception as e:
        logging.error(f"Round generation error: {str(e)}")
        updated_state = cast(State, state.copy())
        updated_state["processing_state"] = "error"
        return updated_state

def generate_final_judgment(state: State) -> State:
    """Generate final judgment"""
    updated_state = cast(State, state.copy())
    updated_state["processing_state"] = "generating_judgment"
    return judge_bot(updated_state)


debate_flow = build_debate_flow()