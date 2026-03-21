function uploaderFile() {
    return {
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
        }
    };
}
