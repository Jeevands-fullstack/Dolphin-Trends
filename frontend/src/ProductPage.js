import React, { useState } from 'react';

function ProductPage({ product, onClose, onBook, allProducts }) {
  const [selectedSize, setSelectedSize] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [showBuyForm, setShowBuyForm] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const shopAddress = "Dolphin Trends, Rajagopala Nagar, Peenya 2nd Stage, Bangalore - 560058";
  const shopLocation = "https://maps.app.goo.gl/zQeV2fcEv2fY625Z7";

  const currentId = product.product_id || product.id;

  const cleanPrice = (priceStr) => {
    if (!priceStr) return 0;
    return parseInt(priceStr.replace(/[^\d]/g, '')) || 0;
  };

  const discount = product.original_price
    ? Math.round((1 - cleanPrice(product.price) / cleanPrice(product.original_price)) * 100)
    : 0;

  const similarProducts = allProducts
    ? allProducts.filter(p => p.category === product.category && (p.product_id || p.id) !== currentId).slice(0, 8)
    : [];

  const handleBuyNow = async () => {
    if (!selectedSize) { alert('⚠️ Please select a size!'); return; }
    if (!customerName || !customerPhone) { alert('⚠️ Name and Phone required!'); return; }

    setBookingLoading(true);

    const bookingPayload = {
      customer_name: customerName,
      customer_phone: customerPhone,
      product_name: `${product.name} (Size: ${selectedSize})`,
      image_url: product.image,
      size: selectedSize,
      price: product.price
    };

    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingPayload)
      });

      if (response.ok) {
        setShowBuyForm(false);
        setCustomerName('');
        setCustomerPhone('');
        setSelectedSize('');
        alert("🎉 Order Request Sent Successfully!\nCheck your WhatsApp for confirmation details shortly. 😊");
      } else {
        alert("❌ Failed to register booking. Try again.");
      }
    } catch (err) {
      console.error("Booking error:", err);
      alert("❌ Server Error while booking.");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <>
      <style>{animations}</style>
      
      <div 
        style={styles.overlay} 
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div style={styles.modal}>
          
          {/* Close Button */}
          <button 
            style={styles.closeBtn}
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>

          {/* Top Section: Image + Details */}
          <div style={styles.topSection}>
          <div style={styles.topSection} className="pp-top-section">
          <div style={styles.imageContainer} className="pp-image-container">
            
            {/* Left - Image */}
            <div style={styles.imageContainer}>
              <img 
                src={product.image} 
                alt={product.name} 
                style={styles.productImage}
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzFhNmNmZiIvPjwvc3ZnPg==';
                }}
              />
              
              {product.available === false && (
                <div style={styles.outOfStockOverlay}>
                  <span style={styles.outOfStockBadge}>🛑 Out of Stock</span>
                </div>
              )}
            </div>

            {/* Right - Details */}
            <div style={styles.details}>
              
              {/* Category Badge */}
              {product.category && (
                <div style={styles.categoryBadge}>
                  {product.category}
                </div>
              )}

              {/* Product Name */}
              <h1 style={styles.productName}>{product.name}</h1>

              {/* Price */}
              <div style={styles.priceSection}>
                <span style={styles.priceMain}>{product.price}</span>
                {product.original_price && discount > 0 && (
                  <>
                    <span style={styles.priceOriginal}>{product.original_price}</span>
                    <span style={styles.discountBadge}>{discount}% OFF</span>
                  </>
                )}
              </div>

              {/* Description */}
              {product.description && (
                <div style={styles.descriptionBox}>
                  {product.description}
                </div>
              )}

              {/* Size Selection */}
              <div style={styles.section}>
                <label style={styles.label}>
                  <span style={styles.labelIcon}>📏</span> Select Size
                </label>
                <div style={styles.sizeGrid}>
                  {sizes.map(size => (
                    <button
                      key={size}
                      type="button"
                      style={selectedSize === size ? styles.sizeBtnActive : styles.sizeBtn}
                      onClick={() => setSelectedSize(size)}
                      disabled={product.available === false}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>

              {/* Buy Now / Out of Stock */}
              {product.available !== false ? (
                !showBuyForm ? (
                  <button 
                    style={styles.buyNowBtn}
                    onClick={() => setShowBuyForm(true)}
                  >
                    🛍️ Buy Now
                  </button>
                ) : (
                  <div style={styles.buyFormContainer}>
                    
                    <div style={styles.formGroup}>
                      <label style={styles.label}>
                        <span style={styles.labelIcon}>👤</span> Your Name
                      </label>
                      <input
                        type="text"
                        placeholder="Enter your full name"
                        value={customerName}
                        onChange={e => setCustomerName(e.target.value)}
                        style={styles.input}
                        maxLength={50}
                      />
                    </div>

                    <div style={styles.formGroup}>
                      <label style={styles.label}>
                        <span style={styles.labelIcon}>📱</span> WhatsApp Number
                      </label>
                      <div style={styles.phoneRow}>
                        <span style={styles.phonePrefix}>+91</span>
                        <input
                          type="tel"
                          placeholder="10-digit number"
                          value={customerPhone}
                          maxLength={10}
                          onChange={e => {
                            const value = e.target.value.replace(/\D/g, '');
                            setCustomerPhone(value);
                          }}
                          style={styles.phoneInput}
                        />
                      </div>
                    </div>

                    <div style={styles.buyActionsRow}>
                      <button 
                        style={{
                          ...styles.confirmBtn,
                          ...(bookingLoading ? styles.btnLoading : {})
                        }}
                        onClick={handleBuyNow}
                        disabled={bookingLoading}
                      >
                        {bookingLoading ? (
                          <span style={styles.loadingContent}>
                            <span style={styles.spinner}></span>
                            Booking...
                          </span>
                        ) : '✅ Confirm'}
                      </button>
                      <button 
                        style={styles.cancelBtn}
                        onClick={() => {
                          setShowBuyForm(false);
                          setCustomerName('');
                          setCustomerPhone('');
                          setSelectedSize('');
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )
              ) : (
                <div style={styles.outOfStockBox}>
                  🛑 This Product is Currently Out of Stock
                </div>
              )}

              {/* Shop Info */}
              <div style={styles.shopInfo}>
                <p style={styles.shopAddress}>📍 {shopAddress}</p>
                <a 
                  href={shopLocation} 
                  target="_blank" 
                  rel="noreferrer"
                  style={styles.mapLink}
                >
                  🗺️ View on Google Maps
                </a>
              </div>
            </div>
          </div>

          {/* Similar Products */}
          {similarProducts.length > 0 && (
            <div style={styles.similarSection}>
              <h3 style={styles.similarTitle}>👗 Similar Products</h3>
              <div style={styles.similarGrid}>
                {similarProducts.map(p => {
                  const simId = p.product_id || p.id;
                  return (
                    <div 
                      key={simId}
                      onClick={() => onBook(p)}
                      style={styles.similarCard}
                    >
                      <img 
                        src={p.image} 
                        alt={p.name} 
                        style={styles.similarImage}
                      />
                      
                      {p.available === false && (
                        <span style={styles.similarOutBadge}>OUT OF STOCK</span>
                      )}
                      
                      <p style={styles.similarName}>{p.name}</p>
                      <p style={styles.similarPrice}>{p.price}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
}

// ✅ Beautiful Animations
const animations = `
  @keyframes slideUpFade {
    from { opacity: 0; transform: translateY(50px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes overlayFade {
    from { opacity: 0; backdrop-filter: blur(0px); }
    to { opacity: 1; backdrop-filter: blur(8px); }
  }
  @keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); opacity: 1; }
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes glowRed {
    0%, 100% { box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4); }
    50% { box-shadow: 0 6px 30px rgba(239, 68, 68, 0.7); }
  }
  @keyframes imageZoom {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
  @keyframes slideUpFade {
    from { opacity: 0; transform: translateY(50px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes overlayFade {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  @keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); opacity: 1; }
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes glowRed {
    0%, 100% { box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4); }
    50% { box-shadow: 0 6px 30px rgba(239, 68, 68, 0.7); }
  }
  @keyframes imageZoom {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
  
  @media (max-width: 768px) {
    .pp-top-section {
      flex-direction: column !important;
    }
    .pp-image-container {
      width: 100% !important;
      min-width: unset !important;
      height: 300px !important;
    }
  }
`;

// ✅ Blue Theme Styles (No reviews, no advance)
const styles = {
  // Overlay
  overlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(11, 19, 41, 0.85)',
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
    zIndex: 99999,
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'center',
    padding: '15px',
    boxSizing: 'border-box',
    overflowY: 'auto',
    animation: 'overlayFade 0.3s ease-out'
  },
  
  // Modal
  modal: {
    background: 'linear-gradient(135deg, #0f1a35 0%, #0a1428 100%)',
    borderRadius: '20px',
    width: '100%',
    maxWidth: '900px',
    maxHeight: '95vh',
    overflowY: 'auto',
    padding: '25px',
    position: 'relative',
    zIndex: 100000,
    boxShadow: '0 25px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(26, 108, 255, 0.2)',
    boxSizing: 'border-box',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    color: '#ffffff',
    animation: 'slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
    border: '1px solid rgba(26, 108, 255, 0.3)'
  },
  
  // Close
  closeBtn: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    cursor: 'pointer',
    fontSize: '1rem',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    backdropFilter: 'blur(10px)'
  },
  
  // Top Section (Image + Details side by side)
  topSection: {
    display: 'flex',
    gap: '25px',
    marginBottom: '25px',
    flexDirection: 'row'
  },
  
  // Image Container
  imageContainer: {
    width: '45%',
    minWidth: '280px',
    height: '450px',
    borderRadius: '16px',
    overflow: 'hidden',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(26, 108, 255, 0.2)',
    position: 'relative',
    flexShrink: 0,
    animation: 'imageZoom 0.5s ease-out'
  },
  
  productImage: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block'
  },
  
  outOfStockOverlay: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 5
  },
  
  outOfStockBadge: {
    background: '#ef4444',
    color: '#fff',
    padding: '12px 24px',
    borderRadius: '8px',
    fontWeight: 'bold',
    fontSize: '16px',
    textTransform: 'uppercase',
    boxShadow: '0 4px 20px rgba(239,68,68,0.7)',
    letterSpacing: '1.5px',
    border: '1px solid rgba(255,255,255,0.3)',
    whiteSpace: 'nowrap'
  },
  
  // Details (Right side)
  details: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  
  // Category Badge
  categoryBadge: {
    display: 'inline-block',
    background: 'rgba(26, 108, 255, 0.15)',
    color: '#4d9fff',
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '0.75rem',
    fontWeight: '600',
    border: '1px solid rgba(26, 108, 255, 0.3)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    alignSelf: 'flex-start'
  },
  
  // Product Name
  productName: {
    color: '#ffffff',
    fontSize: '1.6rem',
    fontWeight: '700',
    margin: '0',
    lineHeight: 1.3
  },
  
  // Price Section
  priceSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    flexWrap: 'wrap'
  },
  
  priceMain: {
    color: '#4d9fff',
    fontSize: '1.7rem',
    fontWeight: '700'
  },
  
  priceOriginal: {
    color: '#7a85a0',
    fontSize: '1rem',
    textDecoration: 'line-through'
  },
  
  discountBadge: {
    background: 'rgba(239, 68, 68, 0.2)',
    color: '#ef4444',
    padding: '3px 10px',
    borderRadius: '6px',
    fontSize: '0.8rem',
    fontWeight: '700',
    border: '1px solid rgba(239, 68, 68, 0.3)'
  },
  
  // Description
  descriptionBox: {
    background: 'rgba(26, 108, 255, 0.08)',
    border: '1px solid rgba(26, 108, 255, 0.2)',
    borderRadius: '10px',
    padding: '12px 15px',
    color: '#c8d6e5',
    fontSize: '0.9rem',
    lineHeight: 1.5,
    fontStyle: 'italic'
  },
  
  // ✅ advanceInfo REMOVED
  
  // Section
  section: {
    // No margin - use gap in parent
  },
  
  label: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    marginBottom: '8px',
    color: '#a0b3d6',
    fontWeight: '600',
    fontSize: '0.85rem',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  
  labelIcon: {
    fontSize: '1rem'
  },
  
  // Size Grid
  sizeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '8px'
  },
  
  sizeBtn: {
    padding: '12px 4px',
    background: 'rgba(26, 108, 255, 0.1)',
    border: '2px solid rgba(26, 108, 255, 0.3)',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: '700',
    fontSize: '0.95rem',
    color: '#a0b3d6',
    textAlign: 'center',
    transition: 'all 0.2s',
    fontFamily: 'inherit'
  },
  
  sizeBtnActive: {
    padding: '12px 4px',
    background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
    border: '2px solid #4d9fff',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: '700',
    fontSize: '0.95rem',
    color: '#ffffff',
    textAlign: 'center',
    boxShadow: '0 0 20px rgba(26, 108, 255, 0.6)',
    transform: 'scale(1.05)',
    fontFamily: 'inherit'
  },
  
  // Buy Now Button
  buyNowBtn: {
    width: '100%',
    padding: '14px',
    background: 'linear-gradient(135deg, #ef4444, #dc2626)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '12px',
    fontSize: '1.05rem',
    fontWeight: '700',
    cursor: 'pointer',
    boxShadow: '0 6px 20px rgba(239, 68, 68, 0.4)',
    transition: 'all 0.2s',
    fontFamily: 'inherit',
    animation: 'glowRed 2s infinite',
    marginTop: '8px'
  },
  
  // Buy Form Container
  buyFormContainer: {
    background: 'rgba(26, 108, 255, 0.08)',
    border: '1px solid rgba(26, 108, 255, 0.2)',
    borderRadius: '12px',
    padding: '15px',
    animation: 'imageZoom 0.3s ease-out'
  },
  
  formGroup: {
    marginBottom: '12px'
  },
  
  input: {
    width: '100%',
    padding: '12px 14px',
    border: '2px solid rgba(26, 108, 255, 0.2)',
    borderRadius: '10px',
    fontSize: '1rem',
    boxSizing: 'border-box',
    outline: 'none',
    background: 'rgba(0, 0, 0, 0.3)',
    color: '#ffffff',
    fontFamily: 'inherit'
  },
  
  phoneRow: {
    display: 'flex',
    alignItems: 'stretch',
    width: '100%'
  },
  
  phonePrefix: {
    padding: '12px 14px',
    background: 'rgba(26, 108, 255, 0.15)',
    border: '2px solid rgba(26, 108, 255, 0.2)',
    borderRight: 'none',
    borderRadius: '10px 0 0 10px',
    color: '#4d9fff',
    fontWeight: '700',
    fontSize: '0.95rem',
    display: 'flex',
    alignItems: 'center'
  },
  
  phoneInput: {
    flex: 1,
    padding: '12px 14px',
    border: '2px solid rgba(26, 108, 255, 0.2)',
    borderLeft: 'none',
    borderRadius: '0 10px 10px 0',
    fontSize: '1rem',
    boxSizing: 'border-box',
    outline: 'none',
    background: 'rgba(0, 0, 0, 0.3)',
    color: '#ffffff',
    fontFamily: 'inherit',
    minWidth: 0
  },
  
  buyActionsRow: {
    display: 'flex',
    gap: '10px',
    marginTop: '5px'
  },
  
  confirmBtn: {
    flex: 1,
    padding: '12px',
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '10px',
    fontSize: '1rem',
    fontWeight: '700',
    cursor: 'pointer',
    boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)',
    fontFamily: 'inherit'
  },
  
  cancelBtn: {
    padding: '12px 20px',
    background: 'rgba(255, 255, 255, 0.1)',
    color: '#ffffff',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '10px',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: 'inherit'
  },
  
  btnLoading: {
    opacity: 0.8,
    cursor: 'not-allowed'
  },
  
  loadingContent: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  },
  
  spinner: {
    display: 'inline-block',
    width: '14px',
    height: '14px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#ffffff',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite'
  },
  
  // Out of Stock Box
  outOfStockBox: {
    padding: '14px',
    background: 'rgba(239,68,68,0.1)',
    borderRadius: '10px',
    color: '#ef4444',
    textAlign: 'center',
    border: '1px solid rgba(239,68,68,0.25)',
    fontWeight: 'bold',
    fontSize: '0.95rem',
    marginTop: '8px'
  },
  
  // Shop Info
  shopInfo: {
    background: 'rgba(26, 108, 255, 0.08)',
    border: '1px solid rgba(26, 108, 255, 0.2)',
    borderRadius: '10px',
    padding: '12px 15px',
    marginTop: '8px',
    textAlign: 'center'
  },
  
  shopAddress: {
    color: '#c8d6e5',
    fontSize: '0.85rem',
    margin: '0 0 8px 0',
    lineHeight: 1.4
  },
  
  mapLink: {
    display: 'inline-block',
    color: '#4d9fff',
    fontSize: '0.85rem',
    textDecoration: 'none',
    fontWeight: '600'
  },
  
  // Similar Products
  similarSection: {
    borderTop: '1px solid rgba(26, 108, 255, 0.2)',
    paddingTop: '20px',
    marginTop: '15px'
  },
  
  similarTitle: {
    color: '#4d9fff',
    fontSize: '1.2rem',
    fontWeight: '700',
    margin: '0 0 15px 0'
  },
  
  similarGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
    gap: '12px'
  },
  
  similarCard: {
    cursor: 'pointer',
    background: '#0f0f1e',
    border: '1px solid #1a4fff44',
    borderRadius: '10px',
    padding: '8px',
    textAlign: 'center',
    transition: 'all 0.2s',
    position: 'relative',
    overflow: 'hidden'
  },
  
  similarImage: {
    width: '100%',
    height: '100px',
    objectFit: 'cover',
    borderRadius: '6px',
    marginBottom: '6px'
  },
  
  similarOutBadge: {
    position: 'absolute',
    top: '35px',
    left: '50%',
    transform: 'translateX(-50%)',
    background: '#ef4444',
    color: '#fff',
    fontSize: '9px',
    padding: '3px 6px',
    borderRadius: '4px',
    fontWeight: 'bold',
    whiteSpace: 'nowrap'
  },
  
  similarName: {
    color: '#f0f4ff',
    fontSize: '0.75rem',
    margin: '0 0 3px 0',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  
  similarPrice: {
    color: '#4d9fff',
    fontSize: '0.85rem',
    fontWeight: 'bold',
    margin: 0
  }
  
  // ✅ reviewsSection REMOVED
  // ✅ reviewCard, reviewStars, etc REMOVED
  // ✅ advanceInfo REMOVED
  // ✅ addReviewBox REMOVED
};

// ✅ Mobile Responsive (Auto-applied)
const mobileStyles = `
  @media (max-width: 768px) {
    .product-page-top {
      flex-direction: column !important;
    }
    .product-page-image {
      width: 100% !important;
      height: 300px !important;
    }
  }
`;

export default ProductPage;
