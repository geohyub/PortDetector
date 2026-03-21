/* RTT Graph - Canvas-based real-time chart with improved visuals */

var Graph = {
    visible: false,
    canvas: null,
    ctx: null,
    colors: ['#00b4d8', '#00e676', '#ffd600', '#ff1744', '#bb86fc', '#ff6d00', '#18ffff', '#f06292'],

    init: function() {
        this.canvas = document.getElementById('rtt-graph-canvas');
        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d');
        }
    },

    toggle: function() {
        this.visible = !this.visible;
        document.getElementById('rtt-graph-panel').style.display = this.visible ? 'block' : 'none';
        if (this.visible) {
            this.init();
            this.refresh();
        }
    },

    refresh: function() {
        if (!this.visible || !this.ctx) return;

        Utils.api('GET', '/api/ping-history').then(function(history) {
            window._rttCache = history;
            Graph.draw(history);
        });
    },

    draw: function(history) {
        var canvas = this.canvas;
        var ctx = this.ctx;

        var rect = canvas.parentElement.getBoundingClientRect();
        var dpr = window.devicePixelRatio || 1;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        var w = rect.width;
        var h = rect.height;
        var padding = { top: 24, right: 16, bottom: 30, left: 50 };
        var chartW = w - padding.left - padding.right;
        var chartH = h - padding.top - padding.bottom;

        // Background
        ctx.fillStyle = '#162029';
        ctx.fillRect(0, 0, w, h);

        var deviceIds = Object.keys(history);
        if (deviceIds.length === 0) {
            ctx.fillStyle = '#5c6e7e';
            ctx.font = '13px Pretendard, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('데이터 수집 중...', w / 2, h / 2);
            return;
        }

        // Find max RTT
        var maxRtt = 10;
        var maxPoints = 0;
        for (var i = 0; i < deviceIds.length; i++) {
            var data = history[deviceIds[i]];
            maxPoints = Math.max(maxPoints, data.length);
            for (var j = 0; j < data.length; j++) {
                if (data[j].rtt_ms !== null && data[j].rtt_ms > maxRtt) {
                    maxRtt = data[j].rtt_ms;
                }
            }
        }
        maxRtt = Math.ceil(maxRtt * 1.2);

        // Draw grid with subtle style
        ctx.strokeStyle = '#1e2d3d';
        ctx.lineWidth = 0.5;
        var gridLines = 4;
        for (var i = 0; i <= gridLines; i++) {
            var y = padding.top + (chartH / gridLines) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(padding.left + chartW, y);
            ctx.stroke();

            ctx.fillStyle = '#5c6e7e';
            ctx.font = '10px Consolas, monospace';
            ctx.textAlign = 'right';
            var val = Math.round(maxRtt - (maxRtt / gridLines) * i);
            ctx.fillText(val + 'ms', padding.left - 6, y + 3);
        }

        // Delay threshold line
        var devices = Dashboard.devices;
        var thresholdY = padding.top + chartH - (200 / maxRtt) * chartH;
        if (thresholdY > padding.top && thresholdY < padding.top + chartH) {
            ctx.strokeStyle = 'rgba(255,23,68,0.25)';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(padding.left, thresholdY);
            ctx.lineTo(padding.left + chartW, thresholdY);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = 'rgba(255,23,68,0.4)';
            ctx.font = '9px Consolas, monospace';
            ctx.textAlign = 'left';
            ctx.fillText('지연 기준', padding.left + chartW - 40, thresholdY - 4);
        }

        // Draw lines per device with filled area
        var legend = [];

        for (var di = 0; di < deviceIds.length; di++) {
            var devId = deviceIds[di];
            var data = history[devId];
            var color = this.colors[di % this.colors.length];

            var devName = devId;
            for (var dd = 0; dd < devices.length; dd++) {
                if (devices[dd].id === devId) { devName = devices[dd].name; break; }
            }
            legend.push({ name: devName, color: color });

            // Fill area
            ctx.beginPath();
            ctx.moveTo(padding.left, padding.top + chartH);
            var started = false;
            for (var j = 0; j < data.length; j++) {
                var x = padding.left + (j / Math.max(maxPoints - 1, 1)) * chartW;
                var rtt = data[j].rtt_ms;
                if (rtt === null) continue;
                var y = padding.top + chartH - (rtt / maxRtt) * chartH;
                if (!started) { ctx.moveTo(x, padding.top + chartH); ctx.lineTo(x, y); started = true; }
                else { ctx.lineTo(x, y); }
            }
            if (started) {
                ctx.lineTo(padding.left + ((data.length - 1) / Math.max(maxPoints - 1, 1)) * chartW, padding.top + chartH);
                ctx.closePath();
                ctx.fillStyle = color.replace(')', ',0.08)').replace('rgb', 'rgba').replace('#', '');
                // Simple alpha fill
                ctx.globalAlpha = 0.12;
                ctx.fillStyle = color;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            // Line
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            started = false;
            for (var j = 0; j < data.length; j++) {
                var x = padding.left + (j / Math.max(maxPoints - 1, 1)) * chartW;
                var rtt = data[j].rtt_ms;
                if (rtt === null) { started = false; continue; }
                var y = padding.top + chartH - (rtt / maxRtt) * chartH;
                if (!started) { ctx.moveTo(x, y); started = true; }
                else { ctx.lineTo(x, y); }
            }
            ctx.stroke();

            // Latest point dot
            if (data.length > 0) {
                var lastRtt = null;
                var lastRttIdx = -1;
                for (var j = data.length - 1; j >= 0; j--) {
                    if (data[j].rtt_ms !== null) { lastRtt = data[j]; lastRttIdx = j; break; }
                }
                if (lastRtt && lastRttIdx >= 0) {
                    var lx = padding.left + (lastRttIdx / Math.max(maxPoints - 1, 1)) * chartW;
                    var ly = padding.top + chartH - (lastRtt.rtt_ms / maxRtt) * chartH;
                    ctx.beginPath();
                    ctx.arc(lx, ly, 3, 0, Math.PI * 2);
                    ctx.fillStyle = color;
                    ctx.fill();
                    ctx.strokeStyle = '#162029';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }

        // Draw legend
        ctx.font = '11px Pretendard, sans-serif';
        var lx = padding.left + 8;
        for (var i = 0; i < legend.length; i++) {
            ctx.fillStyle = legend[i].color;
            ctx.beginPath();
            ctx.arc(lx + 4, padding.top + 6, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#8899a6';
            ctx.textAlign = 'left';
            ctx.fillText(legend[i].name, lx + 12, padding.top + 10);
            lx += ctx.measureText(legend[i].name).width + 28;
        }

        // Time axis
        ctx.fillStyle = '#5c6e7e';
        ctx.font = '9px Consolas, monospace';
        ctx.textAlign = 'center';
        if (maxPoints > 1) {
            var labels = ['최근', '', '', '', '~10분 전'];
            for (var i = 0; i < 5; i++) {
                if (!labels[i]) continue;
                var tx = padding.left + (i / 4) * chartW;
                ctx.fillText(labels[4 - i], tx, padding.top + chartH + 16);
            }
        }
    }
};

// Auto-refresh graph every 5 seconds
setInterval(function() {
    if (Graph.visible) Graph.refresh();
}, 5000);
