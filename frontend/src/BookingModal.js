import React, { useState } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function BookingModal({ product, onClose }) {
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const advanceAmount = Math.ceil(parseInt(product.price.replace(/[^\d]/g, '')) * 0.5) || 0;
  const ownerPhone = "919353838835";

  const handleBooking = async () => {
    if (!customerName || !phone || !selectedSize) {
      alert('⚠️ Please enter your Name, Phone and select a Size!');
      return;
    }

    setLoading(true);

    const bookingData = {
      customer_name: customerName,
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
        const customerMsg = "🎉 *Welcome to Dolphin Trends!* 🐬\n\nHi " + customerName + ",\n\nYou have selected:\n👗 *" + product.name + "*\n📏 Size: " + selectedSize + "\n💰 Price: " + product.price + "\n\n📝 *We are checking stock availability. Our team will contact you shortly.* 🙏\n\n💥 *Explore collections:*\n🔗 https://dolphin-trends-two.vercel.app\n\n📞 Contact: 7411255628\n\nThank you! 😊\n*Team Dolphin Trends* 🐬";
        window.open("https://wa.me/91" + phone + "?text=" + encodeURIComponent(customerMsg), '_blank');

        const ownerMsg = "🛍️ *New Buy Request!*\n\n👗 " + product.name + "\n📏 Size: " + selectedSize + "\n💰 " + product.price + "\n👤 " + customerName + "\n📱 " + phone + "\n\n⚙️ *Admin Panel:*\n🔗 https://dolphin-trends-two.vercel.app";
        window.open("https://wa.me/" + ownerPhone + "?text=" + encodeURIComponent(ownerMsg), '_blank');

        setStep(2);
      } else {
        alert('❌ Booking failed. Please try again.');
      }
    } catch (err) {
      console.error("Booking Error:", err);
      alert('❌ Server connection error!');
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
                <p className="advance-info">💵 Advance: <strong>₹{advanceAmount}</strong> (50%)</p>
              </div>
            </div>

            <div className="form-group">
              <label>📏 Select Size</label>
              <div className="size-options">
                {sizes.map(size => (
                  <button key={size} className={"size-btn " + (selectedSize === size ? 'selected' : '')} onClick={() => setSelectedSize(size)}>{size}</button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>👤 Your Name</label>
              <input type="text" placeholder="Enter your name" value={customerName} onChange={e => setCustomerName(e.target.value)} />
            </div>

            <div className="form-group">
              <label>📱 WhatsApp Number</label>
              <input type="number" placeholder="Enter WhatsApp number" value={phone} onChange={e => setPhone(e.target.value)} />
            </div>

            <button className="submit-btn" onClick={handleBooking} disabled={loading}>
              {loading ? "Processing..." : "📲 Confirm & Send Request"}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2>⏳ Request Submitted!</h2>
            <div style={{ textAlign: 'center', padding: '20px 10px' }}>
              <p style={{ fontSize: '18px', color: '#28a745', fontWeight: 'bold' }}>🎉 Thank you, {customerName}!</p>
              <p style={{ marginTop: '10px', fontSize: '15px' }}>Your booking request has been successfully registered.</p>
              <p style={{ marginTop: '5px', fontSize: '14px', fontWeight: '500', color: '#007bff' }}>📱 Please check your WhatsApp!</p>
              <p style={{ fontSize: '13px', color: '#666', marginTop: '10px' }}>Our team will update you within 5 minutes.</p>
            </div>
            <button onClick={onClose} style={{ width: '100%', padding: '12px', background: '#007bff', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
              OK, Got it! 👍
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default BookingModal;
