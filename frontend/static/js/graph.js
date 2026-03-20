/* RTT Graph - Canvas-based real-time chart */

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
            Graph.draw(history);
        });
    },

    draw: function(history) {
        var canvas = this.canvas;
        var ctx = this.ctx;

        // Set canvas size to actual pixel size
        var rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * (window.devicePixelRatio || 1);
        canvas.height = rect.height * (window.devicePixelRatio || 1);
        ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

        var w = rect.width;
        var h = rect.height;
        var padding = { top: 20, right: 16, bottom: 30, left: 50 };
        var chartW = w - padding.left - padding.right;
        var chartH = h - padding.top - padding.bottom;

        // Clear
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

        // Find max RTT for scaling
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

        // Draw grid
        ctx.strokeStyle = '#263545';
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

        // Draw lines per device
        var devices = Dashboard.devices;
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

            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.beginPath();

            var started = false;
            for (var j = 0; j < data.length; j++) {
                var x = padding.left + (j / Math.max(maxPoints - 1, 1)) * chartW;
                var rtt = data[j].rtt_ms;

                if (rtt === null) continue;
                var y = padding.top + chartH - (rtt / maxRtt) * chartH;

                if (!started) { ctx.moveTo(x, y); started = true; }
                else { ctx.lineTo(x, y); }
            }
            ctx.stroke();
        }

        // Draw legend
        ctx.font = '11px Pretendard, sans-serif';
        var lx = padding.left + 8;
        for (var i = 0; i < legend.length; i++) {
            ctx.fillStyle = legend[i].color;
            ctx.fillRect(lx, padding.top + 2, 12, 3);
            ctx.fillStyle = '#8899a6';
            ctx.textAlign = 'left';
            ctx.fillText(legend[i].name, lx + 16, padding.top + 8);
            lx += ctx.measureText(legend[i].name).width + 32;
        }
    }
};

// Auto-refresh graph every 5 seconds
setInterval(function() {
    if (Graph.visible) Graph.refresh();
}, 5000);
