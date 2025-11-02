// Results Page JavaScript
document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("searchBtn");
  const searchInput = document.getElementById("searchInput");
  const wishlistLink = document.getElementById("wishlistLink");
  const profileLink = document.getElementById("profileLink");
  
  // Get search query from URL
  const urlParams = new URLSearchParams(window.location.search);
  const query = urlParams.get('q');
  
  // Store query in localStorage for back navigation from product details
  if (query) {
    localStorage.setItem('lastSearchQuery', query);
    localStorage.setItem('lastSearchUrl', window.location.href);
  }
  
  if (query) {
    // Set search input value
    searchInput.value = query;
    // Fetch results
    fetchAndDisplayResults(query);
  } else {
    // No query, show error
    showNoResults();
  }
  
  // Handle search button click
  searchBtn.addEventListener("click", () => {
    const newQuery = searchInput.value.trim();
    if (newQuery) {
      window.location.href = `/results?q=${encodeURIComponent(newQuery)}`;
    }
  });
  
  // Handle Enter key
  searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const newQuery = searchInput.value.trim();
      if (newQuery) {
        window.location.href = `/results?q=${encodeURIComponent(newQuery)}`;
      }
    }
  });
  
  // Handle wishlist icon click with authentication check
  wishlistLink.addEventListener("click", async (e) => {
    e.preventDefault();
    
    try {
      const meRes = await fetch('/auth/me');
      const me = await meRes.json();
      
      if (me.authenticated) {
        window.location.href = '/wishlist';
      } else {
        window.location.href = '/login?next=' + encodeURIComponent('/wishlist');
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      window.location.href = '/login';
    }
  });
  
  // Handle profile icon click
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
  
  // Fetch and display results
  async function fetchAndDisplayResults(query) {
    try {
      const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (data.offers && data.offers.length > 0) {
        displayResults(data.offers, query);
      } else {
        showNoResults(query);
      }
    } catch (error) {
      console.error("Error fetching results:", error);
      showError("Failed to fetch results. Please try again.");
    }
  }
  
  async function displayResults(offers, query) {
    const loadingScreen = document.getElementById("loadingScreen");
    const resultsContainer = document.getElementById("resultsContainer");
    const searchTitle = document.getElementById("searchTitle");
    const resultCount = document.getElementById("resultCount");
    const productsGrid = document.getElementById("productsGrid");
    
    // Hide loading, show results
    loadingScreen.style.display = "none";
    resultsContainer.style.display = "block";
    
    // Set title and count
    searchTitle.textContent = `Search Results for "${query}"`;
    resultCount.textContent = `Found ${offers.length} products from multiple stores`;
    
    // Store original offers for sorting
    window.offers = offers;
    
    // Display products
    // Check wishlist status first, then render
    await checkWishlistStatus(offers);
    renderProducts(offers);
    
    // Setup filter buttons
    setupFilters();
  }
  
  // Store wishlist state for icons
  const wishlistState = new Set();

  // Check wishlist status for all products on page load
  async function checkWishlistStatus(offers) {
    try {
      const meRes = await fetch('/auth/me');
      const me = await meRes.json();
      if (!me.authenticated) {
        return;
      }

      // Check each product
      for (const offer of offers) {
        try {
          const checkRes = await fetch(`/api/wishlist/check/${encodeURIComponent(offer.title)}`);
          const checkData = await checkRes.json();
          if (checkData.success && checkData.in_wishlist) {
            wishlistState.add(offer.title);
          }
        } catch (error) {
          // Silently fail for individual checks
        }
      }
    } catch (error) {
      // Silently fail if not authenticated
    }
  }

  function renderProducts(offers) {
    const productsGrid = document.getElementById("productsGrid");
    
    if (offers.length === 0) {
      productsGrid.innerHTML = '<p>No products found</p>';
      return;
    }
    
    let html = "";
    
    offers.forEach((offer, index) => {
      // Build URL for product details page
      const detailsUrl = `/product-details?key=${encodeURIComponent(offer.offer_key || '')}&title=${encodeURIComponent(offer.title || '')}&store=${encodeURIComponent(offer.store || '')}&price_display=${encodeURIComponent(offer.price_display || '')}&image=${encodeURIComponent(offer.image || '')}&url=${encodeURIComponent(offer.url || '')}`;
      
      const isInWishlist = wishlistState.has(offer.title);
      const heartClass = isInWishlist ? 'fa-solid' : 'fa-regular';
      const heartTitle = isInWishlist ? 'Remove from Wishlist' : 'Add to Wishlist';
      
      // Fix image path - use static images folder
      const imagePath = offer.image ? (offer.image.startsWith('http') ? offer.image : `/images/${offer.image}`) : null;
      
      html += `
        <div class="product-card" data-product-index="${index}">
          <div class="product-image">
            ${imagePath ? 
              `<img src="${imagePath}" alt="${offer.title}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\'no-image\\'>No Image</div>'" />` : 
              '<div class="no-image">No Image</div>'
            }
          </div>
          <div class="product-info">
            <h3 class="product-title">${offer.title}</h3>
            <div class="product-details">
              <span class="store-badge ${offer.store}">${offer.store}</span>
              <span class="price">${offer.price_display}</span>
            </div>
            <div class="product-actions">
              <button class="view-product-btn" onclick="window.location.href='${detailsUrl}'">
                View Details
              </button>
              <button class="wishlist-btn" onclick="toggleWishlist('${offer.title.replace(/'/g, "\\'")}', '${offer.store}', ${index}, '${offer.price_display}')" title="${heartTitle}" data-product-title="${offer.title}">
                <i class="${heartClass} fa-heart"></i>
              </button>
            </div>
            
          </div>
        </div>
      `;
    });
    
    productsGrid.innerHTML = html;
  }

  // Toggle wishlist with icon update
  window.toggleWishlist = async function(productName, store, index, productPrice = null) {
    const isInWishlist = wishlistState.has(productName);
    const btn = document.querySelector(`[data-product-title="${productName.replace(/'/g, "\\'")}"]`);
    const icon = btn ? btn.querySelector('i') : null;
    
    try {
      const meRes = await fetch('/auth/me');
      const me = await meRes.json();
      if (!me.authenticated) {
        const next = encodeURIComponent(window.location.href);
        window.location.href = `/login?next=${next}`;
        return;
      }

      if (isInWishlist) {
        // Remove from wishlist
        const checkRes = await fetch(`/api/wishlist/check/${encodeURIComponent(productName)}`);
        const checkData = await checkRes.json();
        
        if (checkData.success && checkData.in_wishlist && checkData.wishlist_item) {
          const removeRes = await fetch('/api/wishlist/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              wishlist_item_id: checkData.wishlist_item.id
            })
          });
          
          const removeData = await removeRes.json();
          if (removeData.success) {
            wishlistState.delete(productName);
            if (icon) {
              icon.classList.remove('fa-solid');
              icon.classList.add('fa-regular');
              btn.title = 'Add to Wishlist';
            }
            showSuccess('Removed from wishlist!');
          }
        }
      } else {
        // Ask for target price when adding to wishlist
        const targetPriceInput = prompt(
          `Add "${productName}" to wishlist?\n\n` +
          `Optional: Enter your target price (₹) or leave blank:\n` +
          (productPrice ? `Current lowest price: ${productPrice}` : ''),
          ''
        );
        
        let targetPrice = null;
        if (targetPriceInput !== null) { // User didn't cancel
          if (targetPriceInput.trim() !== '') {
            // Remove currency symbols and commas, then parse
            const cleaned = targetPriceInput.trim().replace(/[₹,\s]/g, '');
            const parsed = parseFloat(cleaned);
            if (!isNaN(parsed) && parsed > 0) {
              targetPrice = parsed;
            } else {
              alert('Invalid price. Please enter a valid number or leave blank.');
              return;
            }
          }
          
          // Add to wishlist
          const response = await fetch('/api/wishlist/add', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              product_name: productName,
              product_category: getCategoryFromStore(store),
              target_price: targetPrice
            })
          });

          const data = await response.json();
          if (data.success) {
            wishlistState.add(productName);
            if (icon) {
              icon.classList.remove('fa-regular');
              icon.classList.add('fa-solid');
              btn.title = 'Remove from Wishlist';
            }
            showSuccess(targetPrice ? `Added to wishlist with target price ₹${targetPrice.toLocaleString()}!` : 'Product added to wishlist!');
          } else if (response.status === 401) {
            const next = encodeURIComponent(window.location.href);
            window.location.href = `/login?next=${next}`;
          } else {
            alert(data.message || 'Failed to add product to wishlist');
          }
        }
      }
    } catch (error) {
      console.error('Error toggling wishlist:', error);
      alert('Failed to update wishlist');
    }
  };

  // Alias for backward compatibility (using the improved toggleWishlist function)
  window.addToWishlist = window.toggleWishlist;
  
  function setupFilters() {
    const filterBtns = document.querySelectorAll(".filter-btn");
    
    filterBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        // Update active state
        filterBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        // Sort offers
        const sortType = btn.dataset.sort;
        let sortedOffers = [...window.offers];
        
        if (sortType === "price") {
          sortedOffers.sort((a, b) => a.price - b.price);
        } else if (sortType === "price-desc") {
          sortedOffers.sort((a, b) => b.price - a.price);
        } else if (sortType === "store") {
          sortedOffers.sort((a, b) => a.store.localeCompare(b.store));
        }
        
        renderProducts(sortedOffers);
      });
    });
  }

  
  
  function showNoResults(query = "") {
    const loadingScreen = document.getElementById("loadingScreen");
    const noResults = document.getElementById("noResults");
    const noResultsMsg = document.getElementById("noResultsMsg");
    
    loadingScreen.style.display = "none";
    noResults.style.display = "block";
    
    if (query) {
      noResultsMsg.textContent = `Sorry, we couldn't find any products for "${query}". Try searching with different keywords.`;
    } else {
      noResultsMsg.textContent = "Please enter a search query.";
    }
  }
  
  function showError(message) {
    const loadingScreen = document.getElementById("loadingScreen");
    const noResults = document.getElementById("noResults");
    const noResultsMsg = document.getElementById("noResultsMsg");
    
    loadingScreen.style.display = "none";
    noResults.style.display = "block";
    noResultsMsg.textContent = message;
  }

  function getCategoryFromStore(store) {
    // Simple category mapping based on store
    const categoryMap = {
      'flipkart': 'Electronics',
      'amazon': 'Electronics', 
      'reliance digital': 'Electronics',
      'croma': 'Electronics',
      'girias': 'Electronics'
    };
    return categoryMap[store] || 'General';
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