#!/usr/bin/env bash
# Smoke test script for LXCloud (requires the app to be running on localhost:5000)
set -euo pipefail
BASE=${1:-http://127.0.0.1:5000}
OUTDIR="$(dirname "$0")/smoke_results"
mkdir -p "$OUTDIR"

echo "Running smoke tests against $BASE"

# 1) Test GET /auth/register
curl -s -D "$OUTDIR/register_headers.txt" -o "$OUTDIR/register_page.html" "$BASE/auth/register"
echo "Saved register page"

# 2) Test POST /auth/register (expected to either redirect or show validation)
curl -s -D "$OUTDIR/register_post_headers.txt" -o "$OUTDIR/register_post_response.html" -X POST \
  -d "first_name=Smoke&last_name=Tester&username=smoketestuser&email=smoke@example.com&password=Test12345!&confirm_password=Test12345!" \
  "$BASE/auth/register"

# 3) Test admin ui-customization pages (requires admin session). We try without auth to check response codes
curl -s -D "$OUTDIR/ui_dashboard_headers.txt" -o "$OUTDIR/ui_dashboard.html" "$BASE/admin/ui-customization"
curl -s -D "$OUTDIR/ui_login_headers.txt" -o "$OUTDIR/ui_login.html" "$BASE/admin/ui-customization/login"

# Output summary
echo "Smoke test complete. Results in $OUTDIR"
ls -l "$OUTDIR"

echo "Top lines of register_post_response.html:" 
head -n 50 "$OUTDIR/register_post_response.html" || true

echo "Top lines of ui_dashboard.html:" 
head -n 50 "$OUTDIR/ui_dashboard.html" || true

echo "Top lines of ui_login.html:" 
head -n 50 "$OUTDIR/ui_login.html" || true

exit 0