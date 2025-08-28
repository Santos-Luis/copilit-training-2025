#!/usr/bin/env python3
"""
Flight Delay Prediction ML Model
This script builds and trains a machine learning model to predict flight delays
based on various features extracted from historical flight data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import json
import os
from datetime import datetime

class FlightDelayPredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.airport_stats = {}
        self.model_metadata = {}
        
    def load_data(self, csv_path):
        """Load and preprocess the flight data"""
        print(f"Loading data from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} flight records")
        return df
    
    def create_airport_features(self, df):
        """Create aggregate features for airports"""
        print("Creating airport features...")
        
        # Calculate airport statistics
        airport_stats = {}
        
        # For origin airports
        origin_stats = df.groupby('OriginAirportName').agg({
            'ArrDel15': ['count', 'mean', 'std'],
            'DepDelay': ['mean', 'std'],
            'ArrDelay': ['mean', 'std']
        }).round(3)
        
        origin_stats.columns = ['_'.join(col).strip() for col in origin_stats.columns]
        origin_stats = origin_stats.add_prefix('origin_')
        
        # For destination airports
        dest_stats = df.groupby('DestAirportName').agg({
            'ArrDel15': ['count', 'mean', 'std'],
            'DepDelay': ['mean', 'std'],
            'ArrDelay': ['mean', 'std']
        }).round(3)
        
        dest_stats.columns = ['_'.join(col).strip() for col in dest_stats.columns]
        dest_stats = dest_stats.add_prefix('dest_')
        
        # Store for later use during prediction
        self.airport_stats = {
            'origin': origin_stats.to_dict('index'),
            'dest': dest_stats.to_dict('index')
        }
        
        return origin_stats, dest_stats
    
    def feature_engineering(self, df):
        """Create features for the ML model"""
        print("Engineering features...")
        
        # Create a copy to avoid modifying original data
        df_features = df.copy()
        
        # Create airport statistics
        origin_stats, dest_stats = self.create_airport_features(df)
        
        # Add airport statistics to the dataframe
        df_features = df_features.merge(
            origin_stats, 
            left_on='OriginAirportName', 
            right_index=True, 
            how='left'
        )
        
        df_features = df_features.merge(
            dest_stats, 
            left_on='DestAirportName', 
            right_index=True, 
            how='left'
        )
        
        # Create time-based features
        df_features['departure_hour'] = df_features['CRSDepTime'] // 100
        df_features['arrival_hour'] = df_features['CRSArrTime'] // 100
        
        # Create time periods
        df_features['departure_period'] = pd.cut(
            df_features['departure_hour'], 
            bins=[0, 6, 12, 18, 24], 
            labels=['night', 'morning', 'afternoon', 'evening']
        )
        
        # Create distance proxy (simple geographic distance approximation)
        # This is a simplified approach - in practice you'd use actual airport coordinates
        state_codes = {
            'AL': 1, 'AK': 2, 'AZ': 3, 'AR': 4, 'CA': 5, 'CO': 6, 'CT': 7, 'DE': 8, 'FL': 9, 'GA': 10,
            'HI': 11, 'ID': 12, 'IL': 13, 'IN': 14, 'IA': 15, 'KS': 16, 'KY': 17, 'LA': 18, 'ME': 19, 'MD': 20,
            'MA': 21, 'MI': 22, 'MN': 23, 'MS': 24, 'MO': 25, 'MT': 26, 'NE': 27, 'NV': 28, 'NH': 29, 'NJ': 30,
            'NM': 31, 'NY': 32, 'NC': 33, 'ND': 34, 'OH': 35, 'OK': 36, 'OR': 37, 'PA': 38, 'RI': 39, 'SC': 40,
            'SD': 41, 'TN': 42, 'TX': 43, 'UT': 44, 'VT': 45, 'VA': 46, 'WA': 47, 'WV': 48, 'WI': 49, 'WY': 50
        }
        
        df_features['origin_state_code'] = df_features['OriginState'].map(state_codes).fillna(0)
        df_features['dest_state_code'] = df_features['DestState'].map(state_codes).fillna(0)
        df_features['state_distance'] = abs(df_features['origin_state_code'] - df_features['dest_state_code'])
        
        # Create seasonal features
        df_features['season'] = df_features['Month'].map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'fall', 10: 'fall', 11: 'fall'
        })
        
        # Create weekend indicator
        df_features['is_weekend'] = df_features['DayOfWeek'].isin([6, 7]).astype(int)
        
        # Fill NaN values with median/mode
        numeric_columns = df_features.select_dtypes(include=[np.number]).columns
        df_features[numeric_columns] = df_features[numeric_columns].fillna(df_features[numeric_columns].median())
        
        categorical_columns = df_features.select_dtypes(include=['object', 'category']).columns
        for col in categorical_columns:
            df_features[col] = df_features[col].fillna(df_features[col].mode().iloc[0] if not df_features[col].mode().empty else 'Unknown')
        
        return df_features
    
    def prepare_features(self, df):
        """Prepare features for training"""
        print("Preparing features for training...")
        
        # Select features for the model
        feature_columns = [
            'DayOfWeek', 'departure_hour', 'arrival_hour', 'state_distance',
            'is_weekend', 'CRSDepTime', 'CRSArrTime',
            # Airport statistics
            'origin_ArrDel15_count', 'origin_ArrDel15_mean', 'origin_ArrDel15_std',
            'origin_DepDelay_mean', 'origin_DepDelay_std',
            'dest_ArrDel15_count', 'dest_ArrDel15_mean', 'dest_ArrDel15_std',
            'dest_DepDelay_mean', 'dest_DepDelay_std'
        ]
        
        # Categorical features to encode
        categorical_features = ['Carrier', 'departure_period', 'season']
        
        # Encode categorical variables
        df_encoded = df.copy()
        for feature in categorical_features:
            if feature in df.columns:
                if feature not in self.label_encoders:
                    self.label_encoders[feature] = LabelEncoder()
                    df_encoded[feature + '_encoded'] = self.label_encoders[feature].fit_transform(df[feature].astype(str))
                else:
                    # Handle unseen categories during prediction
                    known_categories = set(self.label_encoders[feature].classes_)
                    df_encoded[feature + '_encoded'] = df[feature].astype(str).apply(
                        lambda x: self.label_encoders[feature].transform([x])[0] if x in known_categories else -1
                    )
                feature_columns.append(feature + '_encoded')
        
        # Select final features
        available_features = [col for col in feature_columns if col in df_encoded.columns]
        X = df_encoded[available_features].copy()
        
        # Handle any remaining NaN values
        X = X.fillna(X.median())
        
        self.feature_columns = available_features
        return X
    
    def train_model(self, csv_path):
        """Train the machine learning model"""
        print("Starting model training...")
        
        # Load and prepare data
        df = self.load_data(csv_path)
        df_features = self.feature_engineering(df)
        X = self.prepare_features(df_features)
        y = df_features['ArrDel15']  # Target: 1 if delayed >15 min, 0 otherwise
        
        print(f"Training with {len(X)} samples and {len(X.columns)} features")
        print(f"Target distribution: {y.value_counts().to_dict()}")
        print(f"Delay rate: {y.mean():.3f}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Try different models
        models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100, 
                max_depth=15, 
                min_samples_split=10,
                random_state=42,
                n_jobs=-1
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        best_model = None
        best_score = 0
        best_model_name = ""
        
        for name, model in models.items():
            print(f"\nTraining {name}...")
            
            # Use scaled data for all models
            if name == 'RandomForest':
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                score = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
            else:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                score = roc_auc_score(y_test, model.predict_proba(X_test_scaled)[:, 1])
            
            print(f"{name} ROC-AUC Score: {score:.4f}")
            print(f"Classification Report for {name}:")
            print(classification_report(y_test, y_pred))
            
            if score > best_score:
                best_score = score
                best_model = model
                best_model_name = name
        
        self.model = best_model
        print(f"\nBest model: {best_model_name} with ROC-AUC: {best_score:.4f}")
        
        # Feature importance (for RandomForest)
        if best_model_name == 'RandomForest':
            feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': best_model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 10 Most Important Features:")
            print(feature_importance.head(10))
        
        # Store model metadata
        self.model_metadata = {
            'model_type': best_model_name,
            'roc_auc_score': best_score,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': len(self.feature_columns),
            'delay_rate': float(y.mean()),
            'trained_on': datetime.now().isoformat(),
            'features': self.feature_columns
        }
        
        return self.model
    
    def predict_delay_probability(self, origin_airport, dest_airport, day_of_week, departure_time=None):
        """Predict delay probability for a specific route and day"""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        # Create a sample with the input parameters
        sample_data = {
            'DayOfWeek': day_of_week,
            'departure_hour': 12 if departure_time is None else departure_time // 100,
            'arrival_hour': 15 if departure_time is None else (departure_time // 100) + 3,
            'CRSDepTime': 1200 if departure_time is None else departure_time,
            'CRSArrTime': 1500 if departure_time is None else departure_time + 300,
            'is_weekend': 1 if day_of_week in [6, 7] else 0,
            'state_distance': 2,  # Default moderate distance
        }
        
        # Add airport statistics if available
        if origin_airport in self.airport_stats['origin']:
            for key, value in self.airport_stats['origin'][origin_airport].items():
                sample_data[key] = value
        else:
            # Use average values for unknown airports
            avg_origin_stats = {
                'origin_ArrDel15_count': 500,
                'origin_ArrDel15_mean': 0.22,
                'origin_ArrDel15_std': 0.41,
                'origin_DepDelay_mean': 8.5,
                'origin_DepDelay_std': 25.0
            }
            sample_data.update(avg_origin_stats)
        
        if dest_airport in self.airport_stats['dest']:
            for key, value in self.airport_stats['dest'][dest_airport].items():
                sample_data[key] = value
        else:
            # Use average values for unknown airports
            avg_dest_stats = {
                'dest_ArrDel15_count': 500,
                'dest_ArrDel15_mean': 0.22,
                'dest_ArrDel15_std': 0.41,
                'dest_DepDelay_mean': 8.5,
                'dest_DepDelay_std': 25.0
            }
            sample_data.update(avg_dest_stats)
        
        # Add categorical encodings (use defaults for unknown values)
        sample_data.update({
            'Carrier_encoded': 0,  # Default carrier
            'departure_period_encoded': 1,  # Morning
            'season_encoded': 1  # Default season
        })
        
        # Create DataFrame and ensure all features are present
        sample_df = pd.DataFrame([sample_data])
        
        # Ensure all feature columns are present
        for col in self.feature_columns:
            if col not in sample_df.columns:
                sample_df[col] = 0  # Default value for missing features
        
        # Select only the features used in training
        X_sample = sample_df[self.feature_columns].fillna(0)
        
        # Scale the features
        X_sample_scaled = self.scaler.transform(X_sample)
        
        # Make prediction
        if hasattr(self.model, 'predict_proba'):
            if self.model_metadata.get('model_type') == 'RandomForest':
                probability = self.model.predict_proba(X_sample)[:, 1][0]
            else:
                probability = self.model.predict_proba(X_sample_scaled)[:, 1][0]
        else:
            # Fallback for models without predict_proba
            if self.model_metadata.get('model_type') == 'RandomForest':
                probability = self.model.predict(X_sample)[0]
            else:
                probability = self.model.predict(X_sample_scaled)[0]
        
        return float(probability)
    
    def save_model(self, model_dir):
        """Save the trained model and all necessary components"""
        os.makedirs(model_dir, exist_ok=True)
        
        # Save the model
        joblib.dump(self.model, os.path.join(model_dir, 'flight_delay_model.pkl'))
        
        # Save the scaler
        joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.pkl'))
        
        # Save label encoders
        joblib.dump(self.label_encoders, os.path.join(model_dir, 'label_encoders.pkl'))
        
        # Save airport statistics
        with open(os.path.join(model_dir, 'airport_stats.json'), 'w') as f:
            json.dump(self.airport_stats, f, indent=2)
        
        # Save feature columns
        with open(os.path.join(model_dir, 'feature_columns.json'), 'w') as f:
            json.dump(self.feature_columns, f, indent=2)
        
        # Save model metadata
        with open(os.path.join(model_dir, 'model_metadata.json'), 'w') as f:
            json.dump(self.model_metadata, f, indent=2)
        
        print(f"Model saved to {model_dir}")
    
    def load_model(self, model_dir):
        """Load a trained model and all necessary components"""
        # Load the model
        self.model = joblib.load(os.path.join(model_dir, 'flight_delay_model.pkl'))
        
        # Load the scaler
        self.scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        
        # Load label encoders
        self.label_encoders = joblib.load(os.path.join(model_dir, 'label_encoders.pkl'))
        
        # Load airport statistics
        with open(os.path.join(model_dir, 'airport_stats.json'), 'r') as f:
            self.airport_stats = json.load(f)
        
        # Load feature columns
        with open(os.path.join(model_dir, 'feature_columns.json'), 'r') as f:
            self.feature_columns = json.load(f)
        
        # Load model metadata
        with open(os.path.join(model_dir, 'model_metadata.json'), 'r') as f:
            self.model_metadata = json.load(f)
        
        print(f"Model loaded from {model_dir}")
        print(f"Model type: {self.model_metadata.get('model_type')}")
        print(f"ROC-AUC Score: {self.model_metadata.get('roc_auc_score', 'N/A')}")

def main():
    """Main function to train and save the model"""
    predictor = FlightDelayPredictor()
    
    # Train the model
    csv_path = "../clean-flights.csv"
    predictor.train_model(csv_path)
    
    # Save the model
    model_dir = "./saved_model"
    predictor.save_model(model_dir)
    
    # Test prediction for the example case
    print("\n" + "="*50)
    print("TESTING THE MODEL")
    print("="*50)
    
    # Test case: Tampa International to John Wayne Airport-Orange County on Wednesday
    origin = "Tampa International"
    destination = "John Wayne Airport-Orange County"
    day_of_week = 3  # Wednesday
    
    try:
        probability = predictor.predict_delay_probability(origin, destination, day_of_week)
        print(f"\nPrediction for {origin} → {destination} on Wednesday:")
        print(f"Delay probability (>15 min): {probability:.3f} ({probability*100:.1f}%)")
        
        # Test a few more cases
        test_cases = [
            ("John F. Kennedy International", "Los Angeles International", 1),  # Monday
            ("Chicago O'Hare International", "Miami International", 5),  # Friday
            ("Seattle/Tacoma International", "Boston Logan International", 7),  # Sunday
        ]
        
        print("\nAdditional test cases:")
        for orig, dest, dow in test_cases:
            prob = predictor.predict_delay_probability(orig, dest, dow)
            day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 
                        5: "Friday", 6: "Saturday", 7: "Sunday"}
            print(f"{orig} → {dest} on {day_names[dow]}: {prob:.3f} ({prob*100:.1f}%)")
            
    except Exception as e:
        print(f"Error during prediction: {e}")

if __name__ == "__main__":
    main()
