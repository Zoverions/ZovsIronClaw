
/**
 * Camera Sensor Utility
 * Handles capturing frames from the user's webcam.
 */

export class CameraSensor {
  private stream: MediaStream | null = null;
  private videoTrack: MediaStreamTrack | null = null;
  private imageCapture: ImageCapture | null = null;

  async requestPermission(): Promise<boolean> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      this.videoTrack = this.stream.getVideoTracks()[0];
      this.imageCapture = new ImageCapture(this.videoTrack);
      return true;
    } catch (err) {
      console.error("Camera permission denied or failed:", err);
      return false;
    }
  }

  async captureFrameBlob(): Promise<Blob | null> {
    if (!this.imageCapture) {
        return null;
    }
    try {
        const blob = await this.imageCapture.takePhoto();
        return blob;
    } catch (err) {
        console.error("Failed to capture frame:", err);
        return null;
    }
  }

  stop() {
    if (this.videoTrack) {
        this.videoTrack.stop();
    }
    if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
    }
    this.stream = null;
    this.videoTrack = null;
    this.imageCapture = null;
  }
}
