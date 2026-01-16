"""
Topic-aware seed URLs for fallback retrieval.
Seeds are ONLY used when live search fails.
"""

# Voice Moderation Seeds
SEEDS_VOICE_MODERATION = [
    "https://www.modulate.ai/toxmod",
    "https://unity.com/products/vivox-voice-chat",
    "https://discord.com/safety",
    "https://azure.microsoft.com/en-us/products/ai-services/ai-content-safety",
]

# Medical Imaging Seeds
SEEDS_MEDICAL_IMAGING = [
    "https://www.cancer.gov/about-cancer/screening",
    "https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices",
    "https://pubmed.ncbi.nlm.nih.gov/?term=deep+learning+mammography+cancer+detection",
    "https://www.nature.com/subjects/cancer-screening",
]

# Climate Policy & Energy Seeds
SEEDS_CLIMATE_POLICY_ENERGY = [
    "https://www.iea.org/reports/net-zero-by-2050",
    "https://www.ipcc.ch/report/ar6/wg3/",
    "https://www.worldbank.org/en/topic/climatechange",
    "https://unfccc.int/process-and-meetings/the-paris-agreement/nationally-determined-contributions-ndcs",
    "https://ourworldindata.org/energy",
    "https://www.irena.org/publications",
]

# Generic fallback
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
    ],
    "climate_policy_energy": [
        "net-zero", "net zero", "emissions", "2050", "decarbonization", 
        "energy transition", "renewables", "fossil fuels", "climate policy",
        "ndc", "cop", "carbon", "ipcc", "iea", "unfccc", "paris agreement",
        "developing countries", "emerging markets", "climate finance"
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

KEYWORDS_CLIMATE = [
    "net zero", "emissions", "decarbonization", "energy transition",
    "renewable energy", "climate policy", "ndc", "paris agreement",
    "ipcc", "iea", "developing countries", "climate finance",
    "fossil fuels", "carbon neutral", "mitigation", "cop"
]

def classify_topic(query: str) -> str:
    """
    Classify query topic based on keywords.
    Returns: 'voice_moderation', 'medical_imaging', 'climate_policy_energy', or 'unknown'
    """
    query_lower = query.lower()
    
    # Check each topic
    voice_score = sum(1 for kw in TOPIC_KEYWORDS["voice_moderation"] if kw in query_lower)
    medical_score = sum(1 for kw in TOPIC_KEYWORDS["medical_imaging"] if kw in query_lower)
    climate_score = sum(1 for kw in TOPIC_KEYWORDS["climate_policy_energy"] if kw in query_lower)
    
    # Return topic with highest score
    scores = {
        "climate_policy_energy": climate_score,
        "medical_imaging": medical_score,
        "voice_moderation": voice_score
    }
    
    max_topic = max(scores, key=scores.get)
    if scores[max_topic] > 0:
        return max_topic
    else:
        return "unknown"

def get_seeds_for_topic(topic: str) -> list:
    """Get seed URLs for a specific topic."""
    if topic == "voice_moderation":
        return SEEDS_VOICE_MODERATION
    elif topic == "medical_imaging":
        return SEEDS_MEDICAL_IMAGING
    elif topic == "climate_policy_energy":
        return SEEDS_CLIMATE_POLICY_ENERGY
    else:
        return SEEDS_GENERIC

def get_keywords_for_topic(topic: str) -> list:
    """Get relevance keywords for a specific topic."""
    if topic == "voice_moderation":
        return KEYWORDS_VOICE
    elif topic == "medical_imaging":
        return KEYWORDS_MEDICAL
    elif topic == "climate_policy_energy":
        return KEYWORDS_CLIMATE
    else:
        return []

def rewrite_query_for_search(query: str, topic: str) -> str:
    """
    Rewrite query to be more search-friendly with high-signal keywords.
    """
    # Extract key terms
    words = query.lower().split()
    
    # Topic-specific high-signal terms
    signal_terms = {
        "climate_policy_energy": ["IEA", "IPCC", "World Bank", "NDC", "energy transition", "net zero", "2050", "developing countries"],
        "medical_imaging": ["FDA", "cancer detection", "radiology", "AI diagnosis", "clinical trial"],
        "voice_moderation": ["voice moderation", "speech toxicity", "content moderation", "AI safety"]
    }
    
    # Get signal terms for topic
    terms = signal_terms.get(topic, [])
    
    # Keep important words from original query
    important_words = [w for w in words if len(w) > 4 and w not in ['about', 'what', 'how', 'when', 'where', 'which']]
    
    # Combine: signal terms + important words (first 5)
    rewritten = " ".join(terms[:3] + important_words[:5])
    
    return rewritten if rewritten else query
