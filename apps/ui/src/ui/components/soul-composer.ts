import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { createGCAProvider, GCAProvider, SoulInfo, SoulConfig } from '../../providers/gca-bridge.js';

@customElement('soul-composer')
export class SoulComposer extends LitElement {
    @state() souls: string[] = [];
    @state() details: Record<string, SoulInfo> = {};
    @state() loading = false;
    @state() error: string | null = null;

    @state() baseSoul = 'Architect';
    @state() blendSouls: string[] = [];
    @state() blendWeights: Record<string, number> = {};

    @state() compositeResult: any = null;

    private provider: GCAProvider;

    constructor() {
        super();
        // Default to localhost:8000 for GCA service
        this.provider = createGCAProvider({
            serviceUrl: 'http://localhost:8000',
            riskTolerance: 0.3
        });
    }

    connectedCallback() {
        super.connectedCallback();
        this.fetchSouls();
    }

    async fetchSouls() {
        this.loading = true;
        this.error = null;
        try {
            const result = await this.provider.listSouls();
            this.souls = result.souls;
            this.details = result.details;
            // Ensure baseSoul is valid if not empty
            if (this.souls.length > 0 && !this.souls.includes(this.baseSoul)) {
                this.baseSoul = this.souls[0];
            }
        } catch (e) {
            this.error = `Failed to load souls: ${String(e)}`;
        } finally {
            this.loading = false;
        }
    }

    handleBaseChange(e: Event) {
        this.baseSoul = (e.target as HTMLSelectElement).value;
    }

    handleBlendToggle(soul: string, checked: boolean) {
        if (checked) {
            this.blendSouls = [...this.blendSouls, soul];
            this.blendWeights = { ...this.blendWeights, [soul]: 0.5 }; // Default weight
        } else {
            this.blendSouls = this.blendSouls.filter(s => s !== soul);
            const newWeights = { ...this.blendWeights };
            delete newWeights[soul];
            this.blendWeights = newWeights;
        }
    }

    handleWeightChange(soul: string, value: number) {
        this.blendWeights = { ...this.blendWeights, [soul]: value };
    }

    async handleCompose() {
        this.loading = true;
        this.error = null;
        this.compositeResult = null;

        const weights = this.blendSouls.map(s => this.blendWeights[s]);

        const config: SoulConfig = {
            base_style: this.baseSoul,
            blend_styles: this.blendSouls,
            blend_weights: weights
        };

        try {
            const result = await this.provider.composeSoul(config);
            this.compositeResult = result;
        } catch (e) {
            this.error = `Failed to compose soul: ${String(e)}`;
        } finally {
            this.loading = false;
        }
    }

    static styles = css`
        :host {
            display: block;
            padding: 20px;
            color: #e5e7eb;
            background: #111827;
            border-radius: 8px;
        }

        h2 { margin-top: 0; }

        .section {
            margin-bottom: 24px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }

        .row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }

        select {
            background: #374151;
            color: white;
            border: 1px solid #4b5563;
            padding: 8px;
            border-radius: 4px;
            width: 100%;
            max-width: 300px;
        }

        .checkbox-group {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
        }

        .slider-group {
            margin-top: 12px;
        }

        input[type="range"] {
            width: 100%;
            accent-color: #3b82f6;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s;
        }

        button:hover {
            background: #1d4ed8;
        }

        button:disabled {
            background: #4b5563;
            cursor: not-allowed;
        }

        .error {
            color: #ef4444;
            padding: 12px;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 4px;
            margin-bottom: 16px;
        }

        .result {
            background: #064e3b;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #059669;
        }

        code {
            display: block;
            white-space: pre-wrap;
            background: rgba(0,0,0,0.3);
            padding: 12px;
            border-radius: 4px;
            margin-top: 8px;
            font-family: monospace;
        }
    `;

    render() {
        return html`
            <h2>Soul Composer</h2>

            ${this.error ? html`<div class="error">${this.error}</div>` : nothing}

            <div class="section">
                <h3>1. Select Base Soul</h3>
                <p>The foundation of the conscience.</p>
                <select @change=${this.handleBaseChange} .value=${this.baseSoul}>
                    ${this.souls.map(s => html`<option value=${s} ?selected=${s === this.baseSoul}>${s}</option>`)}
                </select>
                ${this.details[this.baseSoul] ? html`
                    <p style="font-size: 0.9em; opacity: 0.8; margin-top: 8px;">
                        ${this.details[this.baseSoul].description}
                    </p>
                ` : nothing}
            </div>

            <div class="section">
                <h3>2. Blend Styles</h3>
                <p>Mix in traits from other souls.</p>
                <div class="checkbox-group">
                    ${this.souls.filter(s => s !== this.baseSoul).map(s => html`
                        <div class="row">
                            <input type="checkbox"
                                id="blend-${s}"
                                ?checked=${this.blendSouls.includes(s)}
                                @change=${(e: Event) => this.handleBlendToggle(s, (e.target as HTMLInputElement).checked)}
                            >
                            <label for="blend-${s}">${s}</label>
                        </div>
                    `)}
                </div>

                ${this.blendSouls.length > 0 ? html`
                    <div class="slider-group">
                        <h4>Blend Weights</h4>
                        ${this.blendSouls.map(s => html`
                            <div style="margin-bottom: 16px;">
                                <div class="row" style="justify-content: space-between;">
                                    <label>${s}</label>
                                    <span>${(this.blendWeights[s] || 0.5).toFixed(2)}</span>
                                </div>
                                <input type="range"
                                    min="0.1" max="1.0" step="0.1"
                                    .value=${String(this.blendWeights[s] || 0.5)}
                                    @input=${(e: Event) => this.handleWeightChange(s, parseFloat((e.target as HTMLInputElement).value))}
                                >
                            </div>
                        `)}
                    </div>
                ` : nothing}
            </div>

            <button @click=${this.handleCompose} ?disabled=${this.loading}>
                ${this.loading ? 'Composing...' : 'Compose Soul'}
            </button>

            ${this.compositeResult ? html`
                <div class="section result" style="margin-top: 24px;">
                    <h3>Composition Successful</h3>
                    <p><strong>Name:</strong> ${this.compositeResult.name}</p>
                    <p><strong>Traits:</strong> ${this.compositeResult.traits?.join(', ')}</p>
                    <details>
                        <summary>Raw Vector Stats</summary>
                        <code>${JSON.stringify(this.compositeResult, null, 2)}</code>
                    </details>
                </div>
            ` : nothing}
        `;
    }
}
