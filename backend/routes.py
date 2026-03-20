"""Flask REST API routes."""

import threading
from datetime import datetime
from flask import Blueprint, request, jsonify

from backend.models.device import Device

api = Blueprint('api', __name__)

# These will be set by app.py
config_service = None
log_service = None
scan_worker = None
interface_worker = None
ping_worker = None
socketio_ref = None
traffic_service = None


def init_routes(cfg_svc, log_svc, scan_wkr, iface_wkr, ping_wkr=None, sio=None, traf_svc=None):
    global config_service, log_service, scan_worker, interface_worker, ping_worker, socketio_ref, traffic_service
    config_service = cfg_svc
    log_service = log_svc
    scan_worker = scan_wkr
    interface_worker = iface_wkr
    ping_worker = ping_wkr
    socketio_ref = sio
    traffic_service = traf_svc


@api.route('/api/devices', methods=['GET'])
def get_devices():
    devices = config_service.get_devices()
    return jsonify([d.to_dict() for d in devices])


@api.route('/api/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    device = Device.from_dict(data)
    try:
        device = config_service.add_device(device)
        return jsonify(device.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api.route('/api/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    try:
        device = config_service.update_device(device_id, data)
        if device:
            return jsonify(device.to_dict())
        return jsonify({'error': 'Device not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    if config_service.delete_device(device_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Device not found'}), 404


@api.route('/api/devices/export', methods=['GET'])
def export_config():
    return jsonify(config_service.export_config())


@api.route('/api/devices/import', methods=['POST'])
def import_config():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    config_service.import_config(data)
    return jsonify({'success': True})


@api.route('/api/scan', methods=['POST'])
def start_scan():
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({'error': 'IP required'}), 400
    ip = data['ip']
    ports = data.get('ports', '1-1024')
    protocol = data.get('protocol', 'tcp')
    scan_worker.scan(ip, ports, protocol)
    return jsonify({'status': 'scanning', 'ip': ip})


@api.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    return jsonify(interface_worker.get_interfaces())


@api.route('/api/traffic', methods=['GET'])
def get_traffic():
    """Get per-device traffic data."""
    if not traffic_service or not traffic_service.is_available():
        return jsonify({'available': False, 'devices': {}})

    devices = config_service.get_enabled_devices()
    device_ips = [d.ip for d in devices]
    traffic_data = traffic_service.get_device_traffic(device_ips)
    return jsonify({'available': True, 'devices': traffic_data})


@api.route('/api/history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    device_id = request.args.get('device_id')
    entries = log_service.get_history(limit=limit, offset=offset, device_id=device_id)
    return jsonify(entries)


@api.route('/api/history/export', methods=['GET'])
def export_history():
    entries = log_service.get_all_entries()
    if not entries:
        return jsonify([])
    return jsonify(entries)


@api.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(config_service.get_settings())


@api.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    settings = config_service.update_settings(data)
    return jsonify(settings)


@api.route('/api/status', methods=['GET'])
def app_status():
    from config import VERSION, APP_NAME
    return jsonify({'app': APP_NAME, 'version': VERSION, 'status': 'running'})


@api.route('/api/ping-history', methods=['GET'])
def get_ping_history():
    """Get RTT history for graphing."""
    if ping_worker:
        return jsonify(ping_worker.get_rtt_history())
    return jsonify({})


@api.route('/api/discover', methods=['POST'])
def discover():
    """Start subnet auto-discovery."""
    data = request.get_json() or {}
    from backend.services.discovery_service import get_local_subnet, discover_subnet

    subnet = data.get('subnet', get_local_subnet())
    timeout = data.get('timeout', 500)

    def run_discovery():
        def on_progress(scanned, total, found):
            if socketio_ref:
                socketio_ref.emit('discovery_progress', {
                    'scanned': scanned, 'total': total, 'found': len(found),
                })

        results = discover_subnet(subnet, timeout_ms=timeout, callback=on_progress)
        if socketio_ref:
            socketio_ref.emit('discovery_complete', {
                'subnet': subnet, 'hosts': results, 'total_found': len(results),
            })

    t = threading.Thread(target=run_discovery, daemon=True)
    t.start()
    return jsonify({'status': 'scanning', 'subnet': subnet})


@api.route('/api/traceroute', methods=['POST'])
def run_traceroute():
    """Run traceroute to target IP."""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({'error': 'IP required'}), 400

    ip = data['ip']

    def run_trace():
        from backend.services.traceroute_service import traceroute
        hops = traceroute(ip)
        if socketio_ref:
            socketio_ref.emit('traceroute_complete', {'ip': ip, 'hops': hops})

    t = threading.Thread(target=run_trace, daemon=True)
    t.start()
    return jsonify({'status': 'tracing', 'ip': ip})


@api.route('/api/report', methods=['GET'])
def generate_report():
    """Generate status report data."""
    devices = config_service.get_devices()
    interfaces_data = interface_worker.get_interfaces()
    rtt_history = ping_worker.get_rtt_history() if ping_worker else {}
    history = log_service.get_history(limit=50)

    ping_data = {}
    if ping_worker:
        ping_data = ping_worker.get_current_status()

    report = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'devices': [],
        'interfaces': interfaces_data,
        'recent_events': history,
        'summary': {'total': 0, 'online': 0, 'offline': 0, 'delayed': 0},
    }

    for d in devices:
        status_info = ping_data.get(d.id, {})
        dev_report = d.to_dict()
        dev_report['status'] = status_info.get('status', 'unknown')
        dev_report['rtt_ms'] = status_info.get('rtt_ms')
        report['devices'].append(dev_report)

        report['summary']['total'] += 1
        s = dev_report['status']
        if s == 'connected':
            report['summary']['online'] += 1
        elif s == 'disconnected':
            report['summary']['offline'] += 1
        elif s == 'delayed':
            report['summary']['delayed'] += 1

    return jsonify(report)
