"""
System Features Module - Restored
System-level features and utilities
"""

import os
import psutil
import platform

class SystemFeatures:
    def __init__(self):
        self.name = "System Features"
    
    def get_system_info(self):
        """Get system information"""
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'processor': platform.processor(),
            'cpu_count': os.cpu_count(),
        }
        return info
    
    def get_resource_usage(self):
        """Get CPU and memory usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available / (1024**3)  # GB
            }
        except Exception as e:
            print(f"[SYSTEM ERROR] {e}")
            return None
    
    def get_disk_usage(self):
        """Get disk usage"""
        try:
            usage = psutil.disk_usage('/')
            return {
                'total': usage.total / (1024**3),  # GB
                'used': usage.used / (1024**3),
                'percent': usage.percent
            }
        except Exception as e:
            print(f"[DISK ERROR] {e}")
            return None
    
    def optimize_system(self):
        """Optimize system performance"""
        print("[SYSTEM] Running optimization...")
        # Optimization logic here
        return True
    
    def check_system_health(self):
        """Check overall system health"""
        health = {
            'cpu': psutil.cpu_percent(interval=1) < 80,
            'memory': psutil.virtual_memory().percent < 80,
            'disk': psutil.disk_usage('/').percent < 80,
        }
        return health

# Global system features instance
system_features = SystemFeatures()
