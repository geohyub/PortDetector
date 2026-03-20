/* Network Interfaces monitoring + Per-device traffic */

var Interfaces = {
    load: function() {
        Utils.api('GET', '/api/interfaces').then(function(data) {
            Interfaces.update(data);
        });
        this.loadTraffic();
    },

    update: function(interfaces) {
        var tbody = document.getElementById('interfaces-body');
        if (!tbody) return;

        var html = '';
        for (var i = 0; i < interfaces.length; i++) {
            var iface = interfaces[i];
            var statusBadge = iface.is_up ?
                '<span class="badge badge-up">UP</span>' :
                '<span class="badge badge-down">DOWN</span>';

            html += '<tr' + (iface.is_up ? '' : ' style="opacity:0.5"') + '>';
            html += '<td><strong>' + Utils.escapeHtml(iface.name) + '</strong></td>';
            html += '<td>' + statusBadge + '</td>';
            html += '<td>' + (iface.speed_mbps > 0 ? iface.speed_mbps + ' Mbps' : '-') + '</td>';
            html += '<td style="font-family:Consolas,monospace">' + (iface.ipv4 || '-') + '</td>';
            html += '<td>' + Utils.formatBytes(iface.bytes_recv) + '</td>';
            html += '<td>' + Utils.formatBytes(iface.bytes_sent) + '</td>';
            html += '<td style="color:var(--status-green)">' + Utils.formatSpeed(iface.throughput_in) + '</td>';
            html += '<td style="color:var(--accent)">' + Utils.formatSpeed(iface.throughput_out) + '</td>';
            html += '</tr>';
        }
        tbody.innerHTML = html;
    },

    loadTraffic: function() {
        Utils.api('GET', '/api/traffic').then(function(data) {
            var notice = document.getElementById('device-traffic-notice');
            var table = document.getElementById('device-traffic-table');

            if (!data.available) {
                notice.textContent = '관리자 권한으로 실행하면 장비별 트래픽을 확인할 수 있습니다. (우클릭 → 관리자 권한으로 실행)';
                table.style.display = 'none';
                return;
            }

            notice.textContent = '실시간 장비별 트래픽 (5초마다 갱신)';
            table.style.display = 'table';

            var tbody = document.getElementById('device-traffic-body');
            var ips = Object.keys(data.devices).sort();

            if (ips.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">아직 트래픽 데이터가 없습니다</td></tr>';
                return;
            }

            var html = '';
            for (var i = 0; i < ips.length; i++) {
                var ip = ips[i];
                var t = data.devices[ip];
                html += '<tr>';
                html += '<td style="font-family:Consolas,monospace;color:var(--accent)">' + ip + '</td>';
                html += '<td style="color:var(--status-green)">' + Utils.formatSpeed(t.rate_in) + '</td>';
                html += '<td style="color:var(--accent)">' + Utils.formatSpeed(t.rate_out) + '</td>';
                html += '<td>' + Utils.formatBytes(t.bytes_in) + '</td>';
                html += '<td>' + Utils.formatBytes(t.bytes_out) + '</td>';
                html += '<td>' + t.packets_in + '</td>';
                html += '<td>' + t.packets_out + '</td>';
                html += '</tr>';
            }
            tbody.innerHTML = html;
        });
    }
};

// Auto-refresh device traffic on interfaces page
setInterval(function() {
    var page = document.getElementById('page-interfaces');
    if (page && page.classList.contains('active')) {
        Interfaces.loadTraffic();
    }
}, 5000);
