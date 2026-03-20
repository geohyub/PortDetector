/* Dashboard - Device grid with grouping and real-time updates */

var Dashboard = {
    devices: [],
    pingData: {},
    trafficData: {},
    trafficAvailable: false,

    renderDevices: function(devices) {
        this.devices = devices;
        var grid = document.getElementById('device-grid');

        if (!devices || devices.length === 0) {
            grid.innerHTML = '<div class="empty-state">등록된 장비가 없습니다. "장비 추가" 버튼으로 시작하세요.</div>';
            this.updateSummary();
            return;
        }

        // Group devices by category
        var groups = {};
        var noGroup = [];
        for (var i = 0; i < devices.length; i++) {
            var d = devices[i];
            if (d.category) {
                if (!groups[d.category]) groups[d.category] = [];
                groups[d.category].push(d);
            } else {
                noGroup.push(d);
            }
        }

        var html = '';
        var groupNames = Object.keys(groups).sort();

        // Render grouped devices
        for (var g = 0; g < groupNames.length; g++) {
            var groupName = groupNames[g];
            html += '<div class="group-header" style="grid-column:1/-1">' + Utils.escapeHtml(groupName) + '</div>';
            var devs = groups[groupName];
            for (var i = 0; i < devs.length; i++) {
                html += this._renderCard(devs[i]);
            }
        }

        // Ungrouped devices
        if (noGroup.length > 0) {
            if (groupNames.length > 0) {
                html += '<div class="group-header" style="grid-column:1/-1">미분류</div>';
            }
            for (var i = 0; i < noGroup.length; i++) {
                html += this._renderCard(noGroup[i]);
            }
        }

        grid.innerHTML = html;
        this.updateSummary();
    },

    _renderCard: function(d) {
        var ping = this.pingData[d.id] || {};
        var status = ping.status || 'unknown';
        var rtt = ping.rtt_ms;

        var html = '<div class="device-card" data-id="' + d.id + '" data-status="' + status + '">';
        html += '  <div class="device-card-header">';
        html += '    <div class="device-card-title">';
        html += '      <span class="status-dot ' + status + '"></span>';
        html += '      <span class="device-card-name">' + Utils.escapeHtml(d.name) + '</span>';
        html += '    </div>';
        html += '    <div class="device-card-actions">';
        html += '      <button title="포트 스캔" onclick="Scanner.quickScan(\'' + d.ip + '\')">&#9881;</button>';
        html += '      <button title="경로 추적" onclick="Traceroute.quickTrace(\'' + d.ip + '\')">&#8644;</button>';
        html += '      <button title="편집" onclick="Devices.showEditModal(\'' + d.id + '\')">&#9998;</button>';
        html += '      <button title="삭제" onclick="Devices.deleteDevice(\'' + d.id + '\')">&#10005;</button>';
        html += '    </div>';
        html += '  </div>';
        html += '  <div class="device-card-body">';
        html += '    <div class="device-card-ip">' + Utils.escapeHtml(d.ip) + '</div>';
        html += '    <div class="device-card-meta">';

        if (d.category) {
            html += '      <span class="device-card-category">' + Utils.escapeHtml(d.category) + '</span>';
        } else {
            html += '      <span></span>';
        }

        if (status === 'connected' && rtt !== null && rtt !== undefined) {
            var rttClass = rtt < 50 ? 'good' : rtt < 200 ? 'warning' : 'bad';
            html += '      <span class="device-card-rtt ' + rttClass + '">' + rtt + 'ms</span>';
        } else if (status === 'delayed' && rtt !== null && rtt !== undefined) {
            html += '      <span class="device-card-rtt bad">' + rtt + 'ms</span>';
        } else if (status === 'disconnected') {
            html += '      <span class="device-card-rtt bad">타임아웃</span>';
        } else {
            html += '      <span class="device-card-rtt" style="color:var(--text-muted)">--</span>';
        }

        html += '    </div>';
        if (d.ports && d.ports.length > 0) {
            html += '    <div class="device-card-ports">포트: ' + d.ports.join(', ') + '</div>';
        }
        if (d.description) {
            html += '    <div style="font-size:11px;color:var(--text-muted);margin-top:2px">' +
                     Utils.escapeHtml(d.description) + '</div>';
        }

        // Traffic info (if available)
        var traffic = this.trafficData[d.ip];
        if (traffic && this.trafficAvailable) {
            html += '    <div class="device-card-traffic" style="margin-top:6px;font-size:11px;display:flex;gap:12px">';
            html += '      <span style="color:var(--status-green)">&#8595; ' + Utils.formatSpeed(traffic.rate_in) + '</span>';
            html += '      <span style="color:var(--accent)">&#8593; ' + Utils.formatSpeed(traffic.rate_out) + '</span>';
            html += '    </div>';
        }

        html += '  </div></div>';
        return html;
    },

    updateTraffic: function() {
        Utils.api('GET', '/api/traffic').then(function(data) {
            Dashboard.trafficAvailable = data.available;
            if (data.available) {
                Dashboard.trafficData = data.devices;
                // Update traffic display on existing cards
                for (var ip in data.devices) {
                    var t = data.devices[ip];
                    var cards = document.querySelectorAll('.device-card');
                    cards.forEach(function(card) {
                        var ipEl = card.querySelector('.device-card-ip');
                        if (ipEl && ipEl.textContent === ip) {
                            var trafficEl = card.querySelector('.device-card-traffic');
                            if (trafficEl) {
                                trafficEl.innerHTML =
                                    '<span style="color:var(--status-green)">&#8595; ' + Utils.formatSpeed(t.rate_in) + '</span>' +
                                    '<span style="color:var(--accent)">&#8593; ' + Utils.formatSpeed(t.rate_out) + '</span>';
                            }
                        }
                    });
                }
            }
        });
    },

    updatePingResults: function(results) {
        for (var i = 0; i < results.length; i++) {
            var r = results[i];
            this.pingData[r.device_id] = r;

            var card = document.querySelector('.device-card[data-id="' + r.device_id + '"]');
            if (!card) continue;

            card.setAttribute('data-status', r.status);

            var dot = card.querySelector('.status-dot');
            if (dot) dot.className = 'status-dot ' + r.status;

            var rttEl = card.querySelector('.device-card-rtt');
            if (rttEl) {
                if (r.status === 'disconnected') {
                    rttEl.className = 'device-card-rtt bad';
                    rttEl.textContent = '타임아웃';
                } else if (r.rtt_ms !== null && r.rtt_ms !== undefined) {
                    var rttClass = r.rtt_ms < 50 ? 'good' : r.rtt_ms < 200 ? 'warning' : 'bad';
                    rttEl.className = 'device-card-rtt ' + rttClass;
                    rttEl.textContent = r.rtt_ms + 'ms';
                }
            }
        }
        this.updateSummary();
    },

    toggleGraph: function() {
        Graph.toggle();
    },

    updateSummary: function() {
        var el = document.getElementById('device-summary');
        var total = this.devices.length;
        var connected = 0, disconnected = 0, delayed = 0;

        for (var i = 0; i < this.devices.length; i++) {
            var p = this.pingData[this.devices[i].id];
            if (p) {
                if (p.status === 'connected') connected++;
                else if (p.status === 'disconnected') disconnected++;
                else if (p.status === 'delayed') delayed++;
            }
        }

        var parts = ['장비 ' + total + '대'];
        if (connected) parts.push('온라인 ' + connected);
        if (disconnected) parts.push('오프라인 ' + disconnected);
        if (delayed) parts.push('지연 ' + delayed);
        el.textContent = parts.join(' · ');
    }
};
