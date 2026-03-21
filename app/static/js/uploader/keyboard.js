function uploaderKeyboard() {
    return {
        // Button Hold / Long Press Mechanism

        // Start button long press switching logic
        startNavHold(direction) {
            this.stopNavHold(true);
            const now = Date.now();
            const turbo = this.lastNavDirection === direction && now - this.lastNavTapAt < 260;
            this.lastNavDirection = direction;
            this.lastNavTapAt = now;
            const moved = this.shiftPreview(direction);
            if (!moved) return;
            this.navHoldDelayTimer = window.setTimeout(() => {
                this.navHoldRepeatTimer = window.setInterval(() => {
                    const stepMoved = this.shiftPreview(direction);
                    if (!stepMoved) this.stopNavHold();
                }, turbo ? 20 : 100);
            }, 260);
        },

        // End button long press
        stopNavHold(suppressFlush = false) {
            if (this.navHoldDelayTimer) window.clearTimeout(this.navHoldDelayTimer);
            if (this.navHoldRepeatTimer) window.clearInterval(this.navHoldRepeatTimer);
            this.navHoldDelayTimer = null;
            this.navHoldRepeatTimer = null;
            if (!suppressFlush) this.flushNavPaletteRender();
        },

        // Keyboard long press switching logic
        onKeyboardDown(direction) {
            if (!this.totalFiles) return;
            if (this.keyboardHoldDirection === direction) return;
            this.onKeyboardUp(true);
            const now = Date.now();
            const turbo = now - this.lastKeyTapAt < 260;
            this.lastKeyTapAt = now;
            this.keyboardHoldDirection = direction;
            const moved = this.shiftPreview(direction);
            if (!moved) {
                this.onKeyboardUp();
                return;
            }
            this.keyboardHoldDelayTimer = window.setTimeout(() => {
                this.keyboardHoldRepeatTimer = window.setInterval(() => {
                    const stepMoved = this.shiftPreview(direction);
                    if (!stepMoved) this.onKeyboardUp();
                }, turbo ? 20 : 100);
            }, 260);
        },

        // End keyboard long press
        onKeyboardUp(suppressFlush = false) {
            this.keyboardHoldDirection = 0;
            if (this.keyboardHoldDelayTimer) window.clearTimeout(this.keyboardHoldDelayTimer);
            if (this.keyboardHoldRepeatTimer) window.clearInterval(this.keyboardHoldRepeatTimer);
            this.keyboardHoldDelayTimer = null;
            this.keyboardHoldRepeatTimer = null;
            if (!suppressFlush) this.flushNavPaletteRender();
        }
    };
}
