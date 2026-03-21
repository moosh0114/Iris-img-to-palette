function uploaderState() {
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
    };
}
