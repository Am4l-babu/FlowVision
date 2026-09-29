"""
Network Visualization Module
Creates interactive 2D network graphs with color-coded pipes and clickable elements.

This module generates visual representations of the water distribution network
with real-time status updates based on Digital Twin analysis.
"""

import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class NetworkVisualizer:
    """
    Creates interactive network visualizations for the Digital Twin.
    Pipes are color-coded based on leak detection status.
    """
    
    def __init__(self, dataset):
        """
        Initialize visualizer with dataset.
        
        Args:
            dataset: Pandas DataFrame with network data
        """
        self.dataset = dataset
        self.network_graph = None
        self.positions = None
        self._build_network_topology()
    
    def _build_network_topology(self):
        """
        Build network topology from dataset.
        Creates nodes for zones/blocks and edges for pipes.
        """
        G = nx.Graph()
        
        # Extract unique zones and blocks
        zones = self.dataset['Zone'].unique()
        blocks = self.dataset['Block'].unique()
        
        # Add zone nodes (represented as reservoirs/sources)
        for zone in zones:
            G.add_node(zone, node_type='zone', size=30)
        
        # Add block nodes (junctions)
        for block in blocks:
            block_id = f"{block}"
            G.add_node(block_id, node_type='block', size=20)
        
        # Create connections based on dataset pipes
        # Group by pipe to get unique connections
        pipe_groups = self.dataset.groupby(['Zone', 'Block', 'Pipe']).first().reset_index()
        
        for _, row in pipe_groups.iterrows():
            zone = row['Zone']
            block = row['Block']
            pipe = row['Pipe']
            
            # Create edge from zone to block
            edge_id = f"{zone}_{block}_{pipe}"
            G.add_edge(zone, block, pipe_id=edge_id, pipe_name=pipe)
        
        self.network_graph = G
        
        # Create layout using geographic coordinates if available
        self._create_layout()
    
    def _create_layout(self):
        """Create node positions using geographic coordinates or spring layout"""
        # Try geographic layout first
        try:
            positions = {}
            
            # Zone positions (averaged from all pipes in that zone)
            for zone in [n for n, d in self.network_graph.nodes(data=True) if d.get('node_type') == 'zone']:
                zone_data = self.dataset[self.dataset['Zone'] == zone]
                avg_lat = zone_data['Latitude'].mean()
                avg_lon = zone_data['Longitude'].mean()
                # Scale and center
                positions[zone] = (avg_lon, avg_lat)
            
            # Block positions
            for block in [n for n, d in self.network_graph.nodes(data=True) if d.get('node_type') == 'block']:
                block_data = self.dataset[self.dataset['Block'] == block]
                avg_lat = block_data['Latitude'].mean()
                avg_lon = block_data['Longitude'].mean()
                positions[block] = (avg_lon, avg_lat)
            
            self.positions = positions
            
        except Exception:
            # Fall back to spring layout
            self.positions = nx.spring_layout(self.network_graph, k=2, iterations=50)
    
    def create_network_figure(self, pipe_statuses, selected_pipe=None):
        """
        Create interactive Plotly figure showing the network.
        
        Args:
            pipe_statuses: Dict mapping Location_Code to status info
            selected_pipe: Currently selected pipe ID (optional)
        
        Returns:
            Plotly Figure object
        """
        edge_traces = []
        
        # Create edge traces (pipes)
        for edge in self.network_graph.edges(data=True):
            node1, node2, data = edge
            x0, y0 = self.positions[node1]
            x1, y1 = self.positions[node2]
            
            # Get pipe status
            pipe_id = data.get('pipe_id', '')
            status_info = pipe_statuses.get(pipe_id, {})
            status = status_info.get('status', 'NORMAL')
            confidence = status_info.get('confidence', 0)
            flow = status_info.get('flow', 50)
            
            # Determine color based on status and confidence
            if status == 'LEAK':
                if confidence > 60:
                    color = '#ef4444'  # Red
                elif confidence > 30:
                    color = '#f59e0b'  # Yellow/Orange
                else:
                    color = '#10b981'  # Green
            elif status == 'ANOMALY':
                color = '#f59e0b'  # Orange
            else:
                color = '#10b981'  # Green
            
            # Pipe width proportional to flow
            width = max(2, min(flow / 15, 10))
            
            # Highlight if selected
            if selected_pipe and pipe_id == selected_pipe:
                width = width * 1.5
                color = '#8b5cf6'  # Purple for selected
            
            # Create hover text
            hover_text = f"<b>Pipe: {pipe_id}</b><br>"
            hover_text += f"Flow: {flow:.1f} L/min<br>"
            hover_text += f"Status: {status}<br>"
            hover_text += f"Confidence: {confidence:.1f}%"
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=width, color=color),
                hoverinfo='text',
                hovertext=hover_text,
                showlegend=False,
                customdata=[[pipe_id]] * 3  # For click detection
            )
            edge_traces.append(edge_trace)
        
        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        node_hover = []
        
        for node, data in self.network_graph.nodes(data=True):
            x, y = self.positions[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            # Color and size based on node type
            if data.get('node_type') == 'zone':
                node_color.append('#3b82f6')  # Blue for zones
                node_size.append(25)
                node_hover.append(f"<b>Zone: {node}</b><br>Type: Reservoir")
            else:
                node_color.append('#64748b')  # Gray for blocks
                node_size.append(15)
                node_hover.append(f"<b>Block: {node}</b><br>Type: Junction")
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            textfont=dict(size=9, color='#1e293b'),
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white')
            ),
            hoverinfo='text',
            hovertext=node_hover,
            showlegend=False
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title=dict(
                text="Water Distribution Network - Digital Twin View",
                x=0.5,
                xanchor='center',
                font=dict(size=16, color='#1e293b')
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(240,242,245,0.8)',
            paper_bgcolor='white',
            height=500
        )
        
        return fig
    
    def get_active_pipes(self, start_index, window_size=20):
        """
        Get list of active pipes within a time window.
        Useful for populating dropdown selectors in the UI.
        
        Args:
            start_index: Current time index
            window_size: Number of records to look ahead/behind
        
        Returns:
            list: List of pipe IDs (Location_Code) active in this window
        """
        window_start = max(0, start_index - window_size // 2)
        window_end = min(len(self.dataset), start_index + window_size // 2)
        window_data = self.dataset.iloc[window_start:window_end]
        
        active_pipes = sorted(window_data['Location_Code'].unique().tolist())
        return active_pipes
    
    def get_pipe_details(self, pipe_id):
        """
        Get detailed information about a specific pipe.
        
        Args:
            pipe_id: Location_Code of the pipe
        
        Returns:
            dict: Pipe details including connections, length estimate, etc.
        """
        # Parse pipe_id (format: Zone_X_Block_Y_Pipe_Z)
        parts = pipe_id.split('_')
        if len(parts) >= 6:
            zone = f"{parts[0]}_{parts[1]}"
            block = f"{parts[2]}_{parts[3]}"
            pipe = f"{parts[4]}_{parts[5]}"
        else:
            return {'error': 'Invalid pipe ID format'}
        
        # Get pipe data from dataset
        pipe_data = self.dataset[self.dataset['Location_Code'] == pipe_id]
        
        if pipe_data.empty:
            return {'error': 'Pipe not found in dataset'}
        
        # Get first record as representative
        record = pipe_data.iloc[0]
        
        details = {
            'pipe_id': pipe_id,
            'zone': zone,
            'block': block,
            'pipe': pipe,
            'from_node': zone,
            'to_node': block,
            'location': {
                'lat': record['Latitude'],
                'lon': record['Longitude']
            },
            'estimated_length': 1000,  # Default estimate in meters
            'record_count': len(pipe_data)
        }
        
        return details


def test_visualization():
    """Test the visualization module"""
    print("=" * 60)
    print("NETWORK VISUALIZATION - TEST")
    print("=" * 60)
    
    # Load dataset
    print("\n[*] Loading dataset...")
    df = pd.read_csv('data/location_aware_gis_leakage_dataset.csv')
    print(f"[OK] Loaded {len(df)} records")
    
    # Create visualizer
    print("\n[*] Building network topology...")
    viz = NetworkVisualizer(df)
    print(f"[OK] Created network with {viz.network_graph.number_of_nodes()} nodes")
    print(f"[OK] Created network with {viz.network_graph.number_of_edges()} edges")
    
    # Create sample pipe statuses
    print("\n[*] Creating test visualization...")
    pipe_statuses = {}
    
    # Add some sample statuses
    sample_pipes = df['Location_Code'].unique()[:10]
    for i, pipe in enumerate(sample_pipes):
        pipe_statuses[pipe] = {
            'status': 'LEAK' if i % 3 == 0 else 'NORMAL',
            'confidence': 75 if i % 3 == 0 else 10,
            'flow': 50 + i * 5
        }
    
    fig = viz.create_network_figure(pipe_statuses)
    print(f"[OK] Created figure with {len(fig.data)} traces")
    
    # Test pipe details
    print("\n[*] Testing pipe details lookup...")
    sample_pipe = df['Location_Code'].iloc[0]
    details = viz.get_pipe_details(sample_pipe)
    print(f"[OK] Retrieved details for {sample_pipe}")
    print(f"     From: {details.get('from_node')} -> To: {details.get('to_node')}")
    
    print("\n" + "=" * 60)
    print("[OK] Visualization module test passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_visualization()
