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
    let html = '';

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
      const isLowest = priceData.price === lowestPrice;

      html += `
        <div class="store-price ${isLowest ? 'lowest' : ''}">
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

    currentPrices.innerHTML = html;
  }

  function displayPriceChart(priceHistory) {
    const ctx = document.getElementById('priceHistoryChart').getContext('2d');

    // Store colors
    const storeColors = {
      'flipkart': '#2874f0',
      'amazon': '#ff9900',
      'croma': '#00a699',
      'reliance': '#e42529'
    };

    // Prepare datasets
    const datasets = [];

    Object.keys(priceHistory).forEach(store => {
      const history = priceHistory[store];
      
      datasets.push({
        label: store.charAt(0).toUpperCase() + store.slice(1),
        data: history.map(item => ({
          x: item.date,
          y: item.price
        })),
        borderColor: storeColors[store] || '#666',
        backgroundColor: storeColors[store] || '#666',
        tension: 0.1,
        pointRadius: 4,
        pointHoverRadius: 6
      });
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
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString()}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              displayFormats: {
                day: 'MMM d'
              }
            },
            title: {
              display: true,
              text: 'Date'
            }
          },
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: 'Price (₹)'
            },
            ticks: {
              callback: function(value) {
                return '₹' + value.toLocaleString();
              }
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