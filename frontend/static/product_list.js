document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const q = params.get('q') || '';
  const title = params.get('title') || q;
  document.getElementById('plTitle').textContent = `Compare prices for: ${title}`;

  async function loadOffers() {
    if (!q) return;
    const resp = await fetch(`/search?q=${encodeURIComponent(q)}`);
    const data = await resp.json();
    const offers = data.offers || [];
    renderOffers(offers);
  }

  function renderOffers(offers) {
    const grid = document.getElementById('offersGrid');
    grid.innerHTML = offers.map(o => {
      const detailsUrl = `/product-details?key=${encodeURIComponent(o.offer_key || '')}&title=${encodeURIComponent(o.title || '')}&store=${encodeURIComponent(o.store || '')}&price_display=${encodeURIComponent(o.price_display || '')}&image=${encodeURIComponent(o.image || '')}&url=${encodeURIComponent(o.url || '')}`;
      return `
      <div class="pl-card" role="button" tabindex="0" onclick="window.location.href='${detailsUrl}'" onkeypress="if(event.key==='Enter'){window.location.href='${detailsUrl}'}">
        <div class="img">${o.image ? `<img src="${o.image}" alt="${escapeHtml(o.title)}" loading="lazy"/>` : 'No Image'}</div>
        <div class="body">
          <div class="title">${escapeHtml(o.title)}</div>
          <div class="meta"><span class="store">${escapeHtml(o.store)}</span><span class="price">${escapeHtml(o.price_display)}</span></div>
        </div>
      </div>`;
    }).join('');
  }

  function escapeHtml(text) {
    return (text || '').replace(/[&<>"]+/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  loadOffers();
});


