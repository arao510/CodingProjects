#!/bin/bash
# Start the Ask My Docs UI
# Usage: ./start.sh

echo "🔍 Ask My Docs — Starting..."
echo ""

# Check indexes exist
if [ ! -f ".bm25_index.pkl" ]; then
  echo "⚠  Indexes not found. Running ingestion first..."
  python3 ingest.py
fi

echo ""
echo "✅ Starting server at http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

uvicorn app:app --host 0.0.0.0 --port 8000 --reload
