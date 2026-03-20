/* Network Auto-Discovery */

var Discovery = {
    scanning: false,

    start: function() {
        if (this.scanning) return;
        this.scanning = true;

        var subnet = document.getElementById('discovery-subnet').value.trim();
        document.getElementById('discovery-results-body').innerHTML = '';
        document.getElementById('discovery-progress').style.display = 'block';
        document.getElementById('discovery-progress-fill').style.width = '0%';
        document.getElementById('discovery-progress-text').textContent = '탐색 중...';
        document.getElementById('discovery-btn').textContent = '탐색 중...';
        document.getElementById('discovery-btn').disabled = true;

        App.socket.emit('request_discovery', { subnet: subnet });
    },

    onProgress: function(data) {
        var pct = data.total > 0 ? Math.round(data.scanned / data.total * 100) : 0;
        document.getElementById('discovery-progress-fill').style.width = pct + '%';
        document.getElementById('discovery-progress-text').textContent =
            data.scanned + ' / ' + data.total + ' 스캔 완료 (' + data.found + '개 발견)';
    },

    onComplete: function(data) {
        this.scanning = false;
        document.getElementById('discovery-btn').textContent = '탐색 시작';
        document.getElementById('discovery-btn').disabled = false;
        document.getElementById('discovery-progress-fill').style.width = '100%';

        var tbody = document.getElementById('discovery-results-body');
        if (!data.hosts || data.hosts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">발견된 호스트가 없습니다</td></tr>';
            return;
        }

        var html = '';
        for (var i = 0; i < data.hosts.length; i++) {
            var h = data.hosts[i];
            html += '<tr>';
            html += '<td style="font-family:Consolas,monospace">' + Utils.escapeHtml(h.ip) + '</td>';
            html += '<td>' + Utils.escapeHtml(h.hostname || '-') + '</td>';
            html += '<td>' + (h.rtt_ms !== null ? h.rtt_ms + 'ms' : '-') + '</td>';
            html += '<td><button class="btn btn-sm btn-primary" onclick="Discovery.addDevice(\'' +
                    Utils.escapeHtml(h.ip) + '\',\'' + Utils.escapeHtml(h.hostname || '') +
                    '\')">장비 등록</button></td>';
            html += '</tr>';
        }
        tbody.innerHTML = html;

        Utils.showToast(data.total_found + '개 호스트 발견 완료', 'success');
    },

    addDevice: function(ip, hostname) {
        document.getElementById('device-edit-id').value = '';
        document.getElementById('device-name').value = hostname || ip;
        document.getElementById('device-ip').value = ip;
        document.getElementById('device-ports').value = '';
        document.getElementById('device-category').value = '';
        document.getElementById('device-description').value = '자동 탐색으로 발견';
        document.getElementById('device-enabled').checked = true;
        document.getElementById('modal-title').textContent = '장비 추가';
        document.getElementById('device-modal').style.display = 'flex';
    }
};
