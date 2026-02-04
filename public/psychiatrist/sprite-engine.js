/**
 * Sprite Animation Engine for Dr. Sigmund 2000
 * 
 * A lightweight, vanilla JavaScript sprite animation system.
 * Plays mood-based animations using canvas rendering.
 */

class SpriteEngine {
    constructor(canvasId, configPath) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.configPath = configPath;
        this.basePath = configPath.substring(0, configPath.lastIndexOf('/') + 1);
        
        this.config = null;
        this.images = {};
        this.currentMood = 'neutral';
        this.currentFrame = 0;
        this.lastFrameTime = 0;
        this.isPlaying = false;
        this.isLoaded = false;
        this.onLoadCallback = null;
        this.onErrorCallback = null;
    }

    /**
     * Initialize the sprite engine - loads config and preloads all images
     */
    async init() {
        try {
            // Load configuration
            const response = await fetch(this.configPath);
            if (!response.ok) {
                throw new Error(`Failed to load config: ${response.statusText}`);
            }
            this.config = await response.json();
            
            // Set canvas size
            this.canvas.width = this.config.frameSize.width;
            this.canvas.height = this.config.frameSize.height;
            
            // Preload all images
            await this.preloadImages();
            
            this.isLoaded = true;
            console.log('[SpriteEngine] Initialized successfully');
            
            if (this.onLoadCallback) {
                this.onLoadCallback();
            }
            
            return true;
        } catch (error) {
            console.error('[SpriteEngine] Initialization failed:', error);
            if (this.onErrorCallback) {
                this.onErrorCallback(error);
            }
            return false;
        }
    }

    /**
     * Preload all animation frame images
     */
    async preloadImages() {
        const loadPromises = [];
        
        for (const [mood, animation] of Object.entries(this.config.animations)) {
            this.images[mood] = [];
            
            for (const framePath of animation.frames) {
                const promise = new Promise((resolve, reject) => {
                    const img = new Image();
                    img.onload = () => {
                        this.images[mood].push(img);
                        resolve();
                    };
                    img.onerror = () => {
                        console.warn(`[SpriteEngine] Failed to load: ${framePath}`);
                        // Create a placeholder for failed images
                        this.images[mood].push(null);
                        resolve(); // Don't reject, just use null
                    };
                    img.src = this.basePath + framePath;
                });
                loadPromises.push(promise);
            }
        }
        
        await Promise.all(loadPromises);
        console.log(`[SpriteEngine] Loaded ${Object.keys(this.images).length} animation sets`);
    }

    /**
     * Set callback for when engine is loaded
     */
    onLoad(callback) {
        this.onLoadCallback = callback;
        if (this.isLoaded) {
            callback();
        }
    }

    /**
     * Set callback for errors
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }

    /**
     * Start playing the animation
     */
    play() {
        if (!this.isLoaded) {
            console.warn('[SpriteEngine] Cannot play - not loaded yet');
            return;
        }
        
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        this.lastFrameTime = performance.now();
        this.animate();
    }

    /**
     * Stop the animation
     */
    stop() {
        this.isPlaying = false;
    }

    /**
     * Set the current mood animation
     */
    setMood(mood) {
        if (!this.config || !this.config.animations[mood]) {
            console.warn(`[SpriteEngine] Unknown mood: ${mood}, defaulting to neutral`);
            mood = 'neutral';
        }
        
        if (this.currentMood !== mood) {
            console.log(`[SpriteEngine] Mood changed: ${this.currentMood} → ${mood}`);
            this.currentMood = mood;
            this.currentFrame = 0;
        }
    }

    /**
     * Get current mood
     */
    getMood() {
        return this.currentMood;
    }

    /**
     * Main animation loop
     */
    animate() {
        if (!this.isPlaying) return;
        
        const now = performance.now();
        const animation = this.config.animations[this.currentMood];
        const frameDuration = animation.frameDuration;
        
        // Check if it's time for next frame
        if (now - this.lastFrameTime >= frameDuration) {
            this.currentFrame++;
            
            // Loop or stop at end
            if (this.currentFrame >= animation.frames.length) {
                if (animation.loop) {
                    this.currentFrame = 0;
                } else {
                    this.currentFrame = animation.frames.length - 1;
                }
            }
            
            this.lastFrameTime = now;
            this.render();
        }
        
        requestAnimationFrame(() => this.animate());
    }

    /**
     * Render the current frame
     */
    render() {
        const frames = this.images[this.currentMood];
        const img = frames[this.currentFrame];
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (img) {
            // Draw the sprite, scaling to fit canvas
            this.ctx.imageSmoothingEnabled = false; // Keep pixel art crisp
            this.ctx.drawImage(
                img,
                0, 0,
                this.canvas.width,
                this.canvas.height
            );
        } else {
            // Draw placeholder if image failed to load
            this.ctx.fillStyle = '#008080';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.fillStyle = '#00FF00';
            this.ctx.font = '12px "Courier New", monospace';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('LOADING...', this.canvas.width / 2, this.canvas.height / 2);
        }
    }

    /**
     * Check if engine is ready
     */
    isReady() {
        return this.isLoaded;
    }

    /**
     * Get available moods
     */
    getAvailableMoods() {
        if (!this.config) return [];
        return Object.keys(this.config.animations);
    }
}

// Export for module systems, but also make available globally
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpriteEngine;
}
