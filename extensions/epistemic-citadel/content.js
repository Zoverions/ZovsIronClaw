/**
 * OPERATION: EPISTEMIC CITADEL
 * Content Script - The Overlay
 * 
 * This script:
 * 1. Injects "Shield Icon" buttons next to Like/Retweet buttons
 * 2. Applies acoustic filtering to high-velocity, low-quality tweets
 * 3. Communicates with the background script and Supabase
 */

// Configuration
const SUPABASE_URL = 'YOUR_SUPABASE_URL'; // To be replaced with actual URL
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY'; // To be replaced with actual key

// State
let currentUser = null;
let shadowGraph = new Map(); // Cache of post quality scores

/**
 * Initialize the extension
 */
async function init() {
  console.log('[Epistemic Citadel] Initializing...');
  
  // Load user data from storage
  const result = await chrome.storage.local.get(['user']);
  currentUser = result.user;
  
  if (!currentUser) {
    console.log('[Epistemic Citadel] No user found, prompting for setup');
    // TODO: Show setup modal
  }
  
  // Start observing the DOM for new tweets
  observeTweets();
  
  console.log('[Epistemic Citadel] Initialized');
}

/**
 * Observe the DOM for new tweets and process them
 */
function observeTweets() {
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Find tweet articles
            const tweets = node.querySelectorAll?.('article[data-testid="tweet"]') || [];
            tweets.forEach(processTweet);
            
            // Check if the node itself is a tweet
            if (node.matches?.('article[data-testid="tweet"]')) {
              processTweet(node);
            }
          }
        });
      }
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
  
  // Process existing tweets
  document.querySelectorAll('article[data-testid="tweet"]').forEach(processTweet);
}

/**
 * Process a single tweet element
 */
async function processTweet(tweetElement) {
  // Skip if already processed
  if (tweetElement.dataset.epistemicProcessed) {
    return;
  }
  tweetElement.dataset.epistemicProcessed = 'true';
  
  // Extract tweet data
  const tweetData = extractTweetData(tweetElement);
  if (!tweetData) {
    return;
  }
  
  // Inject shield button
  injectShieldButton(tweetElement, tweetData);
  
  // Apply acoustic filter if needed
  await applyAcousticFilter(tweetElement, tweetData);
}

/**
 * Extract tweet data from the DOM element
 */
function extractTweetData(tweetElement) {
  try {
    // Extract tweet ID from the link
    const tweetLink = tweetElement.querySelector('a[href*="/status/"]');
    if (!tweetLink) return null;
    
    const tweetId = tweetLink.href.match(/\/status\/(\d+)/)?.[1];
    if (!tweetId) return null;
    
    // Extract timestamp
    const timeElement = tweetElement.querySelector('time');
    const timestamp = timeElement?.getAttribute('datetime');
    
    // Extract engagement metrics
    const replyCount = extractMetric(tweetElement, 'reply');
    const retweetCount = extractMetric(tweetElement, 'retweet');
    const likeCount = extractMetric(tweetElement, 'like');
    
    // Calculate age in minutes
    const ageMinutes = timestamp 
      ? (Date.now() - new Date(timestamp).getTime()) / (1000 * 60)
      : 0;
    
    return {
      id: tweetId,
      timestamp,
      ageMinutes,
      replyCount,
      retweetCount,
      likeCount,
    };
  } catch (error) {
    console.error('[Epistemic Citadel] Error extracting tweet data:', error);
    return null;
  }
}

/**
 * Extract engagement metric from tweet element
 */
function extractMetric(tweetElement, type) {
  const button = tweetElement.querySelector(`[data-testid="${type}"]`);
  if (!button) return 0;
  
  const text = button.getAttribute('aria-label') || '';
  const match = text.match(/(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

/**
 * Inject the Shield button next to engagement buttons
 */
function injectShieldButton(tweetElement, tweetData) {
  // Find the action bar
  const actionBar = tweetElement.querySelector('[role="group"]');
  if (!actionBar) return;
  
  // Check if shield button already exists
  if (actionBar.querySelector('.epistemic-shield-button')) {
    return;
  }
  
  // Create shield button
  const shieldButton = document.createElement('div');
  shieldButton.className = 'epistemic-shield-button';
  shieldButton.innerHTML = `
    <button class="epistemic-shield-btn" aria-label="Stake reputation on this tweet">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M12 2L4 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-8-5z"/>
      </svg>
    </button>
  `;
  
  // Add click handler
  shieldButton.querySelector('.epistemic-shield-btn').addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    openStakingModal(tweetData);
  });
  
  // Insert into action bar
  actionBar.appendChild(shieldButton);
}

/**
 * Apply acoustic filter to high-velocity, low-quality tweets
 */
async function applyAcousticFilter(tweetElement, tweetData) {
  // Check if tweet is high velocity
  const isHighVelocity = tweetData.likeCount > 100 && tweetData.ageMinutes < 10;
  
  if (!isHighVelocity) {
    return;
  }
  
  // Fetch shadow quality score
  const qualityScore = await getShadowQualityScore(tweetData.id);
  
  // Apply filter if low quality
  if (qualityScore !== null && qualityScore < 0.5) {
    tweetElement.classList.add('epistemic-filtered');
    
    // Add tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'epistemic-filter-tooltip';
    tooltip.textContent = 'Hidden by Acoustic Filter (High Noise/Signal Ratio)';
    tweetElement.appendChild(tooltip);
  }
}

/**
 * Get shadow quality score from Supabase
 */
async function getShadowQualityScore(tweetId) {
  // Check cache first
  if (shadowGraph.has(tweetId)) {
    return shadowGraph.get(tweetId);
  }
  
  try {
    // Query Supabase for quality score
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/posts?external_ref_id=eq.${tweetId}&select=quality_score`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );
    
    if (!response.ok) {
      console.error('[Epistemic Citadel] Error fetching quality score:', response.statusText);
      return null;
    }
    
    const data = await response.json();
    const qualityScore = data[0]?.quality_score || 0;
    
    // Cache the result
    shadowGraph.set(tweetId, qualityScore);
    
    return qualityScore;
  } catch (error) {
    console.error('[Epistemic Citadel] Error fetching quality score:', error);
    return null;
  }
}

/**
 * Open the staking modal
 */
function openStakingModal(tweetData) {
  // Create modal overlay
  const modal = document.createElement('div');
  modal.className = 'epistemic-modal-overlay';
  modal.innerHTML = `
    <div class="epistemic-modal">
      <div class="epistemic-modal-header">
        <h2>Stake Reputation</h2>
        <button class="epistemic-modal-close">&times;</button>
      </div>
      <div class="epistemic-modal-body">
        <p>Stake your reputation on this tweet's long-term value.</p>
        <div class="epistemic-form-group">
          <label for="stake-amount">Amount</label>
          <input type="number" id="stake-amount" min="1" max="100" value="10" />
        </div>
        <div class="epistemic-form-group">
          <label for="stake-thesis">Thesis (Optional)</label>
          <textarea id="stake-thesis" rows="3" placeholder="Why do you believe this content will age well?"></textarea>
        </div>
        <div class="epistemic-info">
          <p><strong>Escrow Period:</strong> 72 hours</p>
          <p><strong>Your Reputation:</strong> ${currentUser?.reputation_score || 100}</p>
        </div>
      </div>
      <div class="epistemic-modal-footer">
        <button class="epistemic-btn epistemic-btn-secondary epistemic-modal-cancel">Cancel</button>
        <button class="epistemic-btn epistemic-btn-primary epistemic-modal-submit">Stake</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Add event listeners
  modal.querySelector('.epistemic-modal-close').addEventListener('click', () => {
    modal.remove();
  });
  
  modal.querySelector('.epistemic-modal-cancel').addEventListener('click', () => {
    modal.remove();
  });
  
  modal.querySelector('.epistemic-modal-submit').addEventListener('click', async () => {
    const amount = parseFloat(document.getElementById('stake-amount').value);
    const thesis = document.getElementById('stake-thesis').value;
    
    await submitStake(tweetData, amount, thesis);
    modal.remove();
  });
  
  // Close on overlay click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

/**
 * Submit a stake to Supabase
 */
async function submitStake(tweetData, amount, thesis) {
  try {
    if (!currentUser) {
      alert('Please set up your account first');
      return;
    }
    
    // First, ensure the post exists in the database
    const postResponse = await fetch(`${SUPABASE_URL}/rest/v1/posts`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({
        external_ref_id: tweetData.id,
        author_id: currentUser.id,
        content: thesis || '',
        created_at: tweetData.timestamp || new Date().toISOString(),
      }),
    });
    
    if (!postResponse.ok) {
      console.error('[Epistemic Citadel] Error creating post:', await postResponse.text());
      alert('Failed to create post');
      return;
    }
    
    const posts = await postResponse.json();
    const postId = posts[0]?.id;
    
    if (!postId) {
      alert('Failed to get post ID');
      return;
    }
    
    // Create the stake
    const stakeResponse = await fetch(`${SUPABASE_URL}/rest/v1/stakes`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: currentUser.id,
        post_id: postId,
        amount: amount,
        status: 'active',
      }),
    });
    
    if (!stakeResponse.ok) {
      console.error('[Epistemic Citadel] Error creating stake:', await stakeResponse.text());
      alert('Failed to create stake');
      return;
    }
    
    alert(`Successfully staked ${amount} reputation!`);
    
    // Update local user reputation
    currentUser.reputation_score -= amount;
    await chrome.storage.local.set({ user: currentUser });
    
  } catch (error) {
    console.error('[Epistemic Citadel] Error submitting stake:', error);
    alert('Failed to submit stake');
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
