import React, { useState, useRef, useEffect } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function Admin({ onProductAdded, editData, onCancelEdit }) {
  const [formData, setFormData] = useState({
    name: '', description: '', price: '', original_price: '', category: 'Tops', available: true
  });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);
  const [adminFullScreenImg, setAdminFullScreenImg] = useState(null);

  useEffect(() => {
    if (editData) {
      setFormData({
        name: editData.name || '',
        description: editData.description || '',
        price: editData.price ? editData.price.replace('₹', '') : '',
        original_price: editData.original_price ? editData.original_price.replace('₹', '') : '',
        category: editData.category || 'Tops',
        available: editData.available !== undefined ? editData.available : true
      });
      setPreview(editData.image || null);
    }
  }, [editData]);

  useEffect(() => { fetchBookings(); }, []);

  const fetchBookings = async () => {
    setBookingsLoading(true);
    try {
      const response = await fetch(`${API}/bookings`);
      if (response.ok) setBookings(await response.json());
    } catch (e) { console.error(e); }
    finally { setBookingsLoading(false); }
  };

  const handleBookingAction = async (bookingId, action) => {
    let confirmMsg = "AGREE madbekka?";
    if (action === "disagree") confirmMsg = "DRESS NO STOCK madbekka?";
    if (action === "size_unavail") confirmMsg = "SIZE NO STOCK madbekka?";
    if (!window.confirm(confirmMsg)) return;
    try {
      const r = await fetch(`${API}/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, { method: 'POST' });
      if (r.ok) { alert('✅ Notification Sent!'); fetchBookings(); }
      else alert('❌ Failed');
    } catch { alert('❌ Server Error'); }
  };

  const handleDeleteBooking = async (bookingId) => {
    if (!bookingId) { alert('❌ Invalid Booking ID!'); return; }
    if (!window.confirm('⚠️ Booking delete madbekka?')) return;
    try {
      const r = await fetch(`${API}/bookings/${bookingId}`, { method: 'DELETE' });
      if (r.ok) { alert('🗑️ Booking Deleted!'); fetchBookings(); }
      else alert(`❌ Delete failed! Status: ${r.status}`);
    } catch { alert('❌ Server Error!'); }
  };

  const handleAddOrUpdateProduct = async () => {
    if (!formData.name || !formData.price) { alert('⚠️ Name mattu Price haki!'); return; }
    setLoading(true);
    const selectedFile = fileInputRef.current?.files[0];

    // ✅ EDIT MODE: PUT / POST request with product_id
    if (editData) {
      const productId = editData.product_id || editData.id;
      if (!productId) { alert('❌ Product ID not found!'); setLoading(false); return; }

      const updatePayload = {
        price: formData.price.startsWith('₹') ? formData.price : `₹${formData.price}`,
        original_price: formData.original_price ? (formData.original_price.startsWith('₹') ? formData.original_price : `₹${formData.original_price}`) : '',
        description: formData.description,
        category: formData.category,
        available: formData.available
      };

      try {
        // ✅ ಇಮೇಜ್ ಚೇಂಜ್ ಮಾಡಿದ್ರೆ ಇಲ್ಲಿಗೆ ಬರುತ್ತೆ (ಇಲ್ಲಿ ಈಗ product_id ಸೇರಿಸಲಾಗಿದೆ)
        if (selectedFile) {
          const imgForm = new FormData();
          imgForm.append('name', formData.name);
          imgForm.append('price', updatePayload.price);
          imgForm.append('original_price', updatePayload.original_price);
          imgForm.append('description', updatePayload.description || '');
          imgForm.append('category', updatePayload.category);
          imgForm.append('available', String(formData.available));
          imgForm.append('file', selectedFile);
          
          // ಬ್ಯಾಕೆಂಡ್‌ನ /products ರೂಟ್‌ಗೆ ಅಪ್ಡೇಟ್ ಮಾಡಲು ಕಳುಹಿಸುತ್ತಿದ್ದೇವೆ
          const r = await fetch(`${API}/products`, { method: 'POST', body: imgForm });
          if (r.ok) {
            alert('🔄 Product & Image Updated!');
            if (onProductAdded) onProductAdded();
          } else {
            alert('❌ Update failed!');
          }
        } else {
          // ಬರೀ ಟೆಕ್ಸ್ಟ್ ಅಪ್ಡೇಟ್ ಮಾಡಿದ್ರೆ ನೇರವಾಗಿ ID ಮೂಲಕ ಕಳುಹಿಸುತ್ತೆ
          const r = await fetch(`${API}/products/${productId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatePayload)
          });
          if (r.ok) {
            alert('🔄 Product Details Updated!');
            if (onProductAdded) onProductAdded();
          } else {
            alert('❌ Update failed!');
          }
        }
      } catch { alert('❌ Server Error!'); }
      finally { setLoading(false); }
      return;
    }

    // ADD MODE: POST request
    const dataToSend = new FormData();
    dataToSend.append('name', formData.name);
    dataToSend.append('price', formData.price.startsWith('₹') ? formData.price : `₹${formData.price}`);
    dataToSend.append('original_price', formData.original_price ? (formData.original_price.startsWith('₹') ? formData.original_price : `₹${formData.original_price}`) : '');
    dataToSend.append('description', formData.description);
    dataToSend.append('category', formData.category);
    dataToSend.append('available', String(formData.available));
    if (selectedFile) dataToSend.append('file', selectedFile);

    try {
      const r = await fetch(`${API}/products`, { method: 'POST', body: dataToSend });
      if (r.ok) {
        alert('✅ Product saved!');
        setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops', available: true });
        setPreview(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
        if (onProductAdded) onProductAdded();
      } else {
        alert(`❌ Save failed!`);
      }
    } catch { alert('❌ Server Error!'); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ background: '#0b1329', padding: '20px', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>

        <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px', marginBottom: '30px' }}>
          <h2 style={{ color: '#4d9fff', marginBottom: '20px' }}>
            {editData ? '🔄 Edit Product Details' : '🛠️ Admin Panel - Add Product'}
          </h2>

          <label style={lbl}>👗 Dress Photo {editData && '(Change madbekidre new file choose madi)'}</label>
          <input type="file" accept="image/*" ref={fileInputRef} onChange={e => { const f = e.target.files[0]; if (f) setPreview(URL.createObjectURL(f)); }} style={{ width: '100%', marginBottom: '15px', color: '#fff' }} />
          {preview && <img src={preview} alt="preview" style={{ width: '100px', borderRadius: '8px', marginBottom: '15px' }} />}

          <label style={lbl}>Product Name {editData && '(Edit mode alli name change agalla)'}</label>
          <input style={{...inp, opacity: editData ? 0.6 : 1}} placeholder="eg: Silk Kurti" value={formData.name}
            onChange={e => { if (!editData) setFormData({ ...formData, name: e.target.value }); }}
            readOnly={!!editData}
          />

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

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '18px 0 10px 0', background: '#0b0b18', padding: '12px', borderRadius: '9px', border: '1px solid rgba(26,108,255,0.2)' }}>
            <input type="checkbox" id="available_box" checked={formData.available}
              onChange={e => setFormData({ ...formData, available: e.target.checked })}
              style={{ width: '19px', height: '19px', cursor: 'pointer' }}
            />
            <label htmlFor="available_box" style={{ color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' }}>
              ✅ Available (Untick madidre Out of Stock agthade)
            </label>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button onClick={handleAddOrUpdateProduct} disabled={loading}
              style={{ flex: 2, padding: '14px', background: editData ? '#e11d48' : '#1a6cff', color: '#fff', border: 'none', borderRadius: '10px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer' }}>
              {loading ? 'Saving...' : editData ? '🔄 Update Product' : '✅ Save Product'}
            </button>
            {editData && (
              <button onClick={onCancelEdit} style={{ flex: 1, padding: '14px', background: '#4b5563', color: '#fff', border: 'none', borderRadius: '10px', fontWeight: 'bold', fontSize: '16px', cursor: 'pointer' }}>
                Cancel
              </button>
            )}
          </div>
        </div>

        {/* Bookings Table */}
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
                    <tr><td colSpan="5" style={{ padding: '30px', textAlign: 'center', color: '#7a85a0' }}>Yaav bookings bandilla!</td></tr>
                  ) : bookings.map(b => (
                    <tr key={b.booking_id} style={{ borderBottom: '1px solid rgba(26,108,255,0.1)' }}>
                      <td style={{ padding: '12px' }}>
                        {b.image_url && (
                          <img src={b.image_url} alt="product"
                            style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '8px', cursor: 'zoom-in' }}
                            onClick={() => setAdminFullScreenImg(b.image_url)}
                            onError={e => e.target.style.display='none'}
                          />
                        )}
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
                        <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 'bold',
                          background: b.status === 'Pending' ? 'rgba(245,158,11,0.2)' : b.status === 'Approved' ? 'rgba(16,185,129,0.2)' : b.status === 'Size Unavailable' ? 'rgba(59,130,246,0.2)' : 'rgba(239,68,68,0.2)',
                          color: b.status === 'Pending' ? '#f59e0b' : b.status === 'Approved' ? '#10b981' : b.status === 'Size Unavailable' ? '#3b82f6' : '#ef4444'
                        }}>
                          {b.status || 'Pending'}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                          {b.status === 'Pending' && (
                            <>
                              <button onClick={() => handleBookingAction(b.booking_id, 'agree')} style={{ padding: '5px 10px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>Agree</button>
                              <button onClick={() => handleBookingAction(b.booking_id, 'size_unavail')} style={{ padding: '5px 10px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>Size No Stock</button>
                              <button onClick={() => handleBookingAction(b.booking_id, 'disagree')} style={{ padding: '5px 10px', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>No Stock</button>
                            </>
                          )}
                          <button onClick={() => handleDeleteBooking(b.booking_id)} style={{ padding: '5px 8px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}>🗑️ Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {adminFullScreenImg && (
        <div onClick={() => setAdminFullScreenImg(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 99999, cursor: 'zoom-out' }}>
          <img src={adminFullScreenImg} alt="Full View" style={{ maxWidth: '95%', maxHeight: '90vh', borderRadius: '8px' }} />
        </div>
      )}
    </div>
  );
}

const lbl = { display: 'block', color: '#7a85a0', fontSize: '0.8rem', marginBottom: '5px', marginTop: '12px' };
const inp = { width: '100%', padding: '10px 13px', marginBottom: '5px', borderRadius: '9px', border: '1px solid rgba(26,108,255,0.25)', background: '#0b0b18', color: '#f0f4ff', boxSizing: 'border-box', fontSize: '14px' };

export default Admin;
