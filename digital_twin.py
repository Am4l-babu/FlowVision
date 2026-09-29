"""
Enhanced Digital Twin Orchestration
Combines ML predictions, physics-based rules, and network state management.

This is the core of the Digital Twin system - it integrates ALL components:
- ML demand prediction
- Physics-informed validation
- Network topology
- Real-time leak detection
- Calibration and learning
"""

import pandas as pd
import numpy as np
from demand_model import load_model, predict_expected_flow
from leak_algorithm import LeakDetector
from physics_rules import PhysicsEngine
import joblib
import os


class EnhancedDigitalTwin:
    """
    Complete Digital Twin system for water network management.
    
    Key Components:
    1. ML Model - Predicts normal consumption
    2. Physics Engine - Validates physical feasibility
    3. Network State - Tracks system condition
    4. Calibration - Learns from deviations
    5. Leak Detection - Multi-signal anomaly detection
   """
    
    def __init__(self, model_path='trained_model.pkl', dataset_path='data/location_aware_gis_leakage_dataset.csv'):
        """Initialize the Enhanced Digital Twin"""
        print("[*] Initializing Enhanced Digital Twin System...")
        
        # Load ML model
        self.model, self.features = load_model(model_path)
        print(f"   [OK] ML Model loaded (features: {', '.join(self.features)})")
        
        # Initialize physics engine
        self.physics_engine = PhysicsEngine()
        print(f"   [OK] Physics Engine initialized")
        
        # Initialize leak detector
        self.leak_detector = LeakDetector(residual_threshold=15.0)
        print(f"   [OK] Leak Detector initialized")
        
        # Load dataset
        self.dataset = pd.read_csv(dataset_path)
        print(f"   [OK] Dataset loaded: {len(self.dataset)} records")
        
        # Build network topology
        self._build_network_state()
        print(f"   [OK] Network topology built: {len(self.network_state)} pipes")
        
        # Initialize calibration
        self.calibration_history = {}
        self.calibration_window = 50  # Number of timesteps to track
        print(f"   [OK] Calibration system ready")
        
        # Prediction cache
        self.prediction_cache = {}
        
        print("[OK] Digital Twin fully operational!\n")
    
    def _build_network_state(self):
        """Build network state from dataset"""
        self.network_state = {}
        
        # Get unique pipes
        unique_pipes = self.dataset['Location_Code'].unique()
        
        for pipe_id in unique_pipes:
            pipe_data = self.dataset[self.dataset['Location_Code'] == pipe_id].iloc[0]
            
            self.network_state[pipe_id] = {
                'zone': pipe_data['Zone'],
                'block': pipe_data['Block'],
                'pipe': pipe_data['Pipe'],
                'location': {
                    'lat': pipe_data['Latitude'],
                    'lon': pipe_data['Longitude']
                },
                'baseline_pressure': None,  # Will be calibrated
                'baseline_flow': None,  # Will be calibrated
                'roughness': 0.01,  # Default pipe roughness
                'health_status': 'HEALTHY',
                'degradation_factor': 1.0
            }
    
    def _calibrate_pipe(self, pipe_id, residual, is_leak):
        """
        Calibrate pipe parameters based on historical deviations.
        
        Principle: If consistent offset (not a leak) → adjust baseline
                   If intermittent spike → flag as leak
        
        This is NOT retraining the ML model.
        This is adjusting expected physical parameters.
        """
        if pipe_id not in self.calibration_history:
            self.calibration_history[pipe_id] = []
        
        # Add current residual to history
        self.calibration_history[pipe_id].append({
            'residual': residual,
            'is_leak': is_leak
        })
        
        # Keep only recent history
        if len(self.calibration_history[pipe_id]) > self.calibration_window:
            self.calibration_history[pipe_id].pop(0)
        
        # Analyze calibration
        history = self.calibration_history[pipe_id]
        if len(history) >= 20:  # Need enough data
            residuals = [h['residual'] for h in history]
            leak_flags = [h['is_leak'] for h in history]
            
            mean_residual = np.mean(residuals)
            std_residual = np.std(residuals)
            leak_rate = sum(leak_flags) / len(leak_flags)
            
            # If consistent offset (low variance, no leaks) → calibrate
            if std_residual < 5 and leak_rate < 0.1 and abs(mean_residual) > 3:
                # Adjust baseline flow expectation
                if self.network_state[pipe_id]['baseline_flow'] is None:
                    self.network_state[pipe_id]['baseline_flow'] = mean_residual
                else:
                    # Smooth adjustment
                    self.network_state[pipe_id]['baseline_flow'] += mean_residual * 0.1
                
                return True  # Calibration applied
        
        return False  # No calibration needed
    
    def get_comprehensive_analysis(self, index):
        """
        Get complete Digital Twin analysis for a specific timestep.
        
        This is the CORE function that combines:
        - ML prediction
        - Physics validation
        - Network state
        - Leak detection
        - Calibration
        
        Returns complete reasoning for UI display.
        """
        # Boundary check
        if index >= len(self.dataset):
            index = len(self.dataset) - 1
        
        row = self.dataset.iloc[index]
        pipe_id = row['Location_Code']
        
        # === STEP 1: ML PREDICTION (Normal Consumption) ===
        if index in self.prediction_cache:
            ml_expected_flow = self.prediction_cache[index]
        else:
            ml_expected_flow = predict_expected_flow(self.model, self.features, row)
            self.prediction_cache[index] = ml_expected_flow
        
        # === STEP 2: APPLY CALIBRATION ===
        calibrated_expected = ml_expected_flow
        if pipe_id in self.network_state and self.network_state[pipe_id]['baseline_flow'] is not None:
            calibrated_expected += self.network_state[pipe_id]['baseline_flow']
        
        # === STEP 3: GET OBSERVATIONS ===
        observed_flow = row['Flow_Rate']
        observed_pressure = row['Pressure']
        
        # === STEP 4: PHYSICS VALIDATION ===
        pipe_physics_data = {
            'flow_rate': observed_flow,
            'pressure': observed_pressure,
            'pipe_length': 1000,  # Default estimate
            'base_pressure': 100  # Assume 100 PSI at source
        }
        
        physics_analysis = self.physics_engine.analyze_pipe_segment(
            pipe_physics_data,
            calibrated_expected
        )
        
        # === STEP 5: ML-BASED LEAK DETECTION ===
        ml_detection = self.leak_detector.detect_leak(
            pipe_id=pipe_id,
            expected_flow=calibrated_expected,
            observed_flow=observed_flow,
            pressure=observed_pressure
        )
        
        # === STEP 6: COMBINE SIGNALS (Multi-Signal Fusion) ===
        ml_status = ml_detection['status']
        physics_status = physics_analysis['physics_status']
        
        ml_confidence = ml_detection['confidence']
        physics_confidence = physics_analysis['physics_confidence']
        
        # Decision fusion
        if ml_status == 'LEAK' and physics_status == 'LEAK':
            final_status = 'LEAK'
            final_confidence = min((ml_confidence + physics_confidence) / 2 * 1.3, 100)  # Boost when both agree
            reasoning_signals = ['ML model detected anomaly', 'Physics rules violated', 'High confidence: Both signals agree']
        elif ml_status == 'LEAK' or physics_status == 'LEAK':
            final_status = 'SUSPECT'
            final_confidence = max(ml_confidence, physics_confidence) * 0.7
            reasoning_signals = ['Single signal detection', 'Requires confirmation']
        else:
            final_status = 'NORMAL'
            final_confidence = min(ml_confidence, physics_confidence)
            reasoning_signals = ['All signals normal']
        
        # === STEP 7: CALIBRATION ===
        residual = observed_flow - calibrated_expected
        calibrated = self._calibrate_pipe(pipe_id, residual, final_status == 'LEAK')
        
        # === STEP 8: BUILD COMPREHENSIVE RESPONSE ===
        analysis = {
            # Identifiers
            'index': index,
            'pipe_id': pipe_id,
            'zone': row['Zone'],
            'block': row['Block'],
            'pipe': row['Pipe'],
            'location': {
                'lat': row['Latitude'],
                'lon': row['Longitude']
            },
            
            # ML Layer
            'ml_expected_flow': round(ml_expected_flow, 2),
            'calibrated_expected_flow': round(calibrated_expected, 2),
            'calibration_offset': round(calibrated_expected - ml_expected_flow, 2) if calibrated_expected != ml_expected_flow else 0,
            
            # Observations
            'observed_flow': round(observed_flow, 2),
            'observed_pressure': round(observed_pressure, 2),
            'temperature': round(row['Temperature'], 2),
            'rpm': round(row['RPM'], 2),
            'vibration': round(row['Vibration'], 2),
            
            # Physics Layer
            'physics_expected_pressure': round(physics_analysis['expected_pressure'], 2),
            'physics_pressure_deviation': round(physics_analysis['pressure_check']['deviation'], 2),
            'physics_signals': physics_analysis['physics_signals'],
            'physics_status': physics_status,
            'physics_confidence': round(physics_confidence, 2),
            
            # ML Detection Layer
            'ml_residual': round(ml_detection['residual'], 2),
            'ml_residual_percentage': round(ml_detection['residual_percentage'], 2),
            'ml_status': ml_status,
            'ml_confidence': round(ml_confidence, 2),
            'ml_reasoning': ml_detection['reasoning'],
            
            # Final Decision
            'status': final_status,
            'confidence': round(final_confidence, 2),
            'reasoning_signals': reasoning_signals,
            'calibrated': calibrated,
            
            # Ground Truth
            'ground_truth': 'LEAK' if row['Leakage_Flag'] == 1 else 'NORMAL',
            'is_correct': (final_status in ['LEAK', 'SUSPECT'] and row['Leakage_Flag'] == 1) or 
                         (final_status == 'NORMAL' and row['Leakage_Flag'] == 0)
        }
        
        return analysis
    
    def get_network_snapshot(self, index):
        """
        Get status of all tracked pipes at a given timestep.
        For performance, we focus on pipes appearing in recent data.
        """
        # Get data around this index (window of ±10 records)
        window_start = max(0, index - 10)
        window_end = min(len(self.dataset), index + 10)
        window_data = self.dataset.iloc[window_start:window_end]
        
        snapshot = {}
        
        # Get unique pipes in this window
        active_pipes = window_data['Location_Code'].unique()
        
        for pipe_id in active_pipes:
            pipe_records = window_data[window_data['Location_Code'] == pipe_id]
            if len(pipe_records) > 0:
                # Use most recent record for this pipe
                latest = pipe_records.iloc[-1]
                latest_index = latest.name
                
                # Get analysis for this pipe
                if latest_index == index:
                    # Use current analysis
                    analysis = self.get_comprehensive_analysis(index)
                else:
                    # Quick status check
                    analysis = self.get_comprehensive_analysis(latest_index)
                
                snapshot[pipe_id] = {
                    'status': analysis['status'],
                    'confidence': analysis['confidence'],
                    'flow': analysis['observed_flow'],
                    'zone': analysis['zone'],
                    'block': analysis['block'],
                   'location': analysis['location']
                }
        
        return snapshot
    
    def get_system_statistics(self, start_index=0, end_index=None):
        """Calculate overall system statistics"""
        if end_index is None or end_index > len(self.dataset):
            end_index = len(self.dataset)
        
        total_records = end_index - start_index
        leaks_detected = 0
        suspects_detected = 0
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        # Sample for performance (every 10th record)
        step = max(1, (end_index - start_index) // 500)
        
        for i in range(start_index, end_index, step):
            analysis = self.get_comprehensive_analysis(i)
            
            if analysis['status'] == 'LEAK':
                leaks_detected += 1
                if analysis['ground_truth'] == 'LEAK':
                    true_positives += 1
                else:
                    false_positives += 1
            elif analysis['status'] == 'SUSPECT':
                suspects_detected += 1
                if analysis['ground_truth'] == 'LEAK':
                    true_positives += 1
                else:
                    false_positives += 1
            else:
                if analysis['ground_truth'] == 'NORMAL':
                    true_negatives += 1
                else:
                    false_negatives += 1
        
        total_checked = true_positives + false_positives + true_negatives + false_negatives
        accuracy = ((true_positives + true_negatives) / total_checked * 100) if total_checked > 0 else 0
        precision = (true_positives / (true_positives + false_positives) * 100) if (true_positives + false_positives) > 0 else 0
        recall = (true_positives / (true_positives + false_negatives) * 100) if (true_positives + false_negatives) > 0 else 0
        
        return {
            'total_records': total_records,
            'total_checked': total_checked,
            'leaks_detected': leaks_detected,
            'suspects_detected': suspects_detected,
            'accuracy': round(accuracy, 2),
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives
        }


def test_enhanced_digital_twin():
    """Test the enhanced digital twin"""
    print("=" * 60)
    print("ENHANCED DIGITAL TWIN - INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize
    dt = EnhancedDigitalTwin()
    
    # Test comprehensive analysis
    print("\n[*] Testing Comprehensive Analysis:")
    for idx in [0, 100, 500]:
        print(f"\n--- Index {idx} ---")
        analysis = dt.get_comprehensive_analysis(idx)
        print(f"Pipe: {analysis['pipe_id']}")
        print(f"ML Expected: {analysis['ml_expected_flow']} | Calibrated: {analysis['calibrated_expected_flow']}")
        print(f"Observed: {analysis['observed_flow']}")
        print(f"ML Status: {analysis['ml_status']} ({analysis['ml_confidence']}%)")
        print(f"Physics Status: {analysis['physics_status']} ({analysis['physics_confidence']}%)")
        print(f"FINAL: {analysis['status']} ({analysis['confidence']}%)")
        print(f"Ground Truth: {analysis['ground_truth']} | Correct: {analysis['is_correct']}")
    
    # Test statistics
    print("\n[*] System Statistics (first 1000 records):")
    stats = dt.get_system_statistics(0, 1000)
    print(f"Accuracy: {stats['accuracy']}%")
    print(f"Precision: {stats['precision']}%")
    print(f"Recall: {stats['recall']}%")
    print(f"Leaks: {stats['leaks_detected']} | Suspects: {stats['suspects_detected']}")
    
    print("\n" + "=" * 60)
    print("[OK] Enhanced Digital Twin operational!")
    print("=" * 60)


if __name__ == "__main__":
    test_enhanced_digital_twin()
