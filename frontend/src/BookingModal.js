import React, { useState } from 'react';

function BookingModal({ product, onClose }) {
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  // Price ಇಂದ ನಂಬರ್ ಮಾತ್ರ ತಗೆದು 50% ಅಡ್ವಾನ್ಸ್ ಲೆಕ್ಕ ಹಾಕುವ ಲಾಜಿಕ್
  const advanceAmount = Math.ceil(parseInt(product.price.replace(/[^\d]/g, '')) * 0.5) || 0;

  const handleBooking = async () => {
    if (!customerName || !phone || !selectedSize) {
      alert('⚠️ Please enter your Name, Phone and select a Size!');
      return;
    }

    setLoading(true);

    // 🟢 ಬ್ಯಾಕೆಂಡ್‌ನ Pydantic Model (BookingPayload) ಗೆ ಮ್ಯಾಚ್ ಆಗುವ ತರಹ ಡೇಟಾ ರೆಡಿ ಮಾಡಲಾಗಿದೆ
    const bookingData = {
      customer_name: customerName,
      customer_phone: phone, // ಇದು Green-API ಗೆ ಹೋಗುತ್ತೆ
      product_name: `${product.name} (Size: ${selectedSize})`, // ಸೈಜ್ ಅನ್ನು ಹೆಸರಿನ ಜೊತೆ ಸೇರಿಸಲಾಗಿದೆ
      image_url: product.image || ""
    };

    try {
      // 🔗 ನಿಮ್ಮ ಒರಿಜಿನಲ್ Render ಬ್ಯಾಕೆಂಡ್ ಲಿಂಕ್‌ಗೆ ಕನೆಕ್ಟ್ ಮಾಡಲಾಗಿದೆ ಜೀವನ್
      const response = await fetch('https://dolphin-trends.onrender.com/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData)
      });

      if (response.ok) {
        // ಬುಕಿಂಗ್ ಸಕ್ಸಸ್ ಆದ್ರೆ ಸ್ಟೆಪ್ 2 (ಪಾಪ್-ಅಪ್ ಮೆಸೇಜ್) ತೋರಿಸುತ್ತೆ
        setStep(2);
      } else {
        alert('❌ Booking failed. Please try again later.');
      }
    } catch (err) {
      console.error("Booking Error:", err);
      alert('❌ Server connection error! Please check your internet.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <button className="modal-close" onClick={onClose} disabled={loading}>✕</button>

        {step === 1 && (
          <>
            <h2>📦 Book Now</h2>

            <div className="modal-product">
              <img src={product.image} alt={product.name} />
              <div>
                <h3>{product.name}</h3>
                <p className="modal-price">{product.price}</p>
                <p className="advance-info">
                  💵 Advance: <strong>₹{advanceAmount}</strong> (50%)
                </p>
              </div>
            </div>

            {/* Size Select */}
            <div className="form-group">
              <label>📏 Select Size</label>
              <div className="size-options">
                {sizes.map(size => (
                  <button
                    key={size}
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
                placeholder="Enter your name"
                value={customerName}
                onChange={e => setCustomerName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>📱 WhatsApp Number</label>
              <input
                type="number"
                placeholder="Enter WhatsApp number (eg: 91...)"
                value={phone}
                onChange={e => setPhone(e.target.value)}
              />
            </div>

            <button className="submit-btn" onClick={handleBooking} disabled={loading}>
              {loading ? "Processing..." : "📲 Confirm & Send Request"}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2>⏳ Request Submitted!</h2>
            <div className="waiting-box" style={{ textAlign: 'center', padding: '20px 10px' }}>
              <p style={{ fontSize: '18px', color: '#28a745', fontWeight: 'bold' }}>
                🎉 Thank you, {customerName}!
              </p>
              <p style={{ marginTop: '10px', fontSize: '15px', color: '#333' }}>
                Your booking request has been successfully registered.
              </p>
              <p style={{ marginTop: '5px', fontSize: '14px', fontWeight: '500', color: '#007bff' }}>
                📱 Please check your WhatsApp! We have sent a waiting confirmation message to your number.
              </p>
              <br/>
              <p style={{ fontSize: '13px', color: '#666' }}>
                Our team will verify the store stock and update you with the final payment link within 5 minutes.
              </p>
            </div>
            <button className="confirm-btn" onClick={onClose} style={{ width: '100%', padding: '12px', background: '#007bff', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
              OK, Got it! 👍
            </button>
          </>
        )}

      </div>
    </div>
  );
}

export default BookingModal;
