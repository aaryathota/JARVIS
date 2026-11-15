"""
Dashboard Server - Web UI for JARVIS Assistant
"""

from flask import Flask, render_template, jsonify, request, redirect, send_from_directory
from flask_cors import CORS
import json
import threading
import os

# Create Flask app with correct template folder
import os
UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui')
app = Flask(__name__, template_folder=UI_DIR, static_folder=UI_DIR)
CORS(app)

# Import modules
from system_stats import system_stats
from alerts_manager import alerts_manager
from event_tracker import event_tracker
from workflow_manager import workflow_manager
from discovery import load_channels
from analytics import performance_summary
from instagram_graph import exchange_code, login_url

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


@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Return the permitted clipping allowlist."""
    try:
        return jsonify({'success': True, 'channels': [channel.__dict__ for channel in load_channels()]})
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500


@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Return locally stored clip performance summaries."""
    try:
        return jsonify({'success': True, 'performance': performance_summary()})
    except Exception as error:
        return jsonify({'success': False, 'error': str(error)}), 500


@app.route('/instagram/login', methods=['GET'])
def instagram_login():
    """Start official Instagram Login."""
    return redirect(login_url())


@app.route('/instagram/callback', methods=['GET'])
def instagram_callback():
    """Exchange Meta's OAuth code and save the local token without displaying it."""
    if request.args.get('error'):
        return f"Instagram login cancelled: {request.args.get('error_description', 'access denied')}", 400
    code = request.args.get('code', '')
    if not code:
        return "Instagram did not return an authorization code.", 400
    try:
        token_data = exchange_code(code)
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        values = {
            'INSTAGRAM_ACCESS_TOKEN': token_data.get('access_token', ''),
            'INSTAGRAM_USER_ID': str(token_data.get('user_id', '')),
        }
        os.environ.update(values)
        existing = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if '=' in line and not line.lstrip().startswith('#'):
                        key, value = line.rstrip('\n').split('=', 1)
                        existing[key] = value
        existing.update(values)
        with open(env_path, 'w', encoding='utf-8') as file:
            for key, value in existing.items():
                file.write(f"{key}={value}\n")
        return "Instagram connected successfully. You can close this tab and restart JARVIS.", 200
    except Exception as error:
        print(f"[INSTAGRAM OAUTH] Callback failed: {error}")
        return "Instagram connection failed. Check the JARVIS terminal log.", 500


@app.route('/instagram/media/<path:filename>', methods=['GET'])
def instagram_media(filename):
    """Serve a temporary clip to Meta during Reel processing."""
    clips_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clips')
    return send_from_directory(clips_dir, filename, max_age=60)

# ---------------- Shorts Studio (control the Shorts creator from the UI) ----------------
import job_status


def _shorts_worker(url, clips, privacy):
    from clip_automation import create_and_upload_clips_from_video
    create_and_upload_clips_from_video(url, num_clips=clips, privacy_status=privacy)


def _daily_worker(limit, dry_run):
    from daily import run_daily_clips
    run_daily_clips(limit=limit, dry_run=dry_run)


@app.route('/api/shorts', methods=['POST'])
def start_shorts():
    """Start creating Shorts from a YouTube URL"""
    data = request.json or {}
    url = str(data.get('url', '')).strip()
    try:
        clips = max(1, min(int(data.get('clips', 2)), 10))
    except (TypeError, ValueError):
        clips = 2
    privacy = data.get('privacy', 'public')
    if privacy not in ('public', 'unlisted', 'private'):
        privacy = 'public'
    if not url.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'error': 'Paste a valid video link'}), 400
    if job_status.is_running():
        return jsonify({'success': False, 'error': 'A Shorts job is already running'}), 409
    job_status.start(clips, url)
    threading.Thread(target=_shorts_worker, args=(url, clips, privacy), daemon=True).start()
    return jsonify({'success': True})


@app.route('/api/shorts/status', methods=['GET'])
def shorts_status():
    """Live step, per-clip progress and log of the Shorts job (also shows voice-started jobs)"""
    snap = job_status.snapshot()
    snap['success'] = True
    return jsonify(snap)


@app.route('/api/daily-clips', methods=['POST'])
def start_daily_clips():
    """Start the unattended daily Shorts batch from the dashboard."""
    data = request.json or {}
    try:
        limit = max(1, min(int(data.get('limit', 10)), 10))
    except (TypeError, ValueError):
        limit = 10
    dry_run = bool(data.get('dry_run', False))
    if job_status.is_running():
        return jsonify({'success': False, 'error': 'A Shorts job is already running'}), 409
    job_status.start(limit, 'daily discovery')
    threading.Thread(target=_daily_worker, args=(limit, dry_run), daemon=True).start()
    return jsonify({'success': True, 'dry_run': dry_run, 'limit': limit})


@app.route('/')
def dashboard():
    """Main dashboard page"""
    if not os.path.isfile(os.path.join(UI_DIR, 'dashboard.html')):
        try:
            found = sorted(os.listdir(UI_DIR)) if os.path.isdir(UI_DIR) else None
        except Exception:
            found = None
        listing = ("The folder exists but contains: " + ", ".join(found or ["(empty)"])) if found is not None else "That folder does not exist yet."
        return (
            "<body style='background:#04060d;color:#d6f3ff;font:16px Segoe UI,sans-serif;padding:40px'>"
            "<h2 style='color:#22e4ff'>Dashboard file not found</h2>"
            f"<p>Put <b>dashboard.html</b> exactly here:</p><pre style='color:#3dffa2'>{os.path.join(UI_DIR, 'dashboard.html')}</pre>"
            f"<p>{listing}</p><p>Then refresh this page.</p></body>"
        ), 404
    return render_template('dashboard.html')

# Global dashboard instance
dashboard_server = DashboardServer(port=5000)

def start_dashboard():
    """Start the dashboard"""
    dashboard_server.start()

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=False, use_reloader=False)