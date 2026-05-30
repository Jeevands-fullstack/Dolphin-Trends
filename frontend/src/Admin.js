import React, { useState, useRef, useEffect } from 'react';

function Admin({ onProductAdded }) {
  const [formData, setFormData] = useState({
    name: '', description: '', price: '', original_price: '', category: 'Tops'
  });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
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
    try {
      const r = await fetch('https://dolphin-trends-3.onrender.com/products', { method: 'POST', body: dataToSend });
      if (r.ok) {
        const result = await r.json();
        alert(result.action === 'updated' ? '🔄 Product updated!' : '✅ Product saved!');
        setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
        setPreview(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
        if (onProductAdded) onProductAdded();
      } else alert('❌ Save failed!');
    } catch { alert('❌ Server Error!'); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ background: '#0b1329', padding: '20px', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>

        {/* Product Form */}
        <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px', marginBottom: '30px' }}>
          <h2 style={{ color: '#4d9fff', marginBottom: '20px' }}>🛠️ Admin Panel - Add / Edit Product</h2>

          <label style={lbl}>👗 Dress Photo</label>
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

          <button onClick={handleAddOrUpdateProduct} disabled={loading}
            style={{ width: '100%', padding: '14px', background: '#1a6cff', color: '#fff', border: 'none', borderRadius: '10px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer', marginTop: '5px' }}>
            {loading ? 'Saving...' : '✅ Save Product'}
          </button>
        </div>

        {/* Bookings Table — Image version only */}
        <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
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
