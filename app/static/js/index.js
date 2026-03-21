/**
 * @fileoverview Main Application & Alpine.js Component
 * Handles the core uploader state, file parsing, keyboard shortcuts, 
 * and HTMX lifecycle interactions.
 */

let lastPointerClientX = -1;
let lastPointerClientY = -1;

/**
 * Initialize the core uploader component of Alpine.js
 * Responsible for managing image preview, color extraction quantity, upload status, and receiving keyboard and screen event operations.
 * @returns {Object} Alpine.js data object
 */
function uploader() {
    return {
        isDark: getStoredTheme() === "dark",
        // whether the theme is in transition
        themeTransitioning: false,


        // The currently displayed image preview URL
        previewUrl: "",
        // All image preview URLs
        previewUrls: [],
        // Loaded image files
        files: [],
        // Total number of files
        totalFiles: 0,
        // Current image index
        currentIndex: 0,
        // Whether the preview image is animating
        previewAnimating: false,
        // The CSS class corresponding to the sliding direction of the preview image
        previewSlideClass: "",
        // Whether the drag-and-drop upload area is active
        dropActive: false,
        // Whether the preview image is being dragged
        previewDragging: false,
        // The starting X coordinate of the drag
        previewDragStartX: 0,
        // The X-axis displacement during the drag
        previewDragDeltaX: 0,


        // Navigation button long press mechanism
        navHoldDelayTimer: null,
        navHoldRepeatTimer: null,
        lastNavTapAt: 0,
        lastNavDirection: 0,


        // Palette State

        // Target number of colors to extract, used as a string bound to the input box
        nColors: "10",
        // Stores the extracted palette data for each image
        extractedPalettes: [],
        paletteRenderTimer: null,
        navPaletteRenderTimer: null,
        holdDelayTimer: null,
        holdRepeatTimer: null,


        // Number of color swatches before submission (for HTMX replacement animation)
        preSubmitDesktopCount: 0,
        // Number of color swatches before submission (for HTMX replacement animation)
        preSubmitMobileCount: 0,


        // Keyboard State
        keyboardHoldDirection: 0,
        keyboardHoldDelayTimer: null,
        keyboardHoldRepeatTimer: null,
        lastKeyTapAt: 0,


        // Misc UI State

        // Whether the backend extraction process is in progress
        isWorking: false,
        // Whether the export panel is displayed
        showExport: false,


        // Theme Methods

        // Toggle dark/light theme
        toggleTheme() {
            if (this.themeTransitioning) return;
            this.themeTransitioning = true;
            this.isDark = !this.isDark;
            applyTheme(this.isDark ? "dark" : "light");
            window.setTimeout(() => {
                this.themeTransitioning = false;
            }, 700);
        },


        // File & Upload Handling

        onUploadAreaClick(e) {
            const target = e?.target;
            if (target?.closest(".iris-nav-btn")) return;
            this.$refs.fileInput.click();
        },

        clearLoadedFiles() {
            this.revokePreviews();
            this.files = [];
            this.totalFiles = 0;
            this.currentIndex = 0;
            this.previewUrl = "";
            this.previewAnimating = false;
            this.previewSlideClass = "";
            this.extractedPalettes = [];
            if (this.navPaletteRenderTimer) {
                window.clearTimeout(this.navPaletteRenderTimer);
                this.navPaletteRenderTimer = null;
            }
            this.stopNavHold(true);
            this.onKeyboardUp(true);
            if (this.$refs?.fileInput) {
                this.$refs.fileInput.value = "";
                const dt = new DataTransfer();
                this.$refs.fileInput.files = dt.files;
            }
            resetUploadAreaBackground();
            this.renderCurrentPalette(true);
        },

        // Configure the file and generate a preview ( this will overwrite any existing files )
        setFiles(filesLike) {
            const files = Array.from(filesLike || []).filter((file) => file && file.type.startsWith("image/"));
            if (!files.length) return;
            let accepted = files;
            if (files.length > MAX_FILES_PER_BATCH) {
                accepted = files.slice(0, MAX_FILES_PER_BATCH);
                showTransientNotice(`Limit is ${MAX_FILES_PER_BATCH} images. Using the first ${MAX_FILES_PER_BATCH}.`);
            }
            this.revokePreviews();
            const dt = new DataTransfer();
            accepted.forEach((file) => dt.items.add(file));
            this.$refs.fileInput.files = dt.files;
            this.files = accepted;
            this.previewUrls = accepted.map((file) => URL.createObjectURL(file));
            this.totalFiles = accepted.length;
            this.currentIndex = 0;
            this.previewUrl = this.previewUrls[0] || "";
            this.previewAnimating = false;
            this.previewSlideClass = "";
            this.extractedPalettes = [];
            if (this.navPaletteRenderTimer) {
                window.clearTimeout(this.navPaletteRenderTimer);
                this.navPaletteRenderTimer = null;
            }
            this.stopNavHold(true);
            this.onKeyboardUp(true);
            resetUploadAreaBackground();
            this.renderCurrentPalette(true);
        },

        // Triggered after selecting a file through the file selector
        onPick(e) {
            const files = e?.target?.files;
            if (!files?.length) {
                if (this.files?.length && this.$refs?.fileInput) {
                    const dt = new DataTransfer();
                    this.files.forEach((file) => dt.items.add(file));
                    this.$refs.fileInput.files = dt.files;
                }
                return;
            }
            this.setFiles(files);
        },

        // Triggered when a file is dropped after dragging
        onDrop(e) {
            this.dropActive = false;
            const files = e?.dataTransfer?.files;
            if (!files?.length) return;
            this.setFiles(files);
        },


        // Preview Navigation

        // Release all Object URLs generated by the preview images to avoid memory leaks
        revokePreviews() {
            this.previewUrls.forEach((url) => URL.revokeObjectURL(url));
            this.previewUrls = [];
        },

        // Get the preview URL relative to the current index
        previewAt(offset) {
            if (!this.totalFiles || !this.previewUrls.length) return "";
            const idx = this.currentIndex + offset;
            if (idx < 0 || idx >= this.totalFiles) return "";
            return this.previewUrls[idx];
        },

        // Switch the specified preview index with transition animation
        setPreviewIndex(nextIndex) {
            if (!this.totalFiles) return;
            const prevIndex = this.currentIndex;
            const clamped = Math.max(0, Math.min(this.totalFiles - 1, nextIndex));
            if (clamped === this.currentIndex) return false;
            this.currentIndex = clamped;
            this.previewUrl = this.previewUrls[clamped] || "";
            this.previewSlideClass = clamped > prevIndex ? "iris-slide-in-right" : "iris-slide-in-left";
            this.previewAnimating = true;
            window.setTimeout(() => {
                this.previewAnimating = false;
                this.previewSlideClass = "";
            }, 260);
            this.scheduleNavPaletteRender();
            return true;
        },

        // Switch the specified preview index with transition animation
        shiftPreview(step) {
            if (!this.totalFiles) return;
            return this.setPreviewIndex(this.currentIndex + step);
        },

        // Mouse drag logic for preview images
        startPreviewDrag(e) {
            if (!this.totalFiles) return;
            this.previewDragging = true;
            this.previewDragStartX = e.clientX;
            this.previewDragDeltaX = 0;
        },
        movePreviewDrag(e) {
            if (!this.previewDragging) return;
            this.previewDragDeltaX = e.clientX - this.previewDragStartX;
        },
        endPreviewDrag() {
            if (!this.previewDragging) return;
            this.previewDragging = false;
            if (Math.abs(this.previewDragDeltaX) > 36) {
                this.shiftPreview(this.previewDragDeltaX < 0 ? 1 : -1);
            }
            this.previewDragDeltaX = 0;
        },

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
        },

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
        },
    };
}

// Global Event Listeners & Bootstrapping

// Apply swatch text contrast correction
document.addEventListener("DOMContentLoaded", () => applySwatchTextContrast());

document.addEventListener("DOMContentLoaded", () => {
    applyTheme(getStoredTheme());
    const alpineData = getUploaderData();
    if (alpineData) alpineData.schedulePaletteRender();
    initExportDockHover(document);
});

// After HTMX is successful, change the result content below
document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event?.target?.id === "result") {
        const alpineData = getUploaderData();
        const palettes = readPaletteDataFromDom(event.target);
        if (alpineData && Array.isArray(palettes) && palettes.length > 0) {
            const n = Math.max(1, parseInt(alpineData.nColors, 10) || 10);
            const previousPalette = alpineData.extractedPalettes?.[alpineData.currentIndex] || [];
            const desktop = document.getElementById("desktop-swatches");
            const mobile = document.getElementById("mobile-swatches");
            const keepDesktop = alpineData.preSubmitDesktopCount || 0;
            const keepMobile = alpineData.preSubmitMobileCount || 0;

            if (desktop) {
                updateSwatchGridLayout(desktop, n);
                renderPaletteGrid(desktop, previousPalette, n, { keepAtLeast: keepDesktop });
            }
            if (mobile) {
                renderPaletteGrid(mobile, previousPalette, n, { keepAtLeast: keepMobile });
            }

            alpineData.extractedPalettes = palettes;
            requestAnimationFrame(() => {
                alpineData.renderCurrentPalette(true, { keepDesktop, keepMobile });
                // Reset the animation length preserved before submission
                alpineData.preSubmitDesktopCount = 0;
                alpineData.preSubmitMobileCount = 0;
            });
        }
        applySwatchTextContrast(event.target);
        initMobileSheetGesture();
        initExportDockHover(event.target);
        keepDockOpenIfPointerInside(event.target);
    }
});

// HTMX Preparation : Pre-requisite checks and animation start point settings
document.body.addEventListener("htmx:beforeRequest", (event) => {
    if (event?.detail?.requestConfig?.path !== "/api/extract") return;
    const alpineData = getUploaderData();
    if (alpineData) {
        const inputEl = alpineData.$refs?.fileInput;
        const inputCount = inputEl?.files?.length || 0;
        const memoryCount = alpineData.files?.length || 0;

        // The file recorded via drag and drop will be resynchronized to input type=file so that the form can be packaged
        if (inputEl && inputCount === 0 && memoryCount > 0) {
            const dt = new DataTransfer();
            alpineData.files.forEach((file) => dt.items.add(file));
            inputEl.files = dt.files;
        }

        // Block submission when no image is selected
        if ((inputEl?.files?.length || 0) === 0) {
            event.preventDefault();
            alpineData.$refs?.fileInput?.click?.();
            return;
        }

        // Limit the maximum number of files
        if ((inputEl?.files?.length || 0) > MAX_FILES_PER_BATCH) {
            event.preventDefault();
            showTransientNotice(`Limit is ${MAX_FILES_PER_BATCH} images per run.`);
            const accepted = Array.from(inputEl.files).slice(0, MAX_FILES_PER_BATCH);
            alpineData.setFiles(accepted);
            return;
        }

        // Record the length of the current color blocks on the screen as the basis for maintaining smooth non-flickering of the staggered animation after HTMX replacement
        alpineData.preSubmitDesktopCount = document.getElementById("desktop-swatches")?.children?.length || 0;
        alpineData.preSubmitMobileCount = document.getElementById("mobile-swatches")?.children?.length || 0;
        alpineData.isWorking = true;
    }
});

// Remove loading status
document.body.addEventListener("htmx:afterRequest", (event) => {
    if (event?.detail?.requestConfig?.path !== "/api/extract") return;
    const alpineData = getUploaderData();
    if (alpineData) alpineData.isWorking = false;
});

// Handle abnormal status not stuck in loading
["htmx:responseError", "htmx:sendError", "htmx:timeout"].forEach((evt) => {
    document.body.addEventListener(evt, (event) => {
        if (event?.detail?.requestConfig?.path !== "/api/extract") return;
        const alpineData = getUploaderData();
        if (alpineData) alpineData.isWorking = false;
    });
});

// Enable the keyboard Enter key to directly submit the form, and use the arrow keys to control all preview switching and color palette number increases and decreases
document.addEventListener("keydown", (event) => {
    const alpineData = getUploaderData();
    if (!alpineData) return;
    const activeTag = String(document.activeElement?.tagName || "").toLowerCase();

    if (activeTag === "textarea") return;
    if (event.key === "Enter" && activeTag !== "input") {
        event.preventDefault();
        const form = document.getElementById("extract-form");
        if (form instanceof HTMLFormElement && alpineData.totalFiles > 0 && !alpineData.isWorking) {
            form.requestSubmit();
        }
        return;
    }
    if (activeTag === "input") return;

    if (event.key === "ArrowLeft") {
        event.preventDefault();
        alpineData.onKeyboardDown(-1);
    } else if (event.key === "ArrowRight") {
        event.preventDefault();
        alpineData.onKeyboardDown(1);
    } else if (event.key === "ArrowUp") {
        event.preventDefault();
        alpineData.stepNColors(1);
    } else if (event.key === "ArrowDown") {
        event.preventDefault();
        alpineData.stepNColors(-1);
    }
});

document.addEventListener("keyup", (event) => {
    const alpineData = getUploaderData();
    if (!alpineData) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        alpineData.onKeyboardUp();
    }
});

// Register mobile swipe gesture
document.addEventListener("DOMContentLoaded", () => {
    initMobileSheetGesture();
});

// Global click detection (for closing Popup Dock on mobile devices)
document.addEventListener("click", (event) => {
    if (!isTouchDevice()) return;
    const target = event.target;
    if (target?.closest(".iris-export-dock")) return;
    closeAllExportDock();
});

// Always record the global pointer position for keepDockOpenIfPointerInside to check
document.addEventListener("pointermove", (event) => {
    lastPointerClientX = event.clientX;
    lastPointerClientY = event.clientY;
}, { passive: true });
