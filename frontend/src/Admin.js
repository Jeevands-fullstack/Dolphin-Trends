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
    /* ⚡ ಇಡೀ ಪೇಜ್ ಕಂಟೇನರ್ - ಮಿನಿಮಮ್ ಹೈಟ್ ಕೊಟ್ಟು ಫೂಟರ್ ಕೆಳಗೆ ತಳ್ಳಲು ಫ್ಲೆಕ್ಸ್ ಮಾಡಲಾಗಿದೆ */
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: '#0b1329' }}>
      
      {/* ─── MAIN CONTENT AREA ─── */}
      <div className="admin-container" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', width: '100%', flex: '1' }}>
        
        {/* ⚡ ಲೇಔಟ್ ಈಗ ಪಕ್ಕಾ Column ಆಗಿದೆ, ಹಾಗಾಗಿ ಬುಕಿಂಗ್ ಲಿಸ್ಟ್ ಯಾವಾಗಲೂ ಕೆಳಗಡೆನೇ ಬರುತ್ತೆ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
          
          {/* ─── 👗 1. ಅಡ್ಮಿನ್ ಫಾರ್ಮ್ ಕಾರ್ಡ್ (ಮೇಲ್ಭಾಗ) ─── */}
          <div className="admin-card" style={{ width: '100%', boxSizing: 'border-box' }}>
            <h2>🛠️ Admin Panel - Add / Edit Product</h2>
            <div className="form-section">
              <div className="input-group" style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#fff' }}>👗 Dress Photo (ಹಳೇ ಪ್ರಾಡಕ್ಟ್ ಅಪ್ಡೇಟ್ ಮಾಡೋದಾದ್ರೆ ಫೋಟೋ ಬೇಡ)</label>
                <input type="file" accept="image/*" ref={fileInputRef} onChange={handleImageChange} className="file-input" style={{ width: '100%' }} />
                {preview && (
                  <div className="image-preview">
                    <img src={preview} alt="Preview" style={{width: '100px', marginTop: '10px', borderRadius: '8px'}} />
                  </div>
                )}
              </div>

              <div className="input-group" style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#fff' }}>Product Name (ಇಲ್ಲಿ ಹಳೇ ಹೆಸರು ಹೊಡೆದರೆ ಅಪ್ಡೇಟ್ ಆಗುತ್ತೆ)</label>
                <input type="text" placeholder="eg: Silk Saree" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
              </div>

              <div className="input-group" style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#fff' }}>Description</label>
                <textarea placeholder="Enter product details..." rows="3" value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
              </div>

              <div className="input-row" style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
                <div className="input-group" style={{ flex: '1' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#fff' }}>Selling Price (₹)</label>
                  <input type="number" placeholder="Selling Price" value={formData.price} onChange={(e) => setFormData({...formData, price: e.target.value})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>
                <div className="input-group" style={{ flex: '1' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#fff' }}>Original Price (₹)</label>
                  <input type="number" placeholder="Original Price" value={formData.original_price} onChange={(e) => setFormData({...formData, original_price: e.target.value})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>
              </div>

              <div className="input-group" style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#fff' }}>Category</label>
                <select value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} style={{ width: '100%', padding: '8px' }}>
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

              <button className="add-btn" onClick={handleAddOrUpdateProduct} disabled={loading} style={{ background: '#007bff', color: 'white', padding: '12px', width: '100%', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' }}>
                {loading ? "Saving/Updating..." : "✅ Save Product"}
              </button>
            </div>
          </div>

          {/* ─── 📥 2. ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಕಾರ್ಡ್ (ಕಾಲಂ ಆಗಿರುವುದರಿಂದ ಇದು ಪಕ್ಕಾ ಕೆಳಗೆ ಬರುತ್ತೆ) ─── */}
          <div className="admin-card" style={{ width: '100%', boxSizing: 'border-box' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ color: '#fff', margin: 0 }}>📥 Customer Bookings List</h2>
              <button onClick={fetchBookings} style={{ padding: '6px 12px', cursor: 'pointer', borderRadius: '4px', background: '#007bff', color: 'white', border: 'none' }}>🔄 Refresh</button>
            </div>

            {bookingsLoading ? (
              <p style={{ color: '#fff' }}>ಬುಕಿಂಗ್ಸ್ ಲೋಡ್ ಆಗುತ್ತಿದೆ ಜೀವನ್...</p>
            ) : (
              <div style={{ overflowX: 'auto', background: '#1e293b', borderRadius: '8px', padding: '10px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
                  <thead>
                    <tr style={{ background: '#334155', borderBottom: '2px solid #475569', color: '#fff' }}>
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
                        <td colSpan="5" style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>ಯಾವ ಬುಕಿಂಗ್ಸ್ ಬಂದಿಲ್ಲ ಜೀವನ್!</td>
                      </tr>
                    ) : (
                      bookings.map((b) => (
                        <tr key={b.booking_id} style={{ borderBottom: '1px solid #334155', color: '#fff' }}>
                          <td style={{ padding: '12px' }}><b style={{ color: '#38bdf8' }}>{b.customer_name}</b></td>
                          <td style={{ padding: '12px' }}>{b.customer_phone}</td>
                          <td style={{ padding: '12px' }}>{b.product_name}</td>
                          <td style={{ padding: '12px', fontWeight: 'bold', color: b.status === 'Pending' ? '#f59e0b' : '#10b981' }}>{b.status}</td>
                          <td style={{ padding: '12px' }}>
                            {b.status === 'Pending' && (
                              <div style={{ display: 'flex', gap: '5px' }}>
                                <button onClick={() => handleBookingAction(b.booking_id, 'agree', b.customer_name)} style={{ background: '#28a745', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Agree</button>
                                <button onClick={() => handleBookingAction(b.booking_id, 'disagree', b.customer_name)} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Disagree</button>
                              </div>
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
      </div>

      {/* ─── 🗺️ 3. FOOTER SECTION (ಯಾವಾಗಲೂ ಇಡೀ ಸ್ಕ್ರೀನ್‌ನ ತೀರಾ ಕೆಳಗೆ ಇರುತ್ತದೆ) ─── */}
      <footer style={{ background: '#020617', color: '#94a3b8', padding: '20px', textAlign: 'center', borderTop: '1px solid #1e293b', width: '100%', marginTop: 'auto' }}>
        <p style={{ margin: '5px 0', color: '#38bdf8', fontWeight: 'bold' }}>🐬 Dolphin Trends | Women's Fashion Store | Bangalore</p>
        <p style={{ margin: '5px 0', fontSize: '14px' }}>📍 Laggere Main Road, Bangalore — 560058</p>
        <p style={{ margin: '5px 0', fontSize: '14px' }}>📞 +91 7411255628 | 💻 Developer by Jeevan JD</p>
      </footer>

    </div>
  );
}

export default Admin;           
