/* Alert Sound - Web Audio API beep with on/off and volume control */

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

    play: function() {
        if (!this.enabled || !this.audioCtx) return;

        // Resume context if suspended (browser autoplay policy)
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        var ctx = this.audioCtx;
        var now = ctx.currentTime;

        // Two-tone alert beep (urgent but not harsh)
        for (var i = 0; i < 3; i++) {
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.type = 'sine';
            osc.frequency.value = i % 2 === 0 ? 880 : 660;
            gain.gain.value = this.volume * 0.3;

            var start = now + i * 0.2;
            osc.start(start);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.15);
            osc.stop(start + 0.15);
        }
    },

    testSound: function() {
        // Update volume from slider before playing
        var slider = document.getElementById('setting-alert-volume');
        if (slider) this.volume = parseInt(slider.value, 10) / 100;

        // Ensure context is initialized on user interaction
        if (!this.audioCtx) this.init();
        var wasEnabled = this.enabled;
        this.enabled = true;
        this.play();
        this.enabled = wasEnabled;
    },

    setEnabled: function(on) {
        this.enabled = on;
    },

    setVolume: function(vol) {
        this.volume = Math.max(0, Math.min(1, vol));
    }
};
