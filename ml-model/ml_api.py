#!/usr/bin/env python3
"""
ML Model API Service for Flight Delay Prediction
This service loads the trained ML model and provides predictions via HTTP API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path to import our model
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from train_model import FlightDelayPredictor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global model instance
predictor = None
model_info = {}

def load_model():
    """Load the trained model on startup"""
    global predictor, model_info
    
    try:
        predictor = FlightDelayPredictor()
        
        # Use absolute path to model directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(script_dir, "saved_model")
        
        if os.path.exists(model_dir):
            predictor.load_model(model_dir)
            
            # Load model metadata
            with open(os.path.join(model_dir, 'model_metadata.json'), 'r') as f:
                model_info = json.load(f)
            
            print(f"✅ Model loaded successfully!")
            print(f"   Model type: {model_info.get('model_type')}")
            print(f"   ROC-AUC Score: {model_info.get('roc_auc_score', 'N/A'):.4f}")
            print(f"   Trained on: {model_info.get('trained_on')}")
            return True
        else:
            print(f"❌ Model directory not found: {model_dir}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'message': 'ML Model API is running',
        'model_loaded': predictor is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/model/info', methods=['GET'])
def model_info_endpoint():
    """Get information about the loaded model"""
    if predictor is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'success': True,
        'model_info': model_info,
        'available_airports': {
            'origin_count': len(predictor.airport_stats.get('origin', {})),
            'dest_count': len(predictor.airport_stats.get('dest', {}))
        }
    })

@app.route('/predict', methods=['POST'])
def predict_delay():
    """Predict flight delay probability"""
    if predictor is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['origin', 'destination', 'dayOfWeek']
        for param in required_params:
            if param not in data:
                return jsonify({
                    'error': f'Missing required parameter: {param}',
                    'required_params': required_params
                }), 400
        
        origin = data['origin']
        destination = data['destination']
        day_of_week = data['dayOfWeek']
        departure_time = data.get('departureTime', None)  # Optional
        
        # Validate day of week
        if not isinstance(day_of_week, int) or day_of_week < 1 or day_of_week > 7:
            return jsonify({
                'error': 'dayOfWeek must be an integer between 1 (Monday) and 7 (Sunday)'
            }), 400
        
        # Make prediction
        probability = predictor.predict_delay_probability(
            origin, destination, day_of_week, departure_time
        )
        
        # Determine confidence level based on available data
        origin_known = origin in predictor.airport_stats.get('origin', {})
        dest_known = destination in predictor.airport_stats.get('dest', {})
        
        if origin_known and dest_known:
            confidence = 'High'
            confidence_score = 0.9
        elif origin_known or dest_known:
            confidence = 'Medium'
            confidence_score = 0.7
        else:
            confidence = 'Low'
            confidence_score = 0.5
        
        # Create response
        day_names = {
            1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday',
            5: 'Friday', 6: 'Saturday', 7: 'Sunday'
        }
        
        # Generate message based on probability
        if probability > 0.3:
            message = 'High likelihood of delay - consider alternative flights'
        elif probability > 0.2:
            message = 'Moderate delay risk'
        else:
            message = 'Low delay risk'
        
        return jsonify({
            'success': True,
            'prediction': {
                'origin': origin,
                'destination': destination,
                'dayOfWeek': day_names[day_of_week],
                'delayProbability': round(probability * 100, 2),  # Convert to percentage
                'probabilityDecimal': round(probability, 4),
                'confidence': confidence,
                'confidenceScore': confidence_score,
                'message': message,
                'dataAvailability': {
                    'originKnown': origin_known,
                    'destinationKnown': dest_known
                },
                'modelInfo': {
                    'type': model_info.get('model_type', 'Unknown'),
                    'accuracy': model_info.get('roc_auc_score', 0)
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e)
        }), 500

@app.route('/airports', methods=['GET'])
def get_airports():
    """Get list of airports known to the model"""
    if predictor is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        origin_airports = list(predictor.airport_stats.get('origin', {}).keys())
        dest_airports = list(predictor.airport_stats.get('dest', {}).keys())
        
        # Get unique airports
        all_airports = list(set(origin_airports + dest_airports))
        all_airports.sort()
        
        return jsonify({
            'success': True,
            'airports': {
                'all': all_airports,
                'origin_only': [apt for apt in origin_airports if apt not in dest_airports],
                'destination_only': [apt for apt in dest_airports if apt not in origin_airports],
                'both': [apt for apt in origin_airports if apt in dest_airports]
            },
            'count': {
                'total_unique': len(all_airports),
                'origin_airports': len(origin_airports),
                'dest_airports': len(dest_airports)
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve airports',
            'message': str(e)
        }), 500

@app.route('/batch-predict', methods=['POST'])
def batch_predict():
    """Predict delays for multiple routes"""
    if predictor is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.get_json()
        
        if 'routes' not in data or not isinstance(data['routes'], list):
            return jsonify({
                'error': 'Request must contain a "routes" array'
            }), 400
        
        predictions = []
        
        for i, route in enumerate(data['routes']):
            try:
                origin = route['origin']
                destination = route['destination']
                day_of_week = route['dayOfWeek']
                departure_time = route.get('departureTime', None)
                
                probability = predictor.predict_delay_probability(
                    origin, destination, day_of_week, departure_time
                )
                
                predictions.append({
                    'index': i,
                    'route': route,
                    'delayProbability': round(probability * 100, 2),
                    'success': True
                })
                
            except Exception as e:
                predictions.append({
                    'index': i,
                    'route': route,
                    'error': str(e),
                    'success': False
                })
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'total_routes': len(data['routes']),
            'successful_predictions': sum(1 for p in predictions if p['success'])
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Batch prediction failed',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🤖 Starting ML Model API Service...")
    
    # Load the model
    if load_model():
        print(f"🚀 ML Model API starting on http://localhost:5000")
        print(f"📋 Available endpoints:")
        print(f"   GET  /health              - Health check")
        print(f"   GET  /model/info          - Model information")
        print(f"   POST /predict             - Single delay prediction")
        print(f"   GET  /airports            - List known airports")
        print(f"   POST /batch-predict       - Batch predictions")
        print()
        
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("❌ Failed to load model. Please train the model first by running:")
        print("   python train_model.py")
        sys.exit(1)
