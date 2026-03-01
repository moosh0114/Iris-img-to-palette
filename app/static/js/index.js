
function applySwatchTextContrast(root = document) {
    const swatches = root.querySelectorAll(".palette-swatch[data-hex]");
    swatches.forEach((swatch) => {
        const hex = String(swatch.dataset.hex || "").trim().replace("#", "");
        if (!/^[0-9a-fA-F]{6}$/.test(hex)) return;
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        swatch.style.color = luminance < 0.52 ? "#f3f3f3" : "#1f1f1f";
    });
}

function uploader() {
    return {
        nColors: "5",
        previewUrl: "",
        dropActive: false,
        holdDelayTimer: null,
        holdRepeatTimer: null,
        sanitizeNColors() {
            const digits = String(this.nColors ?? "").replace(/[^\d]/g, "");
            let value = parseInt(digits || "5", 10);
            if (Number.isNaN(value)) value = 5;
            this.nColors = String(Math.min(12, Math.max(1, value)));
        },
        stepNColors(delta) {
            const current = parseInt(this.nColors, 10);
            const base = Number.isNaN(current) ? 5 : current;
            this.nColors = String(Math.min(12, Math.max(1, base + delta)));
        },
        startAdjust(delta) {
            this.stopAdjust();
            this.stepNColors(delta);
            this.holdDelayTimer = window.setTimeout(() => {
                this.holdRepeatTimer = window.setInterval(() => this.stepNColors(delta), 90);
            }, 500);
        },
        stopAdjust() {
            if (this.holdDelayTimer) window.clearTimeout(this.holdDelayTimer);
            if (this.holdRepeatTimer) window.clearInterval(this.holdRepeatTimer);
            this.holdDelayTimer = null;
            this.holdRepeatTimer = null;
        },
        setFile(file) {
            if (!file || !file.type.startsWith("image/")) return;
            if (this.previewUrl) URL.revokeObjectURL(this.previewUrl);
            const dt = new DataTransfer();
            dt.items.add(file);
            this.$refs.fileInput.files = dt.files;
            this.previewUrl = URL.createObjectURL(file);
        },
        onPick(e) {
            const file = e?.target?.files?.[0];
            if (!file) return;
            this.setFile(file);
        },
        onDrop(e) {
            this.dropActive = false;
            const file = e?.dataTransfer?.files?.[0];
            if (!file) return;
            this.setFile(file);
        },
    };
}

function copyPaletteJson(button) {
    const node = document.getElementById("palette-json");
    if (!node) return;
    navigator.clipboard.writeText(node.innerText || node.textContent || "");
    if (!button) return;
    const originalHtml = button.innerHTML;
    const originalClass = button.className;
    const label = button.querySelector("span");
    if (label) {
        label.textContent = "COPIED";
    } else {
        button.textContent = "COPIED";
    }
    button.classList.add("opacity-50");
    button.disabled = true;
    window.setTimeout(() => {
        button.innerHTML = originalHtml;
        button.className = originalClass;
        button.disabled = false;
    }, 900);
}

document.addEventListener("DOMContentLoaded", () => applySwatchTextContrast());
document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event?.target?.id === "result") applySwatchTextContrast(event.target);
});
