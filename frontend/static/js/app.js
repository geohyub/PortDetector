/* App initialization and navigation */

var App = {
    socket: null,

    init: function() {
        AlertSound.init();
        this.initSocket();
        this.initNavigation();
        this.loadDevices();
    },

    initSocket: function() {
        this.socket = io();

        this.socket.on('connect', function() {
            var el = document.getElementById('connection-status');
            el.innerHTML = '<span class="status-dot connected"></span><span>연결됨</span>';
        });

        this.socket.on('disconnect', function() {
            var el = document.getElementById('connection-status');
            el.innerHTML = '<span class="status-dot disconnected"></span><span>연결 안됨</span>';
        });

        // Ping updates
        this.socket.on('batch_ping_update', function(results) {
            Dashboard.updatePingResults(results);
        });

        // Status changes
        this.socket.on('status_change', function(data) {
            var statusKo = data.new_status === 'connected' ? '연결' :
                           data.new_status === 'disconnected' ? '끊김' : '지연';
            var msg = data.name + ' (' + data.ip + ') → ' + statusKo;
            var type = data.new_status === 'connected' ? 'success' :
                       data.new_status === 'disconnected' ? 'error' : 'warning';
            Utils.showToast(msg, type);

            // Play alert sound on disconnect
            if (data.new_status === 'disconnected') {
                AlertSound.play();
            }
        });

        // Port scan
        this.socket.on('scan_result', function(data) { Scanner.addResult(data); });
        this.socket.on('scan_progress', function(data) { Scanner.updateProgress(data); });
        this.socket.on('scan_complete', function(data) { Scanner.onComplete(data); });

        // Interface updates
        this.socket.on('interface_update', function(data) { Interfaces.update(data.interfaces); });

        // Discovery
        this.socket.on('discovery_progress', function(data) { Discovery.onProgress(data); });
        this.socket.on('discovery_complete', function(data) { Discovery.onComplete(data); });

        // Traceroute
        this.socket.on('traceroute_started', function(data) {
            document.getElementById('traceroute-status').textContent = data.ip + ' 경로 추적 중...';
        });
        this.socket.on('traceroute_complete', function(data) { Traceroute.onComplete(data); });
    },

    initNavigation: function() {
        var items = document.querySelectorAll('.nav-item');
        items.forEach(function(item) {
            item.addEventListener('click', function() {
                var page = this.getAttribute('data-page');
                App.navigateTo(page);
            });
        });
    },

    navigateTo: function(page) {
        document.querySelectorAll('.nav-item').forEach(function(el) {
            el.classList.toggle('active', el.getAttribute('data-page') === page);
        });
        document.querySelectorAll('.page').forEach(function(el) {
            el.classList.toggle('active', el.id === 'page-' + page);
        });
        if (page === 'history') History.loadHistory();
        if (page === 'settings') Settings.loadSettings();
        if (page === 'interfaces') Interfaces.load();
    },

    loadDevices: function() {
        Utils.api('GET', '/api/devices').then(function(devices) {
            Dashboard.renderDevices(devices);
            History.populateFilter(devices);
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Auto-refresh per-device traffic every 5 seconds
setInterval(function() {
    Dashboard.updateTraffic();
}, 5000);
