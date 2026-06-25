import React, { useState, useEffect } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function Admin({ onProductAdded, editData, onCancelEdit, onBackToStore }) {
  // 📝 Product Form States
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [originalPrice, setOriginalPrice] = useState('');
  const [category, setCategory] = useState('Suit Set');
  const [available, setAvailable] = useState(true);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // 📥 Bookings States
  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);
  const [adminFullScreenImg, setAdminFullScreenImg] = useState(null);

  // 🆕 Tab state - toggle between Products and Bookings
  const [activeTab, setActiveTab] = useState('products');

  // ✅ Categories
  const categories = [
    'Suit Set', 'Kurta Sets', 'Kurtha Top', 'Jeans',
    'Plazzo Pants', 'Umbrella Sets', 'Frocks', 'Western Wear',
    'Gym Pants', '250 Tops', '350 Tops', 'Jeans Tops',
    'Leggings', 'Formal Pants', 'Formal Shirt'
  ];

  // 🔄 Edit Mode Load
  useEffect(() => {
    if (editData) {
      setName(editData.name || '');
      setDescription(editData.description || '');
      const p = String(editData.price || '').replace('₹', '').trim();
      setPrice(p);
      const op = String(editData.original_price || '').replace('₹', '').trim();
      setOriginalPrice(op);
      setCategory(editData.category || 'Suit Set');
      setAvailable(editData.available !== false);
      setImagePreview(editData.image || null);
      setImageFile(null); 
      setActiveTab('products'); // Switch to products tab when editing
    } else {
      setName('');
      setDescription('Beautiful design crafted with rich fabric.');
      setPrice('');
      setOriginalPrice('');
      setCategory('Suit Set');
      setAvailable(true);
      setImagePreview(null);
      setImageFile(null);
    }
  }, [editData]);

  // 📥 Bookings Load
  useEffect(() => { 
    fetchBookings(); 
  }, []);

  const fetchBookings = async () => {
    setBookingsLoading(true);
    try {
      const response = await fetch(`${API}/bookings`);
      if (response.ok) {
        const data = await response.json();
        setBookings(data);
      }
    } catch (e) { 
      console.error("Fetch bookings error:", e); 
    } finally { 
      setBookingsLoading(false); 
    }
  };

  // 🟢 🟡 🔴 Booking Actions
  const handleBookingAction = async (bookingId, action) => {
    let confirmMsg = "AGREE madbekka?";
    if (action === "disagree") confirmMsg = "DRESS NO STOCK madbekka?";
    if (action === "size_unavail") confirmMsg = "SIZE NO STOCK madbekka?";
    if (!window.confirm(confirmMsg)) return;
    
    try {
      const r = await fetch(
        `${API}/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, 
        { method: 'POST' }
      );
      if (r.ok) { 
        alert('✅ Customer notified via WhatsApp!'); 
        fetchBookings(); 
      } else {
        const error = await r.json().catch(() => ({}));
        alert(`❌ Failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (err) { 
      console.error("Booking action error:", err);
      alert('❌ Server Error'); 
    }
  };

  // 🗑️ Delete Booking
  const handleDeleteBooking = async (bookingId) => {
    if (!bookingId) { 
      alert('❌ Invalid Booking ID!'); 
      return; 
    }
    if (!window.confirm('⚠️ Booking delete madbekka?')) return;
    
    try {
      const r = await fetch(`${API}/bookings/${bookingId}`, { method: 'DELETE' });
      if (r.ok) { 
        alert('🗑️ Booking Deleted!'); 
        fetchBookings(); 
      } else {
        alert('❌ Delete failed!');
      }
    } catch (err) { 
      console.error("Delete error:", err);
      alert('❌ Server Error!'); 
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.size > 5 * 1024 * 1024) {
      alert('⚠️ File too large! Max 5MB allowed.');
      return;
    }
    
    setImageFile(file);
    const reader = new FileReader();
    reader.onloadend = () => { setImagePreview(reader.result); };
    reader.readAsDataURL(file);
  };

  // 🚀 Product Save/Update Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!name || !price) { 
      alert('⚠️ Name mattu Price haki!'); 
      return; 
    }
    
    if (parseFloat(price) <= 0) {
      alert('⚠️ Price valid number irbeku!');
      return;
    }
    
    setSubmitting(true);

    const formattedPrice = price.startsWith('₹') ? price : `₹${price}`;
    const formattedOriginalPrice = originalPrice 
      ? (originalPrice.startsWith('₹') ? originalPrice : `₹${originalPrice}`) 
      : '';

    try {
      if (editData) {
        const productId = editData.product_id || editData.id;
        
        if (imageFile) {
          // Image change - new POST request
          const imgForm = new FormData();
          imgForm.append('name', name);
          imgForm.append('price', formattedPrice);
          imgForm.append('original_price', formattedOriginalPrice);
          imgForm.append('description', description);
          imgForm.append('category', category);
          imgForm.append('available', String(available));
          imgForm.append('file', imageFile);
          
          const r = await fetch(`${API}/products`, { 
            method: 'POST', 
            body: imgForm 
          });
          
          if (r.ok) {
            alert('🔄 Product & Image Updated!');
            if (onProductAdded) onProductAdded();
            if (onCancelEdit) onCancelEdit();
          } else {
            alert('❌ Update failed!');
          }
        } else {
          // Text only change - PUT request
          const updatePayload = {
            name: name,
            price: formattedPrice,
            original_price: formattedOriginalPrice,
            description: description,
            category: category,
            available: available
          };
          
          const r = await fetch(`${API}/products/${productId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatePayload)
          });
          
          if (r.ok) {
            alert('🔄 Product Details Updated!');
            if (onProductAdded) onProductAdded();
            if (onCancelEdit) onCancelEdit();
          } else {
            alert('❌ Update failed!');
          }
        }
      } else {
        // ADD MODE - New product
        if (!imageFile) {
          alert('⚠️ Photo upload madbeku!');
          setSubmitting(false);
          return;
        }

        const dataToSend = new FormData();
        dataToSend.append('name', name);
        dataToSend.append('price', formattedPrice);
        dataToSend.append('original_price', formattedOriginalPrice);
        dataToSend.append('description', description);
        dataToSend.append('category', category);
        dataToSend.append('available', String(available));
        dataToSend.append('file', imageFile);

        const r = await fetch(`${API}/products`, { 
          method: 'POST', 
          body: dataToSend 
        });
        
        if (r.ok) {
          alert('✅ Product saved!');
          // Reset form
          setName('');
          setDescription('Beautiful design crafted with rich fabric.');
          setPrice('');
          setOriginalPrice('');
          setCategory('Suit Set');
          setAvailable(true);
          setImagePreview(null);
          setImageFile(null);
          if (onProductAdded) onProductAdded();
        } else {
          alert('❌ Save failed!');
        }
      }
    } catch (err) { 
      console.error("Submit error:", err);
      alert('❌ Server Error!'); 
    } finally { 
      setSubmitting(false); 
    }
  };

  // 🆕 Handle cancel edit with confirmation
  const handleCancelEdit = () => {
    if (window.confirm('ಎಡಿಟ್ ರದ್ದು ಮಾಡಿ ಬೇರೆ ಪ್ರಾಡಕ್ಟ್ ಎಡಿಟ್ ಮಾಡಬೇಕೆ?')) {
      if (onCancelEdit) onCancelEdit();
    }
  };

  return (
    <>
      <style>{`
        .admin-tabs {
          display: flex;
          gap: 10px;
          margin-bottom: 25px;
          border-bottom: 2px solid rgba(26,108,255,0.2);
          padding-bottom: 0;
        }
        
        .admin-tab-btn {
          padding: 12px 24px;
          background: transparent;
          border: none;
          color: #7a85a0;
          cursor: pointer;
          font-weight: 600;
          font-size: 15px;
          border-bottom: 3px solid transparent;
          transition: all 0.2s;
          position: relative;
          bottom: -2px;
        }
        
        .admin-tab-btn.active {
          color: #4d9fff;
          border-bottom-color: #4d9fff;
        }
        
        .admin-tab-btn:hover {
          color: #fff;
        }
        
        .admin-back-buttons {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        
        .admin-back-btn {
          padding: 10px 18px;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          font-weight: bold;
          font-size: 14px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          transition: all 0.2s;
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        
        .admin-back-btn.admin {
          background: linear-gradient(135deg, #f59e0b, #d97706);
          color: #fff;
          box-shadow: 0 2px 8px rgba(245,158,11,0.3);
        }
        
        .admin-back-btn.store {
          background: linear-gradient(135deg, #10b981, #059669);
          color: #fff;
          box-shadow: 0 2px 8px rgba(16,185,129,0.3);
        }
        
        .admin-back-btn:hover {
          transform: scale(1.05);
        }
        
        .admin-back-btn.admin:hover {
          box-shadow: 0 4px 12px rgba(245,158,11,0.5);
        }
        
        .admin-back-btn.store:hover {
          box-shadow: 0 4px 12px rgba(16,185,129,0.5);
        }
      `}</style>

      <div style={{ background: '#0b1329', padding: '20px', minHeight: '100vh', boxSizing: 'border-box' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>

          {/* 🆕 HEADER WITH BACK BUTTONS */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            marginBottom: '20px',
            flexWrap: 'wrap',
            gap: '15px'
          }}>
            <h1 style={{ 
              margin: 0, 
              color: '#fff', 
              fontSize: '1.6rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              ⚙️ {editData ? 'Editing Product' : 'Admin Dashboard'}
            </h1>
            
            {/* 🆕 BACK BUTTONS */}
            <div className="admin-back-buttons" style={{ margin: 0 }}>
              {editData ? (
                <>
                  <button 
                    className="admin-back-btn admin"
                    onClick={handleCancelEdit}
                    type="button"
                  >
                    ← ⚙️ Back to Admin Panel
                  </button>
                  <button 
                    className="admin-back-btn store"
                    onClick={onBackToStore}
                    type="button"
                  >
                    ← 🏪 Back to Store
                  </button>
                </>
              ) : (
                <button 
                  className="admin-back-btn store"
                  onClick={onBackToStore}
                  type="button"
                >
                  ← 🏪 Back to Store
                </button>
              )}
            </div>
          </div>

          {/* 🆕 TAB NAVIGATION */}
          <div className="admin-tabs">
            <button 
              className={`admin-tab-btn ${activeTab === 'products' ? 'active' : ''}`}
              onClick={() => setActiveTab('products')}
            >
              📦 Products {editData && '(Editing)'}
            </button>
            <button 
              className={`admin-tab-btn ${activeTab === 'bookings' ? 'active' : ''}`}
              onClick={() => setActiveTab('bookings')}
            >
              📥 Bookings {bookings.filter(b => b.status === 'Pending').length > 0 && 
                `(${bookings.filter(b => b.status === 'Pending').length})`}
            </button>
          </div>

          {/* 📦 PRODUCTS TAB */}
          {activeTab === 'products' && (
            <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid rgba(26,108,255,0.1)', paddingBottom: '15px', textAlign: 'center' }}>
                <h2 style={{ margin: 0, color: '#4d9fff', fontSize: '1.4rem' }}>
                  {editData ? '🔄 Edit Product Details' : '🛠️ Add New Product'}
                </h2>
                {editData && (
                  <button 
                    type="button" 
                    onClick={handleCancelEdit} 
                    style={{ background: '#6b7c96', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem', marginTop: '5px' }}
                  >
                    Cancel Edit
                  </button>
                )}
              </div>

              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div>
                  <label style={lbl}>Dress Photo {editData && '(Change madbekidre new file choose madi)'}</label>
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleFileChange} 
                    required={!editData} 
                    style={{ width: '100%', color: '#fff' }} 
                  />
                  {imagePreview && (
                    <img 
                      src={imagePreview} 
                      alt="preview" 
                      style={{ 
                        width: '100px', 
                        height: '100px',
                        objectFit: 'cover',
                        borderRadius: '8px', 
                        marginTop: '10px',
                        cursor: 'zoom-in'
                      }} 
                      onClick={() => setAdminFullScreenImg(imagePreview)}
                    />
                  )}
                </div>

                <div>
                  <label style={lbl}>Product Name</label>
                  <input 
                    style={inp} 
                    type="text" 
                    placeholder="eg: Silk Kurti" 
                    value={name} 
                    onChange={e => setName(e.target.value)} 
                    required 
                  />
                </div>

                <div>
                  <label style={lbl}>Description</label>
                  <textarea 
                    style={{ ...inp, height: '80px', resize: 'vertical', fontFamily: 'sans-serif' }} 
                    placeholder="Product details..." 
                    value={description} 
                    onChange={e => setDescription(e.target.value)} 
                    required 
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ width: '100%' }}>
                    <label style={lbl}>Selling Price (₹)</label>
                    <input 
                      style={inp} 
                      type="number" 
                      placeholder="500" 
                      value={price} 
                      onChange={e => setPrice(e.target.value)} 
                      required 
                      min="0"
                    />
                  </div>
                  <div style={{ width: '100%' }}>
                    <label style={lbl}>Original Price (₹) <span style={{ color: '#7a85a0' }}>(Optional)</span></label>
                    <input 
                      style={inp} 
                      type="number" 
                      placeholder="800" 
                      value={originalPrice} 
                      onChange={e => setOriginalPrice(e.target.value)} 
                      min="0"
                    />
                  </div>
                </div>

                <div>
                  <label style={lbl}>Category</label>
                  <select 
                    style={inp} 
                    value={category} 
                    onChange={e => setCategory(e.target.value)}
                  >
                    {categories.map(c => (
                      <option key={c} value={c} style={{ background: '#0f1a35' }}>{c}</option>
                    ))}
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '10px 0', background: '#0b0b18', padding: '12px', borderRadius: '9px', border: '1px solid rgba(26,108,255,0.2)' }}>
                  <input 
                    type="checkbox" 
                    id="available_box" 
                    checked={available} 
                    onChange={e => setAvailable(e.target.checked)} 
                    style={{ width: '19px', height: '19px', cursor: 'pointer' }} 
                  />
                  <label htmlFor="available_box" style={{ color: '#fff', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' }}>
                    ✅ Available (Untick madidre Out of Stock agthade)
                  </label>
                </div>

                <button 
                  type="submit" 
                  disabled={submitting} 
                  style={{ 
                    width: '100%', 
                    padding: '14px', 
                    background: editData ? '#e11d48' : '#1a6cff', 
                    color: '#fff', 
                    border: 'none', 
                    borderRadius: '10px', 
                    fontWeight: 'bold', 
                    fontSize: '16px', 
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    opacity: submitting ? 0.7 : 1
                  }}
                >
                  {submitting ? '⏳ Saving...' : editData ? '🔄 Update Product' : '✅ Save Product'}
                </button>
              </form>
            </div>
          )}

          {/* 📥 BOOKINGS TAB */}
          {activeTab === 'bookings' && (
            <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '16px', padding: '25px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2 style={{ color: '#4d9fff', margin: 0, fontSize: '1.3rem' }}>📥 Customer Bookings</h2>
                <button 
                  onClick={fetchBookings} 
                  style={{ padding: '8px 16px', background: '#1a6cff', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  🔄 Refresh
                </button>
              </div>

              {bookingsLoading ? (
                <p style={{ color: '#7a85a0', textAlign: 'center', padding: '20px' }}>Loading Bookings...</p>
              ) : (
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
                        <tr>
                          <td colSpan="5" style={{ padding: '30px', textAlign: 'center', color: '#7a85a0' }}>
                            🕐 Yaav bookings bandilla!
                          </td>
                        </tr>
                      ) : bookings.map(b => (
                        <tr key={b.booking_id} style={{ borderBottom: '1px solid rgba(26,108,255,0.1)' }}>
                          <td style={{ padding: '12px' }}>
                            {b.image_url && (
                              <img 
                                src={b.image_url} 
                                alt="product"
                                style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '8px', cursor: 'zoom-in' }}
                                onClick={() => setAdminFullScreenImg(b.image_url)}
                                onError={e => { e.target.style.display='none'; }}
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
                            <span style={{ 
                              padding: '4px 12px', 
                              borderRadius: '20px', 
                              fontSize: '0.8rem', 
                              fontWeight: 'bold',
                              background: b.status === 'Pending' ? 'rgba(245,158,11,0.2)' : 
                                          b.status === 'Approved' ? 'rgba(16,185,129,0.2)' : 
                                          b.status === 'Size No Stock' ? 'rgba(59,130,246,0.2)' : 
                                          'rgba(239,68,68,0.2)',
                              color: b.status === 'Pending' ? '#f59e0b' : 
                                     b.status === 'Approved' ? '#10b981' : 
                                     b.status === 'Size No Stock' ? '#3b82f6' : 
                                     '#ef4444'
                            }}>
                              {b.status || 'Pending'}
                            </span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                              {b.status === 'Pending' && (
                                <>
                                  <button 
                                    onClick={() => handleBookingAction(b.booking_id, 'agree')} 
                                    style={{ padding: '5px 10px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                                  >
                                    Agree
                                  </button>
                                  <button 
                                    onClick={() => handleBookingAction(b.booking_id, 'size_unavail')} 
                                    style={{ padding: '5px 10px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                                  >
                                    Size No Stock
                                  </button>
                                  <button 
                                    onClick={() => handleBookingAction(b.booking_id, 'disagree')} 
                                    style={{ padding: '5px 10px', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                                  >
                                    No Stock
                                  </button>
                                </>
                              )}
                              <button 
                                onClick={() => handleDeleteBooking(b.booking_id)} 
                                style={{ padding: '5px 8px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                              >
                                🗑️ Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

        </div>

        {/* 🔍 Full Screen Image Viewer */}
        {adminFullScreenImg && (
          <div 
            onClick={() => setAdminFullScreenImg(null)}
            style={{ 
              position: 'fixed', 
              inset: 0, 
              background: 'rgba(0,0,0,0.9)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              zIndex: 99999, 
              cursor: 'zoom-out' 
            }}
          >
            <img 
              src={adminFullScreenImg} 
              alt="Full View" 
              style={{ maxWidth: '95%', maxHeight: '90vh', borderRadius: '8px' }} 
            />
          </div>
        )}
      </div>
    </>
  );
}

const lbl = { 
  display: 'block', 
  color: '#7a85a0', 
  fontSize: '0.85rem', 
  marginBottom: '5px', 
  marginTop: '5px' 
};

const inp = { 
  width: '100%', 
  padding: '11px', 
  marginBottom: '5px', 
  borderRadius: '8px', 
  border: '1px solid rgba(26,108,255,0.3)', 
  background: '#060a15', 
  color: '#fff', 
  boxSizing: 'border-box', 
  fontSize: '0.9rem' 
};

export default Admin;
