function uploaderTheme() {
    return {
        // Toggle dark/light theme
        toggleTheme() {
            if (this.themeTransitioning) return;
            this.themeTransitioning = true;
            this.isDark = !this.isDark;
            applyTheme(this.isDark ? "dark" : "light");
            window.setTimeout(() => {
                this.themeTransitioning = false;
            }, 700);
        }
    };
}
