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

  // Initial load
  loadHistoryAndRender('30');
});


