#!/usr/bin/env python3
"""
Utilitaires pour l'API RAG
"""

import os
import time
import requests
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def wait_for_ollama(base_url: str = "http://localhost:11434", timeout: int = 300) -> bool:
    """
    Attendre que Ollama soit disponible
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama est disponible")
                return True
        except requests.exceptions.ConnectionError:
            logger.info("🔄 Attente d'Ollama...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification d'Ollama: {e}")
            time.sleep(5)
    
    logger.error("❌ Timeout: Ollama n'est pas disponible")
    return False

def check_ollama_model(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Vérifier si un modèle est disponible dans Ollama
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            # Chercher le modèle (avec ou sans tag)
            for available_model in available_models:
                if model_name in available_model or available_model.startswith(model_name):
                    logger.info(f"✅ Modèle {model_name} trouvé: {available_model}")
                    return True
            
            logger.warning(f"⚠️ Modèle {model_name} non trouvé. Modèles disponibles: {available_models}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur vérification modèle: {e}")
        return False

def pull_ollama_model(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Télécharger un modèle Ollama
    """
    try:
        logger.info(f"🔄 Téléchargement du modèle {model_name}...")
        
        response = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=1800  # 30 minutes
        )
        
        if response.status_code == 200:
            # Suivre le progrès du téléchargement
            for line in response.iter_lines():
                if line:
                    try:
                        import json
                        data = json.loads(line.decode('utf-8'))
                        if 'status' in data:
                            logger.info(f"📥 {data['status']}")
                    except:
                        pass
            
            logger.info(f"✅ Modèle {model_name} téléchargé avec succès")
            return True
        else:
            logger.error(f"❌ Erreur téléchargement modèle: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement modèle {model_name}: {e}")
        return False

def ensure_ollama_model(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    S'assurer qu'un modèle Ollama est disponible (le télécharger si nécessaire)
    """
    # Attendre qu'Ollama soit disponible
    if not wait_for_ollama(base_url):
        return False
    
    # Vérifier si le modèle existe
    if check_ollama_model(model_name, base_url):
        return True
    
    # Télécharger le modèle s'il n'existe pas
    logger.info(f"🔄 Modèle {model_name} non trouvé, téléchargement...")
    return pull_ollama_model(model_name, base_url)

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Obtenir des informations sur un fichier
    """
    if not file_path.exists():
        return {}
    
    stat = file_path.stat()
    return {
        'name': file_path.name,
        'size': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'modified': stat.st_mtime,
        'extension': file_path.suffix.lower(),
        'is_supported': file_path.suffix.lower() in {'.pdf', '.txt', '.doc', '.docx'}
    }

def clean_text(text: str) -> str:
    """
    Nettoyer le texte extrait des documents
    """
    if not text:
        return ""
    
    # Supprimer les caractères de contrôle
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Normaliser les espaces
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def format_sources(sources: list) -> str:
    """
    Formater la liste des sources pour l'affichage
    """
    if not sources:
        return "Aucune source"
    
    unique_sources = list(set(sources))
    return ", ".join(unique_sources)

def estimate_tokens(text: str) -> int:
    """
    Estimer le nombre de tokens dans un texte
    """
    # Estimation approximative: 1 token ≈ 4 caractères en français
    return len(text) // 4

def truncate_text(text: str, max_tokens: int = 4000) -> str:
    """
    Tronquer le texte pour respecter la limite de tokens
    """
    estimated_tokens = estimate_tokens(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculer la longueur maximale en caractères
    max_chars = max_tokens * 4
    
    if len(text) <= max_chars:
        return text
    
    # Tronquer en gardant les mots complets
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    
    if last_space > max_chars * 0.8:  # Si on trouve un espace dans les 20% finaux
        truncated = truncated[:last_space]
    
    return truncated + "..."