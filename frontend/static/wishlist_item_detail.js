document.addEventListener('DOMContentLoaded', () => {
  const loadingState = document.getElementById('loadingState');
  const productHeader = document.getElementById('productHeader');
  const productName = document.getElementById('productName');
  const productCategory = document.getElementById('productCategory');
  const targetPriceSection = document.getElementById('targetPriceSection');
  const currentPrices = document.getElementById('currentPrices');
  const updateTargetBtn = document.getElementById('updateTargetBtn');
  const removeItemBtn = document.getElementById('removeItemBtn');

  let itemData = null;
  let priceChart = null;

  // Load item details
  loadItemDetails();

  // Event listeners
  updateTargetBtn.addEventListener('click', handleUpdateTarget);
  removeItemBtn.addEventListener('click', handleRemoveItem);

  // Search functionality
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  
  searchBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    if (query) {
      window.location.href = `/results?q=${encodeURIComponent(query)}`;
    }
  });
  
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const query = searchInput.value.trim();
      if (query) {
        window.location.href = `/results?q=${encodeURIComponent(query)}`;
      }
    }
  });

  async function loadItemDetails() {
    try {
      const response = await fetch(`/api/wishlist/details/${ITEM_ID}`);
      const data = await response.json();

      if (data.success) {
        itemData = data;
        displayItemDetails(data);
      } else {
        showError(data.message || 'Failed to load item details');
        setTimeout(() => {
          window.location.href = '/wishlist';
        }, 2000);
      }
    } catch (error) {
      console.error('Error loading item details:', error);
      showError('Failed to load item details');
    }
  }

  function displayItemDetails(data) {
    loadingState.style.display = 'none';
    productHeader.style.display = 'block';

    // Product header
    productName.textContent = data.item.product_name;
    if (data.item.product_category) {
      productCategory.textContent = data.item.product_category;
    } else {
      productCategory.style.display = 'none';
    }

    // Target price
    if (data.item.target_price) {
      targetPriceSection.innerHTML = `
        <div class="target-price">
          <div class="target-price-header">
            <h4><i class="fa-solid fa-bullseye"></i> Target Price</h4>
            <span class="target-price-value">₹${data.item.target_price.toLocaleString()}</span>
          </div>
          ${data.lowest_price && data.lowest_price <= data.item.target_price ? `
            <div style="margin-top: 10px; padding: 10px; background: #d4edda; border-radius: 8px; color: #155724;">
              <i class="fa-solid fa-check-circle"></i> Target price reached! Lowest price: ₹${data.lowest_price.toLocaleString()}
            </div>
          ` : ''}
        </div>
      `;
    } else {
      targetPriceSection.innerHTML = `
        <div class="target-price">
          <div class="target-price-header">
            <h4><i class="fa-solid fa-bullseye"></i> No Target Price Set</h4>
          </div>
        </div>
      `;
    }

    // Current prices
    displayCurrentPrices(data.current_prices, data.lowest_price);

    // Price history chart
    displayPriceChart(data.price_history);
  }

  function displayCurrentPrices(prices, lowestPrice) {
    if (!prices || Object.keys(prices).length === 0) {
      currentPrices.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #666;">
          <i class="fa-solid fa-info-circle" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
          <p>No price data available. Click "Refresh Prices" to fetch current prices.</p>
        </div>
      `;
      return;
    }

    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">';

    const storeOrder = ['flipkart', 'amazon', 'croma', 'reliance'];
    const sortedStores = Object.keys(prices).sort((a, b) => {
      const indexA = storeOrder.indexOf(a);
      const indexB = storeOrder.indexOf(b);
      if (indexA === -1 && indexB === -1) return a.localeCompare(b);
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    });

    sortedStores.forEach(store => {
      const priceData = prices[store];
      const isLowest = lowestPrice && priceData.price === lowestPrice;

      html += `
        <div class="store-price ${isLowest ? 'lowest' : ''}" data-store="${store}">
          <h4>${store.charAt(0).toUpperCase() + store.slice(1)}</h4>
          <div class="price ${isLowest ? 'lowest' : ''}">${priceData.price_display}</div>
          ${isLowest ? '<div class="lowest-badge">Lowest Price</div>' : ''}
          ${priceData.url ? `
            <a href="${priceData.url}" target="_blank" class="btn btn-primary" style="margin-top: 10px; font-size: 12px; padding: 5px 10px;">
              View on ${store.charAt(0).toUpperCase() + store.slice(1)}
            </a>
          ` : ''}
        </div>
      `;
    });

    html += '</div>';
    currentPrices.innerHTML = html;
  }

  function displayPriceChart(priceHistory) {
    const ctx = document.getElementById('priceHistoryChart').getContext('2d');

    // Destroy existing chart if it exists
    if (priceChart) {
      priceChart.destroy();
    }

    // Store colors
    const storeColors = {
      'flipkart': '#2874f0',
      'amazon': '#ff9900',
      'croma': '#00a699',
      'reliance': '#e42529'
    };

    // Prepare datasets
    const datasets = [];

    if (!priceHistory || Object.keys(priceHistory).length === 0) {
      // Show empty state
      priceChart = new Chart(ctx, {
        type: 'line',
        data: { datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { enabled: false }
          }
        }
      });
      
      // Show message
      const chartContainer = ctx.canvas.parentElement;
      const emptyMsg = document.createElement('div');
      emptyMsg.style.cssText = 'text-align: center; padding: 40px; color: #666;';
      emptyMsg.innerHTML = `
        <i class="fa-solid fa-chart-line" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
        <p>No price history available for the last 30 days.</p>
        <p style="font-size: 14px; margin-top: 8px;">Prices will appear here once price tracking begins.</p>
      `;
      chartContainer.appendChild(emptyMsg);
      return;
    }

    Object.keys(priceHistory).forEach(store => {
      const history = priceHistory[store];
      
      if (history && history.length > 0) {
        datasets.push({
          label: store.charAt(0).toUpperCase() + store.slice(1),
          data: history.map(item => ({
            x: item.date,  // ISO format string - Chart.js will parse it
            y: item.price
          })),
          borderColor: storeColors[store] || '#666',
          backgroundColor: (storeColors[store] || '#666') + '40',  // Add transparency
          fill: false,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          borderWidth: 2
        });
      }
    });

    priceChart = new Chart(ctx, {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 15,
              font: {
                size: 12,
                weight: '500'
              }
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString()}`;
              },
              title: function(context) {
                const date = new Date(context[0].parsed.x);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
              }
            },
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: { size: 13, weight: 'bold' },
            bodyFont: { size: 12 }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              displayFormats: {
                day: 'MMM d'
              },
              tooltipFormat: 'MMM d, yyyy'
            },
            title: {
              display: true,
              text: 'Date',
              font: { size: 13, weight: '600' }
            },
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: 'Price (₹)',
              font: { size: 13, weight: '600' }
            },
            ticks: {
              callback: function(value) {
                return '₹' + value.toLocaleString();
              },
              font: { size: 11 }
            },
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.05)'
            }
          }
        }
      }
    });
  }

  async function handleUpdateTarget() {
    const currentTarget = itemData.item.target_price;
    const newTarget = prompt('Enter your target price:', currentTarget || '');

    if (newTarget && !isNaN(parseFloat(newTarget))) {
      try {
        const response = await fetch('/api/wishlist/update-target-price', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            wishlist_item_id: ITEM_ID,
            target_price: parseFloat(newTarget)
          })
        });

        const data = await response.json();

        if (data.success) {
          showSuccess('Target price updated!');
          loadItemDetails(); // Reload
        } else {
          showError(data.message);
        }
      } catch (error) {
        showError('Failed to update target price');
      }
    }
  }

  async function handleRemoveItem() {
    if (!confirm('Are you sure you want to remove this product from your wishlist?')) {
      return;
    }

    try {
      const response = await fetch('/api/wishlist/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wishlist_item_id: ITEM_ID
        })
      });

      const data = await response.json();

      if (data.success) {
        showSuccess('Product removed from wishlist');
        setTimeout(() => {
          window.location.href = '/wishlist';
        }, 1000);
      } else {
        showError(data.message);
      }
    } catch (error) {
      showError('Failed to remove product');
    }
  }

  function showError(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #f44336;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 1001;
      font-weight: 500;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      document.body.removeChild(notification);
    }, 4000);
  }

  function showSuccess(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #28a745;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      z-index: 1001;
      font-weight: 500;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      document.body.removeChild(notification);
    }, 3000);
  }
});