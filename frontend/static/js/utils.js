/* Utility functions */

var Utils = {
    formatTimestamp: function(iso) {
        if (!iso) return '-';
        var d = new Date(iso);
        var pad = function(n) { return n < 10 ? '0' + n : n; };
        return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    },

    formatFullTimestamp: function(iso) {
        if (!iso) return '-';
        var d = new Date(iso);
        var pad = function(n) { return n < 10 ? '0' + n : n; };
        return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()) +
               ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    },

    formatBytes: function(bytes) {
        if (bytes === 0) return '0 B';
        var units = ['B', 'KB', 'MB', 'GB', 'TB'];
        var i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
    },

    formatSpeed: function(bytesPerSec) {
        if (bytesPerSec === 0) return '0 B/s';
        var units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
        var i = Math.floor(Math.log(bytesPerSec) / Math.log(1024));
        if (i >= units.length) i = units.length - 1;
        return (bytesPerSec / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
    },

    formatDuration: function(seconds) {
        if (seconds < 60) return seconds + '초';
        if (seconds < 3600) return Math.floor(seconds / 60) + '분';
        var h = Math.floor(seconds / 3600);
        var m = Math.floor((seconds % 3600) / 60);
        return h + '시간 ' + (m > 0 ? m + '분' : '');
    },

    showToast: function(message, type) {
        type = type || 'info';
        var container = document.getElementById('toast-container');
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.innerHTML = '<span>' + message + '</span>' +
                          '<button class="toast-close" onclick="this.parentElement.remove()">&times;</button>';
        container.appendChild(toast);
        setTimeout(function() {
            toast.style.animation = 'toastOut 0.25s ease-in forwards';
            setTimeout(function() { toast.remove(); }, 250);
        }, 4000);
    },

    escapeHtml: function(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    api: function(method, url, data) {
        var opts = {
            method: method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (data) opts.body = JSON.stringify(data);
        return fetch(url, opts).then(function(r) { return r.json(); });
    }
};
