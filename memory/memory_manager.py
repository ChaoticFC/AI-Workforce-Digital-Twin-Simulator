"""Persistent Memory Management"""
import json
import os
from datetime import datetime
from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MemoryManager:
    """Manages persistent memory for all agents"""
    
    def __init__(self):
        self.memory_dir = "memory"
        self.data_dir = "data"
        self.ensure_directories()
        self.cycles_file = os.path.join(self.data_dir, "cycles.json")
        self.memory_index = self._load_memory_index()
    
    def ensure_directories(self):
        """Create memory directories if they don't exist"""
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_memory_index(self) -> Dict:
        """Load the memory index"""
        if os.path.exists(self.cycles_file):
            try:
                with open(self.cycles_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load memory index: {e}")
                return {"cycles": [], "total_cycles": 0}
        return {"cycles": [], "total_cycles": 0}
    
    def _save_memory_index(self):
        """Save the memory index"""
        try:
            with open(self.cycles_file, 'w') as f:
                json.dump(self.memory_index, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save memory index: {e}")
    
    def update(self, cycle_data: Dict, reflection: Dict):
        """Update memory with new cycle information"""        
        logger.info(f"Updating memory for cycle {cycle_data['cycle']}")
        
        # Save cycle data
        cycle_file = os.path.join(
            self.data_dir, 
            f"cycle_{cycle_data['cycle']}.json"
        )
        
        try:
            with open(cycle_file, 'w') as f:
                json.dump({
                    "cycle_data": cycle_data,
                    "reflection": reflection
                }, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save cycle data: {e}")
            return
        
        # Update memory index
        self.memory_index["cycles"].append({
            "cycle": cycle_data['cycle'],
            "timestamp": cycle_data['timestamp'],
            "goal": cycle_data['user_goal'],
            "file": cycle_file,
            "score": cycle_data['stages']['evaluation'].get('score', 0.0)
        })
        self.memory_index["total_cycles"] = cycle_data['cycle']
        self._save_memory_index()
        
        logger.info("Memory updated successfully")
    
    def get_context(self, num_previous_cycles: int = 3) -> str:
        """Get context from previous cycles for agent decision making"""        
        context = "## Previous Cycles Summary\n\n"
        
        if not self.memory_index["cycles"]:
            return context + "No previous cycles available.\n"
        
        # Get the most recent cycles
        recent_cycles = self.memory_index["cycles"][-num_previous_cycles:]
        
        for cycle_info in recent_cycles:
            context += f"### Cycle {cycle_info['cycle']}\n"
            context += f"Goal: {cycle_info['goal']}\n"
            context += f"Performance Score: {cycle_info['score']}\n"
            context += f"Date: {cycle_info['timestamp']}\n\n"
        
        return context
    
    def get_performance_history(self) -> List[float]:
        """Get all performance scores"""
        return [
            cycle['score'] 
            for cycle in self.memory_index['cycles']
        ]
    
    def get_statistics(self) -> Dict:
        """Get memory statistics"""
        scores = self.get_performance_history()
        
        if not scores:
            return {
                "total_cycles": 0,
                "average_score": 0.0,
                "best_score": 0.0,
                "improvement": 0.0
            }
        
        return {
            "total_cycles": len(scores),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "improvement": scores[-1] - scores[0] if len(scores) > 1 else 0.0
        }