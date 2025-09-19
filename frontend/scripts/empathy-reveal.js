/* Non-destructive scroll reveal enhancer for Empathy Agent page.
   Usage: ensure root container has class 'empathy-agent-page'. Add data-reveal to elements.
   This script is safe to include once; it silently no-ops if APIs unsupported. */
(function() {
  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return;
  const root = document.querySelector('.empathy-agent-page');
  if (!root) return;
  const nodes = Array.from(root.querySelectorAll('[data-reveal]:not(.is-visible)'));
  if (!nodes.length) return;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) {
    nodes.forEach(n => n.classList.add('is-visible'));
    return;
  }
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -5% 0px' });
  nodes.forEach(n => obs.observe(n));
})();