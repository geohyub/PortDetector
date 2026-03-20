/* Device CRUD operations */

var Devices = {
    showAddModal: function() {
        document.getElementById('modal-title').textContent = '장비 추가';
        document.getElementById('device-edit-id').value = '';
        document.getElementById('device-name').value = '';
        document.getElementById('device-ip').value = '';
        document.getElementById('device-ports').value = '';
        document.getElementById('device-category').value = '';
        document.getElementById('device-description').value = '';
        document.getElementById('device-enabled').checked = true;
        document.getElementById('device-modal').style.display = 'flex';
    },

    showEditModal: function(id) {
        var device = Dashboard.devices.find(function(d) { return d.id === id; });
        if (!device) return;

        document.getElementById('modal-title').textContent = '장비 편집';
        document.getElementById('device-edit-id').value = device.id;
        document.getElementById('device-name').value = device.name;
        document.getElementById('device-ip').value = device.ip;
        document.getElementById('device-ports').value = (device.ports || []).join(', ');
        document.getElementById('device-category').value = device.category || '';
        document.getElementById('device-description').value = device.description || '';
        document.getElementById('device-enabled').checked = device.enabled !== false;
        document.getElementById('device-modal').style.display = 'flex';
    },

    closeModal: function() {
        document.getElementById('device-modal').style.display = 'none';
    },

    saveDevice: function() {
        var id = document.getElementById('device-edit-id').value;
        var name = document.getElementById('device-name').value.trim();
        var ip = document.getElementById('device-ip').value.trim();
        var portsStr = document.getElementById('device-ports').value.trim();
        var category = document.getElementById('device-category').value.trim();
        var description = document.getElementById('device-description').value.trim();
        var enabled = document.getElementById('device-enabled').checked;

        if (!name) { Utils.showToast('장비 이름을 입력하세요', 'error'); return; }
        if (!ip) { Utils.showToast('IP 주소를 입력하세요', 'error'); return; }

        var ports = [];
        if (portsStr) {
            ports = portsStr.split(/[,\s]+/).map(function(p) {
                return parseInt(p.trim(), 10);
            }).filter(function(p) { return !isNaN(p) && p >= 1 && p <= 65535; });
        }

        var data = { name: name, ip: ip, ports: ports, category: category, description: description, enabled: enabled };
        var method = id ? 'PUT' : 'POST';
        var url = id ? '/api/devices/' + id : '/api/devices';

        Utils.api(method, url, data).then(function(result) {
            if (result.error) { Utils.showToast(result.error, 'error'); return; }
            Devices.closeModal();
            Utils.showToast(id ? '장비가 수정되었습니다' : '장비가 추가되었습니다', 'success');
            App.loadDevices();
        });
    },

    deleteDevice: function(id) {
        var device = Dashboard.devices.find(function(d) { return d.id === id; });
        if (!device) return;
        if (!confirm('"' + device.name + '" (' + device.ip + ')을 삭제하시겠습니까?')) return;

        Utils.api('DELETE', '/api/devices/' + id).then(function(result) {
            if (result.error) { Utils.showToast(result.error, 'error'); return; }
            Utils.showToast('장비가 삭제되었습니다', 'success');
            App.loadDevices();
        });
    }
};
