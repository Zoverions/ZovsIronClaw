import { LitElement, html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { CameraSensor } from "../../sensors/camera.js";
import { icons } from "../icons.js";

@customElement("neural-link")
export class NeuralLink extends LitElement {
  @state() isActive = false;
  @state() showManifesto = false;
  @state() permissionGranted = false;
  @state() feedbackMessage: string | null = null;
  @state() feedbackType: "info" | "warning" = "info";

  private camera = new CameraSensor();
  private loopInterval: number | null = null;
  private backendUrl = "http://localhost:8000"; // Assuming local dev, or proxied

  static styles = css`
    :host {
      display: inline-block;
    }

    .toggle-btn {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      font-family: monospace;
      font-size: 0.75rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.2s ease;
      background: #1f2937;
      color: #9ca3af;
      border: 1px solid #374151;
    }

    .toggle-btn:hover {
      background: #374151;
    }

    .toggle-btn.active {
      background: #064e3b; /* green-900 */
      color: #d1fae5; /* green-100 */
      border-color: #10b981; /* green-500 */
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }

    .icon-pulse {
      animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: .5; }
    }

    /* Modal Styles */
    .modal-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      backdrop-filter: blur(4px);
    }

    .modal-content {
      background: #111827;
      border: 1px solid #374151;
      border-radius: 0.5rem;
      padding: 1.5rem;
      max-width: 500px;
      width: 90%;
      color: #e5e7eb;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }

    .modal-header {
      font-size: 1.125rem;
      font-weight: bold;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .warning-box {
      background: rgba(127, 29, 29, 0.3);
      border: 1px solid rgba(239, 68, 68, 0.5);
      padding: 1rem;
      border-radius: 0.25rem;
      margin-bottom: 1rem;
      font-size: 0.875rem;
      color: #fca5a5;
    }

    .terms-list {
      font-size: 0.875rem;
      color: #d1d5db;
      margin-bottom: 1.5rem;
      padding-left: 1rem;
      border-left: 2px solid #4b5563;
    }

    .terms-list p {
      margin-bottom: 0.5rem;
    }

    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
    }

    .btn {
      padding: 0.5rem 1rem;
      border-radius: 0.25rem;
      font-size: 0.875rem;
      font-weight: 500;
      cursor: pointer;
      border: none;
    }

    .btn-secondary {
      background: transparent;
      color: #9ca3af;
    }
    .btn-secondary:hover {
      color: #f3f4f6;
      background: #374151;
    }

    .btn-primary {
      background: #2563eb;
      color: white;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .btn-primary:hover {
      background: #1d4ed8;
    }

    /* Feedback Toast */
    .feedback-toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #1f2937;
      border-left: 4px solid #3b82f6;
      padding: 1rem;
      border-radius: 0.25rem;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
      z-index: 100;
      max-width: 300px;
      animation: slideIn 0.3s ease-out;
    }

    .feedback-toast.warning {
      border-left-color: #ef4444;
    }

    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;

  disconnectedCallback() {
    super.disconnectedCallback();
    this.stopLoop();
  }

  toggleLink() {
    if (this.isActive) {
      // Kill Switch
      this.stopLoop();
    } else {
      if (!this.permissionGranted) {
        this.showManifesto = true;
      } else {
        this.startLoop();
      }
    }
  }

  async handleConsent() {
    this.showManifesto = false;
    const success = await this.camera.requestPermission();
    if (success) {
      this.permissionGranted = true;
      this.startLoop();
    } else {
      alert("Hardware access denied.");
    }
  }

  startLoop() {
    this.isActive = true;
    document.body.classList.add("neural-link-active");

    // Start polling loop (every 5 seconds)
    this.loopInterval = window.setInterval(() => this.captureAndSend(), 5000);

    // Initial capture
    this.captureAndSend();
  }

  stopLoop() {
    this.isActive = false;
    document.body.classList.remove("neural-link-active");
    if (this.loopInterval) {
      clearInterval(this.loopInterval);
      this.loopInterval = null;
    }
    this.camera.stop();
  }

  async captureAndSend() {
    if (!this.isActive) return;

    const blob = await this.camera.captureFrameBlob();
    if (!blob) return;

    const fd = new FormData();
    fd.append("file", blob, "capture.jpg");
    fd.append("modality", "vision");

    try {
        // In real dev, use a proxy or env var for URL.
        // Assuming GCA service is on port 8000 (proxied via gateway or direct)
        const res = await fetch(`${this.backendUrl}/v1/observe`, {
            method: "POST",
            body: fd
        });

        if (res.ok) {
            const data = await res.json();
            if (data.alignment && !data.alignment.aligned) {
                this.showFeedback(data.alignment.reason, "warning");
            }
        }
    } catch (err) {
        console.error("Observer API failed:", err);
    }
  }

  showFeedback(message: string, type: "info" | "warning") {
    this.feedbackMessage = message;
    this.feedbackType = type;
    setTimeout(() => {
        this.feedbackMessage = null;
    }, 8000);
  }

  render() {
    return html`
      <!-- Toggle Button -->
      <button
        class="toggle-btn ${this.isActive ? "active" : ""}"
        @click=${this.toggleLink}
        title="Toggle Observer Module"
      >
        <span class="${this.isActive ? "icon-pulse" : ""}" style="width: 1.25em; height: 1.25em; display: inline-flex;">${icons.ironClaw}</span>
        <span>${this.isActive ? "NEURAL LINK: ACTIVE" : "OBSERVER: OFFLINE"}</span>
      </button>

      <!-- Manifesto Modal -->
      ${this.showManifesto ? html`
        <div class="modal-backdrop">
          <div class="modal-content">
            <div class="modal-header">
               <span>⚠️ NEURAL LINK PROTOCOL</span>
            </div>

            <div class="warning-box">
              <strong>This feature is OPT-IN.</strong><br/>
              Enabling this allows the AI to monitor your visual state to optimize your workflow entropy.
            </div>

            <div class="terms-list">
              <p>• <strong>No Cloud Uploads:</strong> Data is processed locally by the GCA Python Brain.</p>
              <p>• <strong>Ephemeral Storage:</strong> Raw frames are deleted immediately after vector extraction.</p>
              <p>• <strong>Goal Alignment:</strong> Data is used strictly to steer the system toward your GOAL.md.</p>
              <p>• <strong>Revocable:</strong> Close the app or toggle off to sever the link.</p>
            </div>

            <div class="modal-actions">
              <button class="btn btn-secondary" @click=${() => this.showManifesto = false}>ABORT</button>
              <button class="btn btn-primary" @click=${this.handleConsent}>CONFIRM HANDSHAKE</button>
            </div>
          </div>
        </div>
      ` : nothing}

      <!-- Feedback Toast -->
      ${this.feedbackMessage ? html`
        <div class="feedback-toast ${this.feedbackType}">
           <strong>Feedback:</strong> ${this.feedbackMessage}
        </div>
      ` : nothing}
    `;
  }
}
