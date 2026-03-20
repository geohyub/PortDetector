/* History / Event Log */

var History = {
    currentPage: 0,
    pageSize: 50,

    populateFilter: function(devices) {
        var select = document.getElementById('history-filter');
        while (select.options.length > 1) select.remove(1);
        for (var i = 0; i < devices.length; i++) {
            var opt = document.createElement('option');
            opt.value = devices[i].id;
            opt.textContent = devices[i].name + ' (' + devices[i].ip + ')';
            select.appendChild(opt);
        }
    },

    loadHistory: function() {
        var deviceId = document.getElementById('history-filter').value;
        var offset = this.currentPage * this.pageSize;
        var url = '/api/history?limit=' + this.pageSize + '&offset=' + offset;
        if (deviceId) url += '&device_id=' + deviceId;

        Utils.api('GET', url).then(function(entries) {
            History.renderEntries(entries);
        });
    },

    renderEntries: function(entries) {
        var tbody = document.getElementById('history-body');
        if (!entries || entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted)">아직 기록된 이벤트가 없습니다</td></tr>';
            return;
        }

        var html = '';
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i];
            var evtKo = e.event === 'connected' ? '연결' :
                        e.event === 'disconnected' ? '끊김' :
                        e.event === 'delayed' ? '지연' : e.event;
            var eventColor = e.event === 'connected' ? 'color:var(--status-green)' :
                             e.event === 'disconnected' ? 'color:var(--status-red)' :
                             'color:var(--status-yellow)';

            html += '<tr>';
            html += '<td>' + Utils.formatFullTimestamp(e.timestamp) + '</td>';
            html += '<td>' + Utils.escapeHtml(e.device_id) + '</td>';
            html += '<td style="font-family:Consolas,monospace">' + Utils.escapeHtml(e.ip) + '</td>';
            html += '<td style="' + eventColor + ';font-weight:600">' + evtKo + '</td>';
            html += '<td>' + (e.rtt_ms !== null ? e.rtt_ms + 'ms' : '-') + '</td>';
            html += '</tr>';
        }
        tbody.innerHTML = html;
    },

    exportCSV: function() {
        Utils.api('GET', '/api/history/export').then(function(entries) {
            if (!entries || entries.length === 0) {
                Utils.showToast('내보낼 이력이 없습니다', 'warning');
                return;
            }
            var csv = '\uFEFF시각,장비ID,IP,이벤트,RTT(ms)\n';
            for (var i = 0; i < entries.length; i++) {
                var e = entries[i];
                csv += e.timestamp + ',' + e.device_id + ',' + e.ip + ',' +
                       e.event + ',' + (e.rtt_ms !== null ? e.rtt_ms : '') + '\n';
            }
            var blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'PortDetector_이력.csv';
            a.click();
            URL.revokeObjectURL(url);
            Utils.showToast('이력 CSV 내보내기 완료', 'success');
        });
    }
};
