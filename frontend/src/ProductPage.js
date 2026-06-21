import React, { useState } from 'react';

// 🆕 Smart Price Display Component (Same as App.jsx)
function PriceDisplay({ product, size = 'normal' }) {
  const getNumericPrice = (priceStr) => {
    if (!priceStr) return 0;
    return parseInt(String(priceStr).replace(/[^0-9]/g, '')) || 0;
  };

  const currentPrice = getNumericPrice(product.price);
  const originalPrice = getNumericPrice(product.original_price);
  
  let discountPercent = 0;
  let finalOldPrice = originalPrice;
  
  // Calculate discount based on available data
  if (originalPrice > currentPrice && currentPrice > 0) {
    // Has original_price - calculate discount percentage
    discountPercent = Math.round(((originalPrice - currentPrice) / originalPrice) * 100);
  } else if (product.discount_percent && product.discount_percent > 0) {
    // Has discount_percent field - calculate old price
    discountPercent = product.discount_percent;
    finalOldPrice = Math.round(currentPrice / (1 - discountPercent / 100));
  } else {
    // Default 40% discount
    discountPercent = 40;
    finalOldPrice = Math.round(currentPrice / 0.6);
  }

  const isLarge = size === 'large';

  return (
    <div className={`price-row ${isLarge ? 'price-row-large' : ''}`}>
      <span className={`product-price ${isLarge ? 'product-price-large' : ''}`}>
        {product.price}
      </span>
      {finalOldPrice > currentPrice && (
        <>
          <span className={`old-price ${isLarge ? 'old-price-large' : ''}`}>
            ₹{finalOldPrice}
          </span>
          <span className={`discount-tag ${isLarge ? 'discount-tag-large' : ''}`}>
            {discountPercent}% OFF
          </span>
        </>
      )}
    </div>
  );
}

function ProductPage({ product, onClose, onOrderSuccess, allProducts }) {
  const [selectedSize, setSelectedSize] = useState('');
  const [showBuyForm, setShowBuyForm] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!product) return null;

  // 🛍️ Booking submission handler
  const handleBuyNowSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSize) {
      alert('Please select a size first! 📏');
      return;
    }
    if (!customerName.trim() || !customerPhone.trim()) {
      alert('Please fill in your name and phone number! ✍️');
      return;
    }

    setIsSubmitting(true);  
    setErrorMessage('');  

    const backendUrl = 'https://dolphin-trends-3.onrender.com/api-chat-box';   

    const formData = new FormData();
    formData.append('customer_name', customerName);
    formData.append('customer_phone', customerPhone);
    formData.append('product_name', product.name || 'Top');
    formData.append('product_image', product.image || '');
    formData.append('size', selectedSize);
    formData.append('price', String(product.price).replace(/[^0-9]/g, '') || '0');
    formData.append('message', `I want to buy ${product.name} in size ${selectedSize}. Please confirm stock.`);

    try {  
      const response = await fetch(backendUrl, {  
        method: 'POST',  
        body: formData,
      });  

      if (response.ok) {  
        const resData = await response.json();
        
        alert('🎉 Order request received! Opening Chat box...');
        
        setShowBuyForm(false);  
        setCustomerName('');  
        setCustomerPhone('');  
          
        // ✅ FIXED: Use productName (not name) to match ChatBox expectation
        if (onOrderSuccess) {  
          onOrderSuccess({  
            productName: product.name,        // ✅ Changed from 'name' to 'productName'
            name: product.name,                // ✅ Keep both for compatibility
            price: product.price,  
            size: selectedSize,  
            image: product.image,
            customerName: customerName,
            customer_chat_id: resData.customer_chat_id
          });  
        }  
          
        onClose();
      } else {  
        const errorData = await response.json();  
        setErrorMessage(errorData.detail || 'Failed to process booking. Please try again.');  
      }  
    } catch (error) {  
      console.error('Error submitting order:', error);  
      setErrorMessage('Server connection error. Please try again later.');  
    } finally {  
      setIsSubmitting(false);  
    }
  };

  return (
    <>
      <style>{productPageStyles}</style>

      <div className="product-modal-overlay">  
        <div className="product-modal-container">  
          <button className="modal-close-btn" onClick={onClose}>✕</button>  
            
          <div className="product-modal-content">  
            {/* Image Section */}  
            <div className="product-image-section">  
              <div className="image-wrapper">  
                <img 
                  src={product.image || 'https://via.placeholder.com/400'} 
                  alt={product.name} 
                  onClick={() => window.open(product.image, '_blank')}
                  style={{ cursor: 'zoom-in' }}
                />  
              </div>  
            </div>  

            {/* Details Section */}  
            <div className="product-details-section">  
              <span className="brand-tag">{product.category || '250 TOPS'}</span>  
              <h2>{product.name || 'Top'}</h2>  
                
              {/* ✅ DYNAMIC PRICE - No more hardcoded values! */}
              <PriceDisplay product={product} size="large" />  

              {/* Product Description */}  
              <p className="product-description">  
                {product.description || 'Beautiful design crafted with rich fabric. Premium quality tailored to perfection.'}  
              </p>  

              {/* Size Selector */}  
              <div className="size-selector-container">  
                <h3>✏️ Select Size:</h3>  
                <div className="size-buttons-grid">  
                  {['S', 'M', 'L', 'XL', 'XXL'].map((size) => (  
                    <button  
                      key={size}  
                      type="button"  
                      className={`size-btn ${selectedSize === size ? 'active' : ''}`}  
                      onClick={() => setSelectedSize(size)}  
                    >  
                      {size}  
                    </button>  
                  ))}  
                </div>  
              </div>  

              {/* Booking Form or Buy Button */}  
              {!showBuyForm ? (  
                <button   
                  className="main-buy-now-btn"  
                  onClick={() => {  
                    if (!selectedSize) {  
                      alert('Please select a size first! 📏');  
                    } else {  
                      setShowBuyForm(true);  
                    }  
                  }}  
                >  
                  🛍️ Buy Now  
                </button>  
              ) : (  
                <form className="booking-inner-form" onSubmit={handleBuyNowSubmit}>  
                  <h3>Customer Details</h3>  
                    
                  {errorMessage && <p className="error-text-msg">{errorMessage}</p>}  
                    
                  <div className="form-input-group">  
                    <label>Your Name:</label>  
                    <input   
                      type="text"   
                      required   
                      placeholder="Enter your full name"  
                      value={customerName}  
                      onChange={(e) => setCustomerName(e.target.value)}  
                      disabled={isSubmitting}  
                    />  
                  </div>  

                  <div className="form-input-group">  
                    <label>WhatsApp Number:</label>  
                    <input   
                      type="tel"   
                      required   
                      placeholder="e.g., 9876543210"  
                      value={customerPhone}  
                      onChange={(e) => setCustomerPhone(e.target.value)}  
                      disabled={isSubmitting}  
                    />  
                  </div>  

                  <div className="form-action-buttons">  
                    <button   
                      type="button"   
                      className="cancel-form-btn"   
                      onClick={() => setShowBuyForm(false)}  
                      disabled={isSubmitting}  
                    >  
                      Cancel  
                    </button>  
                    <button   
                      type="submit"   
                      className="confirm-form-btn"  
                      disabled={isSubmitting}  
                    >  
                      {isSubmitting ? 'Processing...' : 'Confirm & Open Chat ✅'}  
                    </button>  
                  </div>  
                </form>  
              )}  

              {/* Location Card */}  
              <div className="location-card">  
                <p>📍 Dolphin Trends, Rajagopala Nagar,</p>  
                <p>Peenya 2nd Stage, Bangalore - 560058</p>  
                <a   
                  href="https://maps.app.goo.gl/amrkmppGsdgprtx27"   
                  target="_blank"   
                  rel="noreferrer"   
                  className="maps-link"  
                >  
                  🗺️ View on Google Maps  
                </a>  
              </div>  

              {/* 🆕 Share & Wishlist Buttons */}
              <div className="action-buttons-row">
                <button 
                  className="action-btn share-btn"
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: product.name,
                        text: `Check out ${product.name} at Dolphin Trends!`,
                        url: window.location.href
                      });
                    } else {
                      navigator.clipboard.writeText(window.location.href);
                      alert('🔗 Link copied to clipboard!');
                    }
                  }}
                >
                  📤 Share
                </button>
                <button 
                  className="action-btn wishlist-btn"
                  onClick={() => {
                    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
                    if (wishlist.find(p => p.product_id === product.product_id)) {
                      wishlist = wishlist.filter(p => p.product_id !== product.product_id);
                      alert('💔 Removed from wishlist');
                    } else {
                      wishlist.push(product);
                      alert('❤️ Added to wishlist!');
                    }
                    localStorage.setItem('wishlist', JSON.stringify(wishlist));
                  }}
                >
                  ❤️ Wishlist
                </button>
              </div>

            </div>  
          </div>  
        </div>  
      </div>  
    </>
  );
}

const productPageStyles = `
.product-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(5, 10, 20, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  backdrop-filter: blur(8px);
  padding: 15px;
}

.product-modal-container {
  background: #070f24;
  width: 100%;
  max-width: 460px;
  max-height: 95vh;
  border-radius: 24px;
  overflow-y: auto;
  position: relative;
  animation: modalSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalSlideUp {
  from { transform: translateY(30px) scale(0.95); opacity: 0; }
  to { transform: translateY(0) scale(1); opacity: 1; }
}

.product-modal-container::-webkit-scrollbar { width: 6px; }
.product-modal-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
}

.modal-close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(255, 73, 73, 0.15);
  border: none;
  color: #ff4949;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  font-weight: bold;
  font-size: 14px;
  transition: background 0.2s;
}
.modal-close-btn:hover { background: #ff4949; color: #fff; }

.product-modal-content { display: flex; flex-direction: column; }

.product-image-section { padding: 16px 16px 0 16px; }

.image-wrapper {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 10px;
}

.product-image-section img {
  width: 100%;
  height: auto;
  max-height: 450px;
  object-fit: contain;
  display: block;
}

.product-details-section { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.brand-tag {
  background: rgba(26, 108, 255, 0.15);
  color: #3b82f6;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  display: inline-block;
  width: fit-content;
}
.product-details-section h2 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #fff; }

/* ✅ NEW: Price Display Styles */
.price-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 2px;
  flex-wrap: wrap;
}

.price-row-large {
  gap: 14px;
  margin: 8px 0 12px 0;
}

.product-price {
  font-size: 1.3rem;
  font-weight: bold;
  color: #60a5fa;
}

.product-price-large {
  font-size: 1.8rem;
}

.old-price {
  font-size: 0.9rem;
  text-decoration: line-through;
  color: #64748b;
  opacity: 0.8;
}

.old-price-large {
  font-size: 1.1rem;
}

.discount-tag {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 0.7rem;
  font-weight: bold;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.3);
}

.discount-tag-large {
  padding: 4px 10px;
  font-size: 0.85rem;
}

.product-description {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 14px;
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.5;
  margin: 0;
}

.size-selector-container h3 { margin: 0 0 12px 0; font-size: 1rem; color: #e2e8f0; font-weight: 500; }
.size-buttons-grid { display: flex; gap: 10px; }
.size-btn {
  flex: 1;
  padding: 10px 0;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.2);
  color: #fff;
  border-radius: 10px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.size-btn:hover {
  border-color: rgba(255,255,255,0.4);
  background: rgba(255, 255, 255, 0.05);
}
.size-btn.active {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.main-buy-now-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #ff5c6c, #e63946);
  color: #fff;
  border: none;
  border-radius: 14px;
  font-weight: bold;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 6px 16px rgba(255, 92, 108, 0.25);
  margin-top: 5px;
  transition: all 0.2s;
}
.main-buy-now-btn:hover { 
  transform: scale(1.02);
  box-shadow: 0 8px 20px rgba(255, 92, 108, 0.4);
}
.main-buy-now-btn:active {
  transform: scale(0.98);
}

.booking-inner-form {
  background: rgba(255, 255, 255, 0.02);
  padding: 18px;
  border-radius: 14px;
  border: 1px solid rgba(26, 108, 255, 0.2);
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 5px;
}
.booking-inner-form h3 {
  margin: 0;
  font-size: 14px;
  color: #fff;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.form-input-group { display: flex; flex-direction: column; gap: 6px; }
.form-input-group label { font-size: 12px; color: #94a3b8; }
.form-input-group input {
  padding: 10px;
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #fff;
  outline: none;
  font-size: 13px;
  transition: border-color 0.2s;
}
.form-input-group input:focus { 
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.form-input-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-action-buttons { display: flex; gap: 10px; margin-top: 6px; }
.cancel-form-btn {
  flex: 1;
  padding: 10px;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.15);
  color: #94a3b8;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}
.cancel-form-btn:hover {
  background: rgba(255,255,255,0.05);
  color: #fff;
}
.cancel-form-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.confirm-form-btn {
  flex: 2;
  padding: 10px;
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: bold;
  transition: all 0.2s;
}
.confirm-form-btn:hover { 
  background: linear-gradient(135deg, #059669, #047857);
  transform: scale(1.02);
}
.confirm-form-btn:disabled { 
  opacity: 0.6; 
  cursor: not-allowed;
  transform: none;
}

.error-text-msg { 
  margin: 0; 
  color: #ef4444; 
  font-size: 12px; 
  font-weight: 600;
  background: rgba(239, 68, 68, 0.1);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.location-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 14px;
  font-size: 0.85rem;
  color: #94a3b8;
}
.location-card p { margin: 0 0 4px 0; }
.maps-link { 
  color: #60a5fa; 
  text-decoration: none; 
  font-weight: 500;
  transition: color 0.2s;
}
.maps-link:hover {
  color: #93c5fd;
  text-decoration: underline;
}

/* 🆕 Action Buttons Row */
.action-buttons-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.action-btn {
  flex: 1;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.02);
  color: #c8d6e5;
}

.share-btn:hover {
  background: rgba(26, 108, 255, 0.15);
  border-color: #1a6cff;
  color: #60a5fa;
}

.wishlist-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
  color: #ef4444;
}

/* 🆕 Image zoom cursor */
.product-image-section img {
  cursor: zoom-in;
  transition: transform 0.3s;
}
.product-image-section img:hover {
  transform: scale(1.02);
}

/* Mobile Responsive */
@media (max-width: 480px) {
  .product-modal-container {
    max-width: 100%;
    border-radius: 0;
    max-height: 100vh;
  }
  .product-details-section { padding: 16px; }
  .product-image-section img { max-height: 350px; }
}
`;

export default ProductPage;
