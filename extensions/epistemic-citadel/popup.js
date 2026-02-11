/**
 * OPERATION: EPISTEMIC CITADEL
 * Popup Dashboard Logic
 */

// Configuration
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// State
let currentUser = null;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadUser();
  
  if (currentUser) {
    showDashboard();
    await loadDashboardData();
  } else {
    showOnboarding();
  }
  
  setupEventListeners();
});

/**
 * Load user from storage
 */
async function loadUser() {
  const result = await chrome.storage.local.get(['user']);
  currentUser = result.user || null;
}

/**
 * Show onboarding view
 */
function showOnboarding() {
  document.getElementById('onboarding-view').classList.remove('hidden');
  document.getElementById('dashboard-view').classList.add('hidden');
}

/**
 * Show dashboard view
 */
function showDashboard() {
  document.getElementById('onboarding-view').classList.add('hidden');
  document.getElementById('dashboard-view').classList.remove('hidden');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Create account button
  const createAccountBtn = document.getElementById('create-account-btn');
  if (createAccountBtn) {
    createAccountBtn.addEventListener('click', handleCreateAccount);
  }
  
  // Refresh button
  const refreshBtn = document.getElementById('refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', handleRefresh);
  }
}

/**
 * Handle create account
 */
async function handleCreateAccount() {
  const usernameInput = document.getElementById('username');
  const username = usernameInput.value.trim();
  
  if (!username) {
    alert('Please enter a username');
    return;
  }
  
  const createAccountBtn = document.getElementById('create-account-btn');
  createAccountBtn.disabled = true;
  createAccountBtn.textContent = 'Creating...';
  
  try {
    // Create user in Supabase
    const response = await fetch(`${SUPABASE_URL}/rest/v1/users`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
      },
      body: JSON.stringify({
        username: username,
        reputation_score: 100.0,
        natural_frequency: 0.01,
      }),
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to create user: ${error}`);
    }
    
    const users = await response.json();
    currentUser = users[0];
    
    // Save to storage
    await chrome.storage.local.set({ user: currentUser });
    
    // Show dashboard
    showDashboard();
    await loadDashboardData();
    
  } catch (error) {
    console.error('Error creating account:', error);
    alert(`Failed to create account: ${error.message}`);
    createAccountBtn.disabled = false;
    createAccountBtn.textContent = 'Create Account';
  }
}

/**
 * Handle refresh
 */
async function handleRefresh() {
  const refreshBtn = document.getElementById('refresh-btn');
  refreshBtn.disabled = true;
  
  await loadDashboardData();
  
  setTimeout(() => {
    refreshBtn.disabled = false;
  }, 1000);
}

/**
 * Load dashboard data
 */
async function loadDashboardData() {
  if (!currentUser) return;
  
  // Update user stats
  await updateUserStats();
  
  // Load active stakes
  await loadActiveStakes();
  
  // Load slow feed
  await loadSlowFeed();
}

/**
 * Update user stats
 */
async function updateUserStats() {
  try {
    // Fetch latest user data
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/users?id=eq.${currentUser.id}&select=*`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch user data');
    }
    
    const users = await response.json();
    if (users.length > 0) {
      currentUser = users[0];
      await chrome.storage.local.set({ user: currentUser });
      
      // Update UI
      document.getElementById('reputation-value').textContent = currentUser.reputation_score.toFixed(1);
      document.getElementById('frequency-value').textContent = `${currentUser.natural_frequency.toFixed(3)} Hz`;
    }
  } catch (error) {
    console.error('Error updating user stats:', error);
  }
}

/**
 * Load active stakes
 */
async function loadActiveStakes() {
  try {
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/rpc/get_user_active_stakes`,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: currentUser.id,
        }),
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch active stakes');
    }
    
    const stakes = await response.json();
    
    const stakesList = document.getElementById('active-stakes-list');
    
    if (stakes.length === 0) {
      stakesList.innerHTML = '<div class="empty-state">No active stakes</div>';
      return;
    }
    
    stakesList.innerHTML = stakes.map(stake => `
      <div class="stake-item">
        <div class="stake-header">
          <div class="stake-amount">${stake.amount} REP</div>
          <div class="stake-status ${stake.is_escrowed ? 'active' : 'matured'}">
            ${stake.is_escrowed ? 'In Escrow' : 'Matured'}
          </div>
        </div>
        <div class="stake-info">
          <div class="stake-metric">
            <span class="stake-metric-label">Quality Score:</span>
            <span class="stake-metric-value">${stake.post_quality_score.toFixed(2)}</span>
          </div>
          <div class="stake-metric">
            <span class="stake-metric-label">Estimated ROI:</span>
            <span class="stake-metric-value">${stake.estimated_roi.toFixed(2)}x</span>
          </div>
          <div class="stake-metric">
            <span class="stake-metric-label">Maturity:</span>
            <span class="stake-metric-value">${stake.post_maturity_score.toFixed(2)}</span>
          </div>
        </div>
      </div>
    `).join('');
    
  } catch (error) {
    console.error('Error loading active stakes:', error);
    document.getElementById('active-stakes-list').innerHTML = 
      '<div class="empty-state">Error loading stakes</div>';
  }
}

/**
 * Load slow feed
 */
async function loadSlowFeed() {
  try {
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/rpc/get_slow_feed`,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days_ago: 3,
        }),
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch slow feed');
    }
    
    const posts = await response.json();
    
    const feedList = document.getElementById('slow-feed-list');
    
    if (posts.length === 0) {
      feedList.innerHTML = '<div class="empty-state">No posts in the slow feed yet</div>';
      return;
    }
    
    feedList.innerHTML = posts.map(post => {
      const tweetUrl = post.external_ref_id 
        ? `https://twitter.com/i/web/status/${post.external_ref_id}`
        : '#';
      
      return `
        <div class="feed-item" onclick="window.open('${tweetUrl}', '_blank')">
          <div class="feed-header">
            <div class="feed-metrics">
              <div class="feed-metric">
                <strong>${post.total_stakes}</strong> stakes
              </div>
              <div class="feed-metric">
                <strong>${post.average_roi.toFixed(2)}x</strong> avg ROI
              </div>
            </div>
          </div>
          <div class="feed-content">
            ${post.content || 'View on Twitter →'}
          </div>
          <div class="feed-metrics">
            <div class="feed-metric">Quality: <strong>${post.quality_score.toFixed(2)}</strong></div>
            <div class="feed-metric">Age: <strong>${getRelativeTime(post.created_at)}</strong></div>
          </div>
        </div>
      `;
    }).join('');
    
  } catch (error) {
    console.error('Error loading slow feed:', error);
    document.getElementById('slow-feed-list').innerHTML = 
      '<div class="empty-state">Error loading feed</div>';
  }
}

/**
 * Get relative time string
 */
function getRelativeTime(timestamp) {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  return `${diffDays} days ago`;
}
