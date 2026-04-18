import os
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from tavily import TavilyClient
import cv2
from PIL import Image
from transformers import pipeline

# Import your local forensic engine and database tools
# (Adjust these imports based on where you saved them in your project)
from core.forensics import EnsembleForensicsEngine
from core.media_agent import MediaIntelligenceAgent
import json

# ==========================================
# 1. DEFINE THE STATE DICTIONARY
# ==========================================
# This acts as the "Memory" passed between every agent
class AgentState(TypedDict):
    media_path: str
    media_context: str             # What is happening in the media?
    audio_transcript: str          # Extracted speech transcript
    audio_forensic_data: Dict[str, Any]  # Voice authenticity analysis (verdict, confidence)
    forensic_data: Dict[str, Any]  # Holds CNN scores and verdicts
    identity_data: Dict[str, str]  # Holds Name and Wikipedia Bio
    osint_context: str             # Holds the live news from Tavily
    final_report: str              # Holds the final Markdown output

# ==========================================
# 2. DEFINE THE NODES (The Agents)
# ==========================================

print("⚙️ Loading Hugging Face Vision Captioner (CPU)...")
try:
    captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base", device=-1)
except Exception as e:
    print(f"🚨 Could not load BLIP Vision Model: {e}")
    captioner = None

print("⚙️ Booting Media Intelligence Agent (Audio)...")
try:
    media_agent = MediaIntelligenceAgent()
except Exception as e:
    print(f"🚨 Could not initialize Media Agent: {e}")
    media_agent = None

def extract_middle_frame(media_path: str):
    """Extracts the middle frame of a video and converts it for Hugging Face."""
    cap = cv2.VideoCapture(media_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames // 2))
    ret, frame = cap.read()
    cap.release()

    if ret:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_frame)
    return None

def node_vision_context(state: AgentState) -> AgentState:
    """Node 0: Hugging Face BLIP watches the media to understand the plot."""
    print("\n[LANGGRAPH] 🟢 Entering Node: Vision Context Extraction (Local)")

    media_path = state["media_path"]
    is_video = media_path.lower().endswith((".mp4", ".avi", ".mov"))

    if not media_path or not os.path.exists(media_path):
        return {"media_context": "Could not extract visual frame from media."}

    if is_video:
        pil_image = extract_middle_frame(media_path)
    else:
        try:
            pil_image = Image.open(media_path).convert("RGB")
        except Exception:
            pil_image = None

    if not pil_image:
        return {"media_context": "Could not extract visual frame from media."}

    if captioner is None:
        return {"media_context": "Failed to extract scene context."}

    print("  -> 👁️ BLIP Vision Model is analyzing the scene...")
    try:
        result = captioner(pil_image, max_new_tokens=50)
        caption = result[0]["generated_text"]
        formatted_caption = f"The media shows: {caption.capitalize()}."
        print(f"  -> 📝 Context Extracted: {formatted_caption}")
        return {"media_context": formatted_caption}
    except Exception as e:
        print(f"  -> ⚠️ Vision Error: {e}")
        return {"media_context": "Failed to extract scene context."}

def node_audio_analysis(state: AgentState) -> AgentState:
    """Node 1: Extract transcript and run voice deepfake detection."""
    print("\n[LANGGRAPH] 🟢 Entering Node: Audio Analysis")

    media_path = state.get("media_path", "")
    if not media_path or not os.path.exists(media_path):
        return {
            "audio_transcript": "No audio detected.",
            "audio_forensic_data": {"verdict": "N/A", "confidence": 0.0}
        }

    if media_agent is None:
        return {
            "audio_transcript": "Audio agent unavailable.",
            "audio_forensic_data": {"verdict": "N/A", "confidence": 0.0}
        }

    try:
        print("  -> 🔊 Running ASR + voice forensics...")
        audio_result = media_agent.extract_audio(media_path)
        # Extract transcript and forensic data separately
        transcript = audio_result.get("transcript", "No audio detected.")
        forensic_data = {
            "verdict": audio_result.get("verdict", "N/A"),
            "confidence": audio_result.get("confidence", 0.0)
        }
        return {
            "audio_transcript": transcript,
            "audio_forensic_data": forensic_data
        }
    except Exception as e:
        print(f"  -> ⚠️ Audio Analysis Error: {e}")
        return {
            "audio_transcript": "Audio analysis failed.",
            "audio_forensic_data": {"verdict": "N/A", "confidence": 0.0}
        }

def node_process_media(state: AgentState) -> AgentState:
    """Node 2: Runs DeepFace and the local CNN Ensemble."""
    print("\n[LANGGRAPH] 🟢 Entering Node: Pixel Forensics & Identity Extraction")
    media_path = state["media_path"]
    
    # 1. Run the Local Ensemble CNN
    engine = EnsembleForensicsEngine()
    forensic_results = engine.analyze(media_path)
    
    # 2. Extract Identity (Simulated here: wire your DeepFace function in)
    # Ideally, call your `test_identity.py` logic here. For safety if no match:
    identity_results = {
        "name": "Unknown",
        "description": "No known public figure detected or matched in database."
    }
    
    # Example of how you would load your metadata if DeepFace found a match:
    # metadata = json.load(open('known_faces/metadata.json'))
    # if match_key in metadata: identity_results = metadata[match_key]

    return {"forensic_data": forensic_results, "identity_data": identity_results}

def node_osint_investigation(state: AgentState) -> AgentState:
    """Node 3: Scours the web for threat intelligence using Tavily."""
    print("\n[LANGGRAPH] 🟢 Entering Node: OSINT Threat Intel Gathering")
    
    subject_name = state["identity_data"].get("name", "Unknown")
    
    # If we don't know who it is, skip the specific person search
    if subject_name == "Unknown":
        return {"osint_context": "No public figure identified. General pixel forensics must take priority."}

    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        query = f"Latest news, deepfake rumors, or crypto scams targeting {subject_name} 2024"
        print(f"  -> 🔎 Searching live web: '{query}'")
        
        response = tavily.search(query=query, search_depth="basic", max_results=3)
        
        # Compile the search results into a readable string for the LLM
        context = ""
        for item in response.get("results", []):
            context += f"- {item['title']}: {item['content']}\n"
            
        return {"osint_context": context if context else "No significant recent threat activity found."}
    
    except Exception as e:
        print(f"  -> ⚠️ OSINT Error: {e}")
        return {"osint_context": "OSINT Search failed. Rely purely on pixel forensics."}

def node_xai_report(state: AgentState) -> AgentState:
    """Node 4: The Mastermind LLM writes the final executive brief including Audio."""
    print("\n[LANGGRAPH] 🟢 Entering Node: XAI Report Generation")
    
    # Initialize Groq (Requires GROQ_API_KEY in your .env)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2, # Low temperature for an analytical, factual tone
        max_tokens=1024
    )
    
    prompt_template = PromptTemplate(
        input_variables=[
            "media_context", 
            "audio_transcript", 
            "forensic_data", 
            "audio_forensic_data", 
            "identity_data", 
            "osint_context"
        ],
        template="""
        You are an elite Threat Intelligence Analyst. Your job is to write a formal, non-technical Intelligence Briefing regarding a suspicious piece of media.
        
        DO NOT use any machine learning jargon. Do not mention "CNNs", "pixels", "models", or specific percentage scores. Translate the technical data into plain-English forensic findings.

        ### THE RAW DATA ###
        - Visual Claim in Media: {media_context}
        - Spoken Transcript: "{audio_transcript}"
        - Subject Identified: {identity_data}
        - Visual Lab Results: {forensic_data}
        - Audio Lab Results: {audio_forensic_data}
        - Live News / Threat Intel: {osint_context}

        ### REPORT FORMAT ###
        Generate a professional report using the following Markdown structure exactly:

        # THREAT INTELLIGENCE BRIEFING: MEDIA AUTHENTICITY

        ## 1. Executive Summary
        State clearly whether this media is authentic or artificially generated (a deepfake). Summarize the main visual and audio reasons for this verdict in one to two sentences.

        ## 2. Media Context & Claim
        Describe what is happening in the media. Explain who the identified subject is, what they are doing visually, and what they are explicitly saying based on the transcript.

        ## 3. Visual Forensics Analysis
        Explain the visual tampering in plain English based on the visual lab results. 

        ## 4. Voice & Audio Forensics
        Analyze the audio lab results. State clearly if the voice was determined to be an AI-generated voice clone. Mention the transcript if the spoken words are suspicious or manipulative (like asking for money).
        
        ## 5. Threat Intelligence & Motive
        Connect the media's claim and transcript to the live news data. If the media shows the subject promoting a scam, and the news shows active scams targeting this subject, explicitly state that this media is part of a known, active misinformation campaign. 
        """
    )
    
    # Format the prompt with our entire state dictionary
    formatted_prompt = prompt_template.format(
        media_context=state.get("media_context", "Unknown visual context."),
        audio_transcript=state.get("audio_transcript", "No audio detected."),
        forensic_data=json.dumps(state.get("forensic_data", {})),
        audio_forensic_data=json.dumps(state.get("audio_forensic_data", {})),
        identity_data=json.dumps(state.get("identity_data", {})),
        osint_context=state.get("osint_context", "No OSINT data available.")
    )
    
    # Generate the report
    print("  -> 🧠 Groq is drafting the XAI Brief with Audio Insights...")
    try:
        response = llm.invoke(formatted_prompt)
        report_content = response.content
    except Exception as e:
        print(f"  -> ⚠️ Groq API Error: {e}")
        report_content = "Failed to generate report due to LLM API error."
    
    return {"final_report": report_content}

# ==========================================
# 3. BUILD THE GRAPH PIPELINE
# ==========================================
def build_aispy_workflow():
    workflow = StateGraph(AgentState)
    
    # Add all agents
    workflow.add_node("vision_context", node_vision_context)
    workflow.add_node("audio_analysis", node_audio_analysis)
    workflow.add_node("process_media", node_process_media)
    workflow.add_node("osint_investigation", node_osint_investigation)
    workflow.add_node("xai_report", node_xai_report)
    
    # Define the strict sequence (Vision -> Audio -> Media -> OSINT -> XAI)
    workflow.set_entry_point("vision_context")
    workflow.add_edge("vision_context", "audio_analysis")
    workflow.add_edge("audio_analysis", "process_media")
    workflow.add_edge("process_media", "osint_investigation")
    workflow.add_edge("osint_investigation", "xai_report")
    workflow.add_edge("xai_report", END)
    
    return workflow.compile()

# ==========================================
# 5. COMPATIBILITY WRAPPER FOR FLASK APP
# ==========================================
# Pydantic models for structured output (required by app.py)
from pydantic import BaseModel
from typing import Optional

class ForensicsReport(BaseModel):
    is_manipulated: bool
    fake_probability: float
    visual_evidence: str
    extracted_caption: str

class OSINTReport(BaseModel):
    claim_verified: bool
    debunked: bool
    sources_used: list = []
    key_findings: str = ""

class FinalVerdict(BaseModel):
    verdict: str
    confidence: float
    reasoning: str
    xai_breakdown: str

def run_aispy_pipeline(
    input_type: str,
    media_path: str = None,
    text_claim: str = None,
    identity_data: dict = None,
    request_id: str = None
):
    """
    Entry point for Flask app.py - wraps the LangGraph workflow and returns
    data in the format expected by the frontend.
    
    Returns a dict with:
    - errors: List of error strings
    - final_result: FinalVerdict Pydantic object
    - forensics_data: ForensicsReport Pydantic object
    - osint_data: OSINTReport Pydantic object
    """
    
    print("==================================================")
    print("🚀 STARTING AI-SPY MASTERMIND WORKFLOW")
    print("==================================================")
    
    errors = []
    
    # Initialize state with defaults
    initial_state = {
        "media_path": media_path or "",
        "media_context": text_claim or "No contextual claim provided.",
        "audio_transcript": "No audio detected.",
        "audio_forensic_data": {"verdict": "N/A", "confidence": 0.0},
        "forensic_data": {},
        "identity_data": identity_data or {"name": "Unknown", "description": ""},
        "osint_context": "",
        "final_report": ""
    }
    
    try:
        # Build and run the LangGraph workflow
        compiled_graph = build_aispy_workflow()
        invoke_config = {
            "run_name": "aispy_pipeline",
            "tags": ["aispy", "flask", input_type],
            "metadata": {
                "request_id": request_id or "local-run",
                "input_type": input_type,
                "has_media": bool(media_path),
                "has_text_claim": bool(text_claim)
            }
        }
        final_state = compiled_graph.invoke(initial_state, config=invoke_config)
        
        # Extract outputs from LangGraph state
        forensic_data = final_state.get("forensic_data", {})
        osint_context = final_state.get("osint_context", "")
        final_report = final_state.get("final_report", "")
        
        # Convert forensic data to ForensicsReport
        if isinstance(forensic_data, dict):
            forensics_report = ForensicsReport(
                is_manipulated=forensic_data.get('is_fake', False),
                fake_probability=float(forensic_data.get('confidence', 0)) / 100.0,
                visual_evidence=forensic_data.get('reason', 'No evidence available'),
                extracted_caption=str(forensic_data.get('metrics', {}))
            )
        else:
            forensics_report = ForensicsReport(
                is_manipulated=False,
                fake_probability=0.0,
                visual_evidence="Could not analyze media",
                extracted_caption="N/A"
            )
        
        # Parse OSINT context (simple extraction from text)
        osint_report = OSINTReport(
            claim_verified="verified" in osint_context.lower(),
            debunked="No significant recent threat activity" in osint_context or "debunk" in osint_context.lower(),
            sources_used=[],
            key_findings=osint_context[:200] if osint_context else "No threat intelligence"
        )
        
        # Generate final verdict from XAI report
        is_fake = "deepfake" in final_report.lower() or "fake" in final_report.lower()
        confidence = 0.85 if is_fake else 0.15
        
        verdict = "⚠️ DEEPFAKE DETECTED" if is_fake else "✅ AUTHENTIC"
        
        final_verdict = FinalVerdict(
            verdict=verdict,
            confidence=confidence,
            reasoning=final_report.split("##")[1][:300] if "##" in final_report else final_report[:300],
            xai_breakdown=final_report.split("## ⚖️")[1][:500] if "## ⚖️" in final_report else "See full report for details"
        )
        
        return {
            "errors": errors,
            "final_result": final_verdict,
            "forensics_data": forensics_report,
            "osint_data": osint_report,
            "final_report": final_report,
            "media_context": final_state.get("media_context", "")
        }
    
    except Exception as e:
        errors.append(f"Pipeline error: {str(e)}")
        print(f"❌ Pipeline Error: {e}")
        
        # Return safe defaults on error
        return {
            "errors": errors,
            "final_result": None,
            "forensics_data": ForensicsReport(
                is_manipulated=False,
                fake_probability=0.0,
                visual_evidence="Error during analysis",
                extracted_caption="N/A"
            ),
            "osint_data": OSINTReport(claim_verified=False, debunked=False, sources_used=[])
        }

# ==========================================
# 4. RUNNER FOR TESTING
# ==========================================
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Make sure TAVILY_API_KEY and GROQ_API_KEY are loaded
    
    print("==================================================")
    print("🚀 BOOTING AI-SPY MASTERMIND WORKFLOW")
    print("==================================================")
    
    # Compile the graph
    app = build_aispy_workflow()
    
    # Get input from the user
    test_target = input("\n📁 Enter the path to the media: ").strip().strip("\"'")

    # Run the state machine
    inputs = {"media_path": test_target}

    final_state = app.invoke(inputs)
    
    print("\n" + "="*80)
    print("📄 AI-SPY EXECUTIVE INTELLIGENCE BRIEF")
    print("="*80)
    print(final_state["final_report"])
