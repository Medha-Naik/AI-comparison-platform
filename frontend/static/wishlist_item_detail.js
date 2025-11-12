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

  // Extract ITEM_ID from URL
  const pathParts = window.location.pathname.split('/');
  const ITEM_ID = parseInt(pathParts[pathParts.length - 1], 10);
  
  if (!ITEM_ID || isNaN(ITEM_ID)) {
    console.error('Invalid wishlist item ID in URL');
    showError('Invalid wishlist item');
    setTimeout(() => (window.location.href = '/wishlist'), 2000);
    return;
  }

  // Load item details on page load
  loadItemDetails();

  // Event listeners
  updateTargetBtn.addEventListener('click', handleUpdateTarget);
  removeItemBtn.addEventListener('click', handleRemoveItem);

  // Search functionality
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');

  searchBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    if (query) window.location.href = `/results?q=${encodeURIComponent(query)}`;
  });

  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      const query = searchInput.value.trim();
      if (query) window.location.href = `/results?q=${encodeURIComponent(query)}`;
    }
  });

  async function loadItemDetails() {
    try {
      const response = await fetch(`/api/wishlist/details/${ITEM_ID}`);
      if (!response.ok) {
        if (response.status === 404) {
          showError('Item not found');
        } else {
          showError(`Server responded with ${response.status}`);
        }
        setTimeout(() => (window.location.href = '/wishlist'), 2000);
        return;
      }
      
      const data = await response.json();

      if (data.success && data.item) {
        itemData = data;
        displayItemDetails(data);
      } else {
        showError(data.message || 'Item not found');
        setTimeout(() => (window.location.href = '/wishlist'), 2000);
      }
    } catch (error) {
      console.error('Error loading item details:', error);
      showError('Failed to load item details. Please try again.');
      setTimeout(() => (window.location.href = '/wishlist'), 2000);
    }
  }

  function displayItemDetails(data) {
    loadingState.style.display = 'none';
    productHeader.style.display = 'block';

    const item = data.item;
    productName.textContent = item.product_name;
    if (item.product_category) {
      productCategory.textContent = item.product_category;
    } else {
      productCategory.style.display = 'none';
    }

    // Target price display
    if (item.target_price) {
      const targetMet = data.lowest_price && data.lowest_price <= item.target_price;
      targetPriceSection.innerHTML = `
        <div class="target-price">
          <div class="target-price-header">
            <h4><i class="fa-solid fa-bullseye"></i> Target Price</h4>
            <span class="target-price-value">₹${item.target_price.toLocaleString('en-IN')}</span>
          </div>
          ${targetMet ? `
            <div style="margin-top: 10px; padding: 15px; background: #d4edda; border-radius: 8px; color: #155724; border: 1px solid #c3e6cb;">
              <i class="fa-solid fa-check-circle"></i> <strong>Target price reached!</strong> Lowest current price: ₹${data.lowest_price.toLocaleString('en-IN')}
            </div>` : ''}
        </div>`;
    } else {
      targetPriceSection.innerHTML = `
        <div class="target-price">
          <div class="target-price-header">
            <h4><i class="fa-solid fa-bullseye"></i> No Target Price Set</h4>
            <p style="margin: 10px 0 0 0; color: #fff; font-size: 14px;">Set a target price to get notified when prices drop!</p>
          </div>
        </div>`;
    }

    displayCurrentPrices(data.current_prices, data.lowest_price);
    displayPriceChart(data.price_history);
  }

  function displayCurrentPrices(prices, lowestPrice) {
    if (!prices || Object.keys(prices).length === 0) {
      currentPrices.innerHTML = `
        <div style="text-align:center; padding:40px; color:#666;">
          <i class="fa-solid fa-info-circle" style="font-size:48px; margin-bottom:16px; opacity:0.5;"></i>
          <p style="margin: 0; font-size: 16px;">No price data available yet.</p>
          <p style="margin: 10px 0 0 0; font-size: 14px;">Price data will be updated automatically.</p>
        </div>`;
      return;
    }

    const storeOrder = ['flipkart', 'amazon', 'croma', 'reliance', 'reliance digital'];
    const sortedStores = Object.keys(prices).sort((a, b) => {
      const indexA = storeOrder.indexOf(a.toLowerCase());
      const indexB = storeOrder.indexOf(b.toLowerCase());
      if (indexA === -1 && indexB === -1) return a.localeCompare(b);
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    });

    let html = '<div class="price-grid">';
    sortedStores.forEach(store => {
      const p = prices[store];
      const isLowest = lowestPrice && Math.abs(p.price - lowestPrice) < 0.01;
      const storeName = store.charAt(0).toUpperCase() + store.slice(1);

      html += `
        <div class="store-price ${isLowest ? 'lowest' : ''}">
          <div class="store-header">
            <h4>${storeName}</h4>
            ${isLowest ? '<span class="lowest-badge"><i class="fa-solid fa-star"></i> Lowest</span>' : ''}
          </div>
          <div class="price">₹${p.price.toLocaleString('en-IN')}</div>
          ${p.title ? `<div class="product-title">${p.title}</div>` : ''}
          ${p.url ? `<a href="${p.url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="margin-top: 10px;">
            View on ${storeName} <i class="fa-solid fa-external-link-alt"></i>
          </a>` : ''}
        </div>`;
    });
    html += '</div>';
    currentPrices.innerHTML = html;
  }

  function displayPriceChart(priceHistory) {
    const chartContainer = document.getElementById('priceHistoryChart');
    const ctx = chartContainer.getContext('2d');
    
    if (priceChart) {
      priceChart.destroy();
      priceChart = null;
    }

    if (!priceHistory || Object.keys(priceHistory).length === 0) {
      chartContainer.parentElement.innerHTML = `
        <div style="text-align:center; padding:40px; color:#666;">
          <i class="fa-solid fa-chart-line" style="font-size:48px; margin-bottom:16px; opacity:0.5;"></i>
          <p style="margin: 0; font-size: 16px;">No price history available yet.</p>
          <p style="margin: 10px 0 0 0; font-size: 14px;">Price history will be tracked over time.</p>
        </div>`;
      return;
    }

    const storeColors = {
      'flipkart': '#2874f0',
      'amazon': '#ff9900',
      'croma': '#00a699',
      'reliance': '#e42529',
      'reliance digital': '#e42529'
    };

    const datasets = [];

    Object.keys(priceHistory).forEach(store => {
      const history = priceHistory[store];
      if (history && history.length > 0) {
        const storeLower = store.toLowerCase();
        datasets.push({
          label: store.charAt(0).toUpperCase() + store.slice(1),
          data: history.map(h => ({
            x: new Date(h.date),
            y: h.price
          })),
          borderColor: storeColors[storeLower] || '#666',
          backgroundColor: (storeColors[storeLower] || '#666') + '20',
          fill: false,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5
        });
      }
    });

    if (datasets.length === 0) {
      chartContainer.parentElement.innerHTML = `
        <div style="text-align:center; padding:40px; color:#666;">
          <i class="fa-solid fa-chart-line" style="font-size:48px; margin-bottom:16px; opacity:0.5;"></i>
          <p>No valid price history data available.</p>
        </div>`;
      return;
    }

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
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 15,
              font: {
                size: 12,
                family: 'Poppins, sans-serif'
              }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString('en-IN')}`;
              },
              title: (context) => {
                const date = new Date(context[0].parsed.x);
                return date.toLocaleDateString('en-IN', { 
                  year: 'numeric', 
                  month: 'short', 
                  day: 'numeric' 
                });
              }
            },
            backgroundColor: 'rgba(0,0,0,0.8)',
            padding: 12,
            titleFont: {
              size: 14,
              family: 'Poppins, sans-serif'
            },
            bodyFont: {
              size: 13,
              family: 'Poppins, sans-serif'
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
              text: 'Date',
              font: {
                size: 12,
                family: 'Poppins, sans-serif'
              }
            },
            grid: {
              color: 'rgba(0,0,0,0.05)'
            }
          },
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: 'Price (₹)',
              font: {
                size: 12,
                family: 'Poppins, sans-serif'
              }
            },
            ticks: {
              callback: (value) => '₹' + value.toLocaleString('en-IN')
            },
            grid: {
              color: 'rgba(0,0,0,0.05)'
            }
          }
        }
      }
    });
  }

  async function handleUpdateTarget() {
    const currentTarget = itemData?.item?.target_price || '';
    const newTarget = prompt('Enter your target price (in ₹):', currentTarget);
    
    if (newTarget === null) return; // User cancelled
    
    const parsedTarget = parseFloat(newTarget);
    if (isNaN(parsedTarget) || parsedTarget <= 0) {
      showError('Please enter a valid price');
      return;
    }

    try {
      const response = await fetch('/api/wishlist/update-target-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wishlist_item_id: ITEM_ID,
          target_price: parsedTarget
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        showSuccess('Target price updated successfully!');
        loadItemDetails();
      } else {
        showError(data.message || 'Failed to update target price');
      }
    } catch (error) {
      console.error('Error updating target price:', error);
      showError('Failed to update target price. Please try again.');
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
        body: JSON.stringify({ wishlist_item_id: ITEM_ID })
      });
      
      const data = await response.json();
      
      if (data.success) {
        showSuccess('Product removed from wishlist');
        setTimeout(() => (window.location.href = '/wishlist'), 1000);
      } else {
        showError(data.message || 'Failed to remove product');
      }
    } catch (error) {
      console.error('Error removing product:', error);
      showError('Failed to remove product. Please try again.');
    }
  }

  function showError(msg) {
    showNotification(msg, 'error');
  }

  function showSuccess(msg) {
    showNotification(msg, 'success');
  }

  function showNotification(msg, type) {
    const n = document.createElement('div');
    const bgColor = type === 'error' ? '#f44336' : '#28a745';
    const icon = type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle';
    
    n.style.cssText = `
      position: fixed; top: 20px; right: 20px;
      background: ${bgColor}; color: white; padding: 15px 20px;
      border-radius: 8px; z-index: 10000; font-weight: 500;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      display: flex; align-items: center; gap: 10px;
      max-width: 400px; animation: slideIn 0.3s ease-out;
    `;
    
    n.innerHTML = `<i class="fa-solid ${icon}"></i><span>${msg}</span>`;
    document.body.appendChild(n);
    
    setTimeout(() => {
      n.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => n.remove(), 300);
    }, type === 'error' ? 4000 : 3000);
  }
});

// Add animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);