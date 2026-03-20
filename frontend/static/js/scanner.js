/* Port Scanner UI */

var Scanner = {
    scanning: false,

    quickScan: function(ip) {
        App.navigateTo('scanner');
        document.getElementById('scan-ip').value = ip;
        document.getElementById('scan-ports').value = '21,22,23,25,53,80,110,135,139,143,443,445,993,995,1433,3306,3389,5432,5900,8080,8443';
        this.startScan();
    },

    startScan: function() {
        if (this.scanning) return;
        var ip = document.getElementById('scan-ip').value.trim();
        var ports = document.getElementById('scan-ports').value.trim();
        var protocol = document.getElementById('scan-protocol').value;

        if (!ip) { Utils.showToast('IP 주소를 입력하세요', 'error'); return; }

        this.scanning = true;
        document.getElementById('scan-results-body').innerHTML = '';
        document.getElementById('scan-progress').style.display = 'flex';
        document.getElementById('scan-progress-fill').style.width = '0%';
        document.getElementById('scan-btn').textContent = '스캔 중...';
        document.getElementById('scan-btn').disabled = true;

        Utils.api('POST', '/api/scan', { ip: ip, ports: ports, protocol: protocol });
    },

    addResult: function(data) {
        if (data.state === 'closed') return;
        var tbody = document.getElementById('scan-results-body');
        var badgeClass = data.state === 'open' ? 'badge-open' :
                         data.state.indexOf('filtered') >= 0 ? 'badge-filtered' : 'badge-closed';
        var stateKo = data.state === 'open' ? '열림' :
                      data.state.indexOf('filtered') >= 0 ? '필터링' : '닫힘';

        var tr = document.createElement('tr');
        tr.innerHTML = '<td>' + data.port + '</td>' +
                       '<td><span class="badge ' + badgeClass + '">' + stateKo + '</span></td>' +
                       '<td>' + data.protocol.toUpperCase() + '</td>' +
                       '<td>' + Utils.escapeHtml(data.service_name || '-') + '</td>';
        tbody.appendChild(tr);
    },

    updateProgress: function(data) {
        var pct = data.total > 0 ? Math.round(data.scanned / data.total * 100) : 0;
        document.getElementById('scan-progress-fill').style.width = pct + '%';
        document.getElementById('scan-progress-text').textContent = data.scanned + ' / ' + data.total;
    },

    onComplete: function(data) {
        this.scanning = false;
        document.getElementById('scan-btn').textContent = '스캔 시작';
        document.getElementById('scan-btn').disabled = false;
        document.getElementById('scan-progress-fill').style.width = '100%';
        Utils.showToast('스캔 완료: 열림 ' + data.open_ports + '개, 닫힘 ' + data.closed_ports + '개',
                        data.open_ports > 0 ? 'success' : 'info');
    }
};
