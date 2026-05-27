import React, { useState, useRef, useEffect } from 'react';

function Admin({ onProductAdded }) {
  // ─── 📦 ಸಿಂಪಲ್ ಫಾರ್ಮ್ ಸ್ಟೇಟ್ಸ್ ───
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

  // ─── 📋 ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಸ್ಟೇಟ್ಸ್ ───
  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);

  useEffect(() => {
    fetchBookings();
  }, []);

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

  const handleBookingAction = async (bookingId, action, customerName) => {
    let actionText = action === 'agree' ? "AGREE" : "DISAGREE";
    if (!window.confirm(`Jeevan, do you want to ${actionText} this order?`)) return;

    try {
      const response = await fetch(`https://dolphin-trends-3.onrender.com/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, {
        method: 'POST',
      });
      if (response.ok) {
        alert(`✅ Action successful!`);
        fetchBookings();
      } else {
        alert("❌ Failed to update backend.");
      }
    } catch (error) {
      alert("❌ Server Error!");
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
    }
  };

  // ⚡ 💾 SAVE / UPDATE PRODUCT FUNCTION (BY NAME MATCHING)
  const handleAddOrUpdateProduct = async () => {
    if (!formData.name || !formData.price) {
      alert("⚠️ ದಯವಿಟ್ಟು ಪ್ರಾಡಕ್ಟ್ ಹೆಸರು ಮತ್ತು ಮಾರಾಟದ ಬೆಲೆಯನ್ನು ನಮೂದಿಸಿ!");
      return;
    }

    setLoading(true);
    const file = fileInputRef.current?.files[0];

    const dataToSend = new FormData();
    dataToSend.append('name', formData.name);
    dataToSend.append('price', formData.price.startsWith('₹') ? formData.price : `₹${formData.price}`);
    dataToSend.append('original_price', formData.original_price ? (formData.original_price.startsWith('₹') ? formData.original_price : `₹${formData.original_price}`) : "");
    dataToSend.append('description', formData.description);
    dataToSend.append('category', formData.category);
    if (file) {
      dataToSend.append('file', file);
    }

    try {
      // 🎯 We send everything to a smart upload-or-update endpoint
      const response = await fetch('https://dolphin-trends-3.onrender.com/products', {
        method: 'POST',
        body: dataToSend,
      });

      if (response.ok) {
        const result = await response.json();
        if (result.action === "updated") {
          alert("🔄 ಹಳೇ ಪ್ರಾಡಕ್ಟ್ ಬೆಲೆ/ವಿವರಗಳು ಯಶಸ್ವಿಯಾಗಿ ಅಪ್ಡೇಟ್ ಆಗಿದೆ ಜೀವನ್!");
        } else {
          alert("✅ ಹೊಸ Product ಯಶಸ್ವಿಯಾಗಿ ಸೇವ್ ಆಗಿದೆ!");
        }
        
        setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
        setPreview(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        if (onProductAdded) onProductAdded();
      } else {
        alert("❌ ಸೇವ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ! ಬ್ಯಾಕೆಂಡ್ ಚೆಕ್ ಮಾಡಿ.");
      }
    } catch (error) {
      alert("❌ ಸರ್ವರ್ ಕನೆಕ್ಷನ್ ಎರರ್!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-container" style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* ─── 👗 ಸಿಂಪಲ್ ಫಾರ್ಮ್ ಡಿಸೈನ್ ─── */}
      <div className="admin-card" style={{ marginBottom: '40px' }}>
        <h2>🛠️ Admin Panel - Add / Edit Product</h2>
        <div className="form-section">
          <div className="input-group">
            <label>👗 Dress Photo (ಹಳೇ ಪ್ರಾಡಕ್ಟ್ ಅಪ್ಡೇಟ್ ಮಾಡೋದಾದ್ರೆ ಫೋಟೋ ಬೇಡ)</label>
            <input type="file" accept="image/*" ref={fileInputRef} onChange={handleImageChange} className="file-input" />
            {preview && (
              <div className="image-preview">
                <img src={preview} alt="Preview" style={{width: '100px', marginTop: '10px', borderRadius: '8px'}} />
              </div>
            )}
          </div>

          <div className="input-group">
            <label>Product Name (ಇಲ್ಲಿ ಹಳೇ ಹೆಸರು ಹೊಡೆದರೆ ಅಪ್ಡೇಟ್ ಆಗುತ್ತೆ)</label>
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

          <button className="add-btn" onClick={handleAddOrUpdateProduct} disabled={loading} style={{ background: '#007bff', color: 'white', padding: '10px', width: '100%', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            {loading ? "Saving/Updating..." : "✅ Save Product"}
          </button>
        </div>
      </div>

      <hr style={{ border: '1px solid #ddd', margin: '40px 0' }} />

      {/* ─── 📥 ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಟೇಬಲ್ ─── */}
      <div className="admin-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
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
                  <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {bookings.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '20px', textAlign: 'center', color: 'gray' }}>ಯಾವ ಬುಕಿಂಗ್ಸ್ ಬಂದಿಲ್ಲ ಜೀವನ್!</td>
                  </tr>
                ) : (
                  bookings.map((b) => (
                    <tr key={b.booking_id} style={{ borderBottom: '1px solid #ddd' }}>
                      <td style={{ padding: '12px' }}><b>{b.customer_name}</b></td>
                      <td style={{ padding: '12px' }}>{b.customer_phone}</td>
                      <td style={{ padding: '12px' }}>{b.product_name}</td>
                      <td style={{ padding: '12px' }}>{b.status}</td>
                      <td style={{ padding: '12px' }}>
                        {b.status === 'Pending' && (
                          <>
                            <button onClick={() => handleBookingAction(b.booking_id, 'agree', b.customer_name)} style={{ background: '#28a745', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '8px' }}>Agree</button>
                            <button onClick={() => handleBookingAction(b.booking_id, 'disagree', b.customer_name)} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Disagree</button>
                          </>
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
