// Global Event Listeners & Bootstrapping

let lastPointerClientX = -1;
let lastPointerClientY = -1;

// Apply swatch text contrast correction
document.addEventListener("DOMContentLoaded", () => applySwatchTextContrast());

document.addEventListener("DOMContentLoaded", () => {
    applyTheme(getStoredTheme());
    const alpineData = getUploaderData();
    if (alpineData && typeof alpineData.schedulePaletteRender === "function") {
        alpineData.schedulePaletteRender();
    }
    initExportDockHover(document);
});

function applyExtractResponse(target) {
    if (!target) return;

    const alpineData = getUploaderData();
    const palettes = readPaletteDataFromDom(target);
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
            if (typeof alpineData.renderCurrentPalette === "function") {
                alpineData.renderCurrentPalette(true, { keepDesktop, keepMobile });
            }
            alpineData.preSubmitDesktopCount = 0;
            alpineData.preSubmitMobileCount = 0;
        });
    }
    applySwatchTextContrast(target);
    initMobileSheetGesture();
    initExportDockHover(target);
    keepDockOpenIfPointerInside(target);
}

async function submitExtractBatch(form) {
    const alpineData = getUploaderData();
    if (!alpineData || !(form instanceof HTMLFormElement)) return;

    const inputEl = alpineData.$refs?.fileInput;
    const inputCount = inputEl?.files?.length || 0;
    const memoryCount = alpineData.files?.length || 0;

    if (inputEl && inputCount === 0 && memoryCount > 0) {
        const dt = new DataTransfer();
        alpineData.files.forEach((file) => dt.items.add(file));
        inputEl.files = dt.files;
    }

    const selectedFiles = Array.from(inputEl?.files || []);
    if (selectedFiles.length === 0) {
        alpineData.$refs?.fileInput?.click?.();
        return;
    }

    if (selectedFiles.length > MAX_FILES_PER_BATCH) {
        showTransientNotice(`Limit is ${MAX_FILES_PER_BATCH} images per run.`);
        alpineData.setFiles(selectedFiles.slice(0, MAX_FILES_PER_BATCH));
        return;
    }

    alpineData.preSubmitDesktopCount = document.getElementById("desktop-swatches")?.children?.length || 0;
    alpineData.preSubmitMobileCount = document.getElementById("mobile-swatches")?.children?.length || 0;
    alpineData.isWorking = true;

    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append("images", file));
    formData.append("n_colors", String(alpineData.nColors || "10"));
    formData.append("current_index", String(alpineData.currentIndex || 0));
    formData.append("method", String(alpineData.extractMethod || "kmeans"));

    const result = document.getElementById("result");

    try {
        const response = await fetch("/api/extract", {
            method: "POST",
            body: formData,
        });
        const html = await response.text();

        if (response.status === 429) {
            showTransientNotice("Rate limit exceeded. Please try again in 10 seconds.", 10000);
            return;
        }

        if (result) {
            result.innerHTML = html;
            applyExtractResponse(result);
        }
    } catch {
        showTransientNotice("Upload failed. Please try again.");
    } finally {
        alpineData.isWorking = false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("extract-form");
    if (!(form instanceof HTMLFormElement)) return;

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        void submitExtractBatch(form);
    });
});

// After HTMX is successful, change the result content below
document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event?.target?.id === "result") {
        applyExtractResponse(event.target);
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
