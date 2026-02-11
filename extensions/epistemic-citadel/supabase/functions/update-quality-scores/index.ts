/**
 * Supabase Edge Function: Update Quality Scores
 * 
 * This function runs periodically (via cron) to update quality scores
 * for all posts in the system.
 * 
 * Schedule: Every hour
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

// Import quality scoring logic
// Note: In production, you'd import from a shared module
function getPostAgeHours(createdAt: string): number {
  const created = new Date(createdAt);
  const now = new Date();
  const diffMs = now.getTime() - created.getTime();
  return diffMs / (1000 * 60 * 60);
}

function calculateMaturityScore(createdAt: string): number {
  const ageHours = getPostAgeHours(createdAt);
  return Math.log(1 + ageHours / 24);
}

function calculateInteractionValue(interactions: any[], postCreatedAt: string): number {
  const SAVE_CITE_GROWTH_RATE = 1.5;
  const REACTION_DECAY_RATE = 0.5;
  const postAgeHours = getPostAgeHours(postCreatedAt);
  
  let totalValue = 0;
  
  for (const interaction of interactions) {
    const interactionAgeHours = getPostAgeHours(interaction.created_at);
    const timeSincePost = Math.max(0, postAgeHours - interactionAgeHours);
    
    if (interaction.type === 'save' || interaction.type === 'cite') {
      const timeBonus = Math.sqrt(timeSincePost + 1);
      totalValue += interaction.weight * timeBonus * SAVE_CITE_GROWTH_RATE;
    } else if (interaction.type === 'reaction') {
      const decayFactor = Math.exp(-REACTION_DECAY_RATE * timeSincePost / 24);
      totalValue += interaction.weight * decayFactor;
    }
  }
  
  return totalValue;
}

function calculateQualityScore(post: any, interactions: any[]): number {
  const maturityScore = calculateMaturityScore(post.created_at);
  const interactionValue = calculateInteractionValue(interactions, post.created_at);
  return maturityScore * interactionValue;
}

function hasMatured(createdAt: string): boolean {
  const ESCROW_PERIOD_HOURS = 72;
  const ageHours = getPostAgeHours(createdAt);
  return ageHours >= ESCROW_PERIOD_HOURS;
}

serve(async (req) => {
  try {
    // Create Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    // Fetch all posts that need updating
    const { data: posts, error: postsError } = await supabaseClient
      .from('posts')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(1000);

    if (postsError) {
      throw postsError;
    }

    let updatedCount = 0;
    const errors: string[] = [];

    for (const post of posts) {
      // Fetch interactions for this post
      const { data: interactions, error: interactionsError } = await supabaseClient
        .from('interactions')
        .select('*')
        .eq('post_id', post.id);

      if (interactionsError) {
        errors.push(`Error fetching interactions for post ${post.id}: ${interactionsError.message}`);
        continue;
      }

      // Calculate new scores
      const maturityScore = calculateMaturityScore(post.created_at);
      const qualityScore = calculateQualityScore(post, interactions || []);
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
        errors.push(`Error updating post ${post.id}: ${updateError.message}`);
      } else {
        updatedCount++;
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        updated: updatedCount,
        total: posts.length,
        errors: errors.length > 0 ? errors : undefined,
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 200,
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 500,
      }
    );
  }
});
