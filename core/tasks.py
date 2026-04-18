from crewai import Task
from core.schemas import OSINTReport, FinalVerdict, XAIForensicsReport


def generate_xai_report(forensic_data, identity_data, search_context):
    """
    Generates a balanced, narrative-driven Threat Intelligence Report.
    """

    prompt = f"""
    You are the Lead Threat Intelligence Analyst for AI-SPY.
    Your job is to write a cohesive, executive-level Forensic Briefing that determines if a piece of media is authentic or a deepfake.

    You must perfectly balance the technical pixel analysis with the real-world news and identity context. Do not write a dry, robotic data dump. Write a compelling, accessible, and highly professional intelligence report.

    ### RAW DATA INPUTS ###
    [1. PIXEL FORENSICS]
    - System Verdict: {'DEEPFAKE DETECTED' if forensic_data.get('is_fake') else 'LIKELY AUTHENTIC'}
    - Primary Trigger: {forensic_data.get('reason', 'Unknown')}
    - Raw Metrics: {forensic_data.get('metrics', {})}

    [2. IDENTITY CONTEXT]
    - Subject Detected: {identity_data.get('name', 'Unknown Public Figure')}
    - Known Biography: {identity_data.get('description', 'No bio available.')}

    [3. ACTIVE THREAT OSINT (Live News)]
    - Recent News & Active Scams: {search_context}

    ### REPORT STRUCTURE ###
    Write the final report using Markdown, following this exact structure:

    ## 🎯 Executive Summary
    State the final verdict immediately. In 2-3 sentences, summarize *both* the technical findings and the real-world context. (e.g., "This media is flagged as a synthetic deepfake. Severe facial rendering anomalies coincide directly with active cryptocurrency scams targeting this subject in the news today.")

    ## 📰 Threat Context & Motive
    Start with the human element. Who is the subject, and what is currently happening in the news regarding them? Explicitly connect the live OSINT/News data to why someone might want to fake a video of this person right now.

    ## 🔬 Forensic Evidence (Pixel Analysis)
    Translate the raw metrics into readable, forensic logic.
    - Detail the Face Specialist metrics. If a score dipped low, explain *why* that matters (e.g., "The model detected a severe drop to {forensic_data.get('metrics', {}).get('min_face', 'N/A')}% authenticity, a classic signature of face-swapping algorithms failing to render eye-blinks or jawlines correctly.").
    - Detail the Omni-Scene metrics. Did the background pass inspection?

    ## ⚖️ Final Conclusion
    Tie it all together. How does the technical pixel failure prove the OSINT news theory, or vice versa?

    Tone: Authoritative, accessible, narrative-driven, and balanced. Avoid overly dense robotic jargon; explain the technical numbers like you are briefing a CEO or a journalist.
    """

    return prompt

def build_osint_task(agent, search_query: str):
    """Assigns the OSINT agent to verify the specific claim/caption."""
    return Task(
        description=(
            f"Search the web to verify or debunk this exact claim/context: '{search_query}'. "
            "Use the search tool to find news articles, fact-checks, or official statements. "
            "Ensure you only rely on factual reporting."
        ),
        expected_output="A structured OSINT report containing the verification status, sources, and step-by-step reasoning.",
        agent=agent,
        output_pydantic=OSINTReport # Forces the output to be a clean JSON object
    )

def build_evaluation_task(agent, forensics_data: dict):
    """Assigns the Auditor agent to review all evidence and make a final call."""
    return Task(
        description=(
            "Critically evaluate the provided evidence to determine the final authenticity of the media or claim.\n\n"
            f"FORENSICS DATA (Pixel Analysis):\n{forensics_data}\n\n"
            "OSINT DATA (Web Intelligence):\n"
            "Read the structured OSINT report provided in your context from the previous investigator's task.\n\n"
            "Identify any contradictions between the visual data and web data. Formulate a final verdict based on all provided data."
        ),
        expected_output="A structured final verdict detailing the decision, confidence, and XAI breakdown.",
        agent=agent,
        output_pydantic=FinalVerdict
    )

def build_xai_forensics_task(agent, ensemble_forensics: dict, identity_data: dict, search_context: str):
    """
    Generates a comprehensive XAI forensics report.
    
    Args:
        agent: The XAI Forensics Agent
        ensemble_forensics: Dictionary from EnsembleForensicsEngine.analyze()
        identity_data: Dictionary with subject identity and background info
        search_context: Recent news/threat intel about the subject
    """
    return Task(
        description=generate_xai_report(
            forensic_data=ensemble_forensics,
            identity_data=identity_data,
            search_context=search_context
        ),
        expected_output="A structured XAI forensics report with verdict, confidence, and detailed technical + contextual breakdown.",
        agent=agent,
        output_pydantic=XAIForensicsReport
    )

