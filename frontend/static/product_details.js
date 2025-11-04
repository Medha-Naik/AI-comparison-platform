document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const key = params.get('key');
  const title = params.get('title') || '';
  const store = params.get('store') || '';
  const price = params.get('price_display') || '';
  const image = params.get('image') || '';
  const url = params.get('url') || '';

  // ---- HERO SETUP ----
  document.getElementById('pdTitle').textContent = title;
  document.getElementById('pdStore').textContent = store;
  document.getElementById('pdPrice').textContent = price;
  document.getElementById('pdLink').href = url;

  // Product Image
  const imgWrap = document.getElementById('pdImage');
  if (image) {
    const img = document.createElement('img');
    img.src = image.startsWith('http') ? image : `/images/${image}`;
    img.alt = title;
    img.loading = 'lazy';
    img.onerror = () => (imgWrap.innerHTML = '<div>No Image</div>');
    imgWrap.appendChild(img);
  } else imgWrap.textContent = 'No Image';

  // ---- PRICE HISTORY + CHART ----
  async function loadHistoryAndRender(days = '30') {
    if (!key) return;
    try {
      const resp = await fetch(`/price-history?key=${encodeURIComponent(key)}&days=${encodeURIComponent(days)}`);
      const data = await resp.json();
      const history = data.history || [];
      renderChart(history);
      renderRecommendation(history);
    } catch (e) {
      console.error('Price history load error:', e);
    }
  }

  let chartInstance = null;
  function renderChart(history) {
    const ctx = document.getElementById('pdChart').getContext('2d');
    if (!history.length) return;
    const labels = history.map(h => new Date(h.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
    const values = history.map(h => h.price);
    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Price',
          data: values,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  // ---- BUY/WAIT RECOMMENDATION ----
  function renderRecommendation(history) {
    const div = document.getElementById('priceRecommendation');
    if (!history.length) {
      div.innerHTML = '<p>No price data available yet.</p>';
      return;
    }
    const prices = history.map(h => h.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const latest = prices[prices.length - 1];
    let text = '', icon = '', color = '';
    if (latest <= min * 1.05) {
      text = 'BUY NOW — price near all-time low!'; icon = '🎯'; color = '#16a34a';
    } else if (latest < avg) {
      text = 'Good time to buy'; icon = '✅'; color = '#10b981';
    } else if (latest > avg * 1.1) {
      text = 'Wait for a price drop'; icon = '⏳'; color = '#f59e0b';
    } else {
      text = 'Monitor price trends'; icon = '👀'; color = '#2563eb';
    }
    div.innerHTML = `<p style="color:${color}; font-weight:600;">${icon} ${text}</p>`;
  }

  // ---- WISHLIST ----
  const wishlistBtn = document.getElementById('wishlistBtn');
  const wishlistIcon = wishlistBtn.querySelector('i');
  let isInWishlist = false;

  async function checkWishlistStatus() {
    try {
      const me = await (await fetch('/auth/me')).json();
      if (!me.authenticated) return;
      const check = await (await fetch(`/api/wishlist/check/${encodeURIComponent(title)}`)).json();
      if (check.success && check.in_wishlist) {
        isInWishlist = true;
        wishlistIcon.classList.replace('fa-regular', 'fa-solid');
        wishlistBtn.style.borderColor = '#ef4444';
        wishlistBtn.style.background = '#fef2f2';
        wishlistIcon.style.color = '#ef4444';
      }
    } catch (err) {
      console.error('Wishlist check error:', err);
    }
  }

  wishlistBtn.addEventListener('click', async () => {
    try {
      const me = await (await fetch('/auth/me')).json();
      if (!me.authenticated) {
        window.location.href = `/login?next=${encodeURIComponent(window.location.href)}`;
        return;
      }
      if (isInWishlist) {
        const check = await (await fetch(`/api/wishlist/check/${encodeURIComponent(title)}`)).json();
        if (check.in_wishlist && check.wishlist_item) {
          const remove = await (await fetch('/api/wishlist/remove', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wishlist_item_id: check.wishlist_item.id })
          })).json();
          if (remove.success) {
            isInWishlist = false;
            wishlistIcon.classList.replace('fa-solid', 'fa-regular');
            wishlistBtn.style.borderColor = '#e5e7eb';
            wishlistBtn.style.background = 'none';
            wishlistIcon.style.color = '#666';
          }
        }
      } else {
        const response = await (await fetch('/api/wishlist/add', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_name: title, product_category: 'Electronics' })
        })).json();
        if (response.success) {
          isInWishlist = true;
          wishlistIcon.classList.replace('fa-regular', 'fa-solid');
          wishlistBtn.style.borderColor = '#ef4444';
          wishlistBtn.style.background = '#fef2f2';
          wishlistIcon.style.color = '#ef4444';
        }
      }
    } catch (err) {
      console.error('Wishlist error:', err);
    }
  });

  checkWishlistStatus();

  // ---- AI REVIEW ANALYSIS ----
  async function loadAIReviews() {
    if (!url) return;
    const summaryDiv = document.getElementById('reviewSummary');
    const listDiv = document.getElementById('reviewsList');
    const chartCanvas = document.getElementById('reviewSentimentChart');

    summaryDiv.innerHTML = '<p>Analyzing reviews...</p>';
    listDiv.innerHTML = '<p>Loading detailed reviews...</p>';

    try {
      const resp = await fetch(`/api/reviews/analyze?url=${encodeURIComponent(url)}`);
      const data = await resp.json();

      if (!data.success) {
        summaryDiv.innerHTML = `<p style="color:#ef4444;">${data.error || 'No reviews found.'}</p>`;
        return;
      }

      // Summary
      summaryDiv.innerHTML = `
        <h3>AI Review Summary</h3>
        <p>${data.summary}</p>
      `;

      // --- Compact Pie Chart ---
      chartCanvas.style.width = '260px';
      chartCanvas.style.height = '260px';
      chartCanvas.style.margin = '0 auto';
      chartCanvas.style.display = 'block';

      new Chart(chartCanvas, {
        type: 'pie',
        data: {
          labels: ['Positive', 'Negative'],
          datasets: [{
            data: [data.sentiments.positive, data.sentiments.negative],
            backgroundColor: ['#22c55e', '#ef4444'],
            borderWidth: 2
          }]
        },
        options: {
          responsive: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { font: { size: 13 } }
            }
          }
        }
      });

      // Reviews List
      listDiv.innerHTML = `
        <div>
          <h4>Positive Reviews</h4>
          ${data.positive_reviews.map(r => `<p>✅ ${escapeHtml(r)}</p>`).join('')}
          <h4>Negative Reviews</h4>
          ${data.negative_reviews.map(r => `<p>❌ ${escapeHtml(r)}</p>`).join('')}
        </div>
      `;
    } catch (err) {
      console.error('AI review load error:', err);
      summaryDiv.innerHTML = '<p style="color:#ef4444;">Error loading AI reviews.</p>';
    }
  }

  function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return (text || '').replace(/[&<>"']/g, c => map[c]);
  }

  // ---- INIT ----
  loadHistoryAndRender('30');
  loadAIReviews();
});
