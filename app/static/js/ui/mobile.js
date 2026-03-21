/**
 * UI Component: Mobile Sheet
 * Handles the mobile swipe-up sheet for the color palette.
 */

// Toggle mobile sheet open/close
function toggleMobileSheet() {
    const sheet = document.getElementById("mobile-sheet");
    if (!sheet) return;
    setMobileSheetOpen(sheet, !sheet.classList.contains("open"));
}

// Set mobile sheet open/close state
function setMobileSheetOpen(sheet, shouldOpen) {
    if (!sheet) return;
    sheet.classList.remove("anim-open", "anim-close");
    if (shouldOpen) {
        sheet.classList.add("open", "anim-open");
    } else {
        sheet.classList.add("anim-close");
        window.setTimeout(() => {
            sheet.classList.remove("open");
            sheet.classList.remove("anim-close");
        }, 260);
    }
}

// Initialize mobile sheet gesture
function initMobileSheetGesture() {
    const sheet = document.getElementById("mobile-sheet");
    if (!sheet) return;
    let startY = 0;
    let active = false;

    sheet.addEventListener("touchstart", (e) => {
        if (!e.touches?.length) return;
        active = true;
        startY = e.touches[0].clientY;
    }, { passive: true });

    sheet.addEventListener("touchend", (e) => {
        if (!active || !e.changedTouches?.length) return;
        const delta = e.changedTouches[0].clientY - startY;
        if (delta < -24) {
            setMobileSheetOpen(sheet, true);
        } else if (delta > 24) {
            setMobileSheetOpen(sheet, false);
        }
        active = false;
    }, { passive: true });
}
