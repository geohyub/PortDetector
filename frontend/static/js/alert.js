/* Alert Sound - Different sounds for disconnect/reconnect */

var AlertSound = {
    enabled: true,
    volume: 0.5,
    audioCtx: null,

    init: function() {
        try {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            // Web Audio not supported
        }
    },

    play: function(type) {
        type = type || 'disconnect';
        if (!this.enabled || !this.audioCtx) return;

        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        if (type === 'reconnect') {
            this._playReconnect();
        } else {
            this._playDisconnect();
        }
    },

    _playDisconnect: function() {
        var ctx = this.audioCtx;
        var now = ctx.currentTime;
        var vol = this.volume * 0.3;

        // Urgent two-tone beep x3
        for (var i = 0; i < 3; i++) {
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.value = i % 2 === 0 ? 880 : 660;
            gain.gain.value = vol;
            var start = now + i * 0.2;
            osc.start(start);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.15);
            osc.stop(start + 0.15);
        }
    },

    _playReconnect: function() {
        var ctx = this.audioCtx;
        var now = ctx.currentTime;
        var vol = this.volume * 0.2;

        // Pleasant ascending chime
        var freqs = [523, 659, 784]; // C5, E5, G5
        for (var i = 0; i < 3; i++) {
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.value = freqs[i];
            gain.gain.value = vol;
            var start = now + i * 0.12;
            osc.start(start);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.25);
            osc.stop(start + 0.25);
        }
    },

    testSound: function() {
        var slider = document.getElementById('setting-alert-volume');
        if (slider) this.volume = parseInt(slider.value, 10) / 100;
        if (!this.audioCtx) this.init();
        var wasEnabled = this.enabled;
        this.enabled = true;
        this.play('disconnect');
        setTimeout(function() { AlertSound.play('reconnect'); }, 800);
        this.enabled = wasEnabled;
    },

    setEnabled: function(on) {
        this.enabled = on;
    },

    setVolume: function(vol) {
        this.volume = Math.max(0, Math.min(1, vol));
    }
};
