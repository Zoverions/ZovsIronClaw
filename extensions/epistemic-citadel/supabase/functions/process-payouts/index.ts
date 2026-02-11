/**
 * Supabase Edge Function: Process Payouts
 * 
 * This function processes payouts for matured stakes and updates user reputations.
 * 
 * Schedule: Every 6 hours
 */

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

function getPostAgeHours(createdAt: string): number {
  const created = new Date(createdAt);
  const now = new Date();
  const diffMs = now.getTime() - created.getTime();
  return diffMs / (1000 * 60 * 60);
}

function hasMatured(createdAt: string): boolean {
  const ESCROW_PERIOD_HOURS = 72;
  const ageHours = getPostAgeHours(createdAt);
  return ageHours >= ESCROW_PERIOD_HOURS;
}

function calculatePayout(stake: any, qualityScore: number): {
  roi: number;
  payout: number;
  status: 'yielded' | 'slashed' | 'neutral';
  yield: number;
} {
  const MATURITY_THRESHOLD = 1.0;
  const roi = qualityScore / stake.amount;
  
  if (qualityScore > MATURITY_THRESHOLD) {
    const yieldAmount = stake.amount * (roi - 1);
    return {
      roi,
      payout: stake.amount + yieldAmount,
      status: 'yielded',
      yield: yieldAmount,
    };
  } else if (qualityScore < 0) {
    return {
      roi,
      payout: 0,
      status: 'slashed',
      yield: -stake.amount,
    };
  } else {
    return {
      roi,
      payout: stake.amount,
      status: 'neutral',
      yield: 0,
    };
  }
}

serve(async (req) => {
  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    // Fetch all active stakes with their associated posts
    const { data: stakes, error: stakesError } = await supabaseClient
      .from('stakes')
      .select(`
        *,
        posts (*)
      `)
      .eq('status', 'active');

    if (stakesError) {
      throw stakesError;
    }

    let processedCount = 0;
    const errors: string[] = [];
    const payoutSummary = {
      yielded: 0,
      slashed: 0,
      neutral: 0,
    };

    for (const stake of stakes) {
      const post = stake.posts;

      // Skip if post hasn't matured yet
      if (!hasMatured(post.created_at)) {
        continue;
      }

      // Calculate payout
      const payout = calculatePayout(stake, post.quality_score);
      payoutSummary[payout.status]++;

      // Update stake status
      const { error: updateStakeError } = await supabaseClient
        .from('stakes')
        .update({ status: payout.status })
        .eq('id', stake.id);

      if (updateStakeError) {
        errors.push(`Error updating stake ${stake.id}: ${updateStakeError.message}`);
        continue;
      }

      // Update user reputation
      const { data: user, error: fetchUserError } = await supabaseClient
        .from('users')
        .select('reputation_score')
        .eq('id', stake.user_id)
        .single();

      if (fetchUserError) {
        errors.push(`Error fetching user ${stake.user_id}: ${fetchUserError.message}`);
        continue;
      }

      const newReputation = user.reputation_score + payout.yield;

      const { error: updateUserError } = await supabaseClient
        .from('users')
        .update({ reputation_score: newReputation })
        .eq('id', stake.user_id);

      if (updateUserError) {
        errors.push(`Error updating user reputation: ${updateUserError.message}`);
      } else {
        processedCount++;
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        processed: processedCount,
        total: stakes.length,
        summary: payoutSummary,
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
