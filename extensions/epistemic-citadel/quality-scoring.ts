/**
 * OPERATION: EPISTEMIC CITADEL
 * Algorithmic Logic - Quality Scoring and Payout Calculations
 * 
 * This module implements the "Physics" of the Epistemic Citadel system:
 * - Quality Integral Function
 * - Payout/ROI Calculation
 * - Temporal Decay Functions
 */

export interface Post {
  id: string;
  created_at: string;
  maturity_score: number;
  quality_score: number;
  is_escrowed: boolean;
}

export interface Interaction {
  type: 'save' | 'cite' | 'reaction';
  weight: number;
  created_at: string;
}

export interface Stake {
  id: string;
  amount: number;
  status: 'active' | 'slashed' | 'yielded';
  created_at: string;
}

/**
 * Constants for the quality scoring algorithm
 */
const ESCROW_PERIOD_HOURS = 72; // 72 hours = 3 days
const MATURITY_THRESHOLD = 1.0; // Minimum maturity score for payout
const REACTION_DECAY_RATE = 0.5; // Exponential decay rate for reactions
const SAVE_CITE_GROWTH_RATE = 1.5; // Growth rate for saves/cites over time

/**
 * Calculate the age of a post in hours
 */
export function getPostAgeHours(createdAt: string): number {
  const created = new Date(createdAt);
  const now = new Date();
  const diffMs = now.getTime() - created.getTime();
  return diffMs / (1000 * 60 * 60); // Convert to hours
}

/**
 * Calculate maturity score based on post age
 * Maturity grows logarithmically with time
 * 
 * Formula: maturity = log(1 + age_hours / 24)
 */
export function calculateMaturityScore(createdAt: string): number {
  const ageHours = getPostAgeHours(createdAt);
  return Math.log(1 + ageHours / 24);
}

/**
 * Calculate the weighted value of interactions over time
 * 
 * Logic:
 * - Saves/Cites are Low-Frequency signals. They gain weight as the post ages (√t growth).
 * - Reactions are High-Frequency noise. They are penalized if they don't convert to long-term value (e^-t function).
 */
export function calculateInteractionValue(
  interactions: Interaction[],
  postCreatedAt: string
): number {
  const postAgeHours = getPostAgeHours(postCreatedAt);
  
  let totalValue = 0;
  
  for (const interaction of interactions) {
    const interactionAgeHours = getPostAgeHours(interaction.created_at);
    const timeSincePost = Math.max(0, postAgeHours - interactionAgeHours);
    
    if (interaction.type === 'save' || interaction.type === 'cite') {
      // Low-frequency signals gain value over time (square root growth)
      const timeBonus = Math.sqrt(timeSincePost + 1);
      totalValue += interaction.weight * timeBonus * SAVE_CITE_GROWTH_RATE;
    } else if (interaction.type === 'reaction') {
      // High-frequency signals decay over time (exponential decay)
      const decayFactor = Math.exp(-REACTION_DECAY_RATE * timeSincePost / 24);
      totalValue += interaction.weight * decayFactor;
    }
  }
  
  return totalValue;
}

/**
 * Calculate the Quality Integral (Q) for a post
 * 
 * Q = ∫ (saves + cites) * √t - reactions * e^(-t)
 */
export function calculateQualityScore(
  post: Post,
  interactions: Interaction[]
): number {
  const maturityScore = calculateMaturityScore(post.created_at);
  const interactionValue = calculateInteractionValue(interactions, post.created_at);
  
  // Quality score is the product of maturity and interaction value
  return maturityScore * interactionValue;
}

/**
 * Check if a post has matured (passed escrow period)
 */
export function hasMatured(createdAt: string): boolean {
  const ageHours = getPostAgeHours(createdAt);
  return ageHours >= ESCROW_PERIOD_HOURS;
}

/**
 * Calculate ROI and determine payout status
 * 
 * The "Payout" Function (At t = 72h):
 * - Calculate ROI: Q / stake_amount
 * - If Q > threshold: Return stake + yield (Yield)
 * - If Q < 0: Burn stake (Slash)
 * - Else: Return stake (Neutral)
 */
export function calculatePayout(
  stake: Stake,
  qualityScore: number
): {
  roi: number;
  payout: number;
  status: 'yielded' | 'slashed' | 'neutral';
  yield: number;
} {
  const roi = qualityScore / stake.amount;
  
  if (qualityScore > MATURITY_THRESHOLD) {
    // Positive outcome: return stake + yield
    const yieldAmount = stake.amount * (roi - 1);
    return {
      roi,
      payout: stake.amount + yieldAmount,
      status: 'yielded',
      yield: yieldAmount,
    };
  } else if (qualityScore < 0) {
    // Negative outcome: slash the stake
    return {
      roi,
      payout: 0,
      status: 'slashed',
      yield: -stake.amount,
    };
  } else {
    // Neutral outcome: return stake only
    return {
      roi,
      payout: stake.amount,
      status: 'neutral',
      yield: 0,
    };
  }
}

/**
 * Determine if a tweet should be filtered (blurred) based on velocity and quality
 * 
 * High Velocity = >100 likes in <10 min
 * Low Shadow Quality = quality_score < 0.5
 */
export function shouldFilterTweet(
  likesCount: number,
  ageMinutes: number,
  shadowQualityScore: number
): boolean {
  const isHighVelocity = likesCount > 100 && ageMinutes < 10;
  const isLowQuality = shadowQualityScore < 0.5;
  
  return isHighVelocity && isLowQuality;
}

/**
 * Calculate noise-to-signal ratio for a post
 * Higher ratio = more noise, less signal
 */
export function calculateNoiseSignalRatio(
  reactions: number,
  savesAndCites: number
): number {
  if (savesAndCites === 0) {
    return reactions > 0 ? Infinity : 0;
  }
  return reactions / savesAndCites;
}

/**
 * Update quality scores for all posts (to be run as a cron job)
 * This would typically be implemented as a Supabase Edge Function
 */
export async function updateQualityScores(
  supabaseClient: any
): Promise<void> {
  // Fetch all posts that are still in escrow or recently matured
  const { data: posts, error: postsError } = await supabaseClient
    .from('posts')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(1000);
  
  if (postsError) {
    console.error('Error fetching posts:', postsError);
    return;
  }
  
  for (const post of posts) {
    // Fetch interactions for this post
    const { data: interactions, error: interactionsError } = await supabaseClient
      .from('interactions')
      .select('*')
      .eq('post_id', post.id);
    
    if (interactionsError) {
      console.error(`Error fetching interactions for post ${post.id}:`, interactionsError);
      continue;
    }
    
    // Calculate new scores
    const maturityScore = calculateMaturityScore(post.created_at);
    const qualityScore = calculateQualityScore(post, interactions);
    const isEscrowed = !hasMatured(post.created_at);
    
    // Update the post
    const { error: updateError } = await supabaseClient
      .from('posts')
      .update({
        maturity_score: maturityScore,
        quality_score: qualityScore,
        is_escrowed: isEscrowed,
      })
      .eq('id', post.id);
    
    if (updateError) {
      console.error(`Error updating post ${post.id}:`, updateError);
    }
  }
}

/**
 * Process payouts for matured stakes
 * This would typically be implemented as a Supabase Edge Function
 */
export async function processPayouts(
  supabaseClient: any
): Promise<void> {
  // Fetch all active stakes on matured posts
  const { data: stakes, error: stakesError } = await supabaseClient
    .from('stakes')
    .select(`
      *,
      posts (*)
    `)
    .eq('status', 'active');
  
  if (stakesError) {
    console.error('Error fetching stakes:', stakesError);
    return;
  }
  
  for (const stake of stakes) {
    const post = stake.posts;
    
    // Skip if post hasn't matured yet
    if (!hasMatured(post.created_at)) {
      continue;
    }
    
    // Calculate payout
    const payout = calculatePayout(stake, post.quality_score);
    
    // Update stake status
    const { error: updateStakeError } = await supabaseClient
      .from('stakes')
      .update({ status: payout.status })
      .eq('id', stake.id);
    
    if (updateStakeError) {
      console.error(`Error updating stake ${stake.id}:`, updateStakeError);
      continue;
    }
    
    // Update user reputation
    const { error: updateUserError } = await supabaseClient.rpc(
      'update_user_reputation',
      {
        user_id: stake.user_id,
        amount: payout.yield,
      }
    );
    
    if (updateUserError) {
      console.error(`Error updating user reputation:`, updateUserError);
    }
  }
}
