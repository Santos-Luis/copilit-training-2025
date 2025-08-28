# Flight Delay Prediction ML Model 🤖

A machine learning model that predicts flight delays using historical data and advanced feature engineering. The model can make predictions even for routes with no historical data by learning patterns from the entire dataset.

## 🎯 Model Overview

- **Algorithm**: Gradient Boosting Classifier
- **Performance**: 70.91% ROC-AUC Score
- **Training Data**: 271,940 flight records from 2013
- **Features**: 20+ engineered features
- **Airports**: 70 unique airports

## 🔧 Features Used

### Core Features
- Day of week (1-7)
- Departure/arrival hours
- Airport traffic statistics
- Historical delay rates
- Geographic distance proxy

### Engineered Features
- **Airport Statistics**: 
  - Flight volume per airport
  - Historical delay rates
  - Average delay times
- **Time-based Features**:
  - Time of day periods (morning, afternoon, evening, night)
  - Weekend vs weekday
  - Seasonal patterns
- **Geographic Features**:
  - State-to-state distance approximation
  - Regional patterns

## 📊 Model Performance

```
Classification Report:
              precision    recall  f1-score   support
           0       0.79      0.98      0.88     42644
           1       0.55      0.07      0.12     11744
    accuracy                           0.79     54388

ROC-AUC Score: 0.7091
```

## 🚀 Usage

### Training the Model
```bash
cd ml-model
python train_model.py
```

### Starting the ML API
```bash
cd ml-model
python ml_api.py
```

### Making Predictions
```bash
# Direct ML API call
curl -X POST "http://localhost:5000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Tampa International",
    "destination": "John Wayne Airport-Orange County", 
    "dayOfWeek": 3
  }'

# Via integrated backend API
curl "http://localhost:3000/api/delay-prediction?origin=Tampa%20International&destination=John%20Wayne%20Airport-Orange%20County&dayOfWeek=3"
```

## 🎯 Key Advantages

### 1. **Handles Missing Data**
Unlike simple database lookups, the ML model can predict delays for routes with no historical data by learning patterns from similar routes and airports.

**Example**: Tampa → John Wayne (Orange County) on Wednesday
- **Database Query**: No data available
- **ML Model**: 11.6% delay probability (High confidence)

### 2. **Feature-Rich Predictions**
The model considers multiple factors:
- Airport characteristics and traffic patterns
- Day of week and seasonal effects
- Geographic relationships
- Time-of-day patterns

### 3. **Confidence Scoring**
Provides confidence levels based on data availability:
- **High**: Both airports known to model
- **Medium**: One airport known
- **Low**: Both airports unknown (uses averages)

## 🔬 Technical Details

### Model Training Process
1. **Data Loading**: Load cleaned flight data (271K+ records)
2. **Feature Engineering**: Create 20+ features from raw data
3. **Preprocessing**: Handle missing values, encode categoricals
4. **Model Selection**: Compare RandomForest vs GradientBoosting
5. **Evaluation**: Cross-validation and test set evaluation
6. **Persistence**: Save model, encoders, and metadata

### Prediction Process
1. **Input Validation**: Validate origin, destination, day of week
2. **Feature Creation**: Generate same features used in training
3. **Airport Lookup**: Use known airport stats or defaults
4. **Prediction**: Generate probability using trained model
5. **Confidence Assessment**: Determine confidence based on data availability

## 📁 Model Files

```
ml-model/saved_model/
├── flight_delay_model.pkl    # Trained GradientBoosting model
├── scaler.pkl               # Feature scaler
├── label_encoders.pkl       # Categorical encoders
├── airport_stats.json       # Airport statistics
├── feature_columns.json     # Feature list
└── model_metadata.json      # Model info and performance
```

## 🔄 Integration with Backend

The backend automatically detects ML API availability:

1. **ML Available**: Uses ML predictions for all requests
2. **ML Unavailable**: Falls back to database queries
3. **Hybrid Mode**: Uses ML for unknown routes, database for known routes

## 🧪 Example Predictions

### Known Route (High Historical Data)
```json
{
  "route": "JFK → LAX, Monday",
  "database": "26.5% (117 flights)",
  "ml_model": "23.0% (High confidence)",
  "note": "Both methods available, ML provides generalization"
}
```

### Unknown Route (No Historical Data) 
```json
{
  "route": "Tampa → John Wayne, Wednesday", 
  "database": "No data available",
  "ml_model": "11.6% (High confidence)",
  "note": "ML model enables prediction where database fails"
}
```

## 🎯 Future Improvements

- **Weather Data**: Integrate weather conditions
- **Real-time Updates**: Continuous model retraining
- **Airport Coordinates**: Use actual lat/lon for distance
- **Carrier-specific Models**: Train separate models per airline
- **Ensemble Methods**: Combine multiple algorithms

## 📈 Performance Monitoring

The ML API provides performance metrics:
- Model accuracy and confidence scores
- Prediction response times
- Airport coverage statistics
- Feature importance rankings

Access via: `GET http://localhost:5000/model/info`
