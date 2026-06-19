import React, { useState } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function BookingModal({ product, onClose }) {
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  
  const adminPhones = ["917411255628", "919353344035", "919353838835"];

  const priceNumber = parseInt((product.price || '0').replace(/[^\d]/g, '')) || 0;
  const advanceAmount = Math.ceil(priceNumber * 0.5);

  const handleBooking = async () => {
    if (!customerName.trim()) { alert('⚠️ Please enter your Name!'); return; }
    if (!phone || phone.length !== 10) { alert('⚠️ Please enter valid 10-digit WhatsApp number!'); return; }
    if (!selectedSize) { alert('⚠️ Please select a Size!'); return; }

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
        const customerMsg = `🎉 *Welcome to Dolphin Trends!* 🐬\n\nHi ${customerName},\n\nThank you for choosing us!\n\n👗 *${product.name}*\n📏 Size: *${selectedSize}*\n💰 Price: *${product.price}*\n\n📝 We are checking stock availability. Our team will contact you shortly.\n\n📞 Contact: 9353344035\n\n*Team Dolphin Trends* 🐬`;

        window.open(
          "https://wa.me/91" + phone + "?text=" + encodeURIComponent(customerMsg), 
          '_blank'
        );

        const ownerMsg = `🛍️ *New Buy Request!*\n\n👗 *Product:* ${product.name}\n📏 *Size:* ${selectedSize}\n💰 *Price:* ${product.price}\n👤 *Name:* ${customerName}\n📱 *Phone:* ${phone}\n\n⚙️ *Admin Panel:*\n🔗 https://dolphin-trends-two.vercel.app`;

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
        alert('❌ Booking failed. Please try again.');
      }
    } catch (err) {
      console.error(err);
      alert('❌ Server connection error!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{animations}</style>
      
      <div 
        style={styles.overlay} 
        onClick={(e) => {
          if (e.target === e.currentTarget && !loading) onClose();
        }}
      >
        <div style={styles.modal}>
          
          {/* Close Button */}
          <button 
            style={styles.closeBtn}
            onClick={onClose}
            disabled={loading}
            aria-label="Close"
          >
            ✕
          </button>

          {/* Header */}
          <div style={styles.header}>
            <div style={styles.headerIcon}>📦</div>
            <h2 style={styles.title}>Book Now</h2>
            <p style={styles.subtitle}>Fill details to book this product</p>
          </div>

          {step === 1 && (
            <>
              {/* Product Card with Glow */}
              <div style={styles.productCard}>
                <div style={styles.productImageWrap}>
                  <img 
                    src={product.image} 
                    alt={product.name} 
                    style={styles.productImg}
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzFhNmNmZiIvPjwvc3ZnPg==';
                    }}
                  />
                </div>
                <div style={styles.productInfo}>
                  <h3 style={styles.productName}>{product.name}</h3>
                  <div style={styles.priceRow}>
                    <span style={styles.priceMain}>{product.price}</span>
                    {advanceAmount > 0 && (
                      <span style={styles.advanceBadge}>
                        💰 ₹{advanceAmount} (50%)
                      </span>
                    )}
                  </div>
                </div>
              </div>

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
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>

              {/* Name Input */}
              <div style={styles.section}>
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

              {/* Phone Input */}
              <div style={styles.section}>
                <label style={styles.label}>
                  <span style={styles.labelIcon}>📱</span> WhatsApp Number
                </label>
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
                  ...(loading ? styles.submitBtnLoading : {})
                }}
                onClick={handleBooking} 
                disabled={loading}
              >
                {loading ? (
                  <span style={styles.loadingContent}>
                    <span style={styles.spinner}></span>
                    Processing...
                  </span>
                ) : (
                  <>📲 Confirm & Send Request</>
                )}
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <div style={styles.successContainer}>
                <div style={styles.successIcon}>🎉</div>
                <h2 style={styles.successTitle}>Request Submitted!</h2>
                <p style={styles.successMessage}>
                  Thank you, <strong>{customerName}</strong>!
                </p>
                <p style={styles.successSubtext}>
                  Your booking request has been successfully registered.
                </p>
                
                <div style={styles.summaryCard}>
                  <div style={styles.summaryRow}>
                    <span style={styles.summaryLabel}>👗 Product:</span>
                    <span style={styles.summaryValue}>{product.name}</span>
                  </div>
                  <div style={styles.summaryRow}>
                    <span style={styles.summaryLabel}>📏 Size:</span>
                    <span style={styles.summaryValue}>{selectedSize}</span>
                  </div>
                  <div style={styles.summaryRow}>
                    <span style={styles.summaryLabel}>💰 Price:</span>
                    <span style={styles.summaryValue}>{product.price}</span>
                  </div>
                </div>

                <div style={styles.whatsappNotice}>
                  <span style={styles.whatsappIcon}>📱</span>
                  <div>
                    <strong>Check your WhatsApp!</strong>
                    <p style={styles.whatsappSubtext}>
                      Team will respond within 5 minutes
                    </p>
                  </div>
                </div>
              </div>

              <button onClick={onClose} style={styles.doneBtn}>
                ✅ Done
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}

// ✅ Animations CSS
const animations = `
  @keyframes slideUpFade {
    from {
      opacity: 0;
      transform: translateY(50px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
  
  @keyframes overlayFade {
    from { opacity: 0; backdrop-filter: blur(0px); }
    to { opacity: 1; backdrop-filter: blur(8px); }
  }
  
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
  }
  
  @keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); opacity: 1; }
  }
  
  @keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  @keyframes glow {
    0%, 100% { box-shadow: 0 0 20px rgba(26, 108, 255, 0.4); }
    50% { box-shadow: 0 0 40px rgba(26, 108, 255, 0.8); }
  }
`;

// ✅ Beautiful Blue Theme Styles
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
    alignItems: 'center',
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
    maxWidth: '460px',
    maxHeight: '90vh',
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

  // Close Button
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
    transition: 'all 0.2s',
    backdropFilter: 'blur(10px)'
  },

  // Header
  header: {
    textAlign: 'center',
    marginBottom: '20px',
    paddingTop: '10px'
  },

  headerIcon: {
    fontSize: '3rem',
    marginBottom: '5px',
    display: 'inline-block',
    animation: 'bounceIn 0.6s ease-out'
  },

  title: {
    color: '#4d9fff',
    fontSize: '1.6rem',
    fontWeight: '700',
    margin: '0 0 5px 0',
    background: 'linear-gradient(135deg, #4d9fff, #1a6cff)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text'
  },

  subtitle: {
    color: '#7a85a0',
    fontSize: '0.85rem',
    margin: 0
  },

  // Product Card
  productCard: {
    display: 'flex',
    gap: '15px',
    marginBottom: '20px',
    padding: '15px',
    background: 'rgba(26, 108, 255, 0.08)',
    borderRadius: '14px',
    alignItems: 'center',
    border: '1px solid rgba(26, 108, 255, 0.2)',
    transition: 'transform 0.2s'
  },

  productImageWrap: {
    width: '80px',
    height: '80px',
    borderRadius: '12px',
    overflow: 'hidden',
    flexShrink: 0,
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(26, 108, 255, 0.3)'
  },

  productImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block'
  },

  productInfo: {
    flex: 1,
    minWidth: 0
  },

  productName: {
    margin: '0 0 8px 0',
    color: '#ffffff',
    fontSize: '0.95rem',
    fontWeight: '600',
    lineHeight: 1.3,
    wordBreak: 'break-word'
  },

  priceRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },

  priceMain: {
    color: '#4d9fff',
    fontWeight: 'bold',
    fontSize: '1.1rem'
  },

  advanceBadge: {
    background: 'rgba(16, 185, 129, 0.2)',
    color: '#10b981',
    padding: '3px 8px',
    borderRadius: '6px',
    fontSize: '0.75rem',
    fontWeight: '600',
    display: 'inline-block',
    width: 'fit-content',
    border: '1px solid rgba(16, 185, 129, 0.3)'
  },

  // Section
  section: {
    marginBottom: '16px'
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

  // Size Buttons
  sizeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '8px',
    width: '100%'
  },

  sizeBtn: {
    padding: '12px 4px',
    background: 'rgba(26, 108, 255, 0.1)',
    border: '2px solid rgba(26, 108, 255, 0.3)',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: '700',
    fontSize: '0.9rem',
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
    fontSize: '0.9rem',
    color: '#ffffff',
    textAlign: 'center',
    boxShadow: '0 0 20px rgba(26, 108, 255, 0.6)',
    transform: 'scale(1.05)',
    fontFamily: 'inherit'
  },

  // Input
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
    fontFamily: 'inherit',
    transition: 'border-color 0.2s'
  },

  // Phone Row
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

  // Submit Button
  submitBtn: {
    width: '100%',
    padding: '14px',
    background: 'linear-gradient(135deg, #1a6cff 0%, #004ecc 100%)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '12px',
    fontSize: '1rem',
    fontWeight: '700',
    cursor: 'pointer',
    marginTop: '10px',
    boxShadow: '0 6px 20px rgba(26, 108, 255, 0.4)',
    transition: 'all 0.2s',
    fontFamily: 'inherit',
    animation: 'glow 2s infinite'
  },

  submitBtnLoading: {
    opacity: 0.8,
    cursor: 'not-allowed',
    animation: 'none'
  },

  loadingContent: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px'
  },

  spinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#ffffff',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite'
  },

  // Success (Step 2)
  successContainer: {
    textAlign: 'center',
    padding: '10px 0'
  },

  successIcon: {
    fontSize: '4rem',
    marginBottom: '15px',
    animation: 'bounceIn 0.6s ease-out'
  },

  successTitle: {
    color: '#10b981',
    fontSize: '1.5rem',
    fontWeight: '700',
    margin: '0 0 10px 0'
  },

  successMessage: {
    color: '#ffffff',
    fontSize: '1.05rem',
    margin: '0 0 5px 0'
  },

  successSubtext: {
    color: '#7a85a0',
    fontSize: '0.9rem',
    margin: '0 0 20px 0'
  },

  summaryCard: {
    background: 'rgba(26, 108, 255, 0.08)',
    border: '1px solid rgba(26, 108, 255, 0.2)',
    padding: '15px',
    borderRadius: '12px',
    margin: '15px 0',
    textAlign: 'left'
  },

  summaryRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
  },

  summaryLabel: {
    color: '#7a85a0',
    fontSize: '0.85rem'
  },

  summaryValue: {
    color: '#ffffff',
    fontSize: '0.9rem',
    fontWeight: '600'
  },

  whatsappNotice: {
    background: 'rgba(37, 211, 102, 0.1)',
    border: '1px solid rgba(37, 211, 102, 0.3)',
    borderRadius: '10px',
    padding: '12px 15px',
    marginTop: '15px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    textAlign: 'left'
  },

  whatsappIcon: {
    fontSize: '1.5rem'
  },

  whatsappSubtext: {
    color: '#7a85a0',
    fontSize: '0.8rem',
    margin: '2px 0 0 0'
  },

  doneBtn: {
    width: '100%',
    padding: '14px',
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: '#ffffff',
    border: 'none',
    borderRadius: '12px',
    fontSize: '1rem',
    fontWeight: '700',
    cursor: 'pointer',
    marginTop: '15px',
    boxShadow: '0 6px 20px rgba(16, 185, 129, 0.4)',
    fontFamily: 'inherit'
  }
};

export default BookingModal;
