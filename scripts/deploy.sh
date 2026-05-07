#!/usr/bin/env bash
# Runs on jesse-prod as the `deploy` user. Invoked over SSH by GitHub
# Actions after the runner has rsync'd the working tree to
# /srv/web/journal/repo/.
#
# Idempotent: safe to re-run by hand for debugging.

set -euo pipefail

REPO_DIR=/srv/web/journal/repo
SITE_DIR=/srv/web/journal/site
HEALTH_URL=https://journal.jesselab.space/version.txt

cd "$REPO_DIR"

# 1. Sync nginx site if it changed.
if ! sudo cmp -s nginx/journal.jesselab.space.conf /etc/nginx/sites-available/journal.jesselab.space; then
    sudo cp nginx/journal.jesselab.space.conf /etc/nginx/sites-available/journal.jesselab.space
    sudo ln -sf /etc/nginx/sites-available/journal.jesselab.space /etc/nginx/sites-enabled/journal.jesselab.space
    sudo nginx -t
    sudo systemctl reload nginx
fi

# 2. Publish the static bundle.
mkdir -p "$SITE_DIR"
rsync -a --delete \
    --exclude '.git' \
    --exclude '.github' \
    --exclude 'nginx' \
    --exclude 'scripts' \
    --exclude 'README.md' \
    "$REPO_DIR"/ "$SITE_DIR"/

# 3. Health check — fetch the SHA stamp through nginx.
for i in 1 2 3 4 5; do
    if curl -fsS "$HEALTH_URL" > /dev/null; then
        echo "deploy ok"
        exit 0
    fi
    sleep 1
done

echo "health check failed" >&2
sudo journalctl -u nginx --no-pager -n 30 >&2 || true
exit 1
