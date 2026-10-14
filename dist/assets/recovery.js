'use strict';
const menuButton = document.querySelector('.menu-button');
const menu = document.getElementById('mobile-nav');
const header = document.querySelector('.recovery-header');
function setMenu(open) {
  menu.hidden = !open;
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
}
menuButton.addEventListener('click', () => setMenu(menu.hidden));
menu.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !menu.hidden) { setMenu(false); menuButton.focus(); }
});

// Keep the first view open; reveal the fixed header after a short scroll.
const headerRevealOffset = 120;
let headerUpdatePending = false;
function updateHeader() {
  const visible = window.scrollY >= headerRevealOffset;
  if (!visible && !menu.hidden) setMenu(false);
  header.inert = !visible;
  header.classList.toggle('is-visible', visible);
}
window.addEventListener('scroll', () => {
  if (headerUpdatePending) return;
  headerUpdatePending = true;
  window.requestAnimationFrame(() => {
    updateHeader();
    headerUpdatePending = false;
  });
}, { passive: true });
window.addEventListener('pageshow', updateHeader);
updateHeader();

// Keep Recovery clicks separate from the inherited adult program.
window.dataLayer = window.dataLayer || [];
document.addEventListener('click', event => {
  const link = event.target.closest('a[data-position]');
  if (link) window.dataLayer.push({ event: 'recovery_trial_interest', program: 'Recovery', position: link.dataset.position, destination: link.getAttribute('href') });
});

const bookingBar = document.querySelector('.booking-bar');
const hero = document.querySelector('.hero');
const headerHeight = header.getBoundingClientRect().height;
function updateBookingBar(visible) {
  bookingBar.classList.toggle('is-on', visible);
  bookingBar.inert = !visible;
}
if ('IntersectionObserver' in window) {
  new IntersectionObserver(entries => {
    const entry = entries[0];
    updateBookingBar(!entry.isIntersecting && entry.boundingClientRect.bottom <= headerHeight);
  }, { rootMargin: `-${headerHeight}px 0px 0px 0px` }).observe(hero);
} else {
  updateBookingBar(true);
}

// Enhance the voice track without taking over native horizontal scrolling.
document.querySelectorAll('.voice-carousel').forEach(carousel => {
  const track = carousel.querySelector('.voice-grid');
  const controls = carousel.querySelector('.voice-carousel-controls');
  const previous = controls?.querySelector('.voice-prev');
  const next = controls?.querySelector('.voice-next');
  const cards = track ? Array.from(track.querySelectorAll('.voice-card')) : [];
  if (!track || !controls || !previous || !next || !cards.length) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const tolerance = 2;
  let updatePending = false;

  function updateControls() {
    const maximum = Math.max(0, track.scrollWidth - track.clientWidth);
    const position = Math.max(0, Math.min(track.scrollLeft, maximum));
    controls.hidden = maximum <= tolerance;
    previous.disabled = position <= tolerance;
    next.disabled = maximum - position <= tolerance;
  }

  function queueUpdate() {
    if (updatePending) return;
    updatePending = true;
    window.requestAnimationFrame(() => {
      updatePending = false;
      updateControls();
    });
  }

  function move(direction) {
    const maximum = Math.max(0, track.scrollWidth - track.clientWidth);
    const position = Math.max(0, Math.min(track.scrollLeft, maximum));
    const trackLeft = track.getBoundingClientRect().left + track.clientLeft;
    const scrollPadding = parseFloat(getComputedStyle(track).scrollPaddingLeft) || 0;
    const positions = cards.map((card, index) => index === 0 ? 0 : Math.max(0, Math.min(
      card.getBoundingClientRect().left - trackLeft + track.scrollLeft - scrollPadding,
      maximum
    )));
    const target = direction > 0
      ? positions.find(left => left > position + tolerance)
      : positions.reverse().find(left => left < position - tolerance);
    track.scrollTo({
      left: target ?? (direction > 0 ? maximum : 0),
      behavior: reducedMotion.matches ? 'auto' : 'smooth'
    });
    queueUpdate();
  }

  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  track.addEventListener('scroll', queueUpdate, { passive: true });
  window.addEventListener('resize', queueUpdate, { passive: true });
  window.addEventListener('pageshow', queueUpdate);
  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(queueUpdate);
    observer.observe(track);
    cards.forEach(card => observer.observe(card));
  }
  updateControls();
});
