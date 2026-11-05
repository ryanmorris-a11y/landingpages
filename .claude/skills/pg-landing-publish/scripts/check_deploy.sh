#!/usr/bin/env bash
# check_deploy.sh <commit-sha> <url> [<url> ...]
# Waits (max 15 min) for the GitHub Pages "pages build and deployment" run of <commit-sha> to finish, then checks each URL.
# Prints one line per URL: "OK <url> 200", "FAIL <url> <code>" or "DEPLOYED <url> (http check unavailable: <reason>)".
# Exit 0 = deployment succeeded (and every reachable URL returned 200); 1 = deployment failed or a URL returned non-200; 2 = timeout.
set -u
REPO="${GITHUB_REPO:-ryanmorris-a11y/landingpages}"; SHA="$1"; shift
for i in $(seq 1 90); do
  s=$(gh api "repos/$REPO/actions/runs?head_sha=$SHA" --jq '[.workflow_runs[]|select(.name=="pages build and deployment")][0]|(.status+" "+(.conclusion//""))' 2>/dev/null || true)
  [ "${s%% *}" = "completed" ] && break
  sleep 10
done
[ "${s%% *}" = "completed" ] || { echo "TIMEOUT pages run for $SHA: '$s'"; exit 2; }
[ "${s#* }" = "success" ] || { echo "DEPLOY-FAILED $SHA: $s"; for u in "$@"; do echo "FAIL $u deploy-$s"; done; exit 1; }
sleep 20  # CDN propagation for new folders
rc=0
for u in "$@"; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$u" 2>/tmp/cd_err.$$) || code=""
  if [ "$code" = "200" ]; then echo "OK $u 200"
  elif [ -z "$code" ] || [ "$code" = "000" ]; then echo "DEPLOYED $u (http check unavailable: $(tr -d '\n' </tmp/cd_err.$$ | cut -c1-80))"
  else echo "FAIL $u $code"; rc=1; fi
done
rm -f /tmp/cd_err.$$; exit $rc
