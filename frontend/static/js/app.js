/* App initialization, navigation, keyboard shortcuts, and reconnection */

var App = {
    socket: null,

    init: function() {
        AlertSound.init();
        this.initSocket();
        this.initNavigation();
        this.initKeyboardShortcuts();
        this.loadDevices();
    },

    initSocket: function() {
        this.socket = io({ reconnection: true, reconnectionDelay: 1000, reconnectionAttempts: Infinity });

        this.socket.on('connect', function() {
            var el = document.getElementById('connection-status');
            el.innerHTML = '<span class="status-dot connected"></span><span>연결됨</span>';
        });

        this.socket.on('disconnect', function() {
            var el = document.getElementById('connection-status');
            el.innerHTML = '<span class="status-dot disconnected"></span><span>연결 안됨</span>';
        });

        this.socket.on('reconnect', function() {
            Utils.showToast('서버 재연결 완료', 'success');
            App.loadDevices();
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

            // Play alert sound on disconnect, pleasant chime on reconnect
            if (data.new_status === 'disconnected') {
                AlertSound.play('disconnect');
            } else if (data.new_status === 'connected' && data.old_status === 'disconnected') {
                AlertSound.play('reconnect');
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

    initKeyboardShortcuts: function() {
        document.addEventListener('keydown', function(e) {
            // Skip if typing in input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

            switch (e.key) {
                case '1': App.navigateTo('dashboard'); break;
                case '2': App.navigateTo('scanner'); break;
                case '3': App.navigateTo('discovery'); break;
                case '4': App.navigateTo('traceroute'); break;
                case '5': App.navigateTo('interfaces'); break;
                case '6': App.navigateTo('history'); break;
                case '7': App.navigateTo('settings'); break;
                case 'r': case 'R':
                    if (!e.ctrlKey && !e.metaKey) {
                        App.loadDevices();
                        Utils.showToast('새로고침 완료', 'info');
                    }
                    break;
                case 'g': case 'G':
                    Dashboard.toggleGraph();
                    break;
                case 'n': case 'N':
                    Devices.showAddModal();
                    break;
            }
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
            // Load sparkline data
            Dashboard.refreshSparklines();
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Auto-refresh per-device traffic every 5 seconds (skip if tab hidden)
setInterval(function() {
    if (!document.hidden) Dashboard.updateTraffic();
}, 5000);

// Auto-refresh sparklines every 10 seconds (skip if tab hidden)
setInterval(function() {
    if (!document.hidden) Dashboard.refreshSparklines();
}, 10000);

// Auto-refresh uptime display every 30 seconds
setInterval(function() {
    if (document.hidden) return;
    var uptimeEls = document.querySelectorAll('.device-card-uptime');
    uptimeEls.forEach(function(el) {
        var card = el.closest('.device-card');
        if (!card) return;
        var devId = card.getAttribute('data-id');
        var status = card.getAttribute('data-status');
        el.innerHTML = Dashboard._getUptimeHtml(devId, status);
    });
}, 30000);
