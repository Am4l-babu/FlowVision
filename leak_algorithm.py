"""
Leak Detection Algorithm
Real-time algorithm that compares expected vs observed flow to detect anomalies.
This is the core detection logic for the Digital Twin.
"""

import numpy as np


class LeakDetector:
    """
    Real-time leak detection using residual analysis.
    Compares ML-predicted expected flow with actual observed flow.
    """
    
    def __init__(self, residual_threshold=15.0, pressure_sensitivity=0.9):
        """
        Initialize leak detector with configurable thresholds.
        
        Args:
            residual_threshold: Percentage deviation to flag as leak (default: 15%)
            pressure_sensitivity: Multiplier for pressure drop detection (default: 0.9)
        """
        self.residual_threshold = residual_threshold
        self.pressure_sensitivity = pressure_sensitivity
        self.pressure_history = {}  # Store mean pressure per pipe
    
    def update_pressure_baseline(self, pipe_id, pressure):
        """Update running average of pressure for each pipe"""
        if pipe_id not in self.pressure_history:
            self.pressure_history[pipe_id] = []
        
        self.pressure_history[pipe_id].append(pressure)
        
        # Keep only last 50 readings for rolling average
        if len(self.pressure_history[pipe_id]) > 50:
            self.pressure_history[pipe_id].pop(0)
    
    def detect_leak(self, pipe_id, expected_flow, observed_flow, pressure):
        """
        Main leak detection algorithm.
        
        Digital Twin Logic:
        1. Calculate residual = observed - expected
        2. Calculate residual percentage
        3. Check pressure drop
        4. Make decision with confidence score
        
        Args:
            pipe_id: Identifier for the pipe segment
            expected_flow: ML model prediction (what SHOULD be happening)
            observed_flow: Sensor reading (what IS happening)
            pressure: Current pressure reading
        
        Returns:
            dict: {
                'status': 'LEAK' or 'NORMAL',
                'confidence': 0-100,
                'residual': absolute difference,
                'residual_percentage': percentage difference,
                'pressure_drop': True/False,
                'reasoning': explanation string
            }
        """
        # Update pressure baseline
        self.update_pressure_baseline(pipe_id, pressure)
        
        # Calculate residual (Digital Twin comparison)
        residual = observed_flow - expected_flow
        residual_percentage = (residual / expected_flow) * 100 if expected_flow > 0 else 0
        
        # Check for pressure drop
        mean_pressure = np.mean(self.pressure_history.get(pipe_id, [pressure]))
        pressure_drop = pressure < (mean_pressure * self.pressure_sensitivity)
        
        # Decision logic: High flow + Pressure drop = LEAK
        # (More water flowing out than expected, and pressure is dropping)
        if abs(residual_percentage) > self.residual_threshold and residual > 0:
            # High positive residual indicates leak
            if pressure_drop:
                status = 'LEAK'
                confidence = min(abs(residual_percentage), 100)
                reasoning = f"[!] LEAK: Flow is {residual_percentage:.1f}% higher than expected AND pressure dropped"
            else:
                status = 'LEAK'
                confidence = min(abs(residual_percentage) * 0.7, 100)  # Lower confidence without pressure drop
                reasoning = f"[!] LEAK: Flow is {residual_percentage:.1f}% higher than expected (pressure stable)"
        
        elif abs(residual_percentage) > self.residual_threshold and residual < 0:
            # High negative residual (blockage or sensor issue)
            status = 'ANOMALY'
            confidence = min(abs(residual_percentage), 100)
            reasoning = f"[!] ANOMALY: Flow is {abs(residual_percentage):.1f}% LOWER than expected (possible blockage)"
        
        else:
            # Normal operation
            status = 'NORMAL'
            confidence = max(100 - abs(residual_percentage), 0)
            reasoning = f"[OK] NORMAL: Flow within expected range (±{abs(residual_percentage):.1f}%)"
        
        return {
            'status': status,
            'confidence': round(confidence, 2),
            'residual': round(residual, 2),
            'residual_percentage': round(residual_percentage, 2),
            'pressure_drop': pressure_drop,
            'reasoning': reasoning,
            'expected_flow': round(expected_flow, 2),
            'observed_flow': round(observed_flow, 2),
            'pressure': round(pressure, 2)
        }


def test_leak_algorithm():
    """Unit test for leak detection algorithm"""
    print("=" * 60)
    print("LEAK DETECTION ALGORITHM - UNIT TEST")
    print("=" * 60)
    
    detector = LeakDetector(residual_threshold=15.0)
    
    # Test Case 1: Normal operation
    print("\n[*] Test Case 1: Normal Operation")
    result = detector.detect_leak(
        pipe_id="Zone_1_Block_1_Pipe_1",
        expected_flow=50.0,
        observed_flow=52.0,  # 4% higher, within threshold
        pressure=65.0
    )
    print(f"   Expected: 50.0 | Observed: 52.0")
    print(f"   Status: {result['status']} | Confidence: {result['confidence']}%")
    print(f"   Reasoning: {result['reasoning']}")
    assert result['status'] == 'NORMAL', "Should be NORMAL"
    
    # Test Case 2: Leak detected (high flow + pressure drop)
    print("\n[*] Test Case 2: Leak Detected")
    for i in range(5):
        detector.update_pressure_baseline("Zone_1_Block_1_Pipe_2", 70.0)  # Build baseline
    
    result = detector.detect_leak(
        pipe_id="Zone_1_Block_1_Pipe_2",
        expected_flow=50.0,
        observed_flow=65.0,  # 30% higher
        pressure=55.0  # Pressure dropped
    )
    print(f"   Expected: 50.0 | Observed: 65.0")
    print(f"   Status: {result['status']} | Confidence: {result['confidence']}%")
    print(f"   Reasoning: {result['reasoning']}")
    assert result['status'] == 'LEAK', "Should be LEAK"
    
    # Test Case 3: High residual but no pressure drop
    print("\n[*] Test Case 3: Anomaly (High Flow, Stable Pressure)")
    result = detector.detect_leak(
        pipe_id="Zone_1_Block_1_Pipe_3",
        expected_flow=50.0,
        observed_flow=70.0,  # 40% higher
        pressure=70.0  # Pressure stable
    )
    print(f"   Expected: 50.0 | Observed: 70.0")
    print(f"   Status: {result['status']} | Confidence: {result['confidence']}%")
    print(f"   Reasoning: {result['reasoning']}")
    assert result['status'] == 'LEAK', "Should be LEAK (even without pressure drop)"
    
    print("\n" + "=" * 60)
    print("[OK] All tests passed! Algorithm working correctly.")
    print("=" * 60)


if __name__ == "__main__":
    test_leak_algorithm()
