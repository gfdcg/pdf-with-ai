 PDF avec IA - Système RAG
Un système de Retrieval-Augmented Generation (RAG) puissant pour analyser et interroger des documents PDF avec l'intelligence artificielle.
 Fonctionnalités

 Extraction intelligente de texte depuis des PDFs
 Analyse IA avancée avec modèles de langage
 Interface de questions-réponses intuitive
 Recherche sémantique dans les documents
 API REST pour intégration
 Interface web Streamlit moderne
 Support Docker pour déploiement facile

🏗 Architecture
pdf-with-ai/
 rag_api.py              
 streamlit_app.py        
 utils.py               
docker-compose.yml     
 Dockerfile            
 Dockerfile.streamlit   
 requirements.txt      
Installation et Utilisation
Méthode 1: Installation locale
bash# 1. Cloner le projet
git clone https://github.com/gfdcg/pdf-with-ai.git
cd pdf-with-ai

2. Créer un environnement virtuel
python -m venv rag_env
rag_env\Scripts\activate  # Windows

 3. Installer les dépendances
pip install -r requirements.txt

 4. Lancer l'API
python rag_api.py

5. Ou lancer l'interface Streamlit
streamlit run streamlit_app.py
Méthode 2: Avec Docker (Recommandé)
bash# Lancer tous les services
docker-compose up -d

# Accéder aux services
# - API: http://localhost:8000
# - Interface web: http://localhost:8501
Utilisation
Via l'interface web

Ouvrez http://localhost:8501
Uploadez votre PDF
Posez vos questions en langage naturel
Obtenez des réponses contextuelles

Via l'API REST
pythonimport requests

Upload d'un PDF
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/upload', files=files)

Poser une question
data = {'question': 'Quel est le sujet principal de ce document ?'}
response = requests.post('http://localhost:8000/ask', json=data)
print(response.json())
Programmation directe
pythonfrom rag_api import RAGSystem

 Initialiser le système
rag = RAGSystem()

# Analyser un PDF
rag.process_pdf("document.pdf")

 Poser une question
answer = rag.ask_question("Résume le contenu principal")
print(answer)
Configuration
Variables d'environnement (.env)
env# Modèle de langage
MODEL_NAME=llama2
OLLAMA_URL=http://localhost:11434

 Base de données vectorielle
VECTOR_DB_PATH=./data/vector_db
 API
API_HOST=0.0.0.0
API_PORT=8000
Prérequis

 Python 3.8+
 Ollama (pour les modèles locaux)
Librairies: PyTorch, Transformers, Streamlit
 Espace disque: ~2GB pour les modèles

 Scripts de déploiement
Configuration automatique
bash# Rendre le script exécutable
chmod +x setup.sh
 Lancer l'installation complète
./setup.sh
Fix Docker (si nécessaire)
bashchmod +x fix_docker.sh
./fix_docker.sh
 Endpoints API
MéthodeEndpointDescriptionPOST/uploadUpload et traitement d'un PDFPOST/askPoser une question sur le documentGET/healthVérification de l'état du serviceGET/docsDocumentation interactive
 Contribution

Fork le projet
Créez une branche feature (git checkout -b feature/nouvelle-fonctionnalite)
Commitez vos changements (git commit -am 'Ajout: nouvelle fonctionnalité')
Push vers la branche (git push origin feature/nouvelle-fonctionnalite)
Ouvrez une Pull Request

 Dépannage
Problèmes courants
Erreur Ollama :
bash# Vérifier si Ollama est démarré
ollama serve

# Installer un modèle
ollama pull llama2
Erreur de mémoire :

Réduisez la taille des chunks dans utils.py
Utilisez un modèle plus léger

Port déjà utilisé :
bash# Changer les ports dans docker-compose.yml
# Ou arrêter les services existants
docker-compose down
