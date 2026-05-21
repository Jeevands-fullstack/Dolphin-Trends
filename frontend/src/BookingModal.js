import React, { useState } from 'react';

function BookingModal({ product, onClose }) {
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState('');
  const [step, setStep] = useState(1);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const advanceAmount = Math.ceil(parseInt(product.price.replace('₹', '')) * 0.5);

  const handleBooking = async () => {
    if (!customerName || !phone || !selectedSize) {
      alert('⚠️ Name, Phone ಮತ್ತು Size select ಮಾಡಿ!');
      return;
    }

    const bookingData = {
      customer_name: customerName,
      customer_phone: phone,
      size: selectedSize,
      product_name: product.name,
      product_price: product.price,
      advance_amount: advanceAmount,
      status: "Pending"
    };

    try {
      await fetch('https://dolphin-trends-3.onrender.com/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData)
      });
    } catch (err) {
      console.error(err);
    }

    const ownerPhone = "919353344035";
    const ownerMsg = "🛍 New Booking Request!\n\nProduct: " + product.name + "\nSize: " + selectedSize + "\nPrice: " + product.price + "\nAdvance: Rs." + advanceAmount + "\nCustomer: " + customerName + "\nPhone: " + phone + "\n\nPlease check Admin panel!";
    window.open("https://wa.me/" + ownerPhone + "?text=" + encodeURIComponent(ownerMsg), '_blank');

    setStep(2);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <button className="modal-close" onClick={onClose}>✕</button>

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
              <label>📱 Phone Number</label>
              <input
                type="number"
                placeholder="Enter phone number"
                value={phone}
                onChange={e => setPhone(e.target.value)}
              />
            </div>

            <button className="submit-btn" onClick={handleBooking}>
              📲 Send Booking Request
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2>⏳ Waiting for Confirmation</h2>
            <div className="waiting-box">
              <p>🎉 Your booking request has been sent!</p>
              <p>We will confirm shortly via WhatsApp.</p>
              <br/>
              <p>📱 Check your WhatsApp for updates!</p>
            </div>
            <button className="confirm-btn" onClick={onClose}>
              OK, Got it! 👍
            </button>
          </>
        )}

      </div>
    </div>
  );
}

export default BookingModal;
