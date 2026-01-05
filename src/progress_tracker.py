import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np


class ProgressTracker:
    """Track and visualize study progress"""

    def __init__(self, progress_dir: str):
        self.progress_dir = progress_dir
        self.progress_file = os.path.join(progress_dir, "progress.json")
        self.load_progress()

    def load_progress(self):
        """Load progress data"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "study_sessions": [],
                "quiz_results": [],
                "documents_loaded": [],
                "total_study_hours": 0,
                "start_date": datetime.now().isoformat()
            }

    def save_progress(self):
        """Save progress data"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def update_study_session(self, duration_minutes: int, topic: str, notes: str = ""):
        """Record a study session"""
        session = {
            "date": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "topic": topic,
            "notes": notes
        }

        self.data["study_sessions"].append(session)
        self.data["total_study_hours"] += duration_minutes /
