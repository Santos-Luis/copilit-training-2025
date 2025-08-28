#!/bin/bash

echo "🤖 Starting ML Model API..."
echo "📍 ML API will be available at: http://localhost:5000"
echo "⏳ Please wait while the model loads..."
echo ""

cd ml-model
../.venv/bin/python ml_api.py
