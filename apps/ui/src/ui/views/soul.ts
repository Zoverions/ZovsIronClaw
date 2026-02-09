import { html } from "lit";
import "../components/soul-composer.ts";

export function renderSoul() {
  return html`
    <div class="view-content">
      <div class="card">
        <soul-composer></soul-composer>
      </div>
    </div>
  `;
}
