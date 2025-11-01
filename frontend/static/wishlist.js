// Wishlist Page JavaScript
document.addEventListener("DOMContentLoaded", () => {
  const userEmailInput = document.getElementById('userEmail');
  const loadWishlistBtn = document.getElementById('loadWishlistBtn');
  const wishlistItems = document.getElementById('wishlistItems');
  const emptyWishlist = document.getElementById('emptyWishlist');
  const loadingState = document.getElementById('loadingState');
  const refreshPricesBtn = document.getElementById('refreshPricesBtn');
  const startShoppingBtn = document.getElementById('startShoppingBtn');
  const profileLink = document.getElementById('profileLink');
  
  let currentUserEmail = null;
  let currentWishlist = [];

  // Initialize
  checkIfLoggedIn();
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

    // Start shopping
    startShoppingBtn.addEventListener('click', () => {
      window.location.href = '/';
    });

    // Profile icon click
    if (profileLink) {
      profileLink.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
          const meRes = await fetch('/auth/me');
          const me = await meRes.json();
          
          if (me.authenticated) {
            window.location.href = '/profile';
          } else {
            window.location.href = '/login?next=' + encodeURIComponent('/profile');
          }
        } catch (error) {
          window.location.href = '/login';
        }
      });
    }

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
  }

  function checkStoredEmail() {
    const storedEmail = localStorage.getItem('userEmail');
    if (storedEmail && !currentUserEmail) {
      userEmailInput.value = storedEmail;
      currentUserEmail = storedEmail;
      loadWishlist();
    }
  }

  async function checkIfLoggedIn() {
    try {
      const response = await fetch('/auth/me');
      if (response.ok) {
        const data = await response.json();
        if (data.authenticated && data.user) {
          currentUserEmail = data.user.email;
          localStorage.setItem('userEmail', currentUserEmail);
          
          const emailSection = document.getElementById('emailInputSection');
          if (emailSection) {
            emailSection.style.display = 'none';
          }
          
          const loggedInSection = document.createElement('div');
          loggedInSection.style.cssText = 'margin-bottom: 20px; padding: 15px; background: #e8f5e9; border-radius: 8px; border: 1px solid #4caf50;';
          loggedInSection.innerHTML = `
            <p style="margin: 0; color: #2e7d32; font-size: 14px;">
              <i class="fa-solid fa-user-check"></i> Logged in as: <strong>${data.user.email}</strong>
            </p>
          `;
          
          const container = document.querySelector('.wishlist-container');
          const header = container.querySelector('.wishlist-header');
          if (header) {
            header.after(loggedInSection);
          }
          
          loadWishlistForLoggedInUser();
        }
      }
    } catch (error) {
      console.log('User not logged in, showing email input');
    }
  }

  async function loadWishlistForLoggedInUser() {
    showLoading();
    
    try {
      const response = await fetch('/api/wishlist/me');
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

  async function loadWishlist() {
    const email = userEmailInput.value.trim();
    if (!email) {
      alert('Please enter your email address');
      return;
    }

    currentUserEmail = email;
    localStorage.setItem('userEmail', email);
    
    loadWishlistForLoggedInUser();
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
      
      html += `
        <div class="wishlist-item" data-item-id="${item.id}" style="cursor: pointer;" onclick="window.location.href='/wishlist/details/${item.id}'">
          <div class="wishlist-item-header">
            <div class="wishlist-item-info">
              <h3>${item.product_name}</h3>
              ${item.product_category ? `<div class="category">${item.product_category}</div>` : ''}
              ${lowestPrice ? `<div class="price" style="margin-top: 10px; font-size: 24px; color: #2e7d32;">₹${lowestPrice.toLocaleString()}</div>` : ''}
              <div style="color: #666; font-size: 14px; margin-top: 5px;">
                <i class="fa-solid fa-chart-line"></i> Click to view price history
              </div>
            </div>
            <div class="wishlist-item-actions" onclick="event.stopPropagation()">
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
              ${lowestPrice && lowestPrice <= item.target_price ? `
                <div style="margin-top: 10px; padding: 10px; background: #d4edda; border-radius: 8px; color: #155724;">
                  <i class="fa-solid fa-check-circle"></i> Target price reached!
                </div>
              ` : ''}
            </div>
          ` : ''}
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

  async function removeFromWishlistInner(itemId) {
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
        loadWishlistForLoggedInUser();
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
        loadWishlistForLoggedInUser();
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

  window.removeFromWishlistHandler = removeFromWishlistInner;
});

function removeFromWishlist(itemId) {
  if (window.removeFromWishlistHandler) {
    window.removeFromWishlistHandler(itemId);
  }
}