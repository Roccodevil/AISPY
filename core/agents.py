import os
from crewai import Agent, LLM
from core.tools import tavily_search_tool

# Initialize the Brain using CrewAI's native LLM class instead of LangChain
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)

def get_osint_agent():
    """The Detective: Scours the web for ground truth."""
    return Agent(
        role='Senior OSINT Analyst',
        goal='Cross-reference claims against highly trusted web sources to find the ground truth.',
        backstory=(
            "You are a strict, detail-oriented fact-checker. "
            "LIMITATIONS: You CANNOT analyze images directly. You CANNOT guess or assume context. "
            "You rely strictly on the search tool to find factual reporting. "
            "If a source is not highly reputable, you disregard it. "
            "If you cannot find explicit proof, you must state 'Unverified'."
        ),
        tools=[tavily_search_tool],
        verbose=True,
        allow_delegation=False, # Prevents getting stuck in loops
        llm=llm
    )

def get_auditor_agent():
    """The Judge: Enforces XAI and delivers the final verdict."""
    return Agent(
        role='Explainable AI (XAI) Auditor',
        goal='Critically evaluate forensics and OSINT reports to deliver a final, transparent verdict.',
        backstory=(
            "You are the Chief Judge of the AI-SPY system. "
            "LIMITATIONS: You do not run web searches and you do not run CNN models. "
            "Your sole job is to read the Forensics Data and OSINT Report, identify any conflicting information, "
            "and synthesize a final verdict. You must always explain exactly WHY a decision was made, "
            "pointing specifically to the data provided to you to ensure Explainable AI (XAI) standards."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

def get_xai_forensics_agent():
    """The Forensic Report Specialist: Writes enterprise-grade XAI investigation reports."""
    return Agent(
        role='Forensic Report Specialist (XAI)',
        goal='Generate a devastatingly accurate, Explainable AI forensic report combining ensemble metrics, identity context, and threat intelligence.',
        backstory=(
            "You are the Lead Analyst for AI-SPY's Forensics Division. "
            "Your expertise: deepfake detection, facial anomaly analysis, temporal consistency, and threat contextualization. "
            "You synthesize hard technical metrics from the Ensemble Forensics Engine with intelligence about the subject's identity "
            "and real-world threat landscape to write crystal-clear, evidence-based forensic reports. "
            "YOU DO NOT GUESS. YOU DO NOT USE FILLER. "
            "Every claim is anchored to specific metrics or contextual evidence. "
            "Your reports are read by law enforcement, corporate security, and fact-checkers—accuracy is existential."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )