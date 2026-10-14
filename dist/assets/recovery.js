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
