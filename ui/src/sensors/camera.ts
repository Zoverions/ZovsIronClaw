
/**
 * Camera Sensor Utility
 * Handles capturing frames from the user's webcam using Standard Web APIs (<video> + <canvas>).
 * Compatible with all modern browsers (Chrome, Firefox, Safari/WebKit).
 */

export class CameraSensor {
  private stream: MediaStream | null = null;
  private videoElement: HTMLVideoElement | null = null;
  private canvasElement: HTMLCanvasElement | null = null;

  async requestPermission(): Promise<boolean> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

      // Initialize video element to play the stream (required for capturing frames)
      this.videoElement = document.createElement('video');
      this.videoElement.srcObject = this.stream;
      this.videoElement.playsInline = true;
      this.videoElement.muted = true;
      await this.videoElement.play();

      // Initialize canvas for drawing frames
      this.canvasElement = document.createElement('canvas');

      return true;
    } catch (err) {
      console.error("Camera permission denied or failed:", err);
      return false;
    }
  }

  async captureFrameBlob(): Promise<Blob | null> {
    if (!this.stream || !this.videoElement || !this.canvasElement) {
        return null;
    }

    try {
        // Set canvas dimensions to match video
        const width = this.videoElement.videoWidth;
        const height = this.videoElement.videoHeight;

        if (width === 0 || height === 0) return null;

        this.canvasElement.width = width;
        this.canvasElement.height = height;

        // Draw current video frame to canvas
        const ctx = this.canvasElement.getContext('2d');
        if (!ctx) return null;

        ctx.drawImage(this.videoElement, 0, 0, width, height);

        // Convert to Blob (JPEG)
        return new Promise<Blob | null>((resolve) => {
            this.canvasElement?.toBlob((blob) => {
                resolve(blob);
            }, 'image/jpeg', 0.8);
        });

    } catch (err) {
        console.error("Failed to capture frame:", err);
        return null;
    }
  }

  stop() {
    if (this.videoElement) {
        this.videoElement.pause();
        this.videoElement.srcObject = null;
        this.videoElement.remove();
        this.videoElement = null;
    }

    if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
    }

    this.canvasElement = null;
  }
}
