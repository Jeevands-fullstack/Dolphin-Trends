import React, { useState } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function BookingModal({ product, onClose }) {
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  
  const adminPhones = [
    "917411255628",
    "919353344035",
    "919353838835"
  ];

  const priceNumber = parseInt((product.price || '0').replace(/[^\d]/g, '')) || 0;
  const advanceAmount = Math.ceil(priceNumber * 0.5);

  const handleBooking = async () => {
    if (!customerName.trim()) {
      alert('⚠️ Please enter your Name!');
      return;
    }
    if (!phone || phone.length !== 10 || !/^\d{10}$/.test(phone)) {
      alert('⚠️ Please enter a valid 10-digit WhatsApp number!');
      return;
    }
    if (!selectedSize) {
      alert('⚠️ Please select a Size!');
      return;
    }

    setLoading(true);

    const bookingData = {
      customer_name: customerName.trim(),
      customer_phone: phone,
      product_name: `${product.name} (Size: ${selectedSize})`,
      image_url: product.image || "",
      size: selectedSize,
      price: product.price
    };

    try {
      const response = await fetch(`${API}/api/bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData)
      });

      if (response.ok) {
        const customerMsg = `🎉 *Welcome to Dolphin Trends!* 🐬

Hi ${customerName},

Thank you for choosing us! We have received your order request:

👗 *${product.name}*
📏 Size: *${selectedSize}*
💰 Price: *${product.price}*

📝 *Current Status:* We are checking stock availability. Our team will contact you shortly.

📞 Need Help? Contact: 9353344035

Thank you! 😊
*Team Dolphin Trends* 🐬`;

        window.open(
          "https://wa.me/91" + phone + "?text=" + encodeURIComponent(customerMsg), 
          '_blank'
        );

        const ownerMsg = `🛍️ *New Buy Request!*

👗 *Product:* ${product.name}
📏 *Size:* ${selectedSize}
💰 *Price:* ${product.price}
👤 *Name:* ${customerName}
📱 *Phone:* ${phone}

⚙️ *Admin Panel:*
🔗 https://dolphin-trends-two.vercel.app`;

        adminPhones.forEach((adminPhone, index) => {
          setTimeout(() => {
            window.open(
              "https://wa.me/" + adminPhone + "?text=" + encodeURIComponent(ownerMsg), 
              '_blank'
            );
          }, index * 1000);
        });

        setStep(2);
      } else {
        const errorData = await response.json().catch(() => ({}));
        alert(`❌ Booking failed: ${errorData.detail || 'Please try again.'}`);
      }
    } catch (err) {
      console.error("Booking Error:", err);
      alert('❌ Server connection error! Please check your internet.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={(e) => {
      if (e.target === e.currentTarget && !loading) onClose();
    }}>
      <div style={styles.modal}>
        
        {/* Close Button */}
        <button 
          style={styles.closeBtn}
          onClick={onClose}
          disabled={loading}
        >
          ✕
        </button>

        {step === 1 && (
          <>
            <h2 style={styles.title}>📦 Book Now</h2>
            
            {/* Product Card */}
            <div style={styles.productCard}>
              <img 
                src={product.image} 
                alt={product.name} 
                style={styles.productImg}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={styles.productName}>{product.name}</h3>
                <p style={styles.productPrice}>{product.price}</p>
                {advanceAmount > 0 && (
                  <p style={styles.advanceInfo}>
                    💵 Advance: <strong>₹{advanceAmount}</strong> (50%)
                  </p>
                )}
              </div>
            </div>

            {/* Size Selection */}
            <div style={styles.formGroup}>
              <label style={styles.label}>📏 Select Size</label>
              <div style={styles.sizeGrid}>
                {sizes.map(size => (
                  <button
                    key={size}
                    type="button"
                    style={selectedSize === size ? styles.sizeBtnSelected : styles.sizeBtn}
                    onClick={() => setSelectedSize(size)}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* Name Input */}
            <div style={styles.formGroup}>
              <label style={styles.label}>👤 Your Name</label>
              <input
                type="text"
                placeholder="Enter your full name"
                value={customerName}
                onChange={e => setCustomerName(e.target.value)}
                style={styles.input}
                maxLength={50}
              />
            </div>

            {/* Phone Input */}
            <div style={styles.formGroup}>
              <label style={styles.label}>📱 WhatsApp Number</label>
              <div style={styles.phoneRow}>
                <span style={styles.phonePrefix}>+91</span>
                <input
                  type="tel"
                  placeholder="10-digit number"
                  value={phone}
                  maxLength={10}
                  onChange={e => {
                    const value = e.target.value.replace(/\D/g, '');
                    setPhone(value);
                  }}
                  style={styles.phoneInput}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button 
              style={{
                ...styles.submitBtn,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
              onClick={handleBooking} 
              disabled={loading}
            >
              {loading ? "⏳ Processing..." : "📲 Confirm & Send Request"}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2 style={{ ...styles.title, color: '#28a745' }}>✅ Request Submitted!</h2>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: '60px', marginBottom: '15px' }}>🎉</div>
              <p style={{ fontSize: '20px', color: '#28a745', fontWeight: 'bold', marginBottom: '15px' }}>
                Thank you, {customerName}!
              </p>
              <p style={{ fontSize: '15px', color: '#666', marginBottom: '20px' }}>
                Your booking request has been successfully registered.
              </p>
              <div style={styles.summaryBox}>
                <p style={styles.summaryText}>
                  👗 <strong>Product:</strong> {product.name}
                </p>
                <p style={styles.summaryText}>
                  📏 <strong>Size:</strong> {selectedSize}
                </p>
                <p style={styles.summaryText}>
                  💰 <strong>Price:</strong> {product.price}
                </p>
              </div>
              <p style={{ fontSize: '15px', color: '#007bff', fontWeight: '500', marginTop: '20px' }}>
                📱 Check your WhatsApp for confirmation!
              </p>
              <p style={{ fontSize: '13px', color: '#999', marginTop: '8px' }}>
                ⏰ Team will respond within 5 minutes.
              </p>
            </div>
            <button 
              onClick={onClose} 
              style={styles.submitBtn}
            >
              OK, Got it! 👍
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ✅ ALL STYLES INLINE - Works 100%
const styles = {
  // Overlay
  overlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.8)',
    zIndex: 99999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '15px',
    boxSizing: 'border-box',
    overflowY: 'auto'
  },
  
  // Modal Box
  modal: {
    background: '#ffffff',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '480px',
    maxHeight: '90vh',
    overflowY: 'auto',
    padding: '25px',
    position: 'relative',
    zIndex: 100000,
    boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
    boxSizing: 'border-box',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  
  // Close Button
  closeBtn: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    background: '#f5f5f5',
    border: 'none',
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    cursor: 'pointer',
    fontSize: '1.2rem',
    color: '#666',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10
  },
  
  // Title
  title: {
    color: '#1a1a1a',
    fontSize: '1.4rem',
    fontWeight: '700',
    margin: '0 0 20px 0',
    paddingRight: '40px'
  },
  
  // Product Card
  productCard: {
    display: 'flex',
    gap: '15px',
    marginBottom: '20px',
    padding: '15px',
    background: '#f9f9f9',
    borderRadius: '12px',
    alignItems: 'center'
  },
  
  // Product Image - SMALL (80px)
  productImg: {
    width: '80px',
    height: '80px',
    objectFit: 'cover',
    borderRadius: '8px',
    flexShrink: 0,
    background: '#eee'
  },
  
  productName: {
    margin: '0 0 5px 0',
    color: '#1a1a1a',
    fontSize: '1rem',
    fontWeight: '600',
    lineHeight: 1.3,
    wordBreak: 'break-word'
  },
  
  productPrice: {
    color: '#1a6cff',
    fontWeight: 'bold',
    fontSize: '1.1rem',
    margin: '3px 0'
  },
  
  advanceInfo: {
    color: '#28a745',
    fontSize: '0.85rem',
    margin: '3px 0',
    fontWeight: '500'
  },
  
  // Form Group
  formGroup: {
    marginBottom: '15px',
    width: '100%'
  },
  
  label: {
    display: 'block',
    marginBottom: '8px',
    color: '#333',
    fontWeight: '600',
    fontSize: '0.9rem'
  },
  
  // Input
  input: {
    width: '100%',
    padding: '12px 14px',
    border: '2px solid #e0e0e0',
    borderRadius: '10px',
    fontSize: '1rem',
    boxSizing: 'border-box',
    outline: 'none',
    background: '#fff',
    color: '#1a1a1a',
    transition: 'border-color 0.2s'
  },
  
  // Size Grid - 5 columns
  sizeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '8px',
    width: '100%'
  },
  
  sizeBtn: {
    padding: '12px 8px',
    background: '#f5f5f5',
    border: '2px solid #e0e0e0',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.95rem',
    color: '#333',
    textAlign: 'center',
    transition: 'all 0.2s'
  },
  
  sizeBtnSelected: {
    padding: '12px 8px',
    background: '#1a6cff',
    border: '2px solid #1a6cff',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.95rem',
    color: '#fff',
    textAlign: 'center',
    boxShadow: '0 4px 12px rgba(26,108,255,0.3)'
  },
  
  // Phone Row
  phoneRow: {
    display: 'flex',
    alignItems: 'stretch',
    width: '100%'
  },
  
  phonePrefix: {
    padding: '12px 14px',
    background: '#f5f5f5',
    border: '2px solid #e0e0e0',
    borderRight: 'none',
    borderRadius: '10px 0 0 10px',
    color: '#666',
    fontWeight: '600',
    fontSize: '0.95rem',
    display: 'flex',
    alignItems: 'center',
    whiteSpace: 'nowrap'
  },
  
  phoneInput: {
    flex: 1,
    padding: '12px 14px',
    border: '2px solid #e0e0e0',
    borderLeft: 'none',
    borderRadius: '0 10px 10px 0',
    fontSize: '1rem',
    boxSizing: 'border-box',
    outline: 'none',
    background: '#fff',
    color: '#1a1a1a',
    minWidth: 0
  },
  
  // Submit Button
  submitBtn: {
    width: '100%',
    padding: '14px',
    background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '10px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '10px',
    transition: 'all 0.2s'
  },
  
  // Summary Box (Step 2)
  summaryBox: {
    background: '#f8f9fa',
    padding: '15px',
    borderRadius: '10px',
    margin: '15px 0',
    textAlign: 'left'
  },
  
  summaryText: {
    margin: '5px 0',
    fontSize: '0.95rem',
    color: '#333'
  }
};

// Mobile Responsive (Inline media query replacement)
const mediaQuery = window.matchMedia('(max-width: 480px)');
if (mediaQuery.matches) {
  styles.modal.padding = '20px';
  styles.modal.borderRadius = '16px 16px 0 0';
  styles.productCard.flexDirection = 'column';
  styles.productCard.textAlign = 'center';
  styles.productImg.width = '100%';
  styles.productImg.height = '180px';
}

export default BookingModal;
