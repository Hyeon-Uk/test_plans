#!/bin/bash
# Clone all 65 Tizen packages from gerrit, install change-id hook, checkout tizen branch
set -u
ROOT=/home/hyeonuk/tizen/appfw
GERRIT_USER=KimHyeonuk
GERRIT_HOST=review.tizen.org
GERRIT_PORT=29418

PKGS=(
  "platform/core/appfw/alarm-manager"
  "platform/core/appfw/amd"
  "platform/core/appfw/app-core"
  "platform/core/appfw/app-installers"
  "platform/core/appfw/app-svc"
  "platform/core/appfw/app2sd"
  "platform/core/appfw/appcore-agent"
  "platform/core/appfw/appcore-watch"
  "platform/core/appfw/appcore-widget"
  "platform/core/appfw/aul-1"
  "platform/core/appfw/badge"
  "platform/core/appfw/capmgr"
  "platform/core/appfw/cion"
  "platform/core/appfw/component-based-application"
  "platform/core/appfw/data-control"
  "platform/core/appfw/data-provider-master"
  "platform/core/appfw/event-system"
  "platform/core/appfw/launchpad"
  "platform/core/appfw/libeventsystem"
  "platform/core/appfw/librua"
  "platform/core/appfw/libslp-db-util"
  "platform/core/appfw/manifest-parser"
  "platform/core/appfw/message-port"
  "platform/core/appfw/minicontrol"
  "platform/core/appfw/pkgmgr-info"
  "platform/core/appfw/pkgmgr-server"
  "platform/core/appfw/pkgmgr-tool"
  "platform/core/appfw/rpc-port"
  "platform/core/appfw/rpk-installer"
  "platform/core/appfw/screen-connector"
  "platform/core/appfw/shortcut"
  "platform/core/appfw/slp-pkgmgr"
  "platform/core/appfw/tidl"
  "platform/core/appfw/tizen-action"
  "platform/core/appfw/tizen-core"
  "platform/core/appfw/tizen-theme-manager"
  "platform/core/appfw/tizen-watcher"
  "platform/core/appfw/tpk-backend"
  "platform/core/appfw/tpk-manifest-handlers"
  "platform/core/appfw/ui-gadget-1"
  "platform/core/appfw/unified-backend"
  "platform/core/appfw/united-service"
  "platform/core/appfw/watchface-complication"
  "platform/core/appfw/wgt-backend"
  "platform/core/appfw/wgt-manifest-handlers"
  "platform/core/appfw/widget-service"
  "platform/core/appfw/widget-viewer"
  "platform/core/appfw/xdgmime"
  "platform/core/api/alarm"
  "platform/core/api/app-common"
  "platform/core/api/app-control"
  "platform/core/api/app-event"
  "platform/core/api/app-manager"
  "platform/core/api/application"
  "platform/core/api/capability-manager"
  "platform/core/api/component-manager"
  "platform/core/api/job-scheduler"
  "platform/core/api/media-key"
  "platform/core/api/mime-type"
  "platform/core/api/notification"
  "platform/core/api/package-manager"
  "platform/core/api/preference"
  "platform/core/base/bundle"
  "platform/core/base/syspopup"
  "platform/core/system/buxton2"
)

mkdir -p "$ROOT/logs"

clone_one() {
  local pkgpath="$1"
  local name="${pkgpath##*/}"
  local dest="$ROOT/$name"
  local log="$ROOT/logs/$name.log"
  {
    echo "=== $pkgpath -> $dest"
    if [ -d "$dest/.git" ]; then
      echo "SKIP clone (already exists)"
    else
      git clone "ssh://${GERRIT_USER}@${GERRIT_HOST}:${GERRIT_PORT}/${pkgpath}" "$dest" 2>&1
      if [ ! -d "$dest/.git" ]; then
        echo "CLONE FAILED"
        return 1
      fi
    fi
    cd "$dest" || return 1
    # Install change-id hook
    if [ ! -x ".git/hooks/commit-msg" ]; then
      scp -p -P "$GERRIT_PORT" "${GERRIT_USER}@${GERRIT_HOST}:hooks/commit-msg" .git/hooks/ 2>&1
      chmod +x .git/hooks/commit-msg 2>&1
    fi
    # Checkout tizen branch
    git fetch origin tizen 2>&1
    if git show-ref --verify --quiet refs/heads/tizen; then
      git checkout tizen 2>&1
      git reset --hard origin/tizen 2>&1
    else
      git checkout -B tizen origin/tizen 2>&1 || git checkout -B tizen FETCH_HEAD 2>&1
    fi
    echo "=== DONE $name on branch $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
  } > "$log" 2>&1
}

export -f clone_one
export ROOT GERRIT_USER GERRIT_HOST GERRIT_PORT

# Parallel clones, 8 at a time
printf '%s\n' "${PKGS[@]}" | xargs -n1 -P8 -I{} bash -c 'clone_one "$@"' _ {}

# Summary
echo "=== SUMMARY ==="
ok=0; fail=0
for p in "${PKGS[@]}"; do
  name="${p##*/}"
  if [ -d "$ROOT/$name/.git" ] && (cd "$ROOT/$name" && git rev-parse --verify tizen >/dev/null 2>&1); then
    ok=$((ok+1))
  else
    fail=$((fail+1))
    echo "FAIL: $name"
  fi
done
echo "OK=$ok FAIL=$fail TOTAL=${#PKGS[@]}"
