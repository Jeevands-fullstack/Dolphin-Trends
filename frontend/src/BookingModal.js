import React, { useState } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function BookingModal({ product, onClose }) {
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  
  // ✅ ಎಲ್ಲಾ admin numbers array ನಲ್ಲಿ
  const adminPhones = [
    "917411255628",  // Admin 1
    "919353344035",  // Admin 2
    "919353838835"   // Admin 3 (ನಿಮ್ಮ 3rd admin)
  ];

  // ✅ Price calculation
  const priceNumber = parseInt((product.price || '0').replace(/[^\d]/g, '')) || 0;
  const advanceAmount = Math.ceil(priceNumber * 0.5);

  const handleBooking = async () => {
    // ✅ Validation
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
        // ✅ Customer WhatsApp message
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

        // ✅ Owner WhatsApp message - ಎಲ್ಲಾ admins ಗೆ
        const ownerMsg = `🛍️ *New Buy Request!*

👗 *Product:* ${product.name}
📏 *Size:* ${selectedSize}
💰 *Price:* ${product.price}
👤 *Name:* ${customerName}
📱 *Phone:* ${phone}

⚙️ *Admin Panel:*
🔗 https://dolphin-trends-two.vercel.app`;

        // ✅ Multiple admins ಗೆ WhatsApp open ಮಾಡಿ
        adminPhones.forEach((adminPhone, index) => {
          setTimeout(() => {
            window.open(
              "https://wa.me/" + adminPhone + "?text=" + encodeURIComponent(ownerMsg), 
              '_blank'
            );
          }, index * 1000); // 1 second gap between each
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
    <div className="modal-overlay" onClick={(e) => {
      if (e.target.className === 'modal-overlay' && !loading) onClose();
    }}>
      <div className="modal-box">
        <button 
          className="modal-close" 
          onClick={onClose} 
          disabled={loading}
        >
          ✕
        </button>

        {step === 1 && (
          <>
            <h2>📦 Book Now</h2>
            
            <div className="modal-product">
              <img src={product.image} alt={product.name} />
              <div>
                <h3>{product.name}</h3>
                <p className="modal-price">{product.price}</p>
                {advanceAmount > 0 && (
                  <p className="advance-info">
                    💵 Advance: <strong>₹{advanceAmount}</strong> (50%)
                  </p>
                )}
              </div>
            </div>

            <div className="form-group">
              <label>📏 Select Size</label>
              <div className="size-options">
                {sizes.map(size => (
                  <button
                    key={size}
                    type="button"
                    className={"size-btn " + (selectedSize === size ? 'selected' : '')}
                    onClick={() => setSelectedSize(size)}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>👤 Your Name</label>
              <input
                type="text"
                placeholder="Enter your full name"
                value={customerName}
                onChange={e => setCustomerName(e.target.value)}
                maxLength={50}
              />
            </div>

            <div className="form-group">
              <label>📱 WhatsApp Number</label>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <span style={{ padding: '8px 12px', background: '#f0f0f0', border: '1px solid #ddd', borderRight: 'none', borderRadius: '6px 0 0 6px' }}>
                  +91
                </span>
                <input
                  type="tel"
                  placeholder="10-digit number"
                  value={phone}
                  maxLength={10}
                  onChange={e => {
                    const value = e.target.value.replace(/\D/g, '');
                    setPhone(value);
                  }}
                  style={{ borderRadius: '0 6px 6px 0', flex: 1 }}
                />
              </div>
            </div>

            <button 
              className="submit-btn" 
              onClick={handleBooking} 
              disabled={loading}
            >
              {loading ? "⏳ Processing..." : "📲 Confirm & Send Request"}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2>⏳ Request Submitted!</h2>
            <div style={{ textAlign: 'center', padding: '20px 10px' }}>
              <div style={{ fontSize: '60px', marginBottom: '10px' }}>✅</div>
              <p style={{ fontSize: '20px', color: '#28a745', fontWeight: 'bold' }}>
                🎉 Thank you, {customerName}!
              </p>
              <p style={{ marginTop: '15px', fontSize: '15px', color: '#333' }}>
                Your booking request has been successfully registered.
              </p>
              <div style={{ 
                background: '#f8f9fa', 
                padding: '15px', 
                borderRadius: '8px', 
                marginTop: '20px',
                textAlign: 'left'
              }}>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>
                  👗 <strong>Product:</strong> {product.name}
                </p>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>
                  📏 <strong>Size:</strong> {selectedSize}
                </p>
                <p style={{ margin: '5px 0', fontSize: '14px' }}>
                  💰 <strong>Price:</strong> {product.price}
                </p>
              </div>
              <p style={{ marginTop: '20px', fontSize: '15px', fontWeight: '500', color: '#007bff' }}>
                📱 Please check your WhatsApp!
              </p>
              <p style={{ fontSize: '13px', color: '#666', marginTop: '10px' }}>
                ⏰ Our team will update you within 5 minutes.
              </p>
            </div>
            <button 
              onClick={onClose} 
              style={{ 
                width: '100%', 
                padding: '12px', 
                background: '#007bff', 
                color: '#fff', 
                border: 'none', 
                borderRadius: '6px', 
                cursor: 'pointer', 
                fontWeight: 'bold',
                fontSize: '16px'
              }}
            >
              OK, Got it! 👍
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default BookingModal;
