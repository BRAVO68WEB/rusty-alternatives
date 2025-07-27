"""
Utility functions for the railway finder application.
"""

import pickle
from typing import Any, Optional
from pathlib import Path
import networkx as nx


def save_network(network: nx.Graph, filepath: str) -> None:
    """Save a NetworkX graph to a pickle file."""
    with open(filepath, 'wb') as f:
        pickle.dump(network, f)


def load_network(filepath: str) -> Optional[nx.Graph]:
    """Load a NetworkX graph from a pickle file."""
    try:
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    except (FileNotFoundError, pickle.PickleError):
        return None


def format_distance(distance_km: float) -> str:
    """Format distance in a human-readable way."""
    if distance_km < 1:
        return f"{distance_km * 1000:.0f} m"
    else:
        return f"{distance_km:.1f} km"


def validate_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()


def ensure_directory_exists(filepath: str) -> None:
    """Ensure the directory for a file path exists."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)