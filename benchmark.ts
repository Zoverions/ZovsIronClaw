const permsPermissions = [
  "CreateInstantInvite", "KickMembers", "BanMembers", "Administrator",
  "ManageChannels", "ManageGuild", "AddReactions", "ViewAuditLog",
  "PrioritySpeaker", "Stream", "ViewChannel", "SendMessages",
  "SendTTSMessages", "ManageMessages", "EmbedLinks", "AttachFiles",
  "ReadMessageHistory", "MentionEveryone", "UseExternalEmojis", "ViewGuildInsights",
  "Connect", "Speak", "MuteMembers", "DeafenMembers", "MoveMembers",
  "UseVAD", "ChangeNickname", "ManageNicknames", "ManageRoles", "ManageWebhooks",
  "ManageEmojisAndStickers", "UseApplicationCommands", "RequestToSpeak",
  "ManageEvents", "ManageThreads", "CreatePublicThreads", "CreatePrivateThreads",
  "UseExternalStickers", "SendMessagesInThreads", "UseEmbeddedActivities",
  "ModerateMembers", "ViewCreatorMonetizationAnalytics", "UseSoundboard",
  "UseExternalSounds", "SendVoiceMessages"
];

function runBench(requiredCount) {
  const required = Array.from({ length: requiredCount }, (_, i) => `Perm${i}`);
  // Add some matches
  required[0] = "ViewChannel";
  required[1] = "SendMessages";

  const LOOPS = 100_000;

  let start = performance.now();
  for (let i = 0; i < LOOPS; i++) {
    const missing = required.filter((p) => !permsPermissions.includes(p));
  }
  const baselineTime = performance.now() - start;

  start = performance.now();
  for (let i = 0; i < LOOPS; i++) {
    const permsSet = new Set(permsPermissions);
    const missing = required.filter((p) => !permsSet.has(p));
  }
  const optimizedTime = performance.now() - start;

  console.log(`N = ${requiredCount}, M = ${permsPermissions.length}`);
  console.log(`  Baseline: ${baselineTime.toFixed(2)}ms`);
  console.log(`  Optimized: ${optimizedTime.toFixed(2)}ms`);
}

runBench(2);
runBench(10);
runBench(50);
runBench(100);
runBench(500);
