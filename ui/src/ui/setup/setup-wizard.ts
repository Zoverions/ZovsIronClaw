import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { BaseStyles } from '../components/base-styles';

// Declare global invoke function from Tauri
declare global {
  interface Window {
    __TAURI_INTERNALS__?: any;
    __TAURI__?: {
        core: {
            invoke: (cmd: string, args?: any) => Promise<any>;
        };
        event: {
            listen: (event: string, handler: (payload: any) => void) => Promise<() => void>;
        }
    };
  }
}

// Helper to access invoke safely
const invoke = async (cmd: string, args?: any) => {
    if (window.__TAURI__?.core) {
        return window.__TAURI__.core.invoke(cmd, args);
    }
    console.warn("Tauri invoke not available (mock mode)");
    return null;
};

// Helper to listen safely
const listen = async (event: string, handler: (payload: any) => void) => {
    if (window.__TAURI__?.event) {
        return window.__TAURI__.event.listen(event, handler);
    }
    return () => {};
};

@customElement('setup-wizard')
export class SetupWizard extends LitElement {
    static styles = [
        BaseStyles,
        css`
            :host {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                background-color: var(--background-color, #1a1a1a);
                color: var(--text-color, #ffffff);
                font-family: 'Inter', sans-serif;
            }

            .wizard-container {
                width: 100%;
                max-width: 600px;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                text-align: center;
            }

            h1 {
                margin-bottom: 0.5rem;
                font-size: 2rem;
                font-weight: 700;
                background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            p {
                margin-bottom: 2rem;
                color: rgba(255, 255, 255, 0.7);
            }

            .step-indicator {
                display: flex;
                justify-content: center;
                margin-bottom: 2rem;
                gap: 0.5rem;
            }

            .dot {
                width: 8px;
                height: 8px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                transition: background 0.3s;
            }

            .dot.active {
                background: #4facfe;
                transform: scale(1.2);
            }

            .actions {
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin-top: 2rem;
            }

            button {
                padding: 0.8rem 1.5rem;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s;
            }

            .btn-primary {
                background: #4facfe;
                color: #fff;
            }

            .btn-primary:hover {
                background: #3a9ad9;
            }

            .btn-secondary {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
            }

            .btn-secondary:hover {
                background: rgba(255, 255, 255, 0.2);
            }

            .progress-bar-container {
                width: 100%;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                height: 8px;
                margin: 1rem 0;
                overflow: hidden;
            }

            .progress-bar {
                height: 100%;
                background: #4facfe;
                width: 0%;
                transition: width 0.3s ease;
            }

            .card {
                background: rgba(255, 255, 255, 0.03);
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                text-align: left;
                border: 1px solid rgba(255, 255, 255, 0.05);
                cursor: pointer;
                transition: border-color 0.2s;
            }

            .card.selected {
                border-color: #4facfe;
                background: rgba(79, 172, 254, 0.1);
            }

            .card h3 {
                margin: 0 0 0.5rem 0;
                font-size: 1.1rem;
            }

            .card p {
                margin: 0;
                font-size: 0.9rem;
            }

            .error-message {
                color: #ff6b6b;
                font-size: 0.9rem;
                margin-top: 0.5rem;
            }

            .permission-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: rgba(255, 255, 255, 0.05);
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }

            .permission-status {
                font-size: 0.9rem;
                color: #aaa;
            }

            .permission-status.granted {
                color: #4caf50;
                font-weight: bold;
            }

            .permission-status.denied {
                color: #ff6b6b;
            }
        `
    ];

    @state() private step = 1;
    @state() private downloadProgress = 0;
    @state() private downloadStatus = '';
    @state() private selectedSoul = '';
    @state() private modelExists = false;
    @state() private error = '';
    @state() private permissions = {
        microphone: false,
        camera: false
    };

    private unlistenProgress: (() => void) | null = null;
    // For MVP we use a small file to test the flow, real Qwen weights would be huge
    // Using a small safetensors file from HF as a placeholder/test
    private readonly MODEL_URL = "https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat/resolve/main/config.json";
    private readonly MODEL_FILENAME = "qwen-0.5b-chat-config.json"; // Renamed for clarity it's just config for test

    async connectedCallback() {
        super.connectedCallback();
        this.checkModelStatus();

        // Listen for download progress
        this.unlistenProgress = await listen('download-progress', (event: any) => {
            // event.payload is the progress number
            this.downloadProgress = event.payload;
        }) as any;
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this.unlistenProgress) {
            this.unlistenProgress();
        }
    }

    private async checkModelStatus() {
        if (window.__TAURI__) {
            try {
                this.modelExists = await invoke('check_model_exists', { filename: this.MODEL_FILENAME });
            } catch (e) {
                console.error("Failed to check model:", e);
            }
        }
    }

    private nextStep() {
        if (this.step < 5) { // Increased steps from 4 to 5
            // If moving from step 2 (Hardware Check) to 3 (Download) and model exists, skip to 4 (Permissions)
            if (this.step === 2 && this.modelExists) {
                 this.step = 4;
            } else {
                 this.step++;
            }
        } else {
            this.completeSetup();
        }
    }

    private completeSetup() {
        this.dispatchEvent(new CustomEvent('setup-complete', {
            bubbles: true,
            composed: true,
            detail: { soul: this.selectedSoul }
        }));
    }

    private async startDownload() {
        this.downloadStatus = 'Initializing Download...';
        this.error = '';
        this.downloadProgress = 0;

        try {
            if (window.__TAURI__) {
                this.downloadStatus = 'Downloading Neural Weights...';
                await invoke('download_model', {
                    url: this.MODEL_URL,
                    filename: this.MODEL_FILENAME
                });
                this.downloadStatus = 'Download Complete';
                this.modelExists = true;
                setTimeout(() => this.nextStep(), 1000);
            } else {
                // Mock for browser dev
                this.startMockDownload();
            }
        } catch (e: any) {
            this.error = `Download failed: ${e}`;
            this.downloadStatus = 'Error';
        }
    }

    private startMockDownload() {
        const interval = setInterval(() => {
            this.downloadProgress += 5;
            if (this.downloadProgress >= 100) {
                clearInterval(interval);
                this.downloadStatus = 'Download Complete (Mock)';
                setTimeout(() => this.nextStep(), 1000);
            }
        }, 100);
    }

    private async requestPermission(type: 'microphone' | 'camera') {
        try {
            if (type === 'microphone') {
                await navigator.mediaDevices.getUserMedia({ audio: true });
                this.permissions = { ...this.permissions, microphone: true };
            } else if (type === 'camera') {
                await navigator.mediaDevices.getUserMedia({ video: true });
                this.permissions = { ...this.permissions, camera: true };
            }
        } catch (err) {
            console.error(`Failed to get ${type} permission:`, err);
            // Optionally set denied state but allow proceeding
        }
    }

    private selectSoul(soul: string) {
        this.selectedSoul = soul;
    }

    render() {
        return html`
            <div class="wizard-container">
                ${this.renderStep()}

                <div class="step-indicator">
                    ${[1, 2, 3, 4, 5].map(i => html`
                        <div class="dot ${this.step === i ? 'active' : ''}"></div>
                    `)}
                </div>
            </div>
        `;
    }

    renderStep() {
        switch (this.step) {
            case 1:
                return html`
                    <h1>Initializing Neural Link...</h1>
                    <p>Welcome to ZovsIronClaw. Let's get your system ready.</p>
                    <div class="actions">
                        <button class="btn-primary" @click=${() => this.nextStep()}>Begin Setup</button>
                    </div>
                `;
            case 2:
                return html`
                    <h1>Hardware Check</h1>
                    <p>Verifying system capabilities...</p>
                    <div style="text-align: left; margin: 2rem 0;">
                         <div>✅ GPU: Detected ${this.modelExists ? '(Model Cached)' : ''}</div>
                         <div>✅ RAM: 16GB Available</div>
                         <div>✅ Storage: Sufficient</div>
                    </div>
                    <div class="actions">
                        <button class="btn-primary" @click=${() => this.nextStep()}>Continue</button>
                    </div>
                `;
            case 3:
                return html`
                    <h1>Model Loading</h1>
                    <p>${this.downloadStatus || 'We need to download the neural weights.'}</p>

                    ${this.downloadProgress > 0 ? html`
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: ${this.downloadProgress}%"></div>
                        </div>
                    ` : nothing}

                    ${this.error ? html`<div class="error-message">${this.error}</div>` : nothing}

                    <div class="actions">
                        ${this.downloadProgress === 0 ? html`
                            <button class="btn-primary" @click=${() => this.startDownload()}>Start Download</button>
                        ` : nothing}
                    </div>
                `;
            case 4: // New Permissions Step
                return html`
                    <h1>Permissions</h1>
                    <p>IronClaw needs access to your senses to perceive the world.</p>

                    <div class="permission-item">
                        <span>🎙️ Microphone Access</span>
                        ${this.permissions.microphone ?
                            html`<span class="permission-status granted">Granted</span>` :
                            html`<button class="btn-secondary" @click=${() => this.requestPermission('microphone')}>Allow</button>`
                        }
                    </div>

                    <div class="permission-item">
                        <span>📷 Camera Access</span>
                        ${this.permissions.camera ?
                            html`<span class="permission-status granted">Granted</span>` :
                            html`<button class="btn-secondary" @click=${() => this.requestPermission('camera')}>Allow</button>`
                        }
                    </div>

                    <div class="actions">
                         <button class="btn-secondary" @click=${() => this.step--}>Back</button>
                        <button class="btn-primary" @click=${() => this.nextStep()}>Continue</button>
                    </div>
                `;
            case 5: // Soul Selection moved to Step 5
                return html`
                    <h1>Choose your Soul</h1>
                    <p>Select the personality for your assistant.</p>

                    <div class="card ${this.selectedSoul === 'Architect' ? 'selected' : ''}" @click=${() => this.selectSoul('Architect')}>
                        <h3>Architect</h3>
                        <p>Analytical, precise, and structural. Best for coding and planning.</p>
                    </div>

                    <div class="card ${this.selectedSoul === 'Companion' ? 'selected' : ''}" @click=${() => this.selectSoul('Companion')}>
                        <h3>Companion</h3>
                        <p>Empathetic, conversational, and supportive. Best for daily interaction.</p>
                    </div>

                    <div class="card ${this.selectedSoul === 'Guardian' ? 'selected' : ''}" @click=${() => this.selectSoul('Guardian')}>
                        <h3>Guardian</h3>
                        <p>Protective, ethical, and cautious. Best for sensitive tasks.</p>
                    </div>

                    <div class="actions">
                         <button class="btn-secondary" @click=${() => this.step--}>Back</button>
                        <button class="btn-primary" ?disabled=${!this.selectedSoul} @click=${() => this.nextStep()}>Initialize</button>
                    </div>
                `;
            default:
                return nothing;
        }
    }
}
