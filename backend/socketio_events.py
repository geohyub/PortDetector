"""SocketIO event handlers."""

import threading


def register_socketio_events(socketio, scan_worker, scheduler):

    @socketio.on('connect')
    def handle_connect():
        pass

    @socketio.on('request_scan')
    def handle_scan(data):
        ip = data.get('ip', '')
        ports = data.get('ports', '1-1024')
        protocol = data.get('protocol', 'tcp')
        if ip:
            scan_worker.scan(ip, ports, protocol)

    @socketio.on('update_interval')
    def handle_update_interval(data):
        ping_interval = data.get('ping_interval')
        interface_interval = data.get('interface_interval')
        if ping_interval:
            scheduler.ping_worker.update_interval(int(ping_interval))
        if interface_interval:
            scheduler.interface_worker.update_interval(int(interface_interval))

    @socketio.on('request_traceroute')
    def handle_traceroute(data):
        ip = data.get('ip', '')
        if not ip:
            return

        def run_trace():
            from backend.services.traceroute_service import traceroute
            hops = traceroute(ip)
            socketio.emit('traceroute_complete', {'ip': ip, 'hops': hops})

        t = threading.Thread(target=run_trace, daemon=True)
        t.start()
        socketio.emit('traceroute_started', {'ip': ip})

    @socketio.on('request_discovery')
    def handle_discovery(data):
        subnet = data.get('subnet', '')
        if not subnet:
            from backend.services.discovery_service import get_local_subnet
            subnet = get_local_subnet()

        def run_discovery():
            from backend.services.discovery_service import discover_subnet

            def on_progress(scanned, total, found):
                socketio.emit('discovery_progress', {
                    'scanned': scanned, 'total': total, 'found': len(found),
                })

            results = discover_subnet(subnet, timeout_ms=500, callback=on_progress)
            socketio.emit('discovery_complete', {
                'subnet': subnet, 'hosts': results, 'total_found': len(results),
            })

        t = threading.Thread(target=run_discovery, daemon=True)
        t.start()
        socketio.emit('discovery_started', {'subnet': subnet})
