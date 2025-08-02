#!/bin/bash

# 🔧 Script de correction des problèmes Docker

set -e

echo "🔧 === CORRECTION DES PROBLÈMES DOCKER ==="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 1. Arrêter tous les conteneurs en conflit
print_status "Arrêt des conteneurs existants..."
docker-compose down --remove-orphans 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
print_success "Conteneurs arrêtés"

# 2. Nettoyer les conteneurs et réseaux
print_status "Nettoyage des ressources Docker..."
docker container prune -f
docker network prune -f
print_success "Ressources nettoyées"

# 3. Vérifier les ports
print_status "Vérification des ports..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 8000 occupé, tentative de libération..."
    fuser -k 8000/tcp 2>/dev/null || true
fi

if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 8501 occupé, tentative de libération..."
    fuser -k 8501/tcp 2>/dev/null || true
fi

if lsof -Pi :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 11434 occupé, tentative de libération..."
    fuser -k 11434/tcp 2>/dev/null || true
fi

print_success "Ports vérifiés"

# 4. Reconstruire les images
print_status "Reconstruction des images Docker..."
docker-compose build --no-cache
print_success "Images reconstruites"

# 5. Démarrer les services un par un
print_status "Démarrage d'Ollama..."
docker-compose up -d ollama
sleep 10

print_status "Vérification d'Ollama..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama opérationnel"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Ollama ne répond pas"
        exit 1
    fi
    echo -n "."
    sleep 5
done

print_status "Démarrage de l'API RAG..."
docker-compose up -d rag-api
sleep 15

print_status "Vérification de l'API RAG..."
for i in {1..20}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API RAG opérationnelle"
        break
    fi
    if [ $i -eq 20 ]; then
        print_error "API RAG ne répond pas"
        print_status "Logs de l'API RAG:"
        docker-compose logs rag-api
        exit 1
    fi
    echo -n "."
    sleep 5
done

print_status "Démarrage de Streamlit..."
docker-compose up -d streamlit-app
sleep 10

print_status "Vérification de Streamlit..."
for i in {1..15}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        print_success "Streamlit opérationnel"
        break
    fi
    if [ $i -eq 15 ]; then
        print_warning "Streamlit ne répond pas encore, vérification des logs..."
        docker-compose logs streamlit-app
    fi
    echo -n "."
    sleep 5
done

# 6. Télécharger le modèle Mistral si nécessaire
print_status "Vérification du modèle Mistral..."
if ! curl -s http://localhost:11434/api/tags | grep -q "mistral"; then
    print_status "Téléchargement de Mistral (peut prendre du temps)..."
    docker-compose exec ollama ollama pull mistral
    print_success "Modèle Mistral téléchargé"
else
    print_success "Modèle Mistral déjà présent"
fi

# 7. État final
echo ""
print_success "🎉 CORRECTION TERMINÉE!"
echo ""
echo "📋 === ÉTAT DES SERVICES ==="
docker-compose ps
echo ""
echo "🌐 === URLS DISPONIBLES ==="
echo "   • 🤖 API RAG:      http://localhost:8000"
echo "   • 📊 Documentation: http://localhost:8000/docs"
echo "   • 🖥️  Interface:    http://localhost:8501"
echo "   • 🧠 Ollama:       http://localhost:11434"
echo ""

# 8. Tests de connectivité
print_status "Tests de connectivité finale..."
echo ""

# Test API RAG
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "✅ API RAG (port 8000) - OK"
else
    print_error "❌ API RAG (port 8000) - ERREUR"
fi

# Test Streamlit
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    print_success "✅ Streamlit (port 8501) - OK"
else
    print_error "❌ Streamlit (port 8501) - ERREUR"
fi

# Test Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_success "✅ Ollama (port 11434) - OK"
else
    print_error "❌ Ollama (port 11434) - ERREUR"
fi

echo ""
print_success "🚀 Le système devrait maintenant fonctionner correctement!"
echo ""
echo "💡 Si vous avez encore des problèmes:"
echo "   1. Vérifiez les logs: docker-compose logs -f"
echo "   2. Redémarrez: docker-compose restart"
echo "   3. Nettoyage complet: docker-compose down && docker system prune -f"