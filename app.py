from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="AI Action Safety Decision Layer v2", version="2.0")

# ========== LOAD SEMANTIC MODEL (REAL AI) ==========
print("Loading semantic model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully")

# ========== DANGEROUS PATTERNS (FOR EMBEDDING COMPARISON) ==========
DANGEROUS_EXAMPLES = {
    "data_deletion": [
        "delete all files", "erase system data", "wipe entire disk", "remove everything",
        "delete database", "drop all tables", "truncate users", "purge records",
        "destroy all data", "format drive", "clear all content", "rm rf"
    ],
    "security_bypass": [
        "disable security", "turn off firewall", "stop antivirus", "disable authentication",
        "bypass login", "remove password", "disable encryption", "turn off monitoring",
        "disable 2fa", "bypass security controls", "disable audit"
    ],
    "data_access": [
        "read passwords", "access ssh keys", "view credit cards", "steal api keys",
        "dump database", "extract emails", "read secrets", "export customer data",
        "access user data", "view tokens", "copy database"
    ],
    "financial": [
        "wire money", "transfer funds", "send payment", "change balance",
        "modify price", "refund amount", "adjust payment", "send crypto",
        "withdraw funds", "credit account", "debit wallet"
    ]
}

SAFE_EXAMPLES = [
    "clean temp files", "remove old logs", "delete cache", "clear downloads",
    "remove temporary data", "clean workspace", "delete draft", "remove backup",
    "clear history", "empty trash", "clean up", "remove duplicate"
]

# ========== PRE-COMPUTE EMBEDDINGS ==========
dangerous_embeddings = {}
for intent, examples in DANGEROUS_EXAMPLES.items():
    dangerous_embeddings[intent] = model.encode(examples, normalize_embeddings=True)

safe_embeddings = model.encode(SAFE_EXAMPLES, normalize_embeddings=True)

# ========== REQUEST MODEL ==========
class SafetyRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=1000)
    system_criticality: Literal["low", "medium", "high"] = Field(default="medium")

# ========== SEMANTIC SIMILARITY ENGINE ==========
def semantic_similarity(text: str, embeddings, threshold: float = 0.5):
    """Compute max cosine similarity between text and precomputed embeddings"""
    text_embedding = model.encode([text], normalize_embeddings=True)
    similarities = np.dot(embeddings, text_embedding.T).flatten()
    max_similarity = float(np.max(similarities))
    return max_similarity

def detect_intent_semantic(text: str) -> tuple[str, float, str]:
    """Semantic intent detection using embeddings"""
    text_lower = text.lower()
    
    # Check dangerous intents
    for intent, embeddings in dangerous_embeddings.items():
        similarity = semantic_similarity(text_lower, embeddings)
        if similarity > 0.55:
            return intent, similarity, "semantic_match"
    
    # Check safe patterns
    safe_similarity = semantic_similarity(text_lower, safe_embeddings)
    if safe_similarity > 0.6:
        return "safe", safe_similarity, "semantic_match"
    
    # Default to safe with low confidence
    return "safe", 0.15, "no_match"

# ========== RISK SCORING ENGINE ==========
RISK_WEIGHTS = {
    "data_deletion": 0.95,
    "security_bypass": 0.92,
    "data_access": 0.88,
    "financial": 0.90,
    "safe": 0.10
}

CRITICALITY_MODIFIER = {
    "low": 1.0,
    "medium": 1.3,
    "high": 1.6
}

def compute_risk_score(intent: str, similarity: float, criticality: str) -> float:
    """Compute weighted risk score between 0.0 and 1.0"""
    base_risk = RISK_WEIGHTS.get(intent, 0.10)
    criticality_mult = CRITICALITY_MODIFIER.get(criticality, 1.0)
    
    if intent == "safe":
        weighted_score = base_risk * (1 - similarity)
    else:
        weighted_score = base_risk * similarity * criticality_mult
    
    return min(1.0, max(0.0, weighted_score))

# ========== DECISION LOGIC ==========
def get_risk_level(risk_score: float) -> str:
    if risk_score >= 0.7:
        return "HIGH"
    elif risk_score >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"

def get_action(risk_score: float) -> str:
    if risk_score >= 0.7:
        return "BLOCK"
    elif risk_score >= 0.3:
        return "WARN"
    else:
        return "ALLOW"

def get_category(intent: str) -> str:
    categories = {
        "data_deletion": "Data Deletion",
        "security_bypass": "Security Bypass",
        "data_access": "Data Access",
        "financial": "Financial Actions",
        "safe": "Safe Operation"
    }
    return categories.get(intent, "Unknown")

def get_intent_display(intent: str) -> str:
    displays = {
        "data_deletion": "Data Destruction Intent",
        "security_bypass": "Security Bypass Intent",
        "data_access": "Data Access Intent",
        "financial": "Financial Manipulation Intent",
        "safe": "Safe Operational Intent"
    }
    return displays.get(intent, "Unknown Intent")

def generate_reason(intent: str, similarity: float, action: str, risk_score: float) -> str:
    if intent == "safe":
        if action == "ALLOW":
            return f"Safe operation (confidence: {similarity:.2%})"
        else:
            return f"Borderline safe operation with {similarity:.2%} similarity"
    
    if action == "BLOCK":
        return f"BLOCKED: {get_category(intent)} detected (confidence: {similarity:.2%})"
    elif action == "WARN":
        return f"WARNING: Possible {get_category(intent)} (confidence: {similarity:.2%}) - human review required"
    else:
        return f"Allowed with caution: Low confidence ({similarity:.2%}) for {get_category(intent)}"

# ========== MAIN PROCESSING FUNCTION ==========
def process_request(input_text: str, criticality: str) -> dict:
    """Main pipeline: semantic intent → similarity → risk → decision"""
    
    intent, similarity, match_type = detect_intent_semantic(input_text)
    risk_score = compute_risk_score(intent, similarity, criticality)
    risk_level = get_risk_level(risk_score)
    action = get_action(risk_score)
    category = get_category(intent)
    intent_display = get_intent_display(intent)
    reason = generate_reason(intent, similarity, action, risk_score)
    
    return {
        "input": input_text,
        "intent": intent_display,
        "category": category,
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "action": action,
        "reason": reason,
        "similarity": round(similarity, 4),
        "semantic_match": match_type
    }

# ========== API ENDPOINTS ==========
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0", "model": "all-MiniLM-L6-v2"}

@app.get("/v1/decide")
async def decide_get(input: str, criticality: Literal["low", "medium", "high"] = "medium"):
    """GET endpoint for quick testing"""
    try:
        start = time.time()
        result = process_request(input, criticality)
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/v1/decide")
async def decide_post(request: SafetyRequest):
    """POST endpoint for production use"""
    try:
        start = time.time()
        result = process_request(request.input, request.system_criticality)
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "AI Action Safety Decision Layer v2",
        "version": "2.0",
        "status": "production-ready",
        "model": "all-MiniLM-L6-v2",
        "capabilities": ["semantic_intent_detection", "risk_scoring", "paraphrase_handling"],
        "endpoints": [
            "GET  /health",
            "GET  /v1/decide?input=<text>&criticality=medium",
            "POST /v1/decide"
        ]
    }

@app.get("/v1/batch")
async def batch_decide(inputs: str, criticality: Literal["low", "medium", "high"] = "medium"):
    """Batch endpoint for multiple inputs"""
    try:
        input_list = [i.strip() for i in inputs.split(",")]
        results = []
        for inp in input_list:
            if inp:
                result = process_request(inp, criticality)
                results.append(result)
        return {"count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch error: {str(e)}")
