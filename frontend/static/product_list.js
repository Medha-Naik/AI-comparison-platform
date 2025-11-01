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
    grid.innerHTML = offers.map((o, index) => {
      const detailsUrl = `/product-details?key=${encodeURIComponent(o.offer_key || '')}&title=${encodeURIComponent(o.title || '')}&store=${encodeURIComponent(o.store || '')}&price_display=${encodeURIComponent(o.price_display || '')}&image=${encodeURIComponent(o.image || '')}&url=${encodeURIComponent(o.url || '')}`;
      
      return `
      <div class="pl-card" data-index="${index}">
        <div class="img">${o.image ? `<img src="${o.image}" alt="${escapeHtml(o.title)}" loading="lazy"/>` : 'No Image'}</div>
        <div class="body">
          <div class="title">${escapeHtml(o.title)}</div>
          <div class="meta">
            <span class="store">${escapeHtml(o.store)}</span>
            <span class="price">${escapeHtml(o.price_display)}</span>
          </div>
          <div class="actions">
            <button class="btn-details" data-details-url="${escapeHtml(detailsUrl)}">
              View Details
            </button>
            <a href="${escapeHtml(o.url || '#')}" target="_blank" rel="noopener noreferrer" class="btn-store" onclick="event.stopPropagation()">
              <i class="fa-solid fa-external-link"></i> View on Store
            </a>
          </div>
        </div>
      </div>`;
    }).join('');

    // Add click handlers for "View Details" buttons
    document.querySelectorAll('.btn-details').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const url = btn.getAttribute('data-details-url');
        window.location.href = url;
      });
    });
  }

  function escapeHtml(text) {
    return (text || '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[c]));
  }

  loadOffers();
});