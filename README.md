# Flight Delay Prediction Application 🛫

A complete full-stack application that predicts flight delays using historical data and **machine learning models**. The application can predict delays even for routes with no historical data by learning patterns from the entire dataset.

## 🎯 Key Features

- 📊 **Data Processing**: Automated cleaning of 271,940+ flight records
- 🤖 **Machine Learning**: Gradient Boosting model with 70.9% ROC-AUC accuracy
- 🔧 **Backend API**: Express.js with SQLite database and ML integration
- ⚛️ **Frontend**: React application with search and prediction interface
- 🔮 **Smart Predictions**: Works even for routes with no historical data
- 📈 **Fallback System**: Automatic fallback to database queries if ML unavailable

## � Quick Start

### Option 1: Start All Services
```bash
./start-all-services.sh
```
This starts the ML API (port 5000), Backend API (port 3000), and Frontend (port 3001).

### Option 2: Start Individual Services
```bash
# Start ML Model API
./start-ml-api.sh

# Start Backend API (in another terminal)
./start-backend.sh

# Start Frontend (in another terminal)  
./start-frontend.sh
```

## 🧠 Machine Learning Model

The ML model can predict flight delays using features such as:
- Airport characteristics and traffic patterns
- Day of the week patterns
- Seasonal trends  
- Geographic factors
- Historical delay rates

**Example**: Tampa International → John Wayne Airport-Orange County on Wednesday
- **Database**: No historical data available
- **ML Model**: Predicts 11.6% delay probability with High confidence

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  ML Model API  │
│   React App     │───▶│   Express.js    │───▶│   Flask + ML    │
│   Port: 3001    │    │   Port: 3000    │    │   Port: 5000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │   271K+ flights │
                       └─────────────────┘
```

## 📋 API Endpoints

### Backend API (Port 3000)
- `GET /health` - System health and ML model status
- `GET /api/airports/search?q=<query>` - Search airports
- `GET /api/delay-prediction` - **ML-Enhanced** delay prediction
- `GET /api/route-stats` - Weekly route statistics

### ML Model API (Port 5000)  
- `GET /health` - ML model health check
- `POST /predict` - Direct ML predictions
- `GET /model/info` - Model metadata and performance
- `GET /airports` - Airports known to the model

## 🧪 Testing the ML Enhancement

### Test Case: Route with No Historical Data
```bash
curl "http://localhost:3000/api/delay-prediction?origin=Tampa%20International&destination=John%20Wayne%20Airport-Orange%20County&dayOfWeek=3"
```

**Response with ML Model:**
```json
{
  "success": true,
  "data": {
    "origin": "Tampa International",
    "destination": "John Wayne Airport-Orange County", 
    "dayOfWeek": "Wednesday",
    "delayProbability": 11.63,
    "confidence": "High",
    "source": "ML Model",
    "message": "Low delay risk"
  }
}
```

### Test Case: Route with Historical Data  
```bash
curl "http://localhost:3000/api/delay-prediction?origin=John%20F.%20Kennedy%20International&destination=Los%20Angeles%20International&dayOfWeek=1"
```

The system intelligently chooses between ML predictions and historical data for optimal accuracy.

## 📁 Project Structure

```
├── ml-model/                    # 🤖 Machine Learning Model
│   ├── train_model.py          # Model training script
│   ├── ml_api.py              # Flask API for ML predictions  
│   └── saved_model/           # Trained model files
├── backend/                   # 🔧 Backend API
│   ├── server.js             # Express server with ML integration
│   ├── database.js           # Database management
│   └── README.md             # Backend documentation
├── frontend/                 # ⚛️ React Frontend  
│   ├── src/
│   └── package.json
├── clean-flights.csv         # 📊 Processed flight data
├── start-all-services.sh     # 🚀 Complete system startup
└── README.md                 # This file
```

## 📊 Model Performance

- **Algorithm**: Gradient Boosting Classifier
- **ROC-AUC Score**: 70.91%
- **Training Data**: 271,940 flight records
- **Features**: 20+ engineered features
- **Airports**: 70 unique airports supported
