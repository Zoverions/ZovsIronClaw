import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { BaseStyles } from '../components/base-styles';
import './setup-wizard';
import { SoulManager } from '../controllers/soul-manager';

@customElement('setup-view')
export class SetupView extends LitElement {
    static styles = [
        BaseStyles,
        css`
            :host {
                display: flex;
                width: 100vw;
                height: 100vh;
                background-color: var(--background-color, #1a1a1a);
                color: var(--text-color, #ffffff);
                align-items: center;
                justify-content: center;
            }
        `
    ];

    render() {
        return html`
            <setup-wizard @setup-complete=${this.handleSetupComplete}></setup-wizard>
        `;
    }

    private async handleSetupComplete(e: CustomEvent) {
        const soul = e.detail.soul;
        console.log("Setup Complete with Soul:", soul);

        // Persist the soul choice
        await SoulManager.saveSoulChoice(soul);

        // Navigate to main app
        window.location.hash = '#/';
        window.location.reload();
    }
}
