/**
 * OPERATION: EPISTEMIC CITADEL
 * Background Service Worker
 * 
 * Handles:
 * - Extension lifecycle
 * - Periodic sync with Supabase
 * - Badge updates
 */

// Configuration
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Initialize extension
chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    console.log('[Epistemic Citadel] Extension installed');
    
    // Open onboarding page
    chrome.tabs.create({
      url: 'popup.html?onboarding=true',
    });
  } else if (details.reason === 'update') {
    console.log('[Epistemic Citadel] Extension updated');
  }
  
  // Set up periodic sync alarm
  chrome.alarms.create('sync-reputation', {
    periodInMinutes: 30, // Sync every 30 minutes
  });
});

// Handle alarms
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'sync-reputation') {
    await syncUserReputation();
  }
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_USER') {
    getUserData().then(sendResponse);
    return true; // Keep channel open for async response
  } else if (message.type === 'UPDATE_BADGE') {
    updateBadge(message.count);
  }
});

/**
 * Get user data from storage
 */
async function getUserData() {
  const result = await chrome.storage.local.get(['user']);
  return result.user || null;
}

/**
 * Sync user reputation with Supabase
 */
async function syncUserReputation() {
  try {
    const user = await getUserData();
    if (!user) {
      console.log('[Epistemic Citadel] No user to sync');
      return;
    }
    
    // Fetch latest reputation from Supabase
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/users?id=eq.${user.id}&select=reputation_score,natural_frequency`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );
    
    if (!response.ok) {
      console.error('[Epistemic Citadel] Error syncing reputation:', response.statusText);
      return;
    }
    
    const data = await response.json();
    if (data.length > 0) {
      const updatedUser = {
        ...user,
        reputation_score: data[0].reputation_score,
        natural_frequency: data[0].natural_frequency,
      };
      
      await chrome.storage.local.set({ user: updatedUser });
      console.log('[Epistemic Citadel] Reputation synced:', updatedUser.reputation_score);
      
      // Update badge with reputation change
      const change = updatedUser.reputation_score - user.reputation_score;
      if (change !== 0) {
        updateBadge(Math.round(change));
      }
    }
  } catch (error) {
    console.error('[Epistemic Citadel] Error syncing reputation:', error);
  }
}

/**
 * Update extension badge
 */
function updateBadge(count) {
  if (count > 0) {
    chrome.action.setBadgeText({ text: `+${count}` });
    chrome.action.setBadgeBackgroundColor({ color: '#fbbf24' }); // Amber-400
  } else if (count < 0) {
    chrome.action.setBadgeText({ text: `${count}` });
    chrome.action.setBadgeBackgroundColor({ color: '#ef4444' }); // Red-500
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
  
  // Clear badge after 10 seconds
  setTimeout(() => {
    chrome.action.setBadgeText({ text: '' });
  }, 10000);
}

console.log('[Epistemic Citadel] Background service worker loaded');
