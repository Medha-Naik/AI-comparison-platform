// Wishlist Page JavaScript
document.addEventListener("DOMContentLoaded", () => {
  const userEmailInput = document.getElementById('userEmail');
  const loadWishlistBtn = document.getElementById('loadWishlistBtn');
  const wishlistItems = document.getElementById('wishlistItems');
  const emptyWishlist = document.getElementById('emptyWishlist');
  const loadingState = document.getElementById('loadingState');
  const refreshPricesBtn = document.getElementById('refreshPricesBtn');
  const addProductBtn = document.getElementById('addProductBtn');
  const startShoppingBtn = document.getElementById('startShoppingBtn');
  
  // Modal elements
  const addProductModal = document.getElementById('addProductModal');
  const priceHistoryModal = document.getElementById('priceHistoryModal');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const closePriceModalBtn = document.getElementById('closePriceModalBtn');
  const addProductForm = document.getElementById('addProductForm');
  const cancelAddBtn = document.getElementById('cancelAddBtn');
  
  let currentUserEmail = null;
  let currentWishlist = [];

  // Initialize
  initializeEventListeners();
  checkStoredEmail();

  function initializeEventListeners() {
    // Load wishlist
    loadWishlistBtn.addEventListener('click', loadWishlist);
    userEmailInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') loadWishlist();
    });

    // Refresh prices
    refreshPricesBtn.addEventListener('click', refreshAllPrices);

    // Add product
    addProductBtn.addEventListener('click', () => {
      if (!currentUserEmail) {
        alert('Please enter your email first');
        return;
      }
      showModal(addProductModal);
    });

    // Start shopping
    startShoppingBtn.addEventListener('click', () => {
      window.location.href = '/';
    });

    // Modal events
    closeModalBtn.addEventListener('click', () => hideModal(addProductModal));
    closePriceModalBtn.addEventListener('click', () => hideModal(priceHistoryModal));
    cancelAddBtn.addEventListener('click', () => hideModal(addProductModal));
    addProductForm.addEventListener('submit', handleAddProduct);

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

    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
      if (e.target === addProductModal) hideModal(addProductModal);
      if (e.target === priceHistoryModal) hideModal(priceHistoryModal);
    });
  }

  function checkStoredEmail() {
    const storedEmail = localStorage.getItem('userEmail');
    if (storedEmail) {
      userEmailInput.value = storedEmail;
      currentUserEmail = storedEmail;
      loadWishlist();
    }
  }

  async function loadWishlist() {
    const email = userEmailInput.value.trim();
    if (!email) {
      alert('Please enter your email address');
      return;
    }

    currentUserEmail = email;
    localStorage.setItem('userEmail', email);
    
    showLoading();
    
    try {
      const response = await fetch(`/api/wishlist/${encodeURIComponent(email)}`);
      const data = await response.json();
      
      if (data.success) {
        currentWishlist = data.wishlist;
        displayWishlist(data.wishlist);
      } else {
        showError('Failed to load wishlist');
      }
    } catch (error) {
      console.error('Error loading wishlist:', error);
      showError('Failed to load wishlist');
    }
  }

  function displayWishlist(wishlist) {
    hideLoading();
    
    if (wishlist.length === 0) {
      showEmptyState();
      return;
    }

    wishlistItems.style.display = 'block';
    emptyWishlist.style.display = 'none';
    
    let html = '';
    
    wishlist.forEach(item => {
      const lowestPrice = item.lowest_price;
      const currentPrices = item.current_prices;
      
      html += `
        <div class="wishlist-item" data-item-id="${item.id}">
          <div class="wishlist-item-header">
            <div class="wishlist-item-info">
              <h3>${item.product_name}</h3>
              ${item.product_category ? `<div class="category">${item.product_category}</div>` : ''}
            </div>
            <div class="wishlist-item-actions">
              <button class="btn btn-secondary" onclick="showPriceHistory(${item.id}, '${item.product_name}')">
                <i class="fa-solid fa-chart-line"></i> Price History
              </button>
              <button class="btn btn-danger" onclick="removeFromWishlist(${item.id})">
                <i class="fa-solid fa-trash"></i> Remove
              </button>
            </div>
          </div>
          
          ${item.target_price ? `
            <div class="target-price">
              <div class="target-price-header">
                <h4><i class="fa-solid fa-bullseye"></i> Target Price</h4>
                <span class="target-price-value">₹${item.target_price.toLocaleString()}</span>
              </div>
              <div class="target-price-actions">
                <button class="btn btn-secondary" onclick="updateTargetPrice(${item.id})">
                  <i class="fa-solid fa-edit"></i> Update
                </button>
              </div>
            </div>
          ` : `
            <div class="target-price">
              <div class="target-price-header">
                <h4><i class="fa-solid fa-bullseye"></i> Set Target Price</h4>
              </div>
              <div class="target-price-actions">
                <button class="btn btn-primary" onclick="setTargetPrice(${item.id})">
                  <i class="fa-solid fa-plus"></i> Set Target Price
                </button>
              </div>
            </div>
          `}
          
          <div class="price-display">
            ${Object.entries(currentPrices).map(([store, priceData]) => `
              <div class="store-price ${priceData.price === lowestPrice ? 'lowest' : ''}">
                <h4>${store.charAt(0).toUpperCase() + store.slice(1)}</h4>
                <div class="price ${priceData.price === lowestPrice ? 'lowest' : ''}">${priceData.price_display}</div>
                <div class="date">Updated: ${new Date(priceData.recorded_at).toLocaleDateString()}</div>
                ${priceData.url ? `<a href="${priceData.url}" target="_blank" class="btn btn-primary" style="margin-top: 10px; font-size: 12px; padding: 5px 10px;">View Product</a>` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      `;
    });
    
    wishlistItems.innerHTML = html;
  }

  function showEmptyState() {
    wishlistItems.style.display = 'none';
    emptyWishlist.style.display = 'block';
  }

  function showLoading() {
    loadingState.style.display = 'block';
    wishlistItems.style.display = 'none';
    emptyWishlist.style.display = 'none';
  }

  function hideLoading() {
    loadingState.style.display = 'none';
  }

  function showError(message) {
    hideLoading();
    alert(message);
  }

  async function handleAddProduct(e) {
    e.preventDefault();
    
    const formData = new FormData(addProductForm);
    const productName = document.getElementById('productName').value.trim();
    const productCategory = document.getElementById('productCategory').value.trim();
    const targetPrice = document.getElementById('targetPrice').value;
    
    if (!productName) {
      alert('Product name is required');
      return;
    }
    
    try {
      const response = await fetch('/api/wishlist/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: currentUserEmail,
          product_name: productName,
          product_category: productCategory || null,
          target_price: targetPrice ? parseFloat(targetPrice) : null
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        hideModal(addProductModal);
        addProductForm.reset();
        loadWishlist(); // Reload wishlist
        showSuccess('Product added to wishlist!');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error adding product:', error);
      alert('Failed to add product to wishlist');
    }
  }

  async function removeFromWishlist(itemId) {
    if (!confirm('Are you sure you want to remove this product from your wishlist?')) {
      return;
    }
    
    try {
      const response = await fetch('/api/wishlist/remove', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: currentUserEmail,
          wishlist_item_id: itemId
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        loadWishlist(); // Reload wishlist
        showSuccess('Product removed from wishlist');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error removing product:', error);
      alert('Failed to remove product from wishlist');
    }
  }

  async function refreshAllPrices() {
    if (!currentUserEmail) {
      alert('Please enter your email first');
      return;
    }
    
    refreshPricesBtn.disabled = true;
    refreshPricesBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Refreshing...';
    
    try {
      const response = await fetch('/api/wishlist/update-prices', {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.success) {
        loadWishlist(); // Reload wishlist
        showSuccess('Prices updated successfully!');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error refreshing prices:', error);
      alert('Failed to refresh prices');
    } finally {
      refreshPricesBtn.disabled = false;
      refreshPricesBtn.innerHTML = '<i class="fa-solid fa-sync-alt"></i> Refresh Prices';
    }
  }

  function setTargetPrice(itemId) {
    const targetPrice = prompt('Enter your target price:');
    if (targetPrice && !isNaN(parseFloat(targetPrice))) {
      updateTargetPrice(itemId, parseFloat(targetPrice));
    }
  }

  function updateTargetPrice(itemId) {
    const currentItem = currentWishlist.find(item => item.id === itemId);
    const currentTarget = currentItem ? currentItem.target_price : null;
    const targetPrice = prompt(`Enter your target price:`, currentTarget || '');
    
    if (targetPrice && !isNaN(parseFloat(targetPrice))) {
      updateTargetPriceAPI(itemId, parseFloat(targetPrice));
    }
  }

  async function updateTargetPriceAPI(itemId, targetPrice) {
    try {
      const response = await fetch('/api/wishlist/update-target-price', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_email: currentUserEmail,
          wishlist_item_id: itemId,
          target_price: targetPrice
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        loadWishlist(); // Reload wishlist
        showSuccess('Target price updated!');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error updating target price:', error);
      alert('Failed to update target price');
    }
  }

  async function showPriceHistory(itemId, productName) {
    // This would typically fetch price history from the API
    // For now, we'll show a placeholder
    const modal = document.getElementById('priceHistoryModal');
    const title = document.getElementById('priceHistoryTitle');
    title.textContent = `Price History - ${productName}`;
    
    // Create a simple chart placeholder
    const chartContainer = document.getElementById('priceChart');
    chartContainer.innerHTML = '<p style="text-align: center; padding: 50px; color: #666;">Price history chart would be displayed here</p>';
    
    showModal(modal);
  }

  function showModal(modal) {
    modal.style.display = 'block';
  }

  function hideModal(modal) {
    modal.style.display = 'none';
  }

  function showSuccess(message) {
    // Simple success notification
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

// Global functions for onclick handlers
function removeFromWishlist(itemId) {
  // This will be called from the HTML
  if (window.removeFromWishlist) {
    window.removeFromWishlist(itemId);
  }
}

function showPriceHistory(itemId, productName) {
  // This will be called from the HTML
  if (window.showPriceHistory) {
    window.showPriceHistory(itemId, productName);
  }
}

function updateTargetPrice(itemId) {
  // This will be called from the HTML
  if (window.updateTargetPrice) {
    window.updateTargetPrice(itemId);
  }
}

function setTargetPrice(itemId) {
  // This will be called from the HTML
  if (window.setTargetPrice) {
    window.setTargetPrice(itemId);
  }
}






