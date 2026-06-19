import React, { useState } from 'react';

function ProductPage({ product, onClose, onOrderSuccess, allProducts }) {
  const [selectedSize, setSelectedSize] = useState('');
  const [showBuyForm, setShowBuyForm] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!product) return null;

  // 🛍️ ಬುಕಿಂಗ್ ಕನ್ಫರ್ಮ್ ಮಾಡಿದಾಗ ರನ್ ಆಗುವ ಫಂಕ್ಷನ್
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

    // ಬ್ಯಾಕೆಂಡ್ ಸರ್ವರ್ ಯುಆರ್‌ಎಲ್
    const backendUrl = '/api/bookings'; 

    const orderPayload = {
      customer_name: customerName,
      customer_phone: customerPhone,
      product_name: product.name,
      size: selectedSize,
      price: product.price,
      image_url: product.image || 'https://via.placeholder.com/150',
    };

    try {
      // 🔗 ಬ್ಯಾಕೆಂಡ್‌ಗೆ ಆರ್ಡರ್ ಡೇಟಾ ಕಳಿಸುವುದು
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderPayload),
      });

      if (response.ok) {
        // ಫಾರ್ಮ್ ಕ್ಲಿಯರ್ ಮಾಡುವುದು
        setShowBuyForm(false);
        setCustomerName('');
        setCustomerPhone('');
        
        // 🚀 ಪೇರೆಂಟ್ ಕಾಂಪೊನೆಂಟ್‌ಗೆ ಆರ್ಡರ್ ಡೇಟಾ ಮತ್ತು ಆಟೋ-ಮೆಸೇಜ್ ಸಿಗ್ನಲ್ ಕಳಿಸುವುದು
        if (onOrderSuccess) {
          onOrderSuccess({
            name: product.name,
            price: product.price,
            size: selectedSize,
            image: product.image
          });
        }
        
        onClose(); // ಪ್ರಾಡಕ್ಟ್ ಪೇಜ್ ಮಾಡಲ್ ಕ್ಲೋಸ್ ಮಾಡುವುದು
      } else {
        const errorData = await response.json();
        setErrorMessage(errorData.message || 'Failed to process booking. Please try again.');
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
            {/* ಎಡಭಾಗ: ಪ್ರಾಡಕ್ಟ್ ಇಮೇಜ್ */}
            <div className="product-image-section">
              <div className="image-wrapper">
                <img src={product.image || 'https://via.placeholder.com/400'} alt={product.name} />
              </div>
            </div>

            {/* ಬಲಭಾಗ: ಪ್ರಾಡಕ್ಟ್ ವಿವರಗಳು & ಫಾರ್ಮ್ */}
            <div className="product-details-section">
              <span className="brand-tag">{product.category || '250 TOPS'}</span>
              <h2>{product.name || 'Top'}</h2>
              
              {/* 🏷️ ಪ್ರೀಮಿಯಂ ಪ್ರೈಸಿಂಗ್ ರೋ (40% OFF ಬ್ಯಾಡ್ಜ್ ಜೊತೆ) */}
              <div className="price-row">
                <span className="product-price">{product.price || '₹300'}</span>
                <span className="old-price">₹500</span>
                <span className="discount-tag">40% OFF</span>
              </div>

              {/* ಪ್ರಾಡಕ್ಟ್ ಡಿಸ್ಕ್ರಿಪ್ಷನ್ */}
              <p className="product-description">
                {product.description || 'Beautiful design crafted with rich fabric. Premium quality tailored to perfection.'}
              </p>

              {/* 📏 ಸೈಜ್ ಸೆಲೆಕ್ಷನ್ */}
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

              {/* ಬುಕಿಂಗ್ ಫಾರ್ಮ್ ಅಥವಾ ಬಟನ್ ಹ್ಯಾಂಡ್ಲರ್ */}
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

              {/* 📍 ಗೂಗಲ್ ಮ್ಯಾಪ್ ಲೊಕೇಶನ್ ಕಾರ್ಡ್ */}
              <div className="location-card">
                <p>📍 Dolphin Trends, Rajagopala Nagar,</p>
                <p>Peenya 2nd Stage, Bangalore - 560058</p>
                <a 
                  href="https://maps.google.com" 
                  target="_blank" 
                  rel="noreferrer" 
                  className="maps-link"
                >
                  🗺️ View on Google Maps
                </a>
              </div>

              {/* ⭐ ಕಸ್ಟಮರ್ ರಿವ್ಯೂಸ್ */}
              <div className="reviews-header">
                <span>⭐</span> <span className="reviews-title">Customer Reviews</span>
              </div>

            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ಡಾರ್ಕ್ ಬ್ಲೂ ಮತ್ತು ಪ್ರೀಮಿಯಂ ಮೊಬೈಲ್ ಮ್ಯಾಚಿಂಗ್ ಸ್ಟೈಲ್ಸ್
const productPageStyles = `
  .product-modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 10, 20, 0.85); display: flex; align-items: center; justify-content: center; z-index: 99999; backdrop-filter: blur(8px); padding: 15px; }
  .product-modal-container { background: #070f24; width: 100%; maxWidth: 460px; maxHeight: 92vh; borderRadius: 24px; border: 1px solid rgba(255, 255, 255, 0.08); position: relative; color: #fff; overflow-y: auto; cubic-bezier(0.16, 1, 0.3, 1); box-shadow: 0 24px 48px rgba(0, 0, 0, 0.6); }
  
  /* Custom scrollbar for container */
  .product-modal-container::-webkit-scrollbar { width: 6px; }
  .product-modal-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); borderRadius: 10px; }

  .modal-close-btn { position: absolute; top: 16px; right: 16px; background: rgba(255, 73, 73, 0.15); border: none; color: #ff4949; width: 32px; height: 32px; borderRadius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 10; font-weight: bold; font-size: 14px; transition: background 0.2s; }
  .modal-close-btn:hover { background: #ff4949; color: #fff; }
  
  .product-modal-content { display: flex; flex-direction: column; }
  
  .product-image-section { padding: 16px 16px 0 16px; }
  .image-wrapper { background: #fff; borderRadius: 16px; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 380px; }
  .product-image-section img { width: 100%; height: 100%; object-fit: cover; }
  
  .product-details-section { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
  .brand-tag { background: rgba(26, 108, 255, 0.15); color: #3b82f6; padding: 6px 14px; borderRadius: 20px; fontSize: 0.8rem; fontWeight: bold; display: inline-block; width: fit-content; }
  .product-details-section h2 { margin: 0; fontSize: 1.7rem; fontWeight: 700; color: #fff; }
  
  .price-row { display: flex; align-items: center; gap: 12px; margin-bottom: 2px; }
  .product-price { fontSize: 2rem; fontWeight: bold; color: #60a5fa; }
  .old-price { fontSize: 1.2rem; text-decoration: line-through; color: #64748b; }
  .discount-tag { background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 4px 8px; borderRadius: 6px; fontSize: 0.8rem; fontWeight: bold; }

  .product-description { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); borderRadius: 12px; padding: 14px; fontSize: 0.95rem; color: #94a3b8; lineHeight: 1.5; margin: 0; }
  
  .size-selector-container h3 { margin: 0 0 12px 0; fontSize: 1rem; color: #e2e8f0; fontWeight: 500; }
  .size-buttons-grid { display: flex; gap: 10px; }
  .size-btn { flex: 1; padding: 12px 0; background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #fff; borderRadius: 10px; cursor: pointer; fontWeight: bold; fontSize: 0.95rem; transition: all 0.2s; }
  .size-btn.active { border-color: #ffffff; background: transparent; box-shadow: inset 0 0 5px rgba(255,255,255,0.2); }
  
  .main-buy-now-btn { width: 100%; padding: 16px; background: #ff5c6c; color: #fff; border: none; borderRadius: 14px; fontWeight: bold; fontSize: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 8px 20px rgba(255, 92, 108, 0.25); margin-top: 5px; transition: transform 0.2s; }
  .main-buy-now-btn:hover { transform: scale(1.01); }
  
  .booking-inner-form { background: rgba(255, 255, 255, 0.02); padding: 18px; borderRadius: 14px; border: 1px solid rgba(26, 108, 255, 0.2); display: flex; flex-direction: column; gap: 12px; margin-top: 5px; }
  .booking-inner-form h3 { margin: 0; fontSize: 15px; color: #fff; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.1); }
  .form-input-group { display: flex; flex-direction: column; gap: 6px; }
  .form-input-group label { fontSize: 12px; color: #94a3b8; }
  .form-input-group input { padding: 12px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); borderRadius: 8px; color: #fff; outline: none; fontSize: 13px; }
  .form-input-group input:focus { border-color: #3b82f6; }
  
  .form-action-buttons { display: flex; gap: 10px; margin-top: 6px; }
  .cancel-form-btn { flex: 1; padding: 12px; background: transparent; border: 1px solid rgba(255,255,255,0.15); color: #94a3b8; borderRadius: 8px; cursor: pointer; fontSize: 13px; fontWeight: 600; }
  .confirm-form-btn { flex: 2; padding: 12px; background: #10b981; border: none; color: #fff; borderRadius: 8px; cursor: pointer; fontSize: 13px; fontWeight: bold; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
  .confirm-form-btn:hover { background: #059669; }
  .error-text-msg { margin: 0; color: #ef4444; fontSize: 12px; fontWeight: 600; }

  .location-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); borderRadius: 12px; padding: 14px; fontSize: 0.9rem; color: #94a3b8; }
  .location-card p { margin: 0 0 6px 0; }
  .location-card p:last-of-type { margin: 0 0 10px 0; }
  .maps-link { color: #60a5fa; text-decoration: none; fontWeight: 500; }

  .reviews-header { fontSize: 1.1rem; fontWeight: bold; display: flex; gap: 8px; align-items: center; margin-top: 5px; }
  .reviews-title { color: #60a5fa; }
`;

export default ProductPage;
