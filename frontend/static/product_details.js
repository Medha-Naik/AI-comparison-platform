document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const key = params.get('key');
  const title = params.get('title') || '';
  const store = params.get('store') || '';
  const price = params.get('price_display') || '';
  const image = params.get('image') || '';
  const url = params.get('url') || '';

  // Fix back button navigation
  const backBtn = document.querySelector('.back');
  if (backBtn) {
    backBtn.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Try to get the last search URL from localStorage
      const lastSearchUrl = localStorage.getItem('lastSearchUrl');
      const lastSearchQuery = localStorage.getItem('lastSearchQuery');
      
      if (lastSearchUrl) {
        // Go back to the exact results page
        window.location.href = lastSearchUrl;
      } else if (lastSearchQuery) {
        // Reconstruct the results URL
        window.location.href = `/results?q=${encodeURIComponent(lastSearchQuery)}`;
      } else {
        // Fallback to browser history
        window.history.back();
      }
    });
  }

  // Populate hero section
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

  // Calculate price statistics
  function calculatePriceStats(history) {
    if (!history || history.length === 0) return null;
    
    const prices = history.map(h => h.price);
    const currentPrice = prices[prices.length - 1];
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
    
    // Calculate weekly average (last 7 days)
    const last7Days = history.slice(-7);
    const weeklyAvg = last7Days.length > 0 
      ? last7Days.reduce((sum, h) => sum + h.price, 0) / last7Days.length 
      : avgPrice;
    
    // Calculate trend
    const priceChange = currentPrice - prices[0];
    const priceChangePercent = ((priceChange / prices[0]) * 100).toFixed(1);
    
    return {
      current: currentPrice,
      min: minPrice,
      max: maxPrice,
      avg: avgPrice,
      weeklyAvg: weeklyAvg,
      priceChange: priceChange,
      priceChangePercent: priceChangePercent,
      isIncreasing: priceChange > 0,
      isAtLow: currentPrice <= minPrice * 1.05, // Within 5% of minimum
      isBelowAvg: currentPrice < avgPrice,
      isBelowWeeklyAvg: currentPrice < weeklyAvg
    };
  }

  // Render buy/wait recommendation
  function renderRecommendation(history) {
    const stats = calculatePriceStats(history);
    if (!stats) {
      document.getElementById('priceRecommendation').innerHTML = 
        '<p style="color: #6b7280;">Not enough data for recommendation.</p>';
      return;
    }
    
    // Determine recommendation
    let recommendation = '';
    let recommendClass = '';
    let recommendIcon = '';
    let reasoning = '';
    
    if (stats.isAtLow) {
      recommendation = 'BUY NOW';
      recommendClass = 'recommend-buy';
      recommendIcon = '🎯';
      reasoning = 'Price is at or near its lowest point in this period!';
    } else if (stats.isBelowWeeklyAvg && stats.isBelowAvg) {
      recommendation = 'GOOD TIME TO BUY';
      recommendClass = 'recommend-good';
      recommendIcon = '✅';
      reasoning = 'Price is below both weekly and overall average.';
    } else if (stats.isBelowAvg) {
      recommendation = 'CONSIDER BUYING';
      recommendClass = 'recommend-consider';
      recommendIcon = '👍';
      reasoning = 'Price is below the average price for this period.';
    } else if (stats.currentPrice > stats.weeklyAvg * 1.1) {
      recommendation = 'WAIT FOR BETTER PRICE';
      recommendClass = 'recommend-wait';
      recommendIcon = '⏳';
      reasoning = 'Price is significantly above recent weekly average.';
    } else {
      recommendation = 'MONITOR PRICE';
      recommendClass = 'recommend-monitor';
      recommendIcon = '👀';
      reasoning = 'Price is stable. Consider waiting for a drop.';
    }
    
    // Format currency
    const formatPrice = (price) => `₹${Math.round(price).toLocaleString('en-IN')}`;
    
    const recommendDiv = document.getElementById('priceRecommendation');
    recommendDiv.innerHTML = `
      <div class="recommendation-card ${recommendClass}">
        <div class="recommend-header">
          <span class="recommend-icon">${recommendIcon}</span>
          <span class="recommend-text">${recommendation}</span>
        </div>
        <div class="recommend-reason">${reasoning}</div>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Current Price</div>
          <div class="stat-value">${formatPrice(stats.current)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Lowest Price</div>
          <div class="stat-value stat-positive">${formatPrice(stats.min)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Highest Price</div>
          <div class="stat-value stat-negative">${formatPrice(stats.max)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">30-Day Average</div>
          <div class="stat-value">${formatPrice(stats.avg)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Weekly Average</div>
          <div class="stat-value">${formatPrice(stats.weeklyAvg)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Price Change</div>
          <div class="stat-value ${stats.isIncreasing ? 'stat-negative' : 'stat-positive'}">
            ${stats.isIncreasing ? '↑' : '↓'} ${Math.abs(stats.priceChangePercent)}%
          </div>
        </div>
      </div>
    `;
  }

  // Chart rendering
  let chartInstance = null;
  function renderChart(history) {
    const ctx = document.getElementById('pdChart').getContext('2d');
    
    if (history.length === 0) {
      ctx.font = '14px Poppins';
      ctx.fillStyle = '#6b7280';
      ctx.textAlign = 'center';
      ctx.fillText('No price history available yet', ctx.canvas.width / 2, ctx.canvas.height / 2);
      return;
    }
    
    const labels = history.map(h => {
      const date = new Date(h.date);
      return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
    });
    const values = history.map(h => h.price);
    
    // Calculate average line
    const avgPrice = values.reduce((a, b) => a + b, 0) / values.length;
    
    if (chartInstance) chartInstance.destroy();
    
    chartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Price',
            data: values,
            borderColor: '#2b59c3',
            backgroundColor: 'rgba(43, 89, 195, 0.1)',
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: true
          },
          {
            label: 'Average',
            data: Array(values.length).fill(avgPrice),
            borderColor: '#10b981',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: function(value) {
                return '₹' + value.toLocaleString('en-IN');
              }
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 15
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return context.dataset.label + ': ₹' + context.parsed.y.toLocaleString('en-IN');
              }
            }
          }
        }
      }
    });
  }

  // Load price history and render
  async function loadHistoryAndRender(days = '30') {
    if (!key) {
      document.getElementById('priceRecommendation').innerHTML = 
        '<p style="color: #ef4444;">No product key provided.</p>';
      return;
    }
    
    try {
      const resp = await fetch(`/price-history?key=${encodeURIComponent(key)}&days=${encodeURIComponent(days)}`);
      const data = await resp.json();
      const history = data.history || [];
      
      renderChart(history);
      renderRecommendation(history);
    } catch (e) {
      console.error('Failed to load price history', e);
      document.getElementById('priceRecommendation').innerHTML = 
        '<p style="color: #ef4444;">Error loading price data.</p>';
    }
  }

  // Range button handlers
  const rangeButtons = Array.from(document.querySelectorAll('.range-btn'));
  rangeButtons.forEach(btn => btn.addEventListener('click', async () => {
    rangeButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const days = btn.getAttribute('data-days');
    await loadHistoryAndRender(days);
  }));

  // Load reviews
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

  function escapeHtml(text) {
    const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
    return (text || '').replace(/[&<>"']/g, c => map[c]);
  }

  // Initial loads
  loadHistoryAndRender('30');
  loadReviews();
});