'use strict';
const menuButton = document.querySelector('.menu-button');
const menu = document.getElementById('mobile-nav');
function setMenu(open) {
  menu.hidden = !open;
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
}
menuButton.addEventListener('click', () => setMenu(menu.hidden));
menu.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !menu.hidden) { setMenu(false); menuButton.focus(); } });
window.dataLayer = window.dataLayer || [];
document.addEventListener('click', e => {
  const link=e.target.closest('a[data-reservation], a[data-store-link]');
  if (!link) return;
  window.dataLayer.push({ event: link.hasAttribute('data-reservation') ? 'reserve_click' : 'store_select', program: '大人', store: link.dataset.storeLink || document.body.dataset.store, position: link.dataset.position || 'shoplist', destination: link.href });
});

const bookingBar = document.querySelector('.booking-bar');
const hero = document.querySelector('.adult-hero');
const footer = document.querySelector('.site-footer');
const shopList = document.querySelector('#shoplist');
let pastHero=false, atFooter=false, atShops=false;
function updateBookingBar(){bookingBar.hidden=!pastHero||atFooter||atShops;}
if (bookingBar && 'IntersectionObserver' in window) {
  new IntersectionObserver(entries => { pastHero = !entries[0].isIntersecting && entries[0].boundingClientRect.top < 0; updateBookingBar(); }).observe(hero);
  new IntersectionObserver(entries => { atFooter = entries[0].isIntersecting; updateBookingBar(); }).observe(footer);
  new IntersectionObserver(entries => { atShops = entries[0].isIntersecting; updateBookingBar(); }).observe(shopList);
}

const storeFloating = document.querySelector('.store-floating');
if (storeFloating && hero) {
  function updateStoreFloating(visible) {
    storeFloating.classList.toggle('is-on', visible);
    storeFloating.inert = !visible;
    storeFloating.setAttribute('aria-hidden', String(!visible));
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      updateStoreFloating(!entries[0].isIntersecting && entries[0].boundingClientRect.top < 0);
    }, {threshold: 0}).observe(hero);
  } else {
    updateStoreFloating(true);
  }
  if ('ResizeObserver' in window) {
    new ResizeObserver(() => {
      document.body.style.setProperty('--floating-height', `${storeFloating.offsetHeight}px`);
    }).observe(storeFloating);
  }
}
