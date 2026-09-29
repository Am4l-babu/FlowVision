"""
Physics-Informed Rules for Water Distribution Network
This module implements simplified physical constraints that govern water flow.

IMPORTANT: This is NOT CFD or EPANET.
These are LOGICAL PHYSICAL CONSTRAINTS for explainable Digital Twin reasoning.

Physical Principles:
1. Conservation of Flow (Kirchhoff's Law)
2. Pressure-Flow Relationship (simplified Darcy-Weisbach)
3. Distance-based Pressure Loss
"""

import numpy as np
import pandas as pd


class PhysicsEngine:
    """
    Physics-based calculations for water network.
    Uses simplified rules that are explainable to judges.
    """
    
    def __init__(self, gravity=9.81):
        """
        Initialize physics engine with physical constants.
        
        Args:
            gravity: Gravitational constant (m/s^2)
        """
        self.gravity = gravity
        self.default_roughness = 0.01  # Pipe roughness coefficient
        self.density = 1000  # Water density (kg/m^3)
    
    def calculate_pressure_drop(self, flow_rate, pipe_length=1000, pipe_diameter=0.3, roughness=None):
        """
        Calculate expected pressure drop in a pipe.
        Based on simplified Darcy-Weisbach equation.
        
        Principle: Pressure drop is proportional to flow^2
        Higher flow → More friction → More pressure loss
        
        Args:
            flow_rate: Flow rate (L/min)
            pipe_length: Pipe length (m)
            pipe_diameter: Pipe diameter (m)
            roughness: Pipe roughness coefficient
        
        Returns:
            pressure_drop: Expected pressure drop (PSI)
        """
        if roughness is None:
            roughness = self.default_roughness
        
        # Convert L/min to m^3/s
        flow_m3s = flow_rate / 60000.0
        
        # Calculate velocity
        area = np.pi * (pipe_diameter / 2) ** 2
        velocity = flow_m3s / area if area > 0 else 0
        
        # Simplified Darcy-Weisbach: ΔP = f * (L/D) * (ρ * v^2 / 2)
        friction_factor = roughness * 0.1  # Simplified
        pressure_drop_pa = friction_factor * (pipe_length / pipe_diameter) * (self.density * velocity ** 2 / 2)
        
        # Convert Pa to PSI
        pressure_drop_psi = pressure_drop_pa * 0.000145038
        
        return pressure_drop_psi
    
    def check_flow_conservation(self, flow_in, flow_out, expected_consumption, tolerance=0.15):
        """
        Check if flow conservation is satisfied.
        
        Principle: flow_in = flow_out + consumption
        If flow_in > flow_out + consumption → LEAK (water is lost)
        
        Args:
            flow_in: Inflow (L/min)
            flow_out: Outflow (L/min)
            expected_consumption: Expected consumption (L/min)
            tolerance: Acceptable deviation (15% default)
        
        Returns:
            dict: {
                'conserved': True/False,
                'residual': Excess flow,
                'residual_percentage': Percentage excess,
                'explanation': Human-readable explanation
            }
        """
        # Expected outflow = inflow - consumption
        expected_outflow = flow_in - expected_consumption
        
        # Actual residual
        residual = flow_in - (flow_out + expected_consumption)
        residual_percentage = (residual / flow_in) * 100 if flow_in > 0 else 0
        
        conserved = abs(residual_percentage) <= (tolerance * 100)
        
        if conserved:
            explanation = f"Flow conserved: {residual:.1f} L/min discrepancy ({residual_percentage:.1f}%) is within tolerance"
        else:
            if residual > 0:
                explanation = f"Flow NOT conserved: {residual:.1f} L/min excess ({residual_percentage:.1f}%) - POSSIBLE LEAK"
            else:
                explanation = f"Flow NOT conserved: {abs(residual):.1f} L/min deficit ({abs(residual_percentage):.1f}%) - possible blockage"
        
        return {
            'conserved': conserved,
            'residual': residual,
            'residual_percentage': residual_percentage,
            'explanation': explanation
        }
    
    def estimate_expected_pressure(self, base_pressure, flow_rate, pipe_length=1000):
        """
        Estimate expected pressure at a point given flow conditions.
        
        Args:
            base_pressure: Inlet pressure (PSI)
            flow_rate: Current flow rate (L/min)
            pipe_length: Distance from inlet (m)
        
        Returns:
            expected_pressure: Expected pressure (PSI)
        """
        pressure_drop = self.calculate_pressure_drop(flow_rate, pipe_length)
        expected_pressure = base_pressure - pressure_drop
        
        return max(expected_pressure, 0)  # Pressure can't be negative
    
    def check_pressure_consistency(self, expected_pressure, observed_pressure, tolerance=0.10):
        """
        Check if observed pressure matches expected pressure.
        
        Physical Principle: If observed << expected → Unexpected pressure drop → LEAK
        
        Explanation for Judges:
        When water leaks from a pipe, pressure drops because:
        1. Water escaping creates an additional exit point
        2. Flow resistance changes
        3. System equilibrium is disrupted
        
        This is like a garden hose with a hole - pressure after the hole is lower.
        
        Args:
            expected_pressure: Physics-calculated pressure (PSI)
            observed_pressure: Sensor reading (PSI)
            tolerance: Acceptable deviation (10% default)
        
        Returns:
            dict: {
                'consistent': True/False,
                'deviation': Pressure difference,
                'deviation_percentage': Percentage deviation,
                'explanation': Human-readable explanation
            }
        """
        deviation = observed_pressure - expected_pressure
        deviation_percentage = (deviation / expected_pressure) * 100 if expected_pressure > 0 else 0
        
        consistent = abs(deviation_percentage) <= (tolerance * 100)
        
        if consistent:
            explanation = f"✓ Pressure normal: {deviation:+.1f} PSI ({deviation_percentage:+.1f}%) from expected"
        else:
            if deviation < 0:
                explanation = f"⚠️ PRESSURE DROP DETECTED: {abs(deviation):.1f} PSI below expected ({abs(deviation_percentage):.1f}%) — Water may be escaping!"
            else:
                explanation = f"⚠️ Unexpected pressure rise: {deviation:.1f} PSI above expected ({deviation_percentage:.1f}%) — Possible blockage or valve closure"
        
        return {
            'consistent': consistent,
            'deviation': deviation,
            'deviation_percentage': deviation_percentage,
            'explanation': explanation
        }
    
    def analyze_pipe_segment(self, pipe_data, expected_demand):
        """
        Comprehensive physics analysis of a pipe segment.
        
        Args:
            pipe_data: Dict with flow_rate, pressure, pipe_length, etc.
            expected_demand: Expected consumption (from ML)
        
        Returns:
            dict: Complete physics analysis with multiple signals
        """
        flow_rate = pipe_data.get('flow_rate', 0)
        pressure = pipe_data.get('pressure', 0)
        pipe_length = pipe_data.get('pipe_length', 1000)
        base_pressure = pipe_data.get('base_pressure', 100)  # Assume 100 PSI at source
        
        # 1. Calculate expected pressure based on flow
        expected_pressure = self.estimate_expected_pressure(base_pressure, expected_demand, pipe_length)
        
        # 2. Check pressure consistency
        pressure_check = self.check_pressure_consistency(expected_pressure, pressure)
        
        # 3. Check flow conservation (simplified - assume inflow = expected_demand + observed_flow)
        # In a leak scenario: observed_flow > expected_demand
        flow_residual = flow_rate - expected_demand
        flow_residual_pct = (flow_residual / expected_demand) * 100 if expected_demand > 0 else 0
        
        # 4. Compute physics-based confidence
        # Multiple signals increase confidence
        physics_signals = []
        
        if flow_residual_pct > 15:
            physics_signals.append("Excess flow detected")
        
        if not pressure_check['consistent'] and pressure_check['deviation'] < 0:
            physics_signals.append("Pressure drop confirmed")
        
        # Combine signals
        if len(physics_signals) >= 2:
            physics_status = "LEAK"
            physics_confidence = min(abs(flow_residual_pct) + abs(pressure_check['deviation_percentage']), 100)
        elif len(physics_signals) == 1:
            physics_status = "SUSPECT"
            physics_confidence = min(abs(flow_residual_pct), 50)
        else:
            physics_status = "NORMAL"
            physics_confidence = max(100 - abs(flow_residual_pct), 0)
        
        return {
            'expected_pressure': expected_pressure,
            'observed_pressure': pressure,
            'pressure_check': pressure_check,
            'flow_residual': flow_residual,
            'flow_residual_percentage': flow_residual_pct,
            'physics_signals': physics_signals,
            'physics_status': physics_status,
            'physics_confidence': physics_confidence,
            'explanation': " + ".join(physics_signals) if physics_signals else "No physical anomalies detected"
        }


def test_physics_engine():
    """Test the physics engine with sample scenarios"""
    print("=" * 60)
    print("PHYSICS ENGINE - UNIT TEST")
    print("=" * 60)
    
    engine = PhysicsEngine()
    
    # Test 1: Normal operation
    print("\n[*] Test 1: Normal Operation")
    pipe_data = {
        'flow_rate': 50.0,
        'pressure': 88.0,
        'pipe_length': 1000,
        'base_pressure': 100
    }
    expected_demand = 48.0
    
    result = engine.analyze_pipe_segment(pipe_data, expected_demand)
    print(f"   Flow: {pipe_data['flow_rate']} L/min | Expected: {expected_demand} L/min")
    print(f"   Pressure: {pipe_data['pressure']} PSI | Expected: {result['expected_pressure']:.1f} PSI")
    print(f"   Physics Status: {result['physics_status']}")
    print(f"   Signals: {result['physics_signals']}")
    assert result['physics_status'] in ['NORMAL', 'SUSPECT'], "Should be normal or suspect"
    
    # Test 2: Leak scenario (high flow + pressure drop)
    print("\n[*] Test 2: Leak Scenario")
    pipe_data = {
        'flow_rate': 75.0,
        'pressure': 70.0,
        'pipe_length': 1000,
        'base_pressure': 100
    }
    expected_demand = 50.0
    
    result = engine.analyze_pipe_segment(pipe_data, expected_demand)
    print(f"   Flow: {pipe_data['flow_rate']} L/min | Expected: {expected_demand} L/min")
    print(f"   Pressure: {pipe_data['pressure']} PSI | Expected: {result['expected_pressure']:.1f} PSI")
    print(f"   Physics Status: {result['physics_status']}")
    print(f"   Signals: {result['physics_signals']}")
    print(f"   Confidence: {result['physics_confidence']:.1f}%")
    assert result['physics_status'] == 'LEAK', "Should detect leak"
    
    # Test 3: Pressure drop calculation
    print("\n[*] Test 3: Pressure Drop Calculation")
    drop_low = engine.calculate_pressure_drop(flow_rate=30.0, pipe_length=1000)
    drop_high = engine.calculate_pressure_drop(flow_rate=90.0, pipe_length=1000)
    print(f"   Pressure drop at 30 L/min: {drop_low:.2f} PSI")
    print(f"   Pressure drop at 90 L/min: {drop_high:.2f} PSI")
    print(f"   Ratio (should be ~9, since pressure proportional to flow^2): {drop_high/drop_low:.1f}")
    assert drop_high > drop_low, "Higher flow should cause more pressure drop"
    
    print("\n" + "=" * 60)
    print("[OK] All physics tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_physics_engine()
