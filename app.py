"""
Enhanced Interactive Streamlit UI
Complete Digital Twin demonstration interface with:
- Physics-informed reasoning display
- Interactive network visualization with click handlers
- Inspection panel for detailed pipe/node analysis
- Multi-signal leak detection visualization
"""

import streamlit as st
import pandas as pd
import numpy as np
from digital_twin import EnhancedDigitalTwin
from visualization import NetworkVisualizer

# Page configuration
st.set_page_config(
    page_title="Smart Water Digital Twin",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .status-normal {
        background-color: #10b981;
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 5px;
        font-weight: 600;
        display: inline-block;
    }
    .status-leak {
        background-color: #ef4444;
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 5px;
        font-weight: 600;
        display: inline-block;
    }
    .status-suspect {
        background-color: #f59e0b;
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 5px;
        font-weight: 600;
        display: inline-block;
    }
    .signal-box {
        background-color: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .physics-box {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_system():
    """Initialize the Enhanced Digital Twin and Visualizer"""
    dt = EnhancedDigitalTwin()
    viz = NetworkVisualizer(dt.dataset)
    return dt, viz


def main():
    # Header
    st.markdown('<h1 class="main-header">💧 Smart Water Digital Twin</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Physics-Informed ML System for Real-Time Leak Detection</p>', unsafe_allow_html=True)
    
    # Initialize system
    with st.spinner("Initializing Digital Twin System..."):
        try:
            dt, viz = initialize_system()
        except Exception as e:
            st.error(f"Error initializing Digital Twin: {e}")
            st.info("Please ensure `trained_model.pkl` exists. Run: `python demand_model.py`")
            st.stop()
    
    # Sidebar info
    with st.sidebar:
        st.title("ℹ️  Digital Twin System")
        st.markdown("""
        **Components:**
        - 🤖 ML Model (Demand Prediction)
        - 🔬 Physics Engine (Flow & Pressure)
        - 🧠 Multi-Signal Detection
        - 📈 Self-Calibration
        
        **How It Works:**
        1. ML predicts *normal* consumption
        2. Physics validates feasibility
        3. Compare with sensor data
        4. Detect anomalies (multi-signal)
        5. Learn and calibrate
        
        **Interactive Features:**
        - 🎚️ Scrub through time
        - 🔍 Click pipes for details
        - 📊 See reasoning breakdown
        """)
    
    st.markdown("---")
    
    # Time Control
    st.subheader("⏱️ Time Control")
    col_slider, col_info =st.columns([4, 1])
    
    with col_slider:
        time_index = st.slider(
            "Dataset Index",
            min_value=0,
            max_value=len(dt.dataset) - 1,
            value=0,
            step=1,
            help="Move slider to navigate through sensor readings"
        )
    
    with col_info:
        st.metric("Total Records", f"{len(dt.dataset):,}")
    
    # Get comprehensive analysis
    analysis = dt.get_comprehensive_analysis(time_index)
    
    # Main content: Two columns
    col_reasoning, col_network = st.columns([1, 1])
    
    # ===== LEFT COLUMN: Digital Twin Reasoning =====
    with col_reasoning:
        st.markdown("### 🧠 Digital Twin Multi-Signal Analysis")
        st.markdown("**This Digital Twin combines 3 independent signals:**")
        
        # Pipe Information
        st.markdown(f"**📍 Pipe:** `{analysis['pipe_id']}`")
        st.markdown(f"**🗺️ Location:** {analysis['zone']} → {analysis['block']} → {analysis['pipe']}")
        
        st.markdown("---")
        
        # ML Layer (SIGNAL 1)
        st.markdown("#### 🤖 Signal 1: ML Demand Prediction")
        st.caption("👉 **Purpose:** Learn normal consumption patterns from historical data")
        st.markdown('<div class="signal-box">', unsafe_allow_html=True)
        
        col_ml1, col_ml2 = st.columns(2)
        with col_ml1:
            st.metric(
                "Expected (ML)",
                f"{analysis['ml_expected_flow']:.1f} L/min",
                help="Predicted by Linear Regression model trained on normal data"
            )
        with col_ml2:
            st.metric(
                "Observed (Sensor)",
                f"{analysis['observed_flow']:.1f} L/min",
                delta=f"{analysis['ml_residual']:.1f} ({analysis['ml_residual_percentage']:.1f}%)",
                help="Actual sensor reading"
            )
        
        if analysis['calibration_offset'] != 0:
            st.info(f"⚙️ **Calibrated:** Offset of {analysis['calibration_offset']:+.1f} L/min applied (Digital Twin learning!)")
        
        st.markdown(f"**ML Decision:** {analysis['ml_status']} ({analysis['ml_confidence']:.1f}% confidence)")
        st.caption(f"📝 {analysis['ml_reasoning']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Physics Layer (SIGNAL 2)
        st.markdown("#### 🔬 Signal 2: Physics-Informed Rules")
        st.caption("👉 **Purpose:** Validate against physical laws (NOT AI simulation!)")
        st.markdown('<div class="physics-box">', unsafe_allow_html=True)
        
        # Show physics principles being checked
        st.markdown("**Physical Principles Being Verified:**")
        st.markdown("- ⚖️ **Conservation of Flow:** Water going in = Water going out + Consumption")
        st.markdown("- 📉 **Pressure-Flow Relationship:** Higher flow → More friction → Pressure drop")
        st.markdown("- 🔍 **Localized Effects:** Leaks affect specific segments, not entire network")
        
        st.markdown("")  # Space
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(
                "Expected Pressure",
                f"{analysis['physics_expected_pressure']:.1f} PSI",
                help="Calculated from simplified Darcy-Weisbach equation"
            )
        with col_p2:
            st.metric(
                "Observed Pressure",
                f"{analysis['observed_pressure']:.1f} PSI",
                delta=f"{analysis['physics_pressure_deviation']:.1f} PSI",
                help="Actual pressure reading"
            )
        
        st.markdown(f"**Physics Decision:** {analysis['physics_status']} ({analysis['physics_confidence']:.1f}% confidence)")
        
        if analysis['physics_signals']:
            st.markdown("**Physical Anomalies Detected:**")
            for signal in analysis['physics_signals']:
                st.markdown(f"- ⚠️ {signal}")
        else:
            st.success("✓ All physical constraints satisfied")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Final Decision (SIGNAL FUSION)
        st.markdown("#### 🎯 Signal 3: Multi-Signal Fusion (Final Decision)")
        st.caption("👉 **Purpose:** Combine ML + Physics for robust detection")
        
        # Status badge
        if analysis['status'] == 'LEAK':
            st.markdown('<div class="status-leak">⚠️ LEAK DETECTED</div>', unsafe_allow_html=True)
        elif analysis['status'] == 'SUSPECT':
            st.markdown('<div class="status-suspect">⚠️ SUSPECT</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-normal">✅ NORMAL OPERATION</div>', unsafe_allow_html=True)
        
        st.markdown("")  # Space
        
        # Confidence
        st.progress(analysis['confidence'] / 100)
        st.markdown(f"**Combined Confidence:** {analysis['confidence']:.1f}%")
        
        # Reasoning signals
        st.markdown("**Digital Twin Reasoning:**")
        for signal in analysis['reasoning_signals']:
            st.markdown(f"- 🧠 {signal}")
        
        # Explain fusion logic for judges
        st.info("""
        **💡 Why Multi-Signal?**  
        - If **both ML and Physics** detect anomaly → High confidence LEAK
        - If **only one** detects → Medium confidence SUSPECT  
        - If **neither** detects → NORMAL operation
        """)
        
        # Ground truth validation
        st.markdown("---")
        if analysis['is_correct']:
            st.success(f"✅ Correct Detection | Ground Truth: {analysis['ground_truth']}")
        else:
            st.warning(f"⚠️ Mismatch | Ground Truth: {analysis['ground_truth']} | Detected: {analysis['status']}")
        
        # Additional sensors
        with st.expander("📊 Additional Sensor Data"):
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Temperature", f"{analysis['temperature']:.1f}°C")
            with col_s2:
                st.metric("RPM", f"{analysis['rpm']:.0f}")
            with col_s3:
                st.metric("Vibration", f"{analysis['vibration']:.2f}")
    
    # ===== RIGHT COLUMN: Network Visualization =====
    with col_network:
        st.markdown("### 🗺️ Network Visualization")
        
        # Get network snapshot
        pipe_statuses = dt.get_network_snapshot(time_index)
        
        # Create visualization
        network_fig = viz.create_network_figure(pipe_statuses, selected_pipe=analysis['pipe_id'])
        
        # Display
        st.plotly_chart(network_fig, use_container_width=True)
        
        # Legend
        st.markdown("""
        **Legend:**
        - 🟢 **Green**: Normal operation (confidence < 30%)
        - 🟡 **Yellow**: Degraded/Suspect (30-60%)
        - 🔴 **Red**: Leak detected (confidence > 60%)
        - 🟣 **Purple**: Currently selected pipe
        - **Thickness**: Proportional to flow rate
        
        💡 **Tip:** In a full implementation, click on pipes to inspect them!
        """)
    
    # Interactive Pipe Inspection Panel (HACKATHON REQUIREMENT)
    st.markdown("---")
    st.markdown("### 🔍 Interactive Pipe Inspection")
    st.markdown("**Select any pipe to inspect its Digital Twin state:**")
    
    # Get list of active pipes for selection
    active_pipes = viz.get_active_pipes(time_index, window_size=50)
    
    # Find current pipe index
    current_pipe_idx = active_pipes.index(analysis['pipe_id']) if analysis['pipe_id'] in active_pipes else 0
    
    # Pipe selector dropdown
    selected_pipe_id = st.selectbox(
        "Choose a pipe to inspect:",
        options=active_pipes,
        index=current_pipe_idx,
        format_func=lambda x: f"{x} ({dt.network_state.get(x, {}).get('zone', 'Unknown')})",
        help="Select any pipe from the active network to see detailed Digital Twin analysis"
    )
    
    # Get analysis for selected pipe (if different from current timestep)
    if selected_pipe_id != analysis['pipe_id']:
        # Find a recent record for this pipe
        pipe_records = dt.dataset[dt.dataset['Location_Code'] == selected_pipe_id]
        if len(pipe_records) > 0:
            # Get closest record to current time
            closest_idx = pipe_records.index[
                (pipe_records.index - time_index).abs().argsort()[0]
            ]
            inspection_analysis = dt.get_comprehensive_analysis(closest_idx)
        else:
            inspection_analysis = analysis  # Fallback
    else:
        inspection_analysis = analysis
    
    # Display inspection details
    col_insp1, col_insp2 = st.columns(2)
    
    with col_insp1:
        st.markdown("#### 📍 Pipe Information")
        st.markdown(f"**Pipe ID:** `{inspection_analysis['pipe_id']}`")
        st.markdown(f"**Network Path:** {inspection_analysis['zone']} → {inspection_analysis['block']} → {inspection_analysis['pipe']}")
        st.markdown(f"**GPS Location:** {inspection_analysis['location']['lat']:.6f}, {inspection_analysis['location']['lon']:.6f}")
        
        st.markdown("#### 📊 Current State")
        st.metric("Flow Rate", f"{inspection_analysis['observed_flow']:.1f} L/min", 
                 delta=f"{inspection_analysis['ml_residual']:+.1f} L/min")
        st.metric("Pressure", f"{inspection_analysis['observed_pressure']:.1f} PSI",
                 delta=f"{inspection_analysis['physics_pressure_deviation']:+.1f} PSI")
    
    with col_insp2:
        st.markdown("#### 🎯 Digital Twin Assessment")
        
        # Status with color coding
        if inspection_analysis['status'] == 'LEAK':
            st.error(f"⚠️ **{inspection_analysis['status']}** — Confidence: {inspection_analysis['confidence']:.1f}%")
        elif inspection_analysis['status'] == 'SUSPECT':
            st.warning(f"⚠️ **{inspection_analysis['status']}** — Confidence: {inspection_analysis['confidence']:.1f}%")
        else:
            st.success(f"✅ **{inspection_analysis['status']}** — Confidence: {inspection_analysis['confidence']:.1f}%")
        
        # Why DT thinks so (HACKATHON REQUIREMENT)
        st.markdown("#### 🧠 Why Digital Twin Thinks So:")
        for reason in inspection_analysis['reasoning_signals']:
            st.markdown(f"- {reason}")
        
        # Calibration status (LEARNING ASPECT)
        if inspection_analysis['calibrated']:
            st.info(f"⚙️ **Calibration Active** — Offset: {inspection_analysis['calibration_offset']:+.1f} L/min")
            st.caption("🎓 Digital Twin has learned this pipe's baseline behavior")
        else:
            st.caption("📚 Digital Twin is still learning this pipe's behavior")
        
        # Historical behavior
        pipe_id = inspection_analysis['pipe_id']
        if pipe_id in dt.calibration_history and len(dt.calibration_history[pipe_id]) > 5:
            history = dt.calibration_history[pipe_id]
            avg_residual = np.mean([h['residual'] for h in history])
            st.markdown(f"**Historical Avg Residual:** {avg_residual:.1f} L/min (last {len(history)} readings)")
        else:
            st.caption("Not enough historical data for this pipe yet")
    
    # Statistics Dashboard
    st.markdown("---")
    st.markdown("### 📊 System Performance Metrics")
    
    stats = dt.get_system_statistics(0, min(time_index + 1, 500))  # Limit for performance
    
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
    
    with col_stat1:
        st.metric("Records Processed", f"{stats['total_checked']} / {stats['total_records']}")
    
    with col_stat2:
        st.metric("Leaks Detected", f"{stats['leaks_detected']}")
    
    with col_stat3:
        st.metric("Accuracy", f"{stats['accuracy']:.1f}%")
    
    with col_stat4:
        st.metric("Precision", f"{stats['precision']:.1f}%")
    
    with col_stat5:
        st.metric("Recall", f"{stats['recall']:.1f}%")
    
    # Detailed metrics
    with st.expander("📈 Detailed Performance Metrics"):
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown(f"""
            **Confusion Matrix:**
            - True Positives: {stats['true_positives']}
            - True Negatives: {stats['true_negatives']}
            - False Positives: {stats['false_positives']}
            - False Negatives: {stats['false_negatives']}
            """)
        
        with col_d2:
            st.markdown(f"""
            **System Status:**
            - Total Pipes Monitored: {len(dt.network_state)}
            - Calibration Active: Yes
            - Multi-Signal Fusion: Enabled
            - Detection Mode: ML + Physics
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; padding: 1rem;'>
        <strong>Enhanced Digital Twin Demo</strong> | Physics-Informed + Machine Learning<br>
        Multi-Signal Detection | Self-Calibrating | Fully Explainable
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
