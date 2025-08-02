from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from typing import List, Optional
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG API", description="API pour système RAG avec Ollama")

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = "llama2"  # ou votre modèle préféré

class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    model: Optional[str] = DEFAULT_MODEL

class QueryResponse(BaseModel):
    answer: str
    model_used: str
    context_used: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "RAG API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        # Vérifier la connexion à Ollama
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            return {"status": "healthy", "ollama": "connected", "base_url": OLLAMA_BASE_URL}
        else:
            return {"status": "unhealthy", "ollama": "disconnected", "base_url": OLLAMA_BASE_URL}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "base_url": OLLAMA_BASE_URL}

@app.get("/models")
async def get_available_models():
    """Récupérer la liste des modèles disponibles dans Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            return {"models": models.get("models", [])}
        else:
            raise HTTPException(status_code=500, detail="Impossible de récupérer les modèles")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de la récupération des modèles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de connexion à Ollama: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Effectuer une requête RAG"""
    try:
        # Attendre qu'Ollama soit prêt
        health_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if health_response.status_code != 200:
            raise HTTPException(status_code=503, detail="Service Ollama non disponible")

        # Préparer le prompt avec le contexte si fourni
        if request.context:
            prompt = f"""Contexte: {request.context}

Question: {request.question}

Réponds en te basant sur le contexte fourni. Si l'information n'est pas dans le contexte, indique-le clairement."""
        else:
            prompt = request.question

        # Préparer la requête pour Ollama
        ollama_request = {
            "model": request.model,
            "prompt": prompt,
            "stream": False
        }

        # Envoyer la requête à Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return QueryResponse(
                answer=result.get("response", "Aucune réponse générée"),
                model_used=request.model,
                context_used=request.context
            )
        else:
            logger.error(f"Erreur Ollama: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=500, 
                detail=f"Erreur lors de la génération: {response.text}"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion à Ollama: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur de connexion à Ollama: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur inattendue: {str(e)}")

@app.post("/chat")
async def chat_with_model(request: QueryRequest):
    """Interface de chat simple avec le modèle"""
    try:
        ollama_request = {
            "model": request.model,
            "prompt": request.question,
            "stream": False
        }

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "response": result.get("response", "Aucune réponse générée"),
                "model": request.model
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de la génération")

    except Exception as e:
        logger.error(f"Erreur chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Démarrage de l'API RAG...")
    uvicorn.run(app, host="0.0.0.0", port=8000)