/**
 * UI Component: Export Dock
 * Handles copying and exporting color palettes.
 */

// Copy palette JSON to clipboard
function copyPaletteJson(button) {
    if (isTouchDevice()) {
        const dock = button?.closest(".iris-export-dock");
        if (dock && !dock.classList.contains("open")) {
            dock.classList.add("open");
            return;
        }
    }
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
    closeAllExportDock();
}

// Generate a shorter unique identifier
function shortUniqueId() {
    const t = Date.now().toString(36);
    const p = Math.floor(performance.now()).toString(36);
    const r = Math.floor(Math.random() * 1679616).toString(36);
    return `${t}${p}${r}`;
}

// Export palette to TXT file and download
function exportPaletteTxt(button) {
    const jsonNode = document.getElementById("palette-json");
    if (!jsonNode) return;
    const content = jsonNode.innerText || jsonNode.textContent || "";
    const uploaderData = getUploaderData();
    const count = uploaderData?.extractedPalettes?.length || uploaderData?.totalFiles || 1;
    const filename = `Iris_OKLCH_${count}_${shortUniqueId()}.txt`;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    if (button) {
        button.classList.add("opacity-50");
        window.setTimeout(() => button.classList.remove("opacity-50"), 500);
    }
    closeAllExportDock();
}

// Toggle export dock open/close
function toggleExportDock(triggerButton) {
    const dock = triggerButton?.closest(".iris-export-dock");
    if (!dock) return;
    dock.classList.toggle("open");
}

// Close all export docks on the screen
function closeAllExportDock() {
    document.querySelectorAll(".iris-export-dock.open").forEach((dock) => dock.classList.remove("open"));
}

// Initialize export dock hover effect
function initExportDockHover(root = document) {
    const docks = root.querySelectorAll(".iris-export-dock");
    docks.forEach((dock) => {
        if (dock.dataset.hoverBound === "1") return;
        dock.dataset.hoverBound = "1";
        dock.addEventListener("mouseenter", () => {
            if (isTouchDevice()) return;
            dock.classList.add("open");
        });
        dock.addEventListener("mouseleave", (event) => {
            if (isTouchDevice()) return;
            const next = event.relatedTarget;
            if (next && dock.contains(next)) return;
            dock.classList.remove("open");
        });
    });
}

// Keep dock open if pointer is inside
function keepDockOpenIfPointerInside(root = document) {
    if (typeof lastPointerClientX === "undefined" || typeof lastPointerClientY === "undefined") return;
    if (lastPointerClientX < 0 || lastPointerClientY < 0) return;
    const docks = root.querySelectorAll(".iris-export-dock");
    docks.forEach((dock) => {
        const rect = dock.getBoundingClientRect();
        const inside = lastPointerClientX >= rect.left
            && lastPointerClientX <= rect.right
            && lastPointerClientY >= rect.top
            && lastPointerClientY <= rect.bottom;
        if (inside) dock.classList.add("open");
    });
}
