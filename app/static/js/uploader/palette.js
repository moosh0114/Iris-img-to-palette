function uploaderPalette() {
    return {
        // Palette Rendering & nColors Control

        // Ensure the target number input value is within 1~12
        sanitizeNColors() {
            const digits = String(this.nColors ?? "").replace(/[^\d]/g, "");
            let value = parseInt(digits || "10", 10);
            if (Number.isNaN(value)) value = 10;
            this.nColors = String(Math.min(12, Math.max(1, value)));
        },

        // Increase/decrease the current nColors and reschedule rendering
        stepNColors(delta) {
            const current = parseInt(this.nColors, 10);
            const base = Number.isNaN(current) ? 10 : current;
            this.nColors = String(Math.min(12, Math.max(1, base + delta)));
            this.schedulePaletteRender();
        },

        // Start button long press switching logic
        startAdjust(delta) {
            this.stopAdjust();
            this.stepNColors(delta);
            this.holdDelayTimer = window.setTimeout(() => {
                this.holdRepeatTimer = window.setInterval(() => this.stepNColors(delta), 90);
            }, 500);
        },

        // End button long press
        stopAdjust() {
            if (this.holdDelayTimer) window.clearTimeout(this.holdDelayTimer);
            if (this.holdRepeatTimer) window.clearInterval(this.holdRepeatTimer);
            this.holdDelayTimer = null;
            this.holdRepeatTimer = null;
        },

        // Delay rendering to reduce rendering load
        scheduleNavPaletteRender() {
            if (this.navPaletteRenderTimer) window.clearTimeout(this.navPaletteRenderTimer);
            this.navPaletteRenderTimer = window.setTimeout(() => {
                this.navPaletteRenderTimer = null;
                this.renderCurrentPalette();
            }, 180);
        },
        flushNavPaletteRender() {
            if (this.navPaletteRenderTimer) {
                window.clearTimeout(this.navPaletteRenderTimer);
                this.navPaletteRenderTimer = null;
            }
            this.renderCurrentPalette();
        },
        schedulePaletteRender() {
            if (this.paletteRenderTimer) window.clearTimeout(this.paletteRenderTimer);
            this.paletteRenderTimer = window.setTimeout(() => this.renderCurrentPalette(), 120);
        },

        // Execute the rendering of the color corresponding to the current index
        renderCurrentPalette(commit = false, options = {}) {
            const n = Math.max(1, parseInt(this.nColors, 10) || 10);
            const palette = this.extractedPalettes?.[this.currentIndex] || [];
            const desktop = document.getElementById("desktop-swatches");
            const mobile = document.getElementById("mobile-swatches");
            const keepDesktop = Math.max(0, Number(options.keepDesktop || 0));
            const keepMobile = Math.max(0, Number(options.keepMobile || 0));
            const paletteCount = Array.isArray(palette) ? palette.length : 0;
            const previewLayoutCount = Math.max(n, paletteCount);

            updateSwatchGridLayout(desktop, commit ? n : previewLayoutCount);
            renderPaletteGrid(desktop, palette, n, { commit, keepAtLeast: keepDesktop });
            renderPaletteGrid(mobile, palette, n, { commit, keepAtLeast: keepMobile });
            applyPaletteBackgroundToUploadArea(document);
        }
    };
}
