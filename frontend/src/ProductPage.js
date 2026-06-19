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

    // ಇಲ್ಲಿ ಮುಂದೆ ನಿನ್ನ ಬ್ಯಾಕೆಂಡ್ ಸರ್ವರ್ ಯುಆರ್‌ಎಲ್ ಬರಬೇಕು (ಉದಾಹರಣೆಗೆ: http://localhost:5000/api/bookings)
    const backendUrl = '/api/bookings'; 

    const orderPayload = {
      customer_name: customerName,
      customer_phone: customerPhone,
      product_name: product.name,
      size: selectedSize,
      price: product.price,
      image_url: product.image || 'https://via.placeholder.com/150', // ಫೋಟೋ ಇಲ್ಲದಿದ್ದರೆ ಪ್ಲೇಸ್‌ಹೋಲ್ಡರ್
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
        
        // 🚀 ಪೇರೆಂಟ್ ಕಾಂಪೊನೆಂಟ್‌ಗೆ ಆರ್ಡರ್ ಸಕ್ಸಸ್ ಸಿಗ್ನಲ್ ಕಳಿಸುವುದು (ಇದು ಲೈವ್ ಚಾಟ್ ಬಾಕ್ಸ್ ಓಪನ್ ಮಾಡುತ್ತೆ)
        if (onOrderSuccess) {
          onOrderSuccess({
            productName: product.name,
            size: selectedSize,
            price: product.price
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
              <img src={product.image || 'https://via.placeholder.com/400'} alt={product.name} />
            </div>

            {/* ಬಲಭಾಗ: ಪ್ರಾಡಕ್ಟ್ ವಿವರಗಳು & ಫಾರ್ಮ್ */}
            <div className="product-details-section">
              <span className="brand-tag">Dolphin Trends</span>
              <h2>{product.name}</h2>
              <p className="product-price">{product.price}</p>
              <p className="product-description">
                Premium quality fabric tailored to perfection. Upgrade your wardrobe with our latest fashion collection.
              </p>

              {/* ಸೈಜ್ ಸೆಲೆಕ್ಷನ್ */}
              <div className="size-selector-container">
                <h3>Select Size:</h3>
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

              {/* ಬುಕಿಂಗ್ ಫಾರ್ಮ್ ಅಥವಾ ಬಟನ್ */}
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
                  🛍️ Book Now
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
                      {isSubmitting ? 'Processing...' : 'Confirm Booking ✅'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ಡಾರ್ಕ್ ಬ್ಲೂ ಮತ್ತು ಪ್ರೀಮಿಯಂ ಥೀಮ್ ಸ್ಟೈಲ್ಸ್
const productPageStyles = `
  .product-modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 10, 20, 0.85); display: flex; alignItems: center; justifyContent: center; zIndex: 99999; backdropFilter: blur(8px); padding: 20px; }
  .product-modal-container { background: linear-gradient(135deg, #0f1a35 0%, #0a1428 100%); width: 100%; maxWidth: 850px; borderRadius: 24px; border: 1px solid rgba(26, 108, 255, 0.2); position: relative; color: #fff; overflow: hidden; boxShadow: 0 20px 50px rgba(0,0,0,0.6); animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
  .modal-close-btn { position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff; width: 35px; height: 35px; borderRadius: 50%; cursor: pointer; display: flex; alignItems: center; justifyContent: center; zIndex: 10; transition: background 0.2s; }
  .modal-close-btn:hover { background: #ef4444; border: none; }
  
  .product-modal-content { display: flex; flexWrap: wrap; }
  .product-image-section { flex: 1; minWidth: 320px; background: rgba(0,0,0,0.2); display: flex; alignItems: center; justifyContent: center; padding: 20px; }
  .product-image-section img { maxWidth: 100%; maxHeight: 450px; borderRadius: 16px; objectFit: cover; boxShadow: 0 8px 25px rgba(0,0,0,0.3); }
  
  .product-details-section { flex: 1; minWidth: 320px; padding: 40px 30px; display: flex; flexDirection: column; gap: 15px; }
  .brand-tag { color: #1a6cff; fontSize: 12px; fontWeight: 800; textTransform: uppercase; letterSpacing: 1.5px; }
  .product-details-section h2 { margin: 0; fontSize: 26px; fontWeight: 700; color: #fff; }
  .product-price { fontSize: 22px; fontWeight: 700; color: #10b981; margin: 0; }
  .product-description { fontSize: 14px; color: #a0b3d6; lineHeight: 1.6; margin: 0; }
  
  .size-selector-container h3 { fontSize: 14px; color: #fff; marginBottom: 10px; fontWeight: 600; }
  .size-buttons-grid { display: flex; gap: 10px; flexWrap: wrap; }
  .size-btn { padding: 10px 18px; background: rgba(26, 108, 255, 0.08); border: 1px solid rgba(26, 108, 255, 0.2); color: #fff; borderRadius: 8px; cursor: pointer; fontWeight: 600; fontSize: 13px; transition: all 0.2s; }
  .size-btn:hover { border-color: #1a6cff; background: rgba(26, 108, 255, 0.15); }
  .size-btn.active { background: #1a6cff; border-color: #1a6cff; boxShadow: 0 0 12px rgba(26, 108, 255, 0.4); }
  
  .main-buy-now-btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #1a6cff, #004ecc); color: #fff; border: none; borderRadius: 12px; fontWeight: 700; fontSize: 15px; cursor: pointer; marginTop: 15px; transition: transform 0.2s, boxShadow 0.2s; boxShadow: 0 4px 15px rgba(26, 108, 255, 0.3); }
  .main-buy-now-btn:hover { transform: translateY(-2px); boxShadow: 0 6px 20px rgba(26, 108, 255, 0.5); }
  
  .booking-inner-form { background: rgba(0, 0, 0, 0.2); padding: 20px; borderRadius: 14px; border: 1px solid rgba(26, 108, 255, 0.15); display: flex; flexDirection: column; gap: 12px; marginTop: 10px; animation: fadeIn 0.3s ease; }
  .booking-inner-form h3 { margin: 0; fontSize: 15px; color: #fff; borderBottom: 1px solid rgba(26, 108, 255, 0.1); paddingBottom: 6px; }
  .form-input-group { display: flex; flexDirection: column; gap: 5px; }
  .form-input-group label { fontSize: 12px; color: #a0b3d6; }
  .form-input-group input { padding: 10px; background: rgba(0,0,0,0.3); border: 1px solid rgba(26, 108, 255, 0.2); borderRadius: 8px; color: #fff; outline: none; fontSize: 13px; }
  .form-input-group input:focus { border-color: #1a6cff; }
  
  .form-action-buttons { display: flex; gap: 10px; marginTop: 5px; }
  .cancel-form-btn { flex: 1; padding: 10px; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: #a0b3d6; borderRadius: 8px; cursor: pointer; fontSize: 13px; fontWeight: 600; }
  .cancel-form-btn:hover { background: rgba(255,255,255,0.05); color: #fff; }
  .confirm-form-btn { flex: 2; padding: 10px; background: #10b981; border: none; color: #fff; borderRadius: 8px; cursor: pointer; fontSize: 13px; fontWeight: 700; boxShadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
  .confirm-form-btn:hover { background: #059669; }
  .error-text-msg { margin: 0; color: #ef4444; fontSize: 12px; fontWeight: 600; }

  @keyframes slideUp { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  
  @media (max-width: 768px) { .product-modal-container { maxHeight: 90vh; overflowY: auto; } .product-details-section { padding: 25px 20px; } }
`;

export default ProductPage;
