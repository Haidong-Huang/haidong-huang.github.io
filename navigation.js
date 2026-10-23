(function initSectionNavigation() {
  const header = document.querySelector('.site-header');
  const track = document.querySelector('.section-nav__track');
  const entries = Array.from(document.querySelectorAll('.section-nav__link')).map(link => {
    const url = new URL(link.href);
    const section = url.pathname === location.pathname && url.hash
      ? document.getElementById(url.hash.slice(1)) : null;
    return section ? { link, section } : null;
  }).filter(Boolean);
  if (!header || !track || !entries.length) return;

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let ticking = false;
  let active = null;
  let requested = null;

  function setActive(entry) {
    if (entry === active) return;
    active = entry;
    entries.forEach(candidate => {
      const current = candidate === entry;
      candidate.link.classList.toggle('is-active', current);
      if (current) candidate.link.setAttribute('aria-current', 'location');
      else candidate.link.removeAttribute('aria-current');
    });
    if (track.scrollWidth > track.clientWidth) {
      const bounds = entry.link.getBoundingClientRect();
      const visible = track.getBoundingClientRect();
      if (bounds.left < visible.left || bounds.right > visible.right) {
        track.scrollTo({left: track.scrollLeft + bounds.left - visible.left - (visible.width - bounds.width) / 2,
          behavior: reducedMotion.matches ? 'auto' : 'smooth'});
      }
    }
  }

  function sync() {
    ticking = false;
    const offset = header.getBoundingClientRect().height + 30;
    let current = entries[0];
    entries.forEach(entry => {
      if (entry.section.getBoundingClientRect().top <= offset) current = entry;
    });
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 8) {
      const target = requested && requested.section.getBoundingClientRect();
      current = target && target.top >= header.offsetHeight && target.top < innerHeight
        ? requested : entries[entries.length - 1];
    }
    setActive(current);
  }
  function schedule() {
    if (!ticking) { ticking = true; requestAnimationFrame(sync); }
  }
  function clearTarget() { requested = null; schedule(); }

  entries.forEach(entry => entry.link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    requested = entry;
    entry.section.scrollIntoView({behavior: reducedMotion.matches ? 'auto' : 'smooth', block: 'start'});
    if (location.hash !== entry.link.hash) history.pushState(null, '', entry.link.hash);
    setActive(entry);
    if (event.detail === 0) entry.section.focus({preventScroll: true});
  }));
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', schedule, {passive: true});
  addEventListener('wheel', clearTarget, {passive: true});
  addEventListener('touchstart', clearTarget, {passive: true});
  addEventListener('keydown', event => {
    if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End'].includes(event.key)) clearTarget();
  });
  addEventListener('hashchange', clearTarget);
  addEventListener('popstate', clearTarget);
  addEventListener('pageshow', schedule);
  if (window.ResizeObserver) {
    const observer = new ResizeObserver(schedule);
    observer.observe(header);
    entries.forEach(entry => observer.observe(entry.section));
  }
  if (document.fonts) document.fonts.ready.then(schedule);
  sync();
})();
