#!/bin/bash

echo "🚀 Starting Complete Flight Delay Prediction System..."
echo ""

# Start ML API in background
echo "1️⃣ Starting ML Model API..."
./start-ml-api.sh &
ML_PID=$!

# Wait for ML API to start
echo "⏳ Waiting for ML API to start..."
sleep 8

# Start Backend API 
echo "2️⃣ Starting Backend API..."
./start-backend.sh &
BACKEND_PID=$!

# Wait for Backend to start
echo "⏳ Waiting for Backend API to start..."
sleep 5

# Start Frontend
echo "3️⃣ Starting Frontend..."
./start-frontend.sh &
FRONTEND_PID=$!

echo ""
echo "🎉 All services started!"
echo ""
echo "📊 Available Services:"
echo "   🤖 ML Model API:     http://localhost:5000"
echo "   🔧 Backend API:      http://localhost:3000"  
echo "   ⚛️  Frontend App:     http://localhost:3001"
echo ""
echo "🧪 Test the ML enhancement:"
echo "   curl \"http://localhost:3000/api/delay-prediction?origin=Tampa%20International&destination=John%20Wayne%20Airport-Orange%20County&dayOfWeek=3\""
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping all services...'; kill $ML_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
