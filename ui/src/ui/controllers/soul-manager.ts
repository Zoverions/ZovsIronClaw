// Soul Manager: Handles persistence of the "Soul" state
import { UiSettings } from '../storage.ts';

// Tauri invoke helper
const invoke = async (cmd: string, args?: any) => {
    if ((window as any).__TAURI__?.core) {
        return (window as any).__TAURI__.core.invoke(cmd, args);
    }
    return null;
};

export class SoulManager {
    static async saveSoulChoice(soul: string): Promise<boolean> {
        console.log(`[SoulManager] Birthing entity with soul: ${soul}`);

        // 1. Save to Local Storage (UI State)
        try {
            const settingsStr = localStorage.getItem('openclaw:settings');
            let settings: Partial<UiSettings> = {};
            if (settingsStr) {
                settings = JSON.parse(settingsStr);
            }
            // Add custom field for soul
            (settings as any).activeSoul = soul;
            localStorage.setItem('openclaw:settings', JSON.stringify(settings));
        } catch (e) {
            console.error("Failed to save soul to local storage", e);
        }

        // 2. Persist to Backend (Config file) via Tauri
        try {
            if ((window as any).__TAURI__) {
                await invoke('save_soul_config', { soul_name: soul.toLowerCase() });
                return true;
            }
        } catch (e) {
            console.warn("Backend persistence failed (or not available)", e);
        }

        return false;
    }

    static getActiveSoul(): string {
        try {
            const settingsStr = localStorage.getItem('openclaw:settings');
            if (settingsStr) {
                const settings = JSON.parse(settingsStr);
                return (settings as any).activeSoul || 'Architect'; // Default
            }
        } catch {}
        return 'Architect';
    }
}
