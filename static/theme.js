(() => {
  const key = 'family-points-theme';
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  let saved;
  try { saved = localStorage.getItem(key); } catch (_) {}
  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.textContent = theme === 'dark' ? '☀️ Jasny motyw' : '🌙 Ciemny motyw';
      button.setAttribute('aria-pressed', String(theme === 'dark'));
      button.setAttribute('aria-label', theme === 'dark' ? 'Włącz jasny motyw' : 'Włącz ciemny motyw');
    });
  }
  apply(saved === 'dark' || saved === 'light' ? saved : system.matches ? 'dark' : 'light');
  document.addEventListener('DOMContentLoaded', () => {
    apply(document.documentElement.dataset.theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        saved = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        apply(saved);
        try { localStorage.setItem(key, saved); } catch (_) {}
      });
    });
  });
  system.addEventListener('change', () => {
    if (saved !== 'dark' && saved !== 'light') apply(system.matches ? 'dark' : 'light');
  });
})();
