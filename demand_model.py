"""
ML Demand Prediction Model
Trains a Linear Regression model to predict expected water flow based on operational conditions.
This is the 'Digital Twin' brain that learns normal behavior.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os


def train_demand_model(data_path='data/location_aware_gis_leakage_dataset.csv', save_model=True):
    """
    Train a Linear Regression model to predict expected flow rate.
    
    Args:
        data_path: Path to the dataset CSV
        save_model: Whether to save the trained model to disk
    
    Returns:
        model: Trained LinearRegression model
        metrics: Dictionary of model performance metrics
    """
    # Load dataset
    print("[*] Loading dataset...")
    df = pd.read_csv(data_path)
    
    # Use only NORMAL data for training (no leaks)
    # This teaches the model what "normal" looks like
    normal_data = df[df['Leakage_Flag'] == 0].copy()
    print(f"[OK] Filtered to {len(normal_data)} normal records for training")
    
    # Feature engineering: Select predictors
    # We predict Flow_Rate based on operational conditions
    features = ['Pressure', 'Temperature', 'RPM', 'Operational_Hours', 'Vibration']
    target = 'Flow_Rate'
    
    X = normal_data[features]
    y = normal_data[target]
    
    # Split into train/test (70/30)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    
    # Train Linear Regression model
    print("[*] Training Linear Regression model...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    mae = mean_absolute_error(y_test, y_pred_test)
    
    metrics = {
        'train_r2': train_r2,
        'test_r2': test_r2,
        'mae': mae,
        'features': features
    }
    
    print(f"[OK] Model Training Complete!")
    print(f"   - Training R2 Score: {train_r2:.4f}")
    print(f"   - Test R2 Score: {test_r2:.4f}")
    print(f"   - Mean Absolute Error: {mae:.2f} L/min")
    
    # Save model
    if save_model:
        model_path = 'trained_model.pkl'
        joblib.dump({
            'model': model,
            'features': features
        }, model_path)
        print(f"[SAVED] Model saved to '{model_path}'")
    
    return model, metrics


def load_model(model_path='trained_model.pkl'):
    """Load a pre-trained model from disk"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Please train the model first.")
    
    model_data = joblib.load(model_path)
    return model_data['model'], model_data['features']


def predict_expected_flow(model, features, data_row):
    """
    Predict expected flow for a single data point.
    
    Args:
        model: Trained model
        features: List of feature names
        data_row: Dictionary or Series with feature values
    
    Returns:
        expected_flow: Predicted flow rate
    """
    # Extract features in correct order
    feature_values = [data_row[f] for f in features]
    feature_array = np.array(feature_values).reshape(1, -1)
    
    expected_flow = model.predict(feature_array)[0]
    return expected_flow


if __name__ == "__main__":
    # Train and save the model
    print("=" * 60)
    print("SMART WATER LEAK DETECTION - ML DEMAND MODEL")
    print("=" * 60)
    
    model, metrics = train_demand_model()
    
    print("\n" + "=" * 60)
    print("Training Complete! Model ready for leak detection.")
    print("=" * 60)
