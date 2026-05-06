export function isSlackChannelAllowedByPolicy(params: {
  groupPolicy: "open" | "disabled" | "allowlist";
  isExplicitMatch: boolean;
  channelAllowed: boolean;
}): boolean {
  const { groupPolicy, isExplicitMatch, channelAllowed } = params;
  if (groupPolicy === "disabled") {
    return false;
  }
  if (groupPolicy === "open") {
    return channelAllowed;
  }
  if (!isExplicitMatch) {
    return false;
  }
  return channelAllowed;
}
