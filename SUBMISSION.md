# 🎉 AML LABS - Smart Water Digital Twin

## Team Submission Summary

**Team Name:** AML LABS  
**Team Leader:** Amal Babu  
**Members:** Govind Lal T L, Abel Jeevan, Navaneeth Santosh

---

## ✅ Submission Checklist

### Source Code ✅
All Python scripts and project files included:
- `demand_model.py` - ML demand prediction
- `physics_rules.py` - Physics-informed validation
- `leak_algorithm.py` - Real-time leak detection
- `digital_twin.py` - Digital Twin orchestration
- `visualization.py` - Network visualization
- `app.py` - Streamlit UI
- `data/location_aware_gis_leakage_dataset.csv` - Dataset

### README.md ✅
Complete markdown file with:
- ✅ Team Identity (Team Name & All Member Names)
- ✅ Project Brief (Tools, libraries, algorithms implemented)
- ✅ Comprehensive Digital Twin explanations
- ✅ Demo presentation guide
- ✅ Technical deep dive

### requirements.txt ✅
Full dependency list for running the code:
```
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
plotly>=5.18.0
networkx>=3.1
matplotlib>=3.7.0
joblib>=1.3.0
```

---

## 🚀 Quick Run Instructions

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the ML model
python demand_model.py

# 3. Run the demo
streamlit run app.py
```

The demo will open at `http://localhost:8501`

---

## 📊 What Judges Will See

### 1. Interactive Time Control
- Slider to move through 5,000 sensor readings
- Real-time updates across all panels
- Dynamic network visualization

### 2. Three-Signal Analysis
- **Signal 1:** ML Demand Prediction (Linear Regression)
- **Signal 2:** Physics-Informed Rules (Conservation + Pressure-Flow)
- **Signal 3:** Multi-Signal Fusion (Combined decision)

### 3. Network Visualization
- Color-coded pipes (Green/Yellow/Red)
- Thickness proportional to flow
- Interactive pipe selection dropdown

### 4. Explainable Reasoning
- Every decision traceable
- "Why DT Thinks So" explanations
- Physical principles clearly listed

### 5. Learning System
- Calibration indicators
- Historical trend tracking
- "Digital Twin has learned" messages

---

## 🎯 Key Demo Talking Points

**Opening:**
> "This is a Digital Twin system, not just AI. It combines Machine Learning with Physics-Informed reasoning for fully explainable leak detection."

**During Demo:**
- Show slider movement → Pipes change color
- Select different pipes → Inspection panel updates
- Point out calibration → "The DT is learning!"
- Explain multi-signal → "Both ML and Physics must agree"

**Closing:**
> "The Digital Twin validates predictions against physical laws, learns from observations, and provides transparent reasoning—making it practical for real-world deployment."

---

## 💡 What Makes This a Digital Twin

| Requirement | Our Implementation |
|-------------|-------------------|
| **Physical Representation** | Graph model of water network |
| **Expected Behavior** | ML learns normal consumption |
| **Observed Behavior** | Real sensor data from dataset |
| **Deviation Analysis** | Residual = Observed - Expected |
| **Physical Validation** | Conservation + Pressure-flow rules |
| **Learning & Adaptation** | Calibration system improves over time |
| **Explainability** | All reasoning steps visible in UI |

---

## 🔬 Technical Highlights

### Algorithms Used
1. **Linear Regression** (Supervised Learning) for demand prediction
2. **Physics-Based Residual Analysis** for anomaly detection  
3. **Multi-Signal Fusion** for robust classification
4. **Online Calibration** for continuous improvement

### Libraries Used
- **scikit-learn:** Machine Learning models
- **NetworkX:** Graph-based network modeling
- **Plotly:** Interactive visualizations
- **Streamlit:** User interface framework
- **pandas/numpy:** Data processing

### Key Features
- **No CFD/EPANET:** Simplified, explainable physics
- **No Perfect Data Required:** System adapts with assumptions
- **Real-Time Processing:** Row-by-row leak detection
- **Practical Deployment:** Works on existing infrastructure

---

## 📈 Performance Metrics

Based on the test dataset (5,000 records):
- **Accuracy:** ~83%
- **Recall:** 100% (catches all real leaks)
- **Precision:** ~26% (conservative - better safe than sorry)

The system intentionally errs on caution for critical infrastructure.

---

## 📚 Additional Documentation

- **`demo_guide.md`** - Complete presentation script with timing
- **`README.md`** - Full technical documentation
- **Code Comments** - Every module extensively documented
- **Test Functions** - Run individual files for unit tests

---

## 🎬 Demo Success Criteria

After watching the demo, judges should be able to answer:

✅ What is a Digital Twin? (System of models, not one AI)  
✅ How does ML contribute? (Learns normal patterns)  
✅ What are the physics rules? (Conservation, pressure-flow)  
✅ Why multi-signal fusion? (More robust than single signal)  
✅ How does it learn? (Calibration adjusts baselines)  
✅ Why is it explainable? (All reasoning visible)

---

## 🏆 Hackathon Compliance

✅ **Digital Twin Architecture** - Complete 5-layer system  
✅ **Physics-Informed Logic** - Explicit conservation & pressure rules  
✅ **Machine Learning** - Supervised learning for demand  
✅ **Real-Time Algorithm** - Row-by-row detection  
✅ **Interactive Visualization** - Network graph with selection  
✅ **Learning System** - Calibration improves accuracy  
✅ **Full Explainability** - No black boxes  
✅ **Real Data** - 5,000 sensor readings with ground truth  

---

## 📞 Contact for Questions

**Team Leader:** Amal Babu  
**Team:** Govind Lal T L, Abel Jeevan, Navaneeth Santosh

---

**AML LABS - Making Water Networks Intelligent 💧**
