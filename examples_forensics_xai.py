#!/usr/bin/env python3
"""
Example: Complete AI-SPY Forensics Pipeline with XAI Reporting

This script demonstrates how to use the integrated ensemble forensics engine
combined with OSINT investigation and XAI report generation.
"""

import os
import json
from pathlib import Path

# Import the core components
from core.forensics import EnsembleForensicsEngine
from core.workflow import run_aispy_pipeline


def example_1_simple_image_analysis():
    """Example 1: Analyze a single image using the forensics engine."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Simple Image Analysis")
    print("=" * 70)
    
    # Initialize engine
    print("\n[Step 1] Initializing Ensemble Forensics Engine...")
    engine = EnsembleForensicsEngine()
    
    # For demo, create a placeholder path
    test_image = "./test_media/sample.jpg"
    
    if not os.path.exists(test_image):
        print(f"\n⚠️ Note: {test_image} not found. This is a demonstration of the API.")
        print("In production, you would pass a real image path.")
        print("\nExample result structure:")
        example_result = {
            "type": "image",
            "is_fake": False,
            "confidence": 87.5,
            "reason": "Passed Authentication | Scene: 91.2%, Face: 83.8%",
            "metrics": {
                "scene_real_score": 91.2,
                "face_real_score": 83.8
            }
        }
        print(json.dumps(example_result, indent=2))
    else:
        print(f"\n[Step 2] Analyzing image: {test_image}")
        result = engine.analyze(test_image)
        print("\n[Step 3] Results:")
        print(json.dumps(result, indent=2))
        
        # Interpret results
        if result['is_fake']:
            print(f"\n🚨 VERDICT: DEEPFAKE DETECTED")
            print(f"   Confidence: {result['confidence']:.1f}%")
            print(f"   Reason: {result['reason']}")
        else:
            print(f"\n✓ VERDICT: LIKELY AUTHENTIC")
            print(f"   Confidence: {result['confidence']:.1f}%")


def example_2_video_analysis():
    """Example 2: Analyze a video with frame sampling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Video Analysis with Temporal Consistency Check")
    print("=" * 70)
    
    engine = EnsembleForensicsEngine()
    
    test_video = "./test_media/sample.mp4"
    
    if not os.path.exists(test_video):
        print(f"\n⚠️ Note: {test_video} not found. This is a demonstration.")
        print("Video analysis samples frames intelligently and checks for temporal glitches.")
        print("\nExample result structure for a deepfake video:")
        example_result = {
            "type": "video",
            "is_fake": True,
            "confidence": 94.0,
            "reason": "🚨 SEVERE FACIAL GLITCH | Frame dropped to 38.4% authenticity",
            "metrics": {
                "avg_scene": 85.2,
                "min_scene": 72.1,
                "max_scene": 96.5,
                "avg_face": 71.3,
                "min_face": 38.4,
                "max_face": 88.2,
                "frames_analyzed": 15,
                "total_frames": 450
            }
        }
        print(json.dumps(example_result, indent=2))
        print("\n💡 Key Insight: Notice the 'min_face' dropped to 38.4% at frame 187.")
        print("   This sudden drop is a signature of face-swapping algorithms struggling ")
        print("   with temporal consistency during head movements.")
    else:
        print(f"\n[Step 1] Analyzing video: {test_video}")
        result = engine.analyze(test_video)
        print("\n[Step 2] Results:")
        print(json.dumps(result, indent=2))
        
        # Interpret metrics
        metrics = result.get('metrics', {})
        if 'min_face' in metrics:
            print(f"\n📊 Temporal Analysis:")
            print(f"   Average Face Score: {metrics['avg_face']:.1f}%")
            print(f"   Minimum Face Score: {metrics['min_face']:.1f}%")
            print(f"   Delta (Drop): {metrics['avg_face'] - metrics['min_face']:.1f}%")
            if metrics['min_face'] < 50:
                print(f"   ⚠️ CRITICAL: Large temporal glitch detected!")


def example_3_full_pipeline_with_xai():
    """Example 3: Full LangGraph pipeline with XAI reporting."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Full Pipeline - Forensics + OSINT + XAI Report")
    print("=" * 70)
    
    media_path = "./test_media/deepfake_video.mp4"
    
    # Define identity context (could be from vector DB in production)
    identity_data = {
        "name": "Elon Musk",
        "description": (
            "CEO of Tesla and SpaceX. Known for ambitious yet controversial statements. "
            "Recent news (April 2026): Active deepfake campaign detected on social media "
            "promoting fake Musk endorsements of cryptocurrency tokens for scam purposes."
        )
    }
    
    print(f"\n[Step 1] Subject: {identity_data['name']}")
    print(f"[Step 2] Calling run_aispy_pipeline()...")
    print("   • Module: process_media (ensemble forensics)")
    print("   • Module: crew_investigation (OSINT verification)")
    print("   • Module: xai_forensics_report (comprehensive analysis)")
    
    if not os.path.exists(media_path):
        print(f"\n⚠️ Note: {media_path} not found. Full example output:")
        
        example_state = {
            "ensemble_forensics": {
                "type": "video",
                "is_fake": True,
                "confidence": 94.0,
                "reason": "🚨 SEVERE FACIAL GLITCH | Frame dropped to 38.4% authenticity",
                "metrics": {
                    "avg_scene": 85.2,
                    "min_scene": 72.1,
                    "avg_face": 71.3,
                    "min_face": 38.4,
                    "frames_analyzed": 15
                }
            },
            "osint_data": {
                "claim_verified": False,
                "debunked": True,
                "sources_used": [
                    "https://cointelegraph.com/news/deepfake-musk-crypto-scam",
                    "https://bleepingcomputer.com/news/security/elon-musk-deepfakes",
                    "https://reuters.com/technology/deepfakes"
                ],
                "reasoning": "This exact interview was debunked by Reuters as a deepfake. "
                "The claimed Musk endorsement of 'Rocket Coin' contradicts his official statements."
            },
            "xai_report": {
                "verdict": "SYNTHETIC/DEEPFAKE DETECTED",
                "confidence": 94,
                "forensic_analysis": (
                    "Face authenticity averaged 71.3% across 15 sampled frames. "
                    "Critical failure detected at frame 187: facial confidence plummeted to 38.4%. "
                    "This temporal glitch is characteristic of face-swapping algorithms "
                    "(DeepFaceLive, Roop) struggling during head rotations. Eye regions show jitter."
                ),
                "identity_analysis": (
                    "Subject confirmed as Elon Musk. This deepfake misappropriates "
                    "his identity to falsely endorse a cryptocurrency token."
                ),
                "threat_context": (
                    "Active threat: Rocket Coin cryptocurrency scam campaign targeting retail investors. "
                    "Multiple deepfakes of Musk detected in coordinated wave (April 2026). "
                    "Estimated $2.3M stolen from victims."
                ),
                "executive_summary": (
                    "This is a synthetic deepfake created to commit cryptocurrency fraud. "
                    "Subject identity (Elon Musk) is confirmed to be targeted in active scam campaign. "
                    "Immediate action recommended: report to platform & law enforcement."
                ),
                "technical_breakdown": (
                    "FACIAL ARTIFACTS:\n"
                    "• Eye rendering: Flickering eyelids frame-to-frame (frame 187-192)\n"
                    "• Teeth: Occasional swimming/blending artifacts during speech\n"
                    "• Jawline: Edge-soft artifacts around face boundary\n"
                    "• Temporal: 50.6% confidence drop indicates algorithm failure under rotational stress\n\n"
                    "SCENE ANALYSIS:\n"
                    "• Background consistent (95% authenticity - real office)\n"
                    "• Lighting natural and stable\n"
                    "• No obvious green screen artifacts\n\n"
                    "ASSESSMENT: Professional-quality deepfake using face-swap algorithm. "
                    "Combined with identity fraud context = HIGH threat level."
                )
            }
        }
        
        print("\n[Step 3] Pipeline Results:")
        print("\n--- ENSEMBLE FORENSICS ---")
        fe = example_state['ensemble_forensics']
        print(f"Verdict: {'🚨 FAKE' if fe['is_fake'] else '✓ REAL'}")
        print(f"Confidence: {fe['confidence']}%")
        print(f"Reason: {fe['reason']}")
        
        print("\n--- OSINT INVESTIGATION ---")
        osint = example_state['osint_data']
        print(f"Claim Verified: {osint['claim_verified']}")
        print(f"Debunked: {osint['debunked']}")
        print(f"Sources: {len(osint['sources_used'])} sources found")
        
        print("\n--- XAI FORENSICS REPORT ---")
        xai = example_state['xai_report']
        print(f"Verdict: {xai['verdict']}")
        print(f"Confidence: {xai['confidence']}%")
        print(f"\nExecutive Summary:\n{xai['executive_summary']}")
        print(f"\nTechnical Breakdown:\n{xai['technical_breakdown']}")
    
    else:
        # Production path - actually run the pipeline
        result = run_aispy_pipeline(
            input_type="media",
            media_path=media_path,
            identity_data=identity_data
        )
        
        print("\n[Step 3] Pipeline Complete. Results:")
        print(json.dumps({k: (v.model_dump() if hasattr(v, 'model_dump') else v) 
                          for k, v in result.items()}, indent=2))


def example_4_batch_processing():
    """Example 4: Batch analyze multiple media files."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Batch Processing Multiple Files")
    print("=" * 70)
    
    media_files = [
        "./test_media/video1.mp4",
        "./test_media/video2.mp4",
        "./test_media/image1.jpg",
    ]
    
    print(f"\nBatch processing {len(media_files)} files...")
    
    engine = EnsembleForensicsEngine()
    results = {}
    
    for media_file in media_files:
        if os.path.exists(media_file):
            print(f"\n  Analyzing: {media_file}")
            result = engine.analyze(media_file)
            results[media_file] = result
            print(f"    Result: {'FAKE' if result['is_fake'] else 'REAL'} "
                  f"({result['confidence']:.1f}% confidence)")
        else:
            print(f"\n  ⚠️ {media_file} not found (skipped)")
    
    # Summary report
    print("\n" + "-" * 70)
    print("BATCH SUMMARY:")
    if results:
        fake_count = sum(1 for r in results.values() if r['is_fake'])
        real_count = len(results) - fake_count
        print(f"  Total Analyzed: {len(results)}")
        print(f"  Detected as Fake: {fake_count}")
        print(f"  Detected as Real: {real_count}")
        print(f"  High Confidence (>90%): {sum(1 for r in results.values() if r['confidence'] > 90)}")
    else:
        print("  No files found to analyze")


def example_5_interpreting_metrics():
    """Example 5: Guide to interpreting forensic metrics."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Understanding Forensic Metrics")
    print("=" * 70)
    
    print("""
🎯 METRIC INTERPRETATION GUIDE:

1. FACE REAL SCORE (0-100%)
   ├─ 90-100%: Highly authentic. Natural features, smooth rendering.
   ├─ 80-89%:  Likely authentic. Normal variations acceptable.
   ├─ 70-79%:  Suspicious. Minor artifacts detected.
   ├─ 40-69%:  Likely fake. Significant deepfake signatures.
   └─ <40%:    Almost certainly fake. Severe rendering failures.

2. SCENE REAL SCORE (0-100%)
   ├─ 90-100%: Authentic background. Consistent lighting, no anomalies.
   ├─ 80-89%:  Likely authentic environment.
   ├─ 70-79%:  Suspicious. Background artifacts or lighting issues.
   └─ <70%:    Likely fake background manipulation.

3. TEMPORAL GLITCHES (Video-specific)
   • Look at: min_face vs avg_face
   • If (avg_face - min_face) > 30%: Temporal consistency failure
   • Example: avg_face=71.3%, min_face=38.4% → 32.9% drop
   • Interpretation: Deepfake algorithm failed during head rotation/stress

4. VIDEO METRICS BREAKDOWN
   ├─ avg_scene & min_scene: Background stability over time
   ├─ avg_face & min_face: Facial authenticity over time
   ├─ frames_analyzed: Number of frames sampled (intelligent sampling)
   └─ total_frames: Complete video frame count

📋 SAMPLE METRIC SCENARIOS:

Scenario A: AUTHENTIC IMAGE
├─ scene_real_score: 94.2%
└─ face_real_score: 91.7%
   ➜ VERDICT: Real. Both scores >85%.

Scenario B: SUSPICIOUS IMAGE
├─ scene_real_score: 88.1%
└─ face_real_score: 72.3%
   ➜ VERDICT: Inconclusive. Scene OK, but face shows artifacts.

Scenario C: CLEAR DEEPFAKE VIDEO
├─ avg_face: 68.2%, min_face: 31.5%
├─ avg_scene: 92.1%, min_scene: 88.7%
└─ frames_analyzed: 20/600
   ➜ VERDICT: Fake. Face temporal glitch (36.7% drop) = deepfake signature.
   ➜ ACTION: Block content, report to platform.

Scenario D: PROFESSIONAL DEEPFAKE
├─ avg_face: 82.4%, min_face: 78.1%
├─ avg_scene: 91.3%, min_scene: 89.2%
└─ frames_analyzed: 25/1000
   ➜ VERDICT: Inconclusive. Requires XAI + Identity + OSINT context.
   ➜ ACTION: Cross-reference with subject's identity and recent news.
    """)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AI-SPY: ENSEMBLE FORENSICS & XAI INTEGRATION EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates the integrated forensics pipeline.")
    print("Choose an example to run:\n")
    
    examples = {
        "1": ("Simple Image Analysis", example_1_simple_image_analysis),
        "2": ("Video Analysis (Temporal)", example_2_video_analysis),
        "3": ("Full Pipeline (Forensics+OSINT+XAI)", example_3_full_pipeline_with_xai),
        "4": ("Batch Processing", example_4_batch_processing),
        "5": ("Metrics Interpretation Guide", example_5_interpreting_metrics),
        "all": ("Run All Examples", None),
    }
    
    for key, (desc, _) in examples.items():
        print(f"  {key}: {desc}")
    
    # For automatic demo, run all examples
    print("\n🚀 Running all examples...")
    
    example_5_interpreting_metrics()
    example_1_simple_image_analysis()
    example_2_video_analysis()
    example_3_full_pipeline_with_xai()
    example_4_batch_processing()
    
    print("\n" + "=" * 70)
    print("✓ Examples complete!")
    print("=" * 70)
    print("\nFor production usage, see: FORENSICS_XAI_INTEGRATION.md")
