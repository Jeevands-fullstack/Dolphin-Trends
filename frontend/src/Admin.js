import React, { useState, useRef, useEffect } from 'react';

// App.js ನಿಂದ products ಮತ್ತು fetchProducts (onProductAdded) ಎರಡನ್ನೂ ತಗೋತಿದ್ದೀವಿ
function Admin({ onProductAdded, products = [] }) {
  const [formData, setFormData] = useState({
    name: '', description: '', price: '', original_price: '', category: 'Tops'
  });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editingProductId, setEditingProductId] = useState(null); // Edit ಟ್ರ್ಯಾಕ್ ಮಾಡಲು
  
  const fileInputRef = useRef(null);
  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);

  useEffect(() => { fetchBookings(); }, []);

  const fetchBookings = async () => {
    setBookingsLoading(true);
    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/api/admin/bookings');
      if (response.ok) setBookings(await response.json());
    } catch (e) { console.error(e); }
    finally { setBookingsLoading(false); }
  };

  const handleBookingAction = async (bookingId, action) => {
    if (!window.confirm(`${action === 'agree' ? 'AGREE' : 'DISAGREE'} ಮಾಡಬೇಕಾ?`)) return;
    try {
      const r = await fetch(`https://dolphin-trends-3.onrender.com/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, { method: 'POST' });
      if (r.ok) { alert('✅ Done!'); fetchBookings(); }
      else alert('❌ Failed');
    } catch { alert('❌ Server Error'); }
  };

  // 📝 EDIT ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿದಾಗ ಫಾರ್ಮ್‌ಗೆ ಡೇಟಾ ತುಂಬಲು
  const startEdit = (product) => {
    setEditingProductId(product.product_id || product.id);
    setFormData({
      name: product.name,
      description: product.description || '',
      price: product.price.replace('₹', ''), // ₹ ಸಿಂಬಲ್ ತೆಗೆದು ಬರಿ ನಂಬರ್ ಹಾಕಲು
      original_price: product.original_price ? product.original_price.replace('₹', '') : '',
      category: product.category
    });
    setPreview(product.image); // ಹಳೇ ಫೋಟೋ ಪ್ರಿವ್ಯೂ ತೋರಿಸು
    window.scrollTo({ top: 0, behavior: 'smooth' }); // ಸ್ಕ್ರೀನ್ ಮೇಲೆ ಮೂವ್ ಮಾಡಿ ಫಾರ್ಮ್ ತೋರಿಸಲು
  };

  // ❌ DELETE ಫಂಕ್ಷನ್
  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('⚠️ ನೀವು ಖಚಿತವಾಗಿ ಈ ಪ್ರಾಡಕ್ಟ್ ಅನ್ನು ಡಿಲೀಟ್ ಮಾಡಲು ಬಯಸುತ್ತೀರಾ?')) return;
    try {
      const r = await fetch(`https://dolphin-trends-3.onrender.com/products/${productId}`, {
        method: 'DELETE'
      });
      if (r.ok) {
        alert('🗑️ Product Deleted Successfully!');
        if (onProductAdded) onProductAdded(); // ಲಿಸ್ಟ್ ರಿಫ್ರೆಶ್ ಮಾಡಲು
      } else {
        alert('❌ Delete failed!');
      }
    } catch {
      alert('❌ Server Error while deleting!');
    }
  };

  const handleAddOrUpdateProduct = async () => {
    if (!formData.name || !formData.price) { alert('⚠️ Name ಮತ್ತು Price ಹಾಕಿ!'); return; }
    setLoading(true);
    const file = fileInputRef.current?.files[0];
    const dataToSend = new FormData();
    dataToSend.append('name', formData.name);
    dataToSend.append('price', formData.price.startsWith('₹') ? formData.price : `₹${formData.price}`);
    dataToSend.append('original_price', formData.original_price ? (formData.original_price.startsWith('₹') ? formData.original_price : `₹${formData.original_price}`) : '');
    dataToSend.append('description', formData.description);
    dataToSend.append('category', formData.category);
    if (file) dataToSend.append('file', file);

    // ಎಡಿಟ್ ಮೋಡ್ ನಲ್ಲಿದ್ದರೆ ಅದೇ ID ಗೆ PUT/POST ಮಾಡಬೇಕು (ನಿಮ್ಮ ಬ್ಯಾಕೆಂಡ್ ರೌಟ್ ಪ್ರಕಾರ)
    let url = 'https://dolphin-trends-3.onrender.com/products';
    let method = 'POST';
    if (editingProductId) {
      url = `https://dolphin-trends-3.onrender.com/products/${editingProductId}`;
      method = 'PUT'; // ಒಂದು ವೇಳೆ ನಿಮ್ಮ ಬ್ಯಾಕೆಂಡ್ PUT ಸಪೋರ್ಟ್ ಮಾಡಿದ್ರೆ, ಇಲ್ಲದಿದ್ದರೆ POST ಬಳಸಿ
    }

    try {
      const r = await fetch(url, { method: method, body: dataToSend });
      if (r.ok) {
        alert(editingProductId ? '🔄 Product updated!' : '✅ Product saved!');
        cancelEdit();
        if (onProductAdded) onProductAdded();
      } else alert('❌ Save failed!');
    } catch { alert('❌ Server Error!'); }
    finally { setLoading(false); }
  };

  const cancelEdit = () => {
    setEditingProductId(null);
    setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
    setPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div style={{ background: '#0b1329', padding: '20px', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>

        {/* Product Form */}
        <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px', marginBottom: '30px' }}>
          <h2 style={{ color: '#4d9fff', marginBottom: '20px' }}>
            {editingProductId ? '🔄 Edit Product Mode' : '🛠️ Admin Panel - Add Product'}
          </h2>

          <label style={lbl}>👗 Dress Photo {editingProductId && '(ಬದಲಾಯಿಸಬೇಕಿದ್ದರೆ ಮಾತ್ರ ಫೈಲ್ ಸೆಲೆಕ್ಟ್ ಮಾಡಿ)'}</label>
          <input type="file" accept="image/*" ref={fileInputRef} onChange={e => { const f = e.target.files[0]; if (f) setPreview(URL.createObjectURL(f)); }} style={{ width: '100%', marginBottom: '15px', color: '#fff' }} />
          {preview && <img src={preview} alt="preview" style={{ width: '100px', borderRadius: '8px', marginBottom: '15px' }} />}

          <label style={lbl}>Product Name</label>
          <input style={inp} placeholder="eg: Silk Kurti" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />

          <label style={lbl}>Description</label>
          <textarea style={{ ...inp, height: '80px', resize: 'vertical' }} placeholder="Product details..." value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} />

          <div style={{ display: 'flex', gap: '15px' }}>
            <div style={{ flex: 1 }}>
              <label style={lbl}>Selling Price (₹)</label>
              <input style={inp} type="number" placeholder="500" value={formData.price} onChange={e => setFormData({ ...formData, price: e.target.value })} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={lbl}>Original Price (₹)</label>
              <input style={inp} type="number" placeholder="800" value={formData.original_price} onChange={e => setFormData({ ...formData, original_price: e.target.value })} />
            </div>
          </div>

          <label style={lbl}>Category</label>
          <select style={inp} value={formData.category} onChange={e => setFormData({ ...formData, category: e.target.value })}>
            {['Tops','Kurthas Sets','Jeans','Umbrella Sets','Western wear','250 Tops','Kurtha Tops','Jeans Tops','Leggins','350 Sets','Frocks','Gym Pants','Patiala Pants'].map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button onClick={handleAddOrUpdateProduct} disabled={loading}
              style={{ flex: 2, padding: '14px', background: editingProductId ? '#e11d48' : '#1a6cff', color: '#fff', border: 'none', borderRadius: '10px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer' }}>
              {loading ? 'Saving...' : editingProductId ? '🔄 Update Product' : '✅ Save Product'}
            </button>
            {editingProductId && (
              <button onClick={cancelEdit} style={{ flex: 1, padding: '14px', background: '#4b5563', color: '#fff', border: 'none', borderRadius: '10px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer' }}>
                Cancel
              </button>
            )}
          </div>
        </div>

        {/* 🛍️ ಹೊಸದಾಗಿ ಆಡ್ ಮಾಡಲಾದ ಸೆಕ್ಷನ್: MANAGE & DELETE PRODUCTS LIST */}
        <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px', marginBottom: '30px' }}>
          <h2 style={{ color: '#4d9fff', marginBottom: '20px' }}>📦 Active Products ({products.length})</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(26,108,255,0.3)', color: '#4d9fff', fontSize: '0.85rem' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Image</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Product Details</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Category</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.length === 0 ? (
                  <tr><td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#7a85a0' }}>ಯಾವ ಪ್ರೋಡಕ್ಟ್ ಸಿಗುತ್ತಿಲ್ಲ!</td></tr>
                ) : products.map(p => (
                  <tr key={p.product_id || p.id} style={{ borderBottom: '1px solid rgba(26,108,255,0.1)', color: '#f0f4ff' }}>
                    <td style={{ padding: '12px' }}>
                      <img src={p.image} alt="" style={{ width: '50px', height: '60px', objectFit: 'cover', borderRadius: '6px' }} onError={e => e.target.src='https://via.placeholder.com/50'} />
                    </td>
                    <td style={{ padding: '12px' }}>
                      <div style={{ fontWeight: 'bold' }}>{p.name}</div>
                      <div style={{ color: '#38bdf8', fontSize: '0.85rem' }}>Price: {p.price}</div>
                    </td>
                    <td style={{ padding: '12px' }}><span style={{ background: 'rgba(26,108,255,0.15)', color: '#4d9fff', padding: '3px 8px', borderRadius: '6px', fontSize: '0.8rem' }}>{p.category}</span></td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        <button onClick={() => startEdit(p)} style={{ padding: '6px 12px', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>✏️ Edit</button>
                        <button onClick={() => handleDeleteProduct(p.product_id || p.id)} style={{ padding: '6px 12px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}>🗑️ Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bookings Table */}
        <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px' }}>
          <div style={{ display: 'flex', justifycontent: 'space-between', alignitems: 'center', marginbottom: '20px' }}>
            <h2 style={{ color: '#4d9fff', margin: 0 }}>📥 Customer Bookings</h2>
            <button onClick={fetchBookings} style={{ padding: '8px 16px', background: '#1a6cff', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>🔄 Refresh</button>
          </div>

          {bookingsLoading ? <p style={{ color: '#7a85a0' }}>Loading...</p> : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(26,108,255,0.3)' }}>
                    {['Image', 'Product Info', 'Customer', 'Status', 'Actions'].map(h => (
                      <th key={h} style={{ padding: '12px', textAlign: 'left', color: '#4d9fff', fontSize: '0.85rem' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bookings.length === 0 ? (
                    <tr><td colSpan="5" style={{ padding: '30px', textAlign: 'center', color: '#7a85a0' }}>ಯಾವ bookings ಬಂದಿಲ್ಲ!</td></tr>
                  ) : bookings.map(b => (
                    <tr key={b.booking_id} style={{ borderBottom: '1px solid rgba(26,108,255,0.1)' }}>
                      <td style={{ padding: '12px' }}>
                        {b.image_url && <img src={b.image_url} alt="product" style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '8px' }} onError={e => e.target.style.display='none'} />}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ color: '#f0f4ff', fontWeight: 'bold' }}>{b.product_name}</div>
                        <div style={{ color: '#7a85a0', fontSize: '0.8rem' }}>Size: {b.size} | Price: {b.price}</div>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ color: '#38bdf8', fontWeight: 'bold' }}>{b.customer_name}</div>
                        <div style={{ color: '#7a85a0', fontSize: '0.8rem' }}>📞 {b.customer_phone}</div>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 'bold', background: b.status === 'Pending' ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)', color: b.status === 'Pending' ? '#f59e0b' : '#10b981' }}>
                          {b.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        {b.status === 'Pending' && (
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button onClick={() => handleBookingAction(b.booking_id, 'agree')} style={{ padding: '6px 14px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>Agree</button>
                            <button onClick={() => handleBookingAction(b.booking_id, 'disagree')} style={{ padding: '6px 14px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>No Stock</button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const lbl = { display: 'block', color: '#7a85a0', fontSize: '0.8rem', marginBottom: '5px', marginTop: '12px' };
const inp = { width: '100%', padding: '10px 13px', marginBottom: '5px', borderRadius: '9px', border: '1px solid rgba(26,108,255,0.25)', background: '#0b0b18', color: '#f0f4ff', boxSizing: 'border-box', fontSize: '14px' };

export default Admin;
