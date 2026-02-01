import time
from functools import wraps

class PerformanceMonitor:
    """Monitor query processing performance"""
    
    def __init__(self):
        self.metrics = {
            'queries_processed': 0,
            'total_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def track_query(self, func):
        """Decorator to track query performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            self.metrics['queries_processed'] += 1
            self.metrics['total_time'] += elapsed
            
            return result
        return wrapper
    
    def get_stats(self):
        """Get performance statistics"""
        if self.metrics['queries_processed'] == 0:
            return {
                'queries_processed': 0,
                'average_time': 0,
                'cache_hit_rate': 0
            }
        
        total_cache_operations = self.metrics['cache_hits'] + self.metrics['cache_misses']
        
        return {
            'queries_processed': self.metrics['queries_processed'],
            'average_time': self.metrics['total_time'] / self.metrics['queries_processed'],
            'cache_hit_rate': (self.metrics['cache_hits'] / total_cache_operations * 100) 
                             if total_cache_operations > 0 else 0
        }

# Global monitor instance
perf_monitor = PerformanceMonitor()