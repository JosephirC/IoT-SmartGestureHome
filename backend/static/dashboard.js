const { createApp } = Vue;

createApp({
    data() {
        return {
            cameraUrl: '/camera/video_feed',
            gesture: '',
            lastProcessedGesture: '',
            lastGestureTimestamp: null,
            input: '',
            state: { leds: 'OFF', fans: 'OFF', door: 'CLOSED' },
            logs: [],
            pollInterval: null
        };
    },
    mounted() {
        console.log('[DEBUG] Vue mounted - starting polling');
        this.updateAll();
        this.pollInterval = setInterval(() => this.updateAll(), 2000);
    },
    unmounted() {
        if (this.pollInterval) clearInterval(this.pollInterval);
    },
    methods: {
        async updateAll() {
            console.log('[DEBUG] updateAll() called');
            try {
                const res = await fetch('/api/state');
                if (res.ok) this.state = await res.json();
            } catch (e) {
                console.error('State error:', e);
            }
            try {
                const res = await fetch('/camera/last_gesture');
                if (res.ok) {
                    const data = await res.json();
                    console.log('[DEBUG] last_gesture response:', data);
                    console.log('[DEBUG] stored lastGestureTimestamp:', this.lastGestureTimestamp);
                    this.gesture = data.gesture || '';
                    if (data.gesture && data.timestamp) {
                        console.log('[DEBUG] Gesture received:', data.gesture, 'timestamp:', data.timestamp);
                        if (data.timestamp !== this.lastGestureTimestamp) {
                            console.log('[DEBUG] NEW GESTURE DETECTED, sending POST...');
                            this.lastGestureTimestamp = data.timestamp;
                            await this.processGesture(data.gesture);
                        } else {
                            console.log('[DEBUG] Same timestamp, no POST');
                        }
                    } else {
                        console.log('[DEBUG] No gesture or no timestamp');
                    }
                }
            } catch (e) {
                console.error('Gesture error:', e);
            }
        },
        async processGesture(gesture) {
            try {
                console.log('[DEBUG] processGesture() called with:', gesture);
                const res = await fetch('/api/gesture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ gesture: gesture })
                });
                console.log('[DEBUG] POST /api/gesture status:', res.status);
                if (res.ok) {
                    const data = await res.json();
                    console.log('[DEBUG] POST response:', data);
                    const time = new Date().toLocaleTimeString('fr-FR');
                    if (data.status === 'success') {
                        this.logs.unshift({ msg: `${gesture} → ${data.tool} ${data.action}`, time });
                    } else if (data.status === 'skipped') {
                        this.logs.unshift({ msg: `${gesture} → ${data.message}`, time });
                    } else {
                        this.logs.unshift({ msg: `${gesture} → Error: ${data.message}`, time });
                    }
                    if (this.logs.length > 50) this.logs.pop();
                }
            } catch (e) {
                console.error('[DEBUG] Gesture send error:', e);
            }
        },
        async send() {
            if (!this.input.trim()) return;
            try {
                const res = await fetch('/api/gesture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ gesture: this.input })
                });
                if (res.ok) {
                    const data = await res.json();
                    const time = new Date().toLocaleTimeString('fr-FR');
                    this.logs.unshift({ msg: `${this.input} → ${data.tool}`, time });
                    if (this.logs.length > 50) this.logs.pop();
                    this.input = '';
                    setTimeout(() => this.updateAll(), 500);
                }
            } catch (e) {
                console.error('Send error:', e);
            }
        }
    }
}).mount('#app');
