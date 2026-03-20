/* Settings panel */

var Settings = {
    loadSettings: function() {
        Utils.api('GET', '/api/settings').then(function(s) {
            document.getElementById('setting-ping-interval').value = s.ping_interval_seconds || 5;
            document.getElementById('setting-ping-interval').nextElementSibling.textContent = (s.ping_interval_seconds || 5) + '초';

            document.getElementById('setting-iface-interval').value = s.interface_poll_seconds || 3;
            document.getElementById('setting-iface-interval').nextElementSibling.textContent = (s.interface_poll_seconds || 3) + '초';

            document.getElementById('setting-delay-threshold').value = s.delay_threshold_ms || 200;

            var alertEnabled = s.alert_enabled !== false;
            document.getElementById('setting-alert-enabled').checked = alertEnabled;
            AlertSound.setEnabled(alertEnabled);

            var vol = s.alert_volume !== undefined ? Math.round(s.alert_volume * 100) : 50;
            document.getElementById('setting-alert-volume').value = vol;
            document.getElementById('setting-alert-volume').nextElementSibling.textContent = vol + '%';
            AlertSound.setVolume(vol / 100);
        });
    },

    saveSettings: function() {
        var alertVol = parseInt(document.getElementById('setting-alert-volume').value, 10) / 100;
        var alertOn = document.getElementById('setting-alert-enabled').checked;

        var data = {
            ping_interval_seconds: parseInt(document.getElementById('setting-ping-interval').value, 10),
            interface_poll_seconds: parseInt(document.getElementById('setting-iface-interval').value, 10),
            delay_threshold_ms: parseInt(document.getElementById('setting-delay-threshold').value, 10),
            alert_enabled: alertOn,
            alert_volume: alertVol,
        };

        Utils.api('PUT', '/api/settings', data).then(function(result) {
            if (result.error) { Utils.showToast(result.error, 'error'); return; }

            AlertSound.setEnabled(alertOn);
            AlertSound.setVolume(alertVol);

            if (App.socket) {
                App.socket.emit('update_interval', {
                    ping_interval: data.ping_interval_seconds,
                    interface_interval: data.interface_poll_seconds,
                });
            }
            Utils.showToast('설정이 저장되었습니다', 'success');
        });
    },

    exportConfig: function() {
        Utils.api('GET', '/api/devices/export').then(function(config) {
            var blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'PortDetector_설정.json';
            a.click();
            URL.revokeObjectURL(url);
            Utils.showToast('설정 내보내기 완료', 'success');
        });
    },

    importConfig: function() {
        document.getElementById('config-file-input').click();
    },

    handleImport: function(event) {
        var file = event.target.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function(e) {
            try {
                var config = JSON.parse(e.target.result);
                Utils.api('POST', '/api/devices/import', config).then(function(result) {
                    if (result.error) { Utils.showToast(result.error, 'error'); return; }
                    Utils.showToast('설정 가져오기 완료', 'success');
                    App.loadDevices();
                });
            } catch (err) {
                Utils.showToast('잘못된 JSON 파일입니다', 'error');
            }
        };
        reader.readAsText(file);
        event.target.value = '';
    }
};
