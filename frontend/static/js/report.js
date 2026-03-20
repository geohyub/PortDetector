/* Report Generation */

var Report = {
    reportData: null,

    generate: function() {
        Utils.api('GET', '/api/report').then(function(data) {
            Report.reportData = data;
            Report.render(data);
            document.getElementById('report-modal').style.display = 'flex';
        });
    },

    render: function(data) {
        var container = document.getElementById('report-content');
        var s = data.summary;

        var html = '<div style="margin-bottom:20px">';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">생성 시각</div>';
        html += '<div>' + Utils.formatFullTimestamp(data.generated_at) + '</div>';
        html += '</div>';

        // Summary
        html += '<div class="panel" style="margin-bottom:16px">';
        html += '<div class="panel-title">요약</div>';
        html += '<div style="display:flex;gap:24px;font-size:14px">';
        html += '<div>전체 <strong>' + s.total + '</strong></div>';
        html += '<div style="color:var(--status-green)">온라인 <strong>' + s.online + '</strong></div>';
        html += '<div style="color:var(--status-red)">오프라인 <strong>' + s.offline + '</strong></div>';
        html += '<div style="color:var(--status-yellow)">지연 <strong>' + s.delayed + '</strong></div>';
        html += '</div></div>';

        // Devices
        html += '<div class="panel" style="margin-bottom:16px">';
        html += '<div class="panel-title">장비 상태</div>';
        html += '<table class="data-table"><thead><tr>';
        html += '<th>장비명</th><th>IP</th><th>상태</th><th>RTT</th><th>그룹</th>';
        html += '</tr></thead><tbody>';

        for (var i = 0; i < data.devices.length; i++) {
            var d = data.devices[i];
            var statusKo = d.status === 'connected' ? '연결' :
                           d.status === 'disconnected' ? '끊김' :
                           d.status === 'delayed' ? '지연' : '미확인';
            var statusColor = d.status === 'connected' ? 'var(--status-green)' :
                              d.status === 'disconnected' ? 'var(--status-red)' :
                              d.status === 'delayed' ? 'var(--status-yellow)' : 'var(--text-muted)';

            html += '<tr>';
            html += '<td>' + Utils.escapeHtml(d.name) + '</td>';
            html += '<td style="font-family:Consolas,monospace">' + d.ip + '</td>';
            html += '<td style="color:' + statusColor + ';font-weight:600">' + statusKo + '</td>';
            html += '<td>' + (d.rtt_ms !== null && d.rtt_ms !== undefined ? d.rtt_ms + 'ms' : '-') + '</td>';
            html += '<td>' + Utils.escapeHtml(d.category || '-') + '</td>';
            html += '</tr>';
        }
        html += '</tbody></table></div>';

        // Interfaces
        html += '<div class="panel" style="margin-bottom:16px">';
        html += '<div class="panel-title">네트워크 인터페이스</div>';
        html += '<table class="data-table"><thead><tr>';
        html += '<th>어댑터</th><th>상태</th><th>속도</th><th>IPv4</th>';
        html += '</tr></thead><tbody>';

        for (var i = 0; i < data.interfaces.length; i++) {
            var iface = data.interfaces[i];
            html += '<tr>';
            html += '<td>' + Utils.escapeHtml(iface.name) + '</td>';
            html += '<td style="color:' + (iface.is_up ? 'var(--status-green)' : 'var(--status-red)') + '">' +
                    (iface.is_up ? 'UP' : 'DOWN') + '</td>';
            html += '<td>' + (iface.speed_mbps > 0 ? iface.speed_mbps + ' Mbps' : '-') + '</td>';
            html += '<td style="font-family:Consolas,monospace">' + (iface.ipv4 || '-') + '</td>';
            html += '</tr>';
        }
        html += '</tbody></table></div>';

        // Recent events
        if (data.recent_events && data.recent_events.length > 0) {
            html += '<div class="panel">';
            html += '<div class="panel-title">최근 이벤트 (최대 50건)</div>';
            html += '<table class="data-table"><thead><tr>';
            html += '<th>시각</th><th>장비</th><th>이벤트</th>';
            html += '</tr></thead><tbody>';

            for (var i = 0; i < Math.min(data.recent_events.length, 20); i++) {
                var e = data.recent_events[i];
                var evtKo = e.event === 'connected' ? '연결' :
                            e.event === 'disconnected' ? '끊김' : e.event;
                html += '<tr>';
                html += '<td>' + Utils.formatFullTimestamp(e.timestamp) + '</td>';
                html += '<td>' + e.device_id + ' (' + e.ip + ')</td>';
                html += '<td>' + evtKo + '</td>';
                html += '</tr>';
            }
            html += '</tbody></table></div>';
        }

        container.innerHTML = html;
    },

    close: function() {
        document.getElementById('report-modal').style.display = 'none';
    },

    downloadHTML: function() {
        if (!this.reportData) return;
        var content = document.getElementById('report-content').innerHTML;
        var fullHTML = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>PortDetector 보고서</title>' +
            '<style>body{font-family:Pretendard,sans-serif;background:#1a2332;color:#e8eaed;padding:30px}' +
            'table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px 12px;text-align:left;' +
            'border-bottom:1px solid #263545}th{background:#0f1923;color:#8899a6;font-size:11px;text-transform:uppercase}' +
            'strong{font-weight:700}.panel{background:#1e2d3d;border:1px solid #263545;border-radius:8px;padding:20px;margin-bottom:16px}' +
            '.panel-title{font-size:13px;font-weight:600;color:#8899a6;text-transform:uppercase;margin-bottom:14px}</style>' +
            '</head><body><h1 style="color:#00b4d8;margin-bottom:20px">PortDetector 네트워크 상태 보고서</h1>' +
            content + '</body></html>';

        var blob = new Blob([fullHTML], { type: 'text/html' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'PortDetector_Report_' + new Date().toISOString().slice(0, 10) + '.html';
        a.click();
        URL.revokeObjectURL(url);
        Utils.showToast('보고서 HTML 저장 완료', 'success');
    }
};
