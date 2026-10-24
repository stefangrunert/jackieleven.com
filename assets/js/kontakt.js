// Turnstile's flexible widget needs 300px; use its compact layout on narrow forms.
document.querySelectorAll('.kontakt-formular .cf-turnstile').forEach((widget) => {
  if (widget.parentElement.clientWidth < 300) widget.dataset.size = 'compact';
});
