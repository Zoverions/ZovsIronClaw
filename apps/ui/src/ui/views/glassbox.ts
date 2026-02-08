import { html } from "lit";

export function renderGlassBox() {
  return html`
    <div class="view-content">
      <div class="card">
        <div class="card-header">
          <h3>Geometric Conscience Architecture</h3>
        </div>
        <div class="card-body">
          <p>
            The GlassBox dashboard provides transparency into the AI's reasoning process using Quaternion Process Theory (QPT).
          </p>

          <div style="display: flex; gap: 2rem; margin-top: 2rem;">
            <div style="flex: 1; padding: 1rem; background: var(--bg-surface-2); border-radius: 8px;">
              <h4>w: Context</h4>
              <div style="height: 10px; background: var(--color-blue); width: 80%; margin-top: 0.5rem; border-radius: 4px;"></div>
              <small>Historical recall & Intent</small>
            </div>
            <div style="flex: 1; padding: 1rem; background: var(--bg-surface-2); border-radius: 8px;">
              <h4>x: Analysis</h4>
              <div style="height: 10px; background: var(--color-purple); width: 60%; margin-top: 0.5rem; border-radius: 4px;"></div>
              <small>Decomposition & Parsing</small>
            </div>
            <div style="flex: 1; padding: 1rem; background: var(--bg-surface-2); border-radius: 8px;">
              <h4>y: Synthesis</h4>
              <div style="height: 10px; background: var(--color-green); width: 90%; margin-top: 0.5rem; border-radius: 4px;"></div>
              <small>Generation candidates</small>
            </div>
            <div style="flex: 1; padding: 1rem; background: var(--bg-surface-2); border-radius: 8px;">
              <h4>z: Ethics</h4>
              <div style="height: 10px; background: var(--color-red); width: 100%; margin-top: 0.5rem; border-radius: 4px;"></div>
              <small>Moral Kernel & Entropy</small>
            </div>
          </div>

          <div style="margin-top: 2rem;">
            <h4>Entropy Monitor</h4>
            <div style="height: 200px; background: var(--bg-surface-1); border: 1px dashed var(--border-color); display: flex; align-items: center; justify-content: center;">
              <span style="color: var(--text-dim);">Live entropy stream requires WebSocket connection...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}
