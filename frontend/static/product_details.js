document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const key = params.get('key');
  const title = params.get('title') || '';
  const store = params.get('store') || '';
  const price = params.get('price_display') || '';
  const image = params.get('image') || '';
  const url = params.get('url') || '';

  // Populate hero
  document.getElementById('pdTitle').textContent = title;
  document.getElementById('pdStore').textContent = store;
  document.getElementById('pdPrice').textContent = price;
  document.getElementById('pdLink').href = url;
  const imgWrap = document.getElementById('pdImage');
  if (image) {
    const img = document.createElement('img');
    img.src = image;
    img.alt = title;
    img.loading = 'lazy';
    imgWrap.appendChild(img);
  } else {
    imgWrap.textContent = 'No Image';
  }

  // Reviews
  async function loadReviews() {
    if (!key) return;
    try {
      const resp = await fetch(`/product-reviews?key=${encodeURIComponent(key)}`);
      const data = await resp.json();
      const list = document.getElementById('reviewsList');
      const reviews = data.reviews || [];
      if (reviews.length === 0) {
        list.textContent = 'No reviews available.';
        return;
      }
      list.innerHTML = reviews.map(r => `
        <div class="review">
          <div class="review-title">${escapeHtml(r.title || '')}</div>
          <div class="review-meta">${escapeHtml(r.author || 'Anonymous')} • ${'★'.repeat(r.rating || 0)}</div>
          <div class="review-body">${escapeHtml(r.body || '')}</div>
        </div>
      `).join('');
    } catch (e) {
      console.error('Failed to load reviews', e);
    }
  }

  // Chart
  const rangeButtons = Array.from(document.querySelectorAll('.range-btn'));
  rangeButtons.forEach(btn => btn.addEventListener('click', async () => {
    rangeButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const days = btn.getAttribute('data-days');
    await loadHistoryAndRender(days);
  }));

  async function loadHistoryAndRender(days = '30') {
    if (!key) return;
    const resp = await fetch(`/price-history?key=${encodeURIComponent(key)}&days=${encodeURIComponent(days)}`);
    const data = await resp.json();
    const history = data.history || [];
    renderChart(history);
  }

  let chartInstance = null;
  function renderChart(history) {
    const ctx = document.getElementById('pdChart').getContext('2d');
    const labels = history.map(h => h.date);
    const values = history.map(h => h.price);
    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Price',
          data: values,
          borderColor: '#2b59c3',
          backgroundColor: 'rgba(43, 89, 195, 0.1)',
          tension: 0.25,
          pointRadius: 2
        }]
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: false } },
        plugins: { legend: { display: false } }
      }
    });
  }

  function escapeHtml(text) {
    return (text || '').replace(/[&<>"]+/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  // Initial loads
  loadHistoryAndRender('30');
  loadReviews();
});




