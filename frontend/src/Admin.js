import React, { useState, useRef, useEffect } from 'react';

function Admin({ onProductAdded }) {
  // ─── 📦 1. ಪ್ರಾಡಕ್ಟ್ ಆಡ್ ಮಾಡೋ ಸ್ಟೇಟ್ಸ್ ───
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    original_price: '',
    category: 'Tops'
  });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  // ─── 📋 2. ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಮ್ಯಾನೇಜ್ ಮಾಡೋ ಹೊಸ ಸ್ಟೇಟ್ಸ್ ───
  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);

  // ವೆಬ್‌ಸೈಟ್ ಓಪನ್ ಆದಾಗ ಬುಕಿಂಗ್ಸ್ ಲೋಡ್ ಮಾಡೋಕೆ useEffect
  useEffect(() => {
    fetchBookings();
  }, []);

  // 📥 ಬ್ಯಾಕೆಂಡ್‌ನಿಂದ ಬುಕಿಂಗ್ಸ್ ಡೇಟಾ ತರೋ ಫಂಕ್ಷನ್
  const fetchBookings = async () => {
    setBookingsLoading(true);
    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/api/admin/bookings');
      if (response.ok) {
        const data = await response.json();
        setBookings(data);
      }
    } catch (error) {
      console.error("Error fetching bookings:", error);
    } finally {
      setBookingsLoading(false);
    }
  };

  // ⚡ Agree / Disagree ಕ್ಲಿಕ್ ಮಾಡಿದಾಗ ರನ್ ಆಗೋ ಡಬಲ್ ಕನ್‌ಫರ್ಮ್ ಮ್ಯಾಜಿಕ್
const handleBookingAction = async (bookingId, action, customerName, customerPhone, productName, productPrice) => {
  let actionText = action === 'agree' ? "AGREE" : "DISAGREE";
  if (!window.confirm(`Jeevan, do you want to ${actionText} this order?`)) return;

  try {
    // Backend update row
    const response = await fetch(`https://dolphin-trends.onrender.com/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, {
      method: 'POST',
    });

    if (response.ok) {
      // ✅ 'Agree' kottaga Green-API moolaka Customer ge message hogutthe
      if (action === 'agree') {
        const messageToSend = 
          `Hello ${customerName},\n\n` +
          `Great news! The product you selected (*${productName}*) is AVAILABLE! 🎉\n\n` +
          `💰 *Price:* ${productPrice}\n\n` +
          `📍 *Shop Location:* https://maps.google.com/?q=Dolphin+Trends+Laggere\n` +
          `🏪 *Main Branch Address:* Anikethana Kishore Kendra Laggere, Bangalore - 560058\n\n` +
          `✨ *Next Steps:*\n` +
          `• If you really love this product, you can pay a small advance amount to secure and confirm your order book.\n` +
          `• Otherwise, you can just ignore this message and directly visit our shop to explore more designs!\n\n` +
          `We look forward to serving you!\n` +
          `Best regards,\n` +
          `Dolphin Trends 🐬`;

        // Green-API request to send WhatsApp to customer
        await fetch(`https://api.green-api.com/waInstanceYOUR_INSTANCE_ID/sendMessage/YOUR_API_TOKEN`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chatId: `${customerPhone}@c.us`,
            message: messageToSend
          })
        });
      }

      alert(`✅ Action successful! Notification processed.`);
      fetchBookings();
    } else {
      alert("❌ Failed to update backend.");
    }
  } catch (error) {
    alert("❌ Server Error!");
  }
};

  // ಇಮೇಜ್ ಪ್ರಿವ್ಯೂ ಚೇಂಜ್ ಹ್ಯಾಂಡ್ಲರ್
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
    }
  };

  // ಪ್ರಾಡಕ್ಟ್ ಆಡ್ ಮಾಡೋ ಒರಿಜಿನಲ್ ಫಂಕ್ಷನ್
  const handleAddProduct = async () => {
    const file = fileInputRef.current.files[0];

    if (!formData.name || !formData.price || !file) {
      alert("⚠️ ದಯವಿಟ್ಟು ಫೋಟೋ, ಹೆಸರು ಮತ್ತು ಮಾರಾಟದ ಬೆಲೆಯನ್ನು ನಮೂದಿಸಿ!");
      return;
    }

    setLoading(true);

    const dataToSend = new FormData();
    dataToSend.append('name', formData.name);
    dataToSend.append('price', `₹${formData.price}`);
    dataToSend.append('original_price', formData.original_price ? `₹${formData.original_price}` : "");
    dataToSend.append('description', formData.description);
    dataToSend.append('category', formData.category);
    dataToSend.append('file', file);

    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/products', {
        method: 'POST',
        body: dataToSend,
      });

      if (response.ok) {
        alert("✅ Product ಯಶಸ್ವಿಯಾಗಿ ಸೇವ್ ಆಗಿದೆ!");
        setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
        setPreview(null);
        fileInputRef.current.value = "";
        if (onProductAdded) onProductAdded();
      } else {
        alert("❌ ಸೇವ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ! ಬ್ಯಾಕೆಂಡ್ ಚೆಕ್ ಮಾಡಿ.");
      }
    } catch (error) {
      alert("❌ ಸರ್ವರ್ ಕನೆಕ್ಷನ್ ಎರರ್! Backend run ಆಗುತ್ತಿದೆಯೇ ನೋಡಿ.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-container" style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* ─── 👗 ಸೆಕ್ಷನ್ 1: ಆಡ್ ಪ್ರಾಡಕ್ಟ್ ಫಾರ್ಮ್ ─── */}
      <div className="admin-card" style={{ marginBottom: '40px' }}>
        <h2>🛠️ Admin Panel - Add Product</h2>
        <div className="form-section">
          <div className="input-group">
            <label>👗 Dress Photo</label>
            <input type="file" accept="image/*" ref={fileInputRef} onChange={handleImageChange} className="file-input" />
            {preview && (
              <div className="image-preview">
                <img src={preview} alt="Preview" style={{width: '100px', marginTop: '10px', borderRadius: '8px'}} />
              </div>
            )}
          </div>

          <div className="input-group">
            <label>Product Name</label>
            <input type="text" placeholder="eg: Silk Saree" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
          </div>

          <div className="input-group">
            <label>Description</label>
            <textarea placeholder="Enter product details..." rows="3" value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} />
          </div>

          <div className="input-row">
            <div className="input-group">
              <label>Selling Price (₹)</label>
              <input type="number" placeholder="Selling Price" value={formData.price} onChange={(e) => setFormData({...formData, price: e.target.value})} />
            </div>
            <div className="input-group">
              <label>Original Price (₹)</label>
              <input type="number" placeholder="Original Price" value={formData.original_price} onChange={(e) => setFormData({...formData, original_price: e.target.value})} />
            </div>
          </div>

          <div className="input-group">
            <label>Category</label>
            <select value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
              <option value="Tops">Tops</option>
              <option value="Kurthas Sets">Kurthas Sets</option>
              <option value="Jeans">Jeans</option>
              <option value="Umbrella Sets">Umbrella Sets</option>
              <option value="Western wear">Western wear</option>
              <option value="250 Tops">250 Tops</option>
              <option value="Kurtha Tops">Kurtha Tops</option>
              <option value="Jeans Tops">Jeans Tops</option>
              <option value="Leggins">Leggins</option>
              <option value="350 Sets">350 Sets</option>
              <option value="frocks">frocks</option>
            </select>
          </div>

          <button className="add-btn" onClick={handleAddProduct} disabled={loading}>
            {loading ? "Saving..." : "✅ Add Product"}
          </button>
        </div>
      </div>

      <hr style={{ border: '1px solid #ddd', margin: '40px 0' }} />

      {/* ─── 📥 ಸೆಕ್ಷನ್ 2: ಹೊಸ ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಟೇಬಲ್ ─── */}
      <div className="admin-card">
        <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>📥 Customer Bookings List</h2>
          <button onClick={fetchBookings} style={{ padding: '6px 12px', cursor: 'pointer', borderRadius: '4px', background: '#007bff', color: 'white', border: 'none' }}>🔄 Refresh</button>
        </div>

        {bookingsLoading ? (
          <p>ಬುಕಿಂಗ್ಸ್ ಲೋಡ್ ಆಗುತ್ತಿದೆ ಜೀವನ್...</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
              <thead>
                <tr style={{ background: '#f4f4f4', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Customer Name</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Phone</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Product Name</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Photo</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {bookings.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ padding: '20px', textAlign: 'center', color: 'gray' }}>ಯಾವ ಬುಕಿಂಗ್ಸ್ ಬಂದಿಲ್ಲ ಜೀವನ್!</td>
                  </tr>
                ) : (
                  bookings.map((b) => (
                    <tr key={b.booking_id} style={{ borderBottom: '1px solid #ddd' }}>
                      <td style={{ padding: '12px' }}><b>{b.customer_name}</b></td>
                      <td style={{ padding: '12px' }}>{b.customer_phone}</td>
                      <td style={{ padding: '12px' }}>{b.product_name}</td>
                      <td style={{ padding: '12px' }}>
                        <a href={b.image_url} target="_blank" rel="noreferrer">View 📸</a>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px', 
                          borderRadius: '4px', 
                          fontSize: '12px',
                          fontWeight: 'bold',
                          background: b.status === 'Pending' ? '#ffeaa7' : b.status === 'Approved-WaitingPayment' ? '#ffe0b2' : '#dfe6e9',
                          color: b.status === 'Pending' ? '#d63031' : b.status === 'Approved-WaitingPayment' ? '#e65100' : '#2d3436'
                        }}>
                          {b.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        {b.status === 'Pending' ? (
                          <>
                            <button 
                              onClick={() => handleBookingAction(b.booking_id, 'agree', b.customer_name)}
                              style={{ background: '#28a745', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '8px', fontWeight: 'bold' }}
                            >
                              Agree
                            </button>
                            <button 
                              onClick={() => handleBookingAction(b.booking_id, 'disagree', b.customer_name)}
                              style={{ background: '#dc3545', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                            >
                              Disagree
                            </button>
                          </>
                        ) : b.status === 'Approved-WaitingPayment' ? (
                          <span style={{ color: '#e65100', fontWeight: 'bold', fontSize: '14px' }}>Waiting Payment ⏳</span>
                        ) : (
                          <span style={{ color: 'gray' }}>Done</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}

export default Admin;
