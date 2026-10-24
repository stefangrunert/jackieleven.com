<?php
// Copy to app/config.local.php (ignored by Git) or set JACKIE_RESEND_API_KEY
// in PHP-FPM/Apache. Use a sending-only key restricted to unpubli.sh.
return [
    'resend_api_key' => '',
    // Production widget restricted to jackieleven.com; secret stays server-side.
    // Or JACKIE_TURNSTILE_SITEKEY / JACKIE_TURNSTILE_SECRET in PHP-FPM.
    'turnstile_sitekey' => '',
    'turnstile_secret' => '',
    // Optional for werkzeug/livevideos.php (or JACKIE_YOUTUBE_API_KEY): YouTube Data API
    // key to check embedding, age and country restrictions. Without it, oEmbed is used.
    'youtube_api_key' => '',
    // Embed fan recordings on release pages (or JACKIE_FAN_VIDEOS=1). Official only by default.
    'fan_videos' => false,
];
