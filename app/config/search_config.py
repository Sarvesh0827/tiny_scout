"""
Search configuration defining intent guardrails, domain trust scores, and tiered ranking logic.
"""

# Priority 1: Query Intent Guardrails configuration
INTENT_GUARDRAILS = {
    "voice_moderation": {
        "required_terms": ["voice", "audio", "speech", "moderation", "toxicity", "safety"],
        "negative_terms": ["voice agent", "call center", "voice generator", "text-to-speech", "tts", "voice cloning", "customer service agent"],
        "min_required_hits": 1  # At least one required term must build present
    },
    "medical_imaging": {
        "required_terms": ["cancer", "tumor", "detection", "diagnosis", "screening", "radiology"],
        "negative_terms": ["home remedy", "natural cure", "herbal", "alternative medicine"],
        "min_required_hits": 1
    },
    "climate_policy_energy": {
        "required_terms": ["net-zero", "emissions", "policy", "energy", "climate", "transition"],
        "negative_terms": ["conspiracy", "hoax", "fake", "denial"],
        "min_required_hits": 1
    }
}

# Priority 2: Targeted query templates
QUERY_TEMPLATES = {
    "voice_moderation": [
        '"{base_query}" vendor',
        '"{base_query}" platform',
        '"{base_query}" API',
        '"{base_query}" solution'
    ]
}

# Priority 3: Domain Trust Scores (Tiered System)
# Tier A: 1.0 (Official, Verified, High Authority)
# Tier B: 0.7 (Industry News, Reputable Blogs)
# Tier C: 0.3 (General, Low Authority)
DOMAIN_TRUST_SCORES = {
    # Voice Moderation
    "modulate.ai": 1.0,
    "unity.com": 1.0,
    "discord.com": 0.9,
    "microsoft.com": 0.9,
    "spectrumlabsai.com": 0.9,
    "hivemoderation.com": 0.9,
    "krisp.ai": 0.8,
    "speechly.com": 0.8,
    "techcrunch.com": 0.7,
    "venturebeat.com": 0.7,
    "medium.com": 0.4,
    
    # Climate
    "iea.org": 1.0,
    "ipcc.ch": 1.0,
    "worldbank.org": 1.0,
    "unfccc.int": 1.0,
    "ourworldindata.org": 0.9,
    "nature.com": 0.9,
    "science.org": 0.9,
    
    # Medical
    "cancer.gov": 1.0,
    "fda.gov": 1.0,
    "nih.gov": 1.0,
    "who.int": 1.0,
    "cdc.gov": 1.0,
    "mayoclinic.org": 0.8
}

DEFAULT_TRUST_SCORE = 0.5

def get_domain_trust_score(url: str) -> float:
    """Extract domain and return trust score."""
    from urllib.parse import urlparse
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Exact match
        if domain in DOMAIN_TRUST_SCORES:
            return DOMAIN_TRUST_SCORES[domain]
            
        # Suffix match (e.g., blog.modulate.ai matches modulate.ai)
        for trusted_domain, score in DOMAIN_TRUST_SCORES.items():
            if domain.endswith(trusted_domain):
                return score
                
        return DEFAULT_TRUST_SCORE
    except:
        return DEFAULT_TRUST_SCORE
