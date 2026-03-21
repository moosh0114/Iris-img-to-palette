/**
 * @fileoverview DOM Utilities
 * This file contains reusable functions for selecting elements, handling UI notifications,
 * and manipulating palette grid layouts and background styles.
 */

const MAX_FILES_PER_BATCH = 1000;

// Device & Global Selectors

// Detect if the current device supports touch
function isTouchDevice() {
    return window.matchMedia("(hover: none)").matches || "ontouchstart" in window;
}

// Get the main image upload area element
function getUploadAreaElement() {
    return document.getElementById("upload-area");
}

// Get the Alpine.js data instance mounted on the DOM
function getUploaderData() {
    const uploaderRoot = document.querySelector("[x-data]");
    return uploaderRoot?._x_dataStack?.[0];
}

// Notifications & Contrast

// Show transient notice (Toast)
function showTransientNotice(message) {
    const text = String(message || "").trim();
    if (!text) return;

    const existing = document.querySelector(".iris-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "iris-toast";
    toast.textContent = text;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add("show");
    });
    window.setTimeout(() => {
        toast.classList.remove("show");
        window.setTimeout(() => toast.remove(), 220);
    }, 1200);
}

/**
 * Calculate high-contrast text color (black or white) based on background color
 * @param {string} hexcolor "#RRGGBB" or "RRGGBB" format
 * @returns {string} "#000000" or "#FFFFFF"
*/
function getContrastYIQ(hexcolor) {
    let hex = String(hexcolor).replace("#", "");
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    if (hex.length !== 6) return "#FFFFFF";

    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);

    // YIQ formula
    const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
    return (yiq >= 128) ? "rgba(0, 0, 0, 0.75)" : "rgba(255, 255, 255, 0.95)";
}

/**
 * Ensure text on swatches ( color codes ) is clearly visible against any background color ( automatically switches between black and white text )
 * @param {Document | HTMLElement} root Root node to search, defaults to document
*/
function applySwatchTextContrast(root = document) {
    const swatches = root.querySelectorAll(".palette-swatch[data-hex]");
    swatches.forEach((swatch) => {
        const hex = swatch.getAttribute("data-hex") || "";
        const leftTextColor = getContrastYIQ(hex);

        const label = swatch.querySelector(".palette-label");
        if (!label) return;

        label.style.backgroundImage = `linear-gradient(120deg, ${leftTextColor} 20%, var(--text-right) 80%)`;
        label.style.webkitBackgroundClip = "text";
        label.style.backgroundClip = "text";
        label.style.webkitTextFillColor = "transparent";
        label.style.color = "transparent";
        label.style.textShadow = "none";
    });
}

// Upload Area Background

function getDefaultUploadGradient() {
    return "linear-gradient(120deg, var(--primary-color) 30%, var(--mid-band) 30% 70%, var(--primary-color) 70%)";
}

/**
 * Update the upload area background with a fade-in fade-out transition
 * @param {string} nextBackground New CSS background value
*/
function setUploadAreaBackground(nextBackground) {
    const uploadArea = getUploadAreaElement();
    if (!uploadArea) return;

    const next = String(nextBackground || "").trim();
    const currentInline = String(uploadArea.style.background || "").trim();
    const currentComputed = String(window.getComputedStyle(uploadArea).background || "").trim();
    const previous = currentInline || currentComputed;

    uploadArea.querySelectorAll(".iris-upload-gradient-fade").forEach((node) => node.remove());

    if (!previous || previous === next) {
        uploadArea.style.background = next;
        return;
    }

    const fadeLayer = document.createElement("div");
    fadeLayer.className = "iris-upload-gradient-fade";
    fadeLayer.style.background = previous;
    uploadArea.insertBefore(fadeLayer, uploadArea.firstChild);

    uploadArea.style.background = next;
    requestAnimationFrame(() => {
        fadeLayer.style.opacity = "0";
    });
    window.setTimeout(() => {
        fadeLayer.remove();
    }, 320);
}

function resetUploadAreaBackground() {
    setUploadAreaBackground(getDefaultUploadGradient());
}

/**
 * Generate gradient background for upload area based on current palette
 * @param {Document | HTMLElement} root
*/
function applyPaletteBackgroundToUploadArea(root = document) {
    const uploadArea = getUploadAreaElement();
    if (!uploadArea) return;

    const uploaderData = getUploaderData();
    const currentPalette = uploaderData?.extractedPalettes?.[uploaderData.currentIndex] || [];
    const colors = currentPalette
        .map((item) => String(item?.hex || "").trim())
        .filter((hex) => /^#?[0-9a-fA-F]{6}$/.test(hex))
        .map((hex) => (hex.startsWith("#") ? hex : `#${hex}`));

    if (!colors.length) {
        resetUploadAreaBackground();
        return;
    }

    const n = colors.length;
    const leftCount = Math.ceil(n / 2);
    const rightCount = n - leftCount;
    const leftColors = colors.slice(0, leftCount);
    const rightColors = colors.slice(leftCount);
    const midStart = 30;
    const midEnd = 70;
    const gradientStops = [];

    if (leftCount > 0) {
        leftColors.forEach((color, index) => {
            const start = (midStart * index) / leftCount;
            const end = (midStart * (index + 1)) / leftCount;
            gradientStops.push(`${color} ${start}% ${end}%`);
        });
    }

    gradientStops.push(`transparent ${midStart}% ${midEnd}%`);

    if (rightCount > 0) {
        rightColors.forEach((color, index) => {
            const start = midEnd + ((100 - midEnd) * index) / rightCount;
            const end = midEnd + ((100 - midEnd) * (index + 1)) / rightCount;
            gradientStops.push(`${color} ${start}% ${end}%`);
        });
    }

    setUploadAreaBackground(`linear-gradient(120deg, ${gradientStops.join(", ")})`);
}

// Palette Grid Rendering

/**
 * Read palette JSON data stored in DOM (usually injected by HTMX after update)
 * @param {Document | HTMLElement} root 
 * @returns {Array | null}
*/
function readPaletteDataFromDom(root = document) {
    const node = root.querySelector("#palettes-data");
    if (!node) return null;
    try {
        const parsed = JSON.parse(node.textContent || "[]");
        return Array.isArray(parsed) ? parsed : null;
    } catch {
        return null;
    }
}

/**
 * Adjust swatch container Grid Layout to switch between different column counts based on the number of colors
 * @param {HTMLElement} container 
 * @param {number} count 
*/
function updateSwatchGridLayout(container, count) {
    if (!container) return;
    container.classList.remove("grid-cols-5", "grid-cols-6");
    container.classList.add(count >= 11 ? "grid-cols-6" : "grid-cols-5");
}

/**
 * Render actual swatch DOM structure
 * @param {HTMLElement} container Swatch container
 * @param {Array} palette Current color data array
 * @param {number} targetCount Target generation count
 * @param {Object} options Other options settings
*/
function renderPaletteGrid(container, palette, targetCount = 10, options = {}) {
    if (!container) return;
    const commit = Boolean(options.commit);
    const keepAtLeast = Math.max(0, Number(options.keepAtLeast || 0));
    const fadeMs = 300;
    const sourceColors = Array.isArray(palette) ? palette : [];
    const colors = sourceColors.slice(0, targetCount);
    const baseTarget = Math.max(1, targetCount);
    const previewTarget = Math.max(baseTarget, sourceColors.length);
    const keepCount = commit ? Math.max(baseTarget, keepAtLeast) : Math.max(previewTarget, keepAtLeast);
    const finalCount = commit ? baseTarget : previewTarget;

    while (container.children.length < keepCount) {
        const node = document.createElement("div");
        node.className = "h-16 sm:h-22 rounded-xl iris-swatch-empty iris-swatch-fade-in";
        container.appendChild(node);
        window.setTimeout(() => node.classList.remove("iris-swatch-fade-in"), fadeMs);
    }

    for (let i = 0; i < keepCount; i += 1) {
        const node = container.children[i];
        if (!(node instanceof HTMLElement)) continue;

        if (i < baseTarget && i < colors.length) {
            const hex = String(colors[i]?.hex || "");
            const text = hex.replace("#", "").toUpperCase();
            node.className = "palette-swatch flex h-16 sm:h-22 min-w-0 items-center justify-center rounded-xl px-2 text-center text-lg tracking-wide iris-shadow-main";
            node.setAttribute("data-hex", hex);
            node.style.setProperty("--swatch-left", hex);
            node.innerHTML = `<span class="palette-label">${text}</span>`;
            node.classList.remove("iris-swatch-dim", "iris-swatch-fade-out");
        } else if (i < baseTarget) {
            node.className = "h-16 sm:h-22 rounded-xl iris-swatch-empty";
            node.removeAttribute("data-hex");
            node.style.removeProperty("--swatch-left");
            node.innerHTML = "";
            node.classList.remove("iris-swatch-dim", "iris-swatch-fade-out");
        } else if (i < sourceColors.length) {
            const hex = String(sourceColors[i]?.hex || "");
            const text = hex.replace("#", "").toUpperCase();
            node.className = "palette-swatch flex h-16 sm:h-22 min-w-0 items-center justify-center rounded-xl px-2 text-center text-lg tracking-wide iris-shadow-main";
            node.setAttribute("data-hex", hex);
            node.style.setProperty("--swatch-left", hex);
            node.innerHTML = `<span class="palette-label">${text}</span>`;
            node.classList.add("iris-swatch-dim");
            node.classList.remove("iris-swatch-fade-out");
        } else {
            node.classList.remove("iris-swatch-dim");
            node.classList.add("iris-swatch-fade-out");
        }
    }

    if (container.children.length > finalCount) {
        for (let i = finalCount; i < container.children.length; i += 1) {
            const node = container.children[i];
            if (!(node instanceof HTMLElement)) continue;
            node.classList.remove("iris-swatch-dim");
            node.classList.add("iris-swatch-fade-out");
        }
        window.setTimeout(() => {
            while (container.children.length > finalCount) {
                container.removeChild(container.lastElementChild);
            }
            applySwatchTextContrast(container);
        }, fadeMs);
        return;
    }

    applySwatchTextContrast(container);
}
