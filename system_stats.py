"""
System Stats Module - Real-time system monitoring with beautiful output
"""

import psutil
import platform
from datetime import datetime

class SystemStats:
    def __init__(self):
        self.name = "System Stats"
    
    def get_cpu_stats(self):
        """Get CPU usage statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                'usage_percent': cpu_percent,
                'core_count': cpu_count,
                'frequency_ghz': cpu_freq.current / 1000 if cpu_freq else 0
            }
        except Exception as e:
            print(f"[CPU ERROR] {e}")
            return None
    
    def get_memory_stats(self):
        """Get memory usage statistics"""
        try:
            memory = psutil.virtual_memory()
            
            return {
                'total_gb': memory.total / (1024**3),
                'used_gb': memory.used / (1024**3),
                'available_gb': memory.available / (1024**3),
                'percent': memory.percent
            }
        except Exception as e:
            print(f"[MEMORY ERROR] {e}")
            return None
    
    def get_disk_stats(self):
        """Get disk usage statistics"""
        try:
            disk = psutil.disk_usage('/')
            
            return {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent
            }
        except Exception as e:
            print(f"[DISK ERROR] {e}")
            return None
    
    def get_network_stats(self):
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            
            return {
                'bytes_sent': net_io.bytes_sent / (1024**2),  # MB
                'bytes_recv': net_io.bytes_recv / (1024**2),  # MB
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except Exception as e:
            print(f"[NETWORK ERROR] {e}")
            return None
    
    def get_process_count(self):
        """Get number of running processes"""
        try:
            return len(psutil.pids())
        except Exception as e:
            print(f"[PROCESS ERROR] {e}")
            return 0
    
    def get_top_processes(self, limit=5):
        """Get top CPU/Memory consuming processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
            
            return top_cpu
        except Exception as e:
            print(f"[PROCESS ERROR] {e}")
            return []
    
    def get_battery_status(self):
        """Get battery status if available"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'percent': battery.percent,
                    'secsleft': battery.secsleft,
                    'power_plugged': battery.power_plugged
                }
            return None
        except Exception as e:
            return None
    
    def format_system_stats(self):
        """Format all system stats for display"""
        cpu = self.get_cpu_stats()
        memory = self.get_memory_stats()
        disk = self.get_disk_stats()
        battery = self.get_battery_status()
        process_count = self.get_process_count()
        
        output = "\n" + "="*60
        output += "\n📊 SYSTEM STATS\n"
        output += "="*60 + "\n"
        
        if cpu:
            output += f"💻 CPU Usage: {cpu['usage_percent']}% ({cpu['core_count']} cores @ {cpu['frequency_ghz']:.1f} GHz)\n"
        
        if memory:
            output += f"🧠 Memory: {memory['used_gb']:.1f}GB / {memory['total_gb']:.1f}GB ({memory['percent']}%)\n"
        
        if disk:
            output += f"💾 Disk: {disk['used_gb']:.1f}GB / {disk['total_gb']:.1f}GB ({disk['percent']}%)\n"
        
        output += f"⚙️  Processes: {process_count} running\n"
        
        if battery:
            status = "🔌 Plugged in" if battery['power_plugged'] else "🔋 On battery"
            output += f"🔋 Battery: {battery['percent']}% - {status}\n"
        
        output += "="*60 + "\n"
        
        return output
    
    def speak_system_stats(self, speak_function):
        """Speak system stats to user"""
        cpu = self.get_cpu_stats()
        memory = self.get_memory_stats()
        disk = self.get_disk_stats()
        
        message = f"System stats: "
        
        if cpu:
            message += f"CPU is at {int(cpu['usage_percent'])} percent. "
        
        if memory:
            message += f"Memory is at {int(memory['percent'])} percent with {memory['available_gb']:.1f} gigabytes available. "
        
        if disk:
            message += f"Disk is at {int(disk['percent'])} percent full. "
        
        speak_function(message)
        print(self.format_system_stats())


# Global instance
system_stats = SystemStats()
