<?php /** @var string $dienst — eigene, reduzierte SVG-Zeichen für die Hörlinks. */ ?>
<svg class="musik-icon" viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
<?php if ($dienst === 'spotify'): ?>
  <circle cx="12" cy="12" r="9.25" stroke="currentColor" stroke-width="1.5"/>
  <path d="M6.8 9.1c3.2-1.1 7.2-.9 10.3.8M7.6 12.2c2.7-.8 5.8-.6 8.5.7M8.4 15.1c2.2-.5 4.5-.3 6.7.7" stroke="currentColor" stroke-width="1.65" stroke-linecap="round"/>
<?php elseif ($dienst === 'apple'): ?>
  <path d="M9 17.2V6.8l10-2.1v10.5M9 10l10-2.1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <ellipse cx="6.5" cy="17.8" rx="3.2" ry="2.25" transform="rotate(-18 6.5 17.8)" fill="currentColor"/>
  <ellipse cx="16.5" cy="15.8" rx="3.2" ry="2.25" transform="rotate(-18 16.5 15.8)" fill="currentColor"/>
<?php elseif ($dienst === 'youtube'): ?>
  <rect x="2.5" y="5" width="19" height="14" rx="4" stroke="currentColor" stroke-width="1.5"/>
  <path d="m10 8.5 6 3.5-6 3.5z" fill="currentColor"/>
<?php elseif ($dienst === 'qobuz'): ?>
  <circle cx="10.5" cy="10.5" r="7.5" stroke="currentColor" stroke-width="1.6"/>
  <circle cx="10.5" cy="10.5" r="2.25" stroke="currentColor" stroke-width="1.4"/>
  <path d="m14.7 15.7 5 5h-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
<?php elseif ($dienst === 'amazon'): ?>
  <path d="M5 14V7.5l3.2 3.7 3.3-3.7V14M15 14V7.5h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M3.5 17.5c4.7 3 10.9 3.4 16.4-.4m-3.1-.7 3.8-.1-.8 3.3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
<?php elseif ($dienst === 'bandcamp'): ?>
  <path d="m8 6-6 12h14l6-12z" fill="currentColor"/>
<?php endif; ?>
</svg>
