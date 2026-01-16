"""
Topic-aware seed URLs for fallback retrieval.
Seeds are ONLY used when live search fails.
"""

# Voice Moderation Seeds (only for voice/speech/toxicity queries)
SEEDS_VOICE_MODERATION = [
    "https://www.modulate.ai/toxmod",
    "https://unity.com/products/vivox-voice-chat",
    "https://discord.com/safety",
    "https://azure.microsoft.com/en-us/products/ai-services/ai-content-safety",
]

# Medical Imaging Seeds (only for medical/cancer/radiology queries)
SEEDS_MEDICAL_IMAGING = [
    "https://www.cancer.gov/about-cancer/screening",
    "https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices",
    "https://pubmed.ncbi.nlm.nih.gov/?term=deep+learning+mammography+cancer+detection",
    "https://www.rsna.org/news/2023/ai-radiology",
    "https://www.nature.com/subjects/cancer-screening",
]

# Generic fallback (only if topic cannot be determined)
SEEDS_GENERIC = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
]

# Topic classification keywords
TOPIC_KEYWORDS = {
    "voice_moderation": [
        "voice", "speech", "toxicity", "harassment", "moderation", 
        "discord", "gaming", "chat", "audio", "vocal"
    ],
    "medical_imaging": [
        "cancer", "radiology", "imaging", "mammography", "ct", "mri",
        "biopsy", "screening", "diagnosis", "medical", "tumor", "oncology"
    ]
}

# Relevance keywords (for scoring)
KEYWORDS_VOICE = [
    "voice moderation", "speech toxicity", "voice chat safety", "harassment",
    "real-time", "toxicity", "content moderation", "audio", "transcription moderation",
    "voice chat", "safety tools", "automated moderation", "proactive voice"
]

KEYWORDS_MEDICAL = [
    "cancer detection", "medical imaging", "radiology", "ai diagnosis",
    "deep learning", "mammography", "ct scan", "mri", "screening",
    "sensitivity", "specificity", "radiologist", "accuracy"
]

def classify_topic(query: str) -> str:
    """
    Classify query topic based on keywords.
    Returns: 'voice_moderation', 'medical_imaging', or 'unknown'
    """
    query_lower = query.lower()
    
    # Check voice moderation
    voice_score = sum(1 for kw in TOPIC_KEYWORDS["voice_moderation"] if kw in query_lower)
    
    # Check medical imaging
    medical_score = sum(1 for kw in TOPIC_KEYWORDS["medical_imaging"] if kw in query_lower)
    
    if medical_score > voice_score and medical_score > 0:
        return "medical_imaging"
    elif voice_score > 0:
        return "voice_moderation"
    else:
        return "unknown"

def get_seeds_for_topic(topic: str) -> list:
    """Get seed URLs for a specific topic."""
    if topic == "voice_moderation":
        return SEEDS_VOICE_MODERATION
    elif topic == "medical_imaging":
        return SEEDS_MEDICAL_IMAGING
    else:
        return SEEDS_GENERIC

def get_keywords_for_topic(topic: str) -> list:
    """Get relevance keywords for a specific topic."""
    if topic == "voice_moderation":
        return KEYWORDS_VOICE
    elif topic == "medical_imaging":
        return KEYWORDS_MEDICAL
    else:
        return []
