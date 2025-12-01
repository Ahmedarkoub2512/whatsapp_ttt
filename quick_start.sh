#!/bin/bash

# Quick Start Script for Advanced RAG System
# ==========================================

echo "=============================================="
echo "🚀 Advanced RAG System - Quick Start"
echo "=============================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo ""
echo "📥 Installing/Updating requirements..."
pip install -r requirements.txt --quiet

# Check ChromaDB
echo ""
echo "🔍 Checking ChromaDB status..."
if docker ps | grep -q chroma; then
    echo "✅ ChromaDB is running"
else
    echo "❌ ChromaDB is NOT running!"
    echo "Please start ChromaDB first:"
    echo "  docker run -d -p 8000:8000 chromadb/chroma"
    exit 1
fi

# Menu
echo ""
echo "=============================================="
echo "What would you like to do?"
echo "=============================================="
echo "1) Run Advanced Ingestion (re-index data)"
echo "2) Test Advanced RAG System"
echo "3) Run WhatsApp Bot"
echo "4) Verify Current Collection"
echo "5) Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔄 Running Advanced Ingestion..."
        echo "=============================================="
        python src/advanced_ingest.py
        ;;
    2)
        echo ""
        echo "🧪 Testing Advanced RAG System..."
        echo "=============================================="
        python test_advanced_rag.py
        ;;
    3)
        echo ""
        echo "💬 Starting WhatsApp Bot..."
        echo "=============================================="
        python src/app.py
        ;;
    4)
        echo ""
        echo "📊 Verifying Collection..."
        echo "=============================================="
        python verify_ingestion_final.py
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice!"
        exit 1
        ;;
esac

echo ""
echo "=============================================="
echo "✅ Done!"
echo "=============================================="
