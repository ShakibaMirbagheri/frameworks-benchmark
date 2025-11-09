"""
Utility functions for benchmarking
"""
import yaml
import time
import os
from typing import Dict, Any, List
from functools import wraps
import json


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file and set environment variables"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set OpenAI API key as environment variable
    if 'openai' in config and 'api_key' in config['openai']:
        os.environ['OPENAI_API_KEY'] = config['openai']['api_key']
    
    return config


def time_step(step_name: str):
    """Decorator to time a function step"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"\n[STEP] Starting: {step_name}")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                print(f"[STEP] Completed: {step_name} - Time: {elapsed_time:.4f}s")
                return result, elapsed_time
            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"[STEP] Failed: {step_name} - Time: {elapsed_time:.4f}s - Error: {str(e)}")
                raise
                
        return wrapper
    return decorator


class BenchmarkLogger:
    """Logger for benchmark results"""
    
    def __init__(self, framework_name: str):
        self.framework_name = framework_name
        self.steps: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """Start benchmark"""
        self.start_time = time.time()
        print(f"\n{'='*60}")
        print(f"BENCHMARK: {self.framework_name}")
        print(f"{'='*60}")
        
    def log_step(self, step_name: str, duration: float, details: str = ""):
        """Log a step"""
        step_info = {
            "step": step_name,
            "duration": duration,
            "details": details,
            "timestamp": time.time()
        }
        self.steps.append(step_info)
        print(f"  → {step_name}: {duration:.4f}s {f'({details})' if details else ''}")
        
    def end(self):
        """End benchmark"""
        self.end_time = time.time()
        total_time = self.end_time - self.start_time
        print(f"\n{'='*60}")
        print(f"Total Time: {total_time:.4f}s")
        print(f"{'='*60}\n")
        return total_time
        
    def get_results(self) -> Dict[str, Any]:
        """Get benchmark results"""
        return {
            "framework": self.framework_name,
            "total_time": self.end_time - self.start_time if self.end_time else 0,
            "steps": self.steps,
            "step_count": len(self.steps)
        }
        
    def save_results(self, filename: str):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.get_results(), f, indent=2)

