<?php /** @var string $dienst — eigene, reduzierte SVG-Zeichen für die Hörlinks. */ ?>
<svg class="musik-icon" viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
<?php if ($dienst === 'spotify'): ?>
  <circle cx="12" cy="12" r="9.25" stroke="currentColor" stroke-width="1.5"/>
  <path d="M6.8 9.1c3.2-1.1 7.2-.9 10.3.8M7.6 12.2c2.7-.8 5.8-.6 8.5.7M8.4 15.1c2.2-.5 4.5-.3 6.7.7" stroke="currentColor" stroke-width="1.65" stroke-linecap="round"/>
<?php elseif ($dienst === 'apple'): ?>
  <path d="M9 17.2V6.8l10-2.1v10.5M9 10l10-2.1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <ellipse cx="6.5" cy="17.8" rx="3.2" ry="2.25" transform="rotate(-18 6.5 17.8)" fill="currentColor"/>
  <ellipse cx="16.5" cy="15.8" rx="3.2" ry="2.25" transform="rotate(-18 16.5 15.8)" fill="currentColor"/>
<?php endif; ?>
</svg>
