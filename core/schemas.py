from pydantic import BaseModel, Field
from typing import List, Optional, TypedDict, Dict, Any

# ==========================================
# ENSEMBLE FORENSICS DATA CONTRACTS
# ==========================================

class EnsembleForensicMetrics(BaseModel):
    """Raw metrics from the dual-engine forensics analyzer."""
    type: str = Field(description="'image' or 'video'")
    scene_real_score: Optional[float] = Field(description="Scene authenticity score (0-100)", default=None)
    face_real_score: Optional[float] = Field(description="Face authenticity score (0-100)", default=None)
    avg_scene: Optional[float] = Field(description="Average scene score across video frames", default=None)
    min_scene: Optional[float] = Field(description="Minimum scene score (video)", default=None)
    avg_face: Optional[float] = Field(description="Average face score across video frames", default=None)
    min_face: Optional[float] = Field(description="Minimum face score (video)", default=None)
    frames_analyzed: Optional[int] = Field(description="Number of frames analyzed (video)", default=None)

class EnsembleForensicsReport(BaseModel):
    """Structured output from EnsembleForensicsEngine."""
    type: str = Field(description="'image' or 'video'")
    is_fake: bool = Field(description="Ensemble verdict: is this synthetic?")
    confidence: float = Field(description="Confidence level (0-100)")
    reason: str = Field(description="Plain-English explanation of the verdict")
    metrics: EnsembleForensicMetrics = Field(description="Raw forensic metrics")

# ==========================================
# CREW-AI AGENT OUTPUT SCHEMAS
# ==========================================

class ForensicsReport(BaseModel):
    """Data contract for the Forensics Agent."""
    is_manipulated: bool = Field(description="True if AI detects pixel manipulation.")
    fake_probability: float = Field(description="0.0 to 1.0 confidence of manipulation.")
    visual_evidence: str = Field(description="Specific visual anomalies or 'No tampering detected'.")
    extracted_caption: str = Field(description="What the vision model saw in the media.")

class OSINTReport(BaseModel):
    """Data contract for the OSINT Investigator Agent."""
    claim_verified: bool = Field(description="True if web sources confirm the context/claim.")
    debunked: bool = Field(description="True if explicitly debunked by reliable sources.")
    sources_used: List[str] = Field(description="URLs of trusted sources found.")
    reasoning: str = Field(description="Step-by-step logic matching the sources to the media/claim.")

class FinalVerdict(BaseModel):
    """Data contract for the Chief Auditor Agent (The final output)."""
    verdict: str = Field(description="Must be exactly: Real, Fake, Misleading, or Unverified")
    confidence: int = Field(description="0 to 100 final confidence score")
    reasoning: str = Field(description="Short executive summary (1-2 sentences).")
    xai_breakdown: str = Field(description="Detailed Explainable AI breakdown of how Forensics and OSINT contributed to the decision.")

class XAIForensicsReport(BaseModel):
    """Explainable AI report combining forensics + identity + context."""
    verdict: str = Field(description="AUTHENTIC, SYNTHETIC/DEEPFAKE, or INCONCLUSIVE")
    confidence: int = Field(description="0 to 100 confidence")
    forensic_analysis: str = Field(description="Technical breakdown of face/scene metrics")
    identity_analysis: str = Field(description="How subject's identity relates to media context")
    threat_context: str = Field(description="News/scam context - is subject being targeted?")
    executive_summary: str = Field(description="1-3 sentence verdict with critical reasoning")
    technical_breakdown: str = Field(description="Deep dive into facial artifacts, temporal consistency, background anomalies")

# ==========================================
# LANGGRAPH GLOBAL STATE
# ==========================================

class InvestigationState(TypedDict):
    """The global state dictionary passed between all LangGraph nodes."""
    input_type: str            # 'media', 'text', or 'both'
    media_path: Optional[str]  # Path to local image/frame
    text_claim: Optional[str]  # User's text input
    search_query: str          # The finalized query used for the OSINT search
    
    # Agent Outputs appended as the graph runs
    forensics_data: Optional[ForensicsReport]
    ensemble_forensics: Optional[EnsembleForensicsReport]  # NEW: Dual-engine results
    identity_data: Optional[Dict[str, Any]]  # NEW: Person identification & bio
    osint_data: Optional[OSINTReport]
    final_result: Optional[FinalVerdict]
    xai_report: Optional[XAIForensicsReport]  # NEW: Comprehensive XAI analysis
    
    # System health
    errors: List[str]
