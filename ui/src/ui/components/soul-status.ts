import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { BaseStyles } from './base-styles';

@customElement('soul-status')
export class SoulStatus extends LitElement {
    static styles = [
        BaseStyles,
        css`
            :host {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 16px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: all 0.3s ease;
            }

            .pulse {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #4caf50;
                box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
                animation: pulse-green 2s infinite;
            }

            .pulse.emergent {
                background: #ffd700;
                animation: pulse-gold 1.5s infinite;
                box-shadow: 0 0 10px 2px rgba(255, 215, 0, 0.4);
            }

            .pulse.high-entropy {
                background: #ff5722;
                animation: pulse-red 0.5s infinite;
            }

            .stats {
                display: flex;
                flex-direction: column;
                font-size: 0.8rem;
                line-height: 1.2;
            }

            .label {
                color: rgba(255, 255, 255, 0.5);
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .value {
                color: #fff;
                font-weight: 600;
            }

            @keyframes pulse-green {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
            }

            @keyframes pulse-gold {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); }
                50% { transform: scale(1.1); box-shadow: 0 0 15px 5px rgba(255, 215, 0, 0.4); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
            }

            @keyframes pulse-red {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }
        `
    ];

    @property({ type: String }) status = 'Aligned';
    @property({ type: String }) soul = 'Architect';
    @property({ type: Number }) entropy = 0.2;
    @property({ type: Boolean }) isEmergent = false;

    render() {
        let pulseClass = '';
        if (this.isEmergent) pulseClass = 'emergent';
        else if (this.entropy > 0.7) pulseClass = 'high-entropy';

        return html`
            <div class="pulse ${pulseClass}"></div>
            <div class="stats">
                <span class="label">Soul Status</span>
                <span class="value">${this.soul} • ${this.status}</span>
            </div>
            <div class="stats" style="border-left: 1px solid rgba(255,255,255,0.1); padding-left: 12px;">
                <span class="label">Entropy</span>
                <span class="value">${(this.entropy * 100).toFixed(0)}%</span>
            </div>
        `;
    }
}
