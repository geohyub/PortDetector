/* Traceroute UI */

var Traceroute = {
    tracing: false,

    start: function() {
        if (this.tracing) return;
        var ip = document.getElementById('traceroute-ip').value.trim();
        if (!ip) { Utils.showToast('IP 주소를 입력하세요', 'error'); return; }

        this.tracing = true;
        document.getElementById('traceroute-btn').textContent = '추적 중...';
        document.getElementById('traceroute-btn').disabled = true;
        document.getElementById('traceroute-status').style.display = 'block';
        document.getElementById('traceroute-status').textContent = ip + '까지 경로를 추적하는 중... (최대 30홉)';
        document.getElementById('traceroute-results').innerHTML = '';

        App.socket.emit('request_traceroute', { ip: ip });
    },

    onComplete: function(data) {
        this.tracing = false;
        document.getElementById('traceroute-btn').textContent = '추적 시작';
        document.getElementById('traceroute-btn').disabled = false;
        document.getElementById('traceroute-status').textContent =
            data.ip + ' → ' + data.hops.length + '개 홉 완료';

        var container = document.getElementById('traceroute-results');
        if (!data.hops || data.hops.length === 0) {
            container.innerHTML = '<div class="empty-state">경로를 추적할 수 없습니다</div>';
            return;
        }

        var html = '<div class="panel">';
        for (var i = 0; i < data.hops.length; i++) {
            var hop = data.hops[i];
            var ipDisplay = hop.ip === '*' ? '<span style="color:var(--status-red)">* 응답 없음</span>' :
                           '<span style="color:var(--accent)">' + hop.ip + '</span>';

            var rttDisplay = '';
            if (hop.avg_rtt !== null && hop.avg_rtt !== undefined) {
                var rttColor = hop.avg_rtt < 50 ? 'var(--status-green)' :
                               hop.avg_rtt < 200 ? 'var(--status-yellow)' : 'var(--status-red)';
                rttDisplay = '<span style="color:' + rttColor + '">' + hop.avg_rtt + 'ms</span>';
                rttDisplay += ' <span style="color:var(--text-muted);font-size:11px">(' +
                              (hop.rtt1 !== null ? hop.rtt1 : '*') + ' / ' +
                              (hop.rtt2 !== null ? hop.rtt2 : '*') + ' / ' +
                              (hop.rtt3 !== null ? hop.rtt3 : '*') + ' ms)</span>';
            } else {
                rttDisplay = '<span style="color:var(--text-muted)">-</span>';
            }

            html += '<div class="hop-row">';
            html += '  <span class="hop-num">' + hop.hop + '</span>';
            html += '  <span class="hop-ip">' + ipDisplay + '</span>';
            html += '  <span class="hop-rtt">' + rttDisplay + '</span>';
            html += '</div>';
        }
        html += '</div>';
        container.innerHTML = html;
    },

    quickTrace: function(ip) {
        App.navigateTo('traceroute');
        document.getElementById('traceroute-ip').value = ip;
        this.start();
    }
};
