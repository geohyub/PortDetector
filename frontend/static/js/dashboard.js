/* Dashboard - Device grid with grouping, sparklines, and real-time updates */

var Dashboard = {
    devices: [],
    pingData: {},
    trafficData: {},
    trafficAvailable: false,
    statusChangeTime: {},  // device_id -> timestamp when status last changed

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

        for (var g = 0; g < groupNames.length; g++) {
            var groupName = groupNames[g];
            var devs = groups[groupName];
            var onlineCount = 0;
            for (var i = 0; i < devs.length; i++) {
                var p = this.pingData[devs[i].id];
                if (p && p.status === 'connected') onlineCount++;
            }
            html += '<div class="group-header" style="grid-column:1/-1">' +
                    Utils.escapeHtml(groupName) +
                    ' <span style="color:var(--status-green);font-size:11px;margin-left:8px">' +
                    onlineCount + '/' + devs.length + '</span></div>';
            for (var i = 0; i < devs.length; i++) {
                html += this._renderCard(devs[i]);
            }
        }

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
        this._drawAllSparklines();
    },

    _renderCard: function(d) {
        var ping = this.pingData[d.id] || {};
        var status = ping.status || 'unknown';
        var rtt = ping.rtt_ms;
        var disabledClass = d.enabled === false ? ' disabled' : '';

        var html = '<div class="device-card' + disabledClass + '" data-id="' + d.id + '" data-status="' + status + '">';
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

        // Sparkline canvas
        html += '    <canvas class="device-card-sparkline" data-device-id="' + d.id + '"></canvas>';

        // Uptime duration
        var uptimeHtml = this._getUptimeHtml(d.id, status);
        if (uptimeHtml) {
            html += '    <div class="device-card-uptime">' + uptimeHtml + '</div>';
        }

        if (d.ports && d.ports.length > 0) {
            html += '    <div class="device-card-ports">포트: ' + d.ports.join(', ') + '</div>';
        }
        if (d.description) {
            html += '    <div style="font-size:11px;color:var(--text-muted);margin-top:2px">' +
                     Utils.escapeHtml(d.description) + '</div>';
        }

        // Traffic info
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

    _getUptimeHtml: function(deviceId, status) {
        var changeTime = this.statusChangeTime[deviceId];
        if (!changeTime || status === 'unknown') return '';

        var elapsed = Math.floor((Date.now() - changeTime) / 1000);
        var label, cls;

        if (status === 'connected') {
            label = '연결 유지';
            cls = 'uptime-ok';
        } else if (status === 'disconnected') {
            label = '끊김';
            cls = 'uptime-bad';
        } else {
            label = '지연';
            cls = 'uptime-warn';
        }

        return '<span class="' + cls + '">' + label + ' ' + Utils.formatDuration(elapsed) + '</span>';
    },

    _drawAllSparklines: function() {
        var canvases = document.querySelectorAll('.device-card-sparkline');
        canvases.forEach(function(canvas) {
            var devId = canvas.getAttribute('data-device-id');
            Dashboard._drawSparkline(canvas, devId);
        });
    },

    _drawSparkline: function(canvas, deviceId) {
        var data = [];
        // Use ping history from graph API if available, else use last few pings
        if (window._rttCache && window._rttCache[deviceId]) {
            data = window._rttCache[deviceId];
        }

        var rect = canvas.getBoundingClientRect();
        var dpr = window.devicePixelRatio || 1;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        var ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        var w = rect.width;
        var h = rect.height;

        // Clear
        ctx.clearRect(0, 0, w, h);

        if (data.length < 2) return;

        // Last 30 points
        var pts = data.slice(-30);
        var maxRtt = 10;
        for (var i = 0; i < pts.length; i++) {
            if (pts[i].rtt_ms !== null && pts[i].rtt_ms > maxRtt) maxRtt = pts[i].rtt_ms;
        }
        maxRtt *= 1.2;

        // Draw filled area
        ctx.beginPath();
        ctx.moveTo(0, h);
        var hasPoint = false;
        for (var i = 0; i < pts.length; i++) {
            var x = (i / (pts.length - 1)) * w;
            var rtt = pts[i].rtt_ms;
            if (rtt === null) {
                if (hasPoint) { ctx.lineTo(x, h); }
                continue;
            }
            var y = h - (rtt / maxRtt) * (h - 2);
            if (!hasPoint) { ctx.moveTo(x, h); ctx.lineTo(x, y); hasPoint = true; }
            else { ctx.lineTo(x, y); }
        }
        ctx.lineTo(w, h);
        ctx.closePath();

        var gradient = ctx.createLinearGradient(0, 0, 0, h);
        gradient.addColorStop(0, 'rgba(0,180,216,0.25)');
        gradient.addColorStop(1, 'rgba(0,180,216,0.02)');
        ctx.fillStyle = gradient;
        ctx.fill();

        // Draw line
        ctx.beginPath();
        hasPoint = false;
        for (var i = 0; i < pts.length; i++) {
            var x = (i / (pts.length - 1)) * w;
            var rtt = pts[i].rtt_ms;
            if (rtt === null) { hasPoint = false; continue; }
            var y = h - (rtt / maxRtt) * (h - 2);
            if (!hasPoint) { ctx.moveTo(x, y); hasPoint = true; }
            else { ctx.lineTo(x, y); }
        }
        ctx.strokeStyle = '#00b4d8';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    },

    updateTraffic: function() {
        Utils.api('GET', '/api/traffic').then(function(data) {
            Dashboard.trafficAvailable = data.available;
            if (data.available) {
                Dashboard.trafficData = data.devices;
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
            var prevStatus = this.pingData[r.device_id] ? this.pingData[r.device_id].status : null;
            this.pingData[r.device_id] = r;

            // Track status change time
            if (prevStatus !== r.status) {
                this.statusChangeTime[r.device_id] = Date.now();
            }

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

            // Update uptime display
            var uptimeEl = card.querySelector('.device-card-uptime');
            if (uptimeEl) {
                var html = this._getUptimeHtml(r.device_id, r.status);
                uptimeEl.innerHTML = html;
            }
        }
        this.updateSummary();
    },

    toggleGraph: function() {
        Graph.toggle();
    },

    updateSummary: function() {
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

        // Update summary bar
        var el;
        el = document.getElementById('summary-total');
        if (el) el.textContent = total;
        el = document.getElementById('summary-online');
        if (el) el.textContent = connected;
        el = document.getElementById('summary-delayed');
        if (el) el.textContent = delayed;
        el = document.getElementById('summary-offline');
        if (el) el.textContent = disconnected;

        // Update header summary text
        var summaryEl = document.getElementById('device-summary');
        var parts = ['장비 ' + total + '대'];
        if (connected) parts.push('온라인 ' + connected);
        if (disconnected) parts.push('오프라인 ' + disconnected);
        if (delayed) parts.push('지연 ' + delayed);
        summaryEl.textContent = parts.join(' · ');

        // Update page title with status
        if (disconnected > 0) {
            document.title = '(' + disconnected + ' 끊김) PortDetector';
        } else {
            document.title = 'PortDetector';
        }
    },

    refreshSparklines: function() {
        Utils.api('GET', '/api/ping-history').then(function(history) {
            window._rttCache = history;
            Dashboard._drawAllSparklines();
        });
    }
};
