"""
Dashboard Server - Web UI for JARVIS Assistant
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import threading
import os

# Create Flask app with correct template folder
app = Flask(__name__, template_folder='ui', static_folder='ui')
CORS(app)

# Import modules
from system_stats import system_stats
from alerts_manager import alerts_manager
from event_tracker import event_tracker
from workflow_manager import workflow_manager

class DashboardServer:
    def __init__(self, port=5000):
        self.port = port
        self.running = False
    
    def start(self):
        """Start the dashboard server"""
        self.running = True
        thread = threading.Thread(target=self._run_server, daemon=True)
        thread.start()
        print(f"[DASHBOARD] Server starting on http://localhost:{self.port}")
    
    def _run_server(self):
        """Run Flask server"""
        try:
            app.run(host='localhost', port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            print(f"[DASHBOARD ERROR] {e}")

# API Routes
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        cpu = system_stats.get_cpu_stats()
        memory = system_stats.get_memory_stats()
        disk = system_stats.get_disk_stats()
        battery = system_stats.get_battery_status()
        processes = system_stats.get_top_processes(5)
        
        return jsonify({
            'success': True,
            'cpu': cpu,
            'memory': memory,
            'disk': disk,
            'battery': battery,
            'processes': processes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    try:
        return jsonify({
            'success': True,
            'alerts': alerts_manager.alerts,
            'count': len(alerts_manager.alerts)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.json
        title = data.get('title')
        alert_type = data.get('type', 'reminder')
        minutes = data.get('minutes', 10)
        details = data.get('details', '')
        
        alert = alerts_manager.create_alert(title, alert_type, minutes, details)
        return jsonify({'success': True, 'alert': alert})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        alerts_manager.delete_alert(alert_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get recent events"""
    try:
        minutes = request.args.get('minutes', 60, type=int)
        events = event_tracker.get_events_since(minutes)
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get all workflows"""
    try:
        return jsonify({
            'success': True,
            'workflows': workflow_manager.workflows,
            'count': len(workflow_manager.workflows)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'success': True,
        'status': 'online',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

# Global dashboard instance
dashboard_server = DashboardServer(port=5000)

def start_dashboard():
    """Start the dashboard"""
    dashboard_server.start()

if __name__ == '__main__':
    dashboard_server.start()
