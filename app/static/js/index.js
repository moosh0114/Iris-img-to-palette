/**
 * @fileoverview Main Application & Alpine.js Component
 * Handles the core uploader state, file parsing, keyboard shortcuts, 
 * and HTMX lifecycle interactions.
 */

/**
 * Initialize the core uploader component of Alpine.js
 * Responsible for managing image preview, color extraction quantity, upload status, and receiving keyboard and screen event operations.
 * @returns {Object} Alpine.js data object
 */
function uploader() {
    return {
        ...uploaderState(),
        ...uploaderTheme(),
        ...uploaderFile(),
        ...uploaderPreview(),
        ...uploaderPalette(),
        ...uploaderKeyboard()
    };
}
