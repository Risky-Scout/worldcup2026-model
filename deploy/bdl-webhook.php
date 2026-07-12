<?php
/**
 * BDL Webhook Receiver
 * Deployed to: /tools/odds-scanner/predictions/worldcup/bdl-webhook.php
 * Public URL:  https://sportsodds.wizardofodds.com/tools/odds-scanner/predictions/worldcup/bdl-webhook.php
 *
 * On receiving a valid BDL event, triggers the live.yml GitHub Actions workflow
 * so the X-Ray page updates within seconds instead of waiting for the 80s cron.
 */

// ── Config ────────────────────────────────────────────────────────────────────
$WEBHOOK_SECRET  = getenv('WEBHOOK_SECRET')  ?: ''; // set in server env / .htaccess
$GITHUB_TOKEN    = getenv('GITHUB_TOKEN')    ?: ''; // fine-grained PAT: actions:write
$GITHUB_REPO     = 'Risky-Scout/worldcup2026-model';
$WORKFLOW_FILE   = 'live.yml';

// ── Only accept POST ──────────────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

// ── Read body ─────────────────────────────────────────────────────────────────
$body = file_get_contents('php://input');

// ── Validate BDL signature (HMAC-SHA256) ─────────────────────────────────────
if ($WEBHOOK_SECRET !== '') {
    $sig_header = $_SERVER['HTTP_X_BDL_SIGNATURE'] ?? $_SERVER['HTTP_X_WEBHOOK_SIGNATURE'] ?? '';
    $expected   = 'sha256=' . hash_hmac('sha256', $body, $WEBHOOK_SECRET);
    if (!hash_equals($expected, $sig_header)) {
        http_response_code(401);
        exit('Unauthorized');
    }
}

// ── Parse event ───────────────────────────────────────────────────────────────
$event = json_decode($body, true);
if (!$event) {
    http_response_code(400);
    exit('Bad Request');
}

// ── Log event type for debugging ─────────────────────────────────────────────
$event_type = $event['event'] ?? $event['type'] ?? 'unknown';
error_log("BDL webhook received: {$event_type}");

// ── Only trigger pipeline for relevant events ─────────────────────────────────
$trigger_events = ['goal', 'score_update', 'status_change', 'match_start', 
                   'match_end', 'card', 'substitution', 'period_start', 'period_end',
                   'game.started', 'game.ended', 'game.updated'];
$should_trigger = false;
foreach ($trigger_events as $te) {
    if (stripos($event_type, $te) !== false || $event_type === $te) {
        $should_trigger = true;
        break;
    }
}

// Always trigger for WORLDCUP events — any event is worth a refresh
$league = strtoupper($event['league'] ?? $event['sport'] ?? $event['competition'] ?? '');
if (strpos($league, 'WORLD') !== false || strpos($league, 'WC') !== false || strpos($league, 'FIFA') !== false) {
    $should_trigger = true;
}

if (!$should_trigger) {
    http_response_code(200);
    echo json_encode(['ok' => true, 'action' => 'ignored', 'event' => $event_type]);
    exit;
}

// ── Trigger GitHub Actions live.yml via workflow_dispatch ─────────────────────
if ($GITHUB_TOKEN !== '') {
    $gh_payload = json_encode([
        'ref'    => 'main',
        'inputs' => ['trigger_source' => 'bdl_webhook', 'event_type' => $event_type]
    ]);

    $ch = curl_init("https://api.github.com/repos/{$GITHUB_REPO}/actions/workflows/{$WORKFLOW_FILE}/dispatches");
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $gh_payload,
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . $GITHUB_TOKEN,
            'Accept: application/vnd.github+json',
            'X-GitHub-Api-Version: 2022-11-28',
            'Content-Type: application/json',
            'User-Agent: WoO-BDL-Webhook/1.0',
        ],
        CURLOPT_TIMEOUT        => 10,
    ]);
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    $triggered = ($http_code === 204); // GitHub returns 204 No Content on success
    error_log("GitHub dispatch: HTTP {$http_code}");
} else {
    $triggered = false;
    $http_code = 0;
}

// ── Respond to BDL ───────────────────────────────────────────────────────────
http_response_code(200);
header('Content-Type: application/json');
echo json_encode([
    'ok'        => true,
    'event'     => $event_type,
    'triggered' => $triggered,
    'gh_status' => $http_code,
]);
