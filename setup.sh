#!/bin/bash

# 🚀 Script de configuration et lancement du système RAG Docker

set -e

echo "🐳 === SETUP RAG SYSTEM WITH DOCKER ==="
echo ""

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
print_status "Vérification des prérequis..."

if ! command -v docker &> /dev/null; then
    print_error "Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

print_success "Docker et Docker Compose sont installés"

# Création des répertoires nécessaires
print_status "Création des répertoires..."

mkdir -p data
mkdir -p faiss_index

print_success "Répertoires créés"

# Vérification des fichiers
print_status "Vérification des fichiers de configuration..."

required_files=("docker-compose.yml" "Dockerfile" "requirements.txt" "rag_api.py")

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_error "Fichier manquant: $file"
        exit 1
    fi
done

print_success "Tous les fichiers de configuration sont présents"

# Construction et lancement
print_status "Construction des images Docker..."
docker-compose build

print_success "Images construites avec succès"

print_status "Lancement des services..."
docker-compose up -d

print_success "Services démarrés"

# Attendre que les services soient prêts
print_status "Attente du démarrage des services..."
sleep 10

# Vérifier le statut d'Ollama
print_status "Vérification du statut d'Ollama..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama est opérationnel"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Ollama ne répond pas après 5 minutes"
        exit 1
    fi
    echo -n "."
    sleep 10
done

# Télécharger le modèle Mistral si nécessaire
print_status "Vérification du modèle Mistral..."
if ! curl -s http://localhost:11434/api/tags | grep -q "mistral";