/**
 * Theme Management Utilities
 * Handles the application's light/dark mode state.
 */

/**
 * Retrieve theme settings stored in local storage
 * @returns {"light" | "dark"} Default is "light"
 */
function getStoredTheme() {
    try {
        const theme = localStorage.getItem("iris-theme");
        return theme === "dark" ? "dark" : "light";
    } catch {
        return "light";
    }
}

/**
 * Apply the specified theme (theme), add fade-in fade-out animation, and update LocalStorage
 * @param {"light" | "dark"} theme Target theme
 */
function applyTheme(theme) {
    const safeTheme = theme === "dark" ? "dark" : "light";
    const uploadArea = getUploadAreaElement();
    const previousUploadBackground = uploadArea ? String(window.getComputedStyle(uploadArea).background || "").trim() : "";

    document.documentElement.setAttribute("data-theme", safeTheme);
    try {
        localStorage.setItem("iris-theme", safeTheme);
    } catch {
        // ignore storage failures
    }

    // Handle upload area background animation effect
    if (uploadArea && previousUploadBackground) {
        const fadeLayer = document.createElement("div");
        fadeLayer.className = "iris-upload-theme-fade";
        fadeLayer.style.background = previousUploadBackground;
        uploadArea.insertBefore(fadeLayer, uploadArea.firstChild);

        requestAnimationFrame(() => {
            fadeLayer.style.opacity = "0";
        });

        window.setTimeout(() => {
            fadeLayer.remove();
        }, 720);
    }

    // Update Alpine.js data state
    const uploaderData = getUploaderData();
    if (uploaderData) uploaderData.isDark = safeTheme === "dark";
}
