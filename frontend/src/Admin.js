import React, { useState, useRef, useEffect } from 'react';

function Admin({ onProductAdded }) {
  // ─── 📦 1. ಪ್ರಾಡಕ್ಟ್ ಆಡ್ ಮತ್ತು ಎಡಿಟ್ ಸ್ಟೇಟ್ಸ್ ───
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

  // Products List & Editing States
  const [products, setProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [editingProductId, setEditingProductId] = useState(null);

  // ─── 📋 2. ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಸ್ಟೇಟ್ಸ್ ───
  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);

  // ವೆಬ್‌ಸೈಟ್ ಲೋಡ್ ಆದಾಗ ಬುಕಿಂಗ್ಸ್ ಮತ್ತು ಪ್ರಾಡಕ್ಟ್ಸ್ ಎರಡನ್ನೂ ತರೋಣ
  useEffect(() => {
    fetchBookings();
    fetchProducts();
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

  // 📥 ಬ್ಯಾಕೆಂಡ್‌ನಿಂದ ಪ್ರಾಡಕ್ಟ್ಸ್ ಲಿಸ್ಟ್ ತರೋ ಫಂಕ್ಷನ್
  const fetchProducts = async () => {
    setProductsLoading(true);
    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/products');
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setProductsLoading(false);
    }
  };

  // ⚡ Agree / Disagree ಬುಕಿಂಗ್ ಆಕ್ಷನ್
  const handleBookingAction = async (bookingId, action, customerName) => {
    let actionText = action === 'agree' ? "AGREE" : "DISAGREE";
    if (!window.confirm(`Jeevan, do you want to ${actionText} this order?`)) return;

    try {
      const response = await fetch(`https://dolphin-trends-3.onrender.com/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, {
        method: 'POST',
      });

      if (response.ok) {
        alert(`✅ Action successful! Notification processed via Backend.`);
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

  // ➕ ಪ್ರಾಡಕ್ಟ್ ಆಡ್ ಮಾಡೋ ಫಂಕ್ಷನ್
  const handleAddProduct = async () => {
    const file = fileInputRef.current.files[0];

    if (!formData.name || !formData.price || !file) {
      alert("⚠️ ದಯವಿಟ್ಟು ಫೋಟೋ, ಹೆಸರು ಮತ್ತು ಮಾರಾಟದ ಬೆಲೆಯನ್ನು ನಮೂದಿಸಿ!");
      return;
    }

    setLoading(true);

    const dataToSend = new FormData();
    dataToSend.append('name', formData.name);
    dataToSend.append('price', formData.price.startsWith('₹') ? formData.price : `₹${formData.price}`);
    dataToSend.append('original_price', formData.original_price ? (formData.original_price.startsWith('₹') ? formData.original_price : `₹${formData.original_price}`) : "");
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
        fetchProducts(); // Refresh List
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

  // 📝 ಎಡಿಟ್ ಮೋಡ್ ಆನ್ ಮಾಡೋ ಫಂಕ್ಷನ್
  const startEditProduct = (product) => {
    setEditingProductId(product.product_id);
    setFormData({
      name: product.name,
      description: product.description || '',
      price: product.price.replace('₹', ''),
      original_price: product.original_price ? product.original_price.replace('₹', '') : '',
      category: product.category || 'Tops'
    });
    setPreview(product.image);
    window.scrollTo({ top: 0, behavior: 'smooth' }); // ಫಾರ್ಮ್ ಇರೋ ಜಾಗಕ್ಕೆ ಸ್ಕ್ರಾಲ್ ಆಗುತ್ತೆ
  };

  // 💾 ಎಡಿಟ್ ಮಾಡಿದ ಪ್ರಾಡಕ್ಟ್ ಅನ್ನು ಸೇವ್ (SAVE/UPDATE) ಮಾಡೋ ಫಂಕ್ಷನ್
  const handleUpdateProduct = async () => {
    if (!editingProductId) return;
    setLoading(true);

    const updatedData = {
      name: formData.name,
      description: formData.description,
      price: `₹${formData.price}`,
      original_price: formData.original_price ? `₹${formData.original_price}` : "",
      category: formData.category,
      image: preview // Keeps existing image URL safely
    };

    try {
      const response = await fetch(`https://dolphin-trends-3.onrender.com/api/products/${editingProductId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedData),
      });

      if (response.ok) {
        alert("✅ Product ಯಶಸ್ವಿಯಾಗಿ ಅಪ್ಡೇಟ್ ಆಗಿದೆ ಜೀವನ್!");
        setEditingProductId(null);
        setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
        setPreview(null);
        fetchProducts(); // Refresh list
        if (onProductAdded) onProductAdded();
      } else {
        alert("❌ ಅಪ್ಡೇಟ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.");
      }
    } catch (error) {
      alert("❌ ಸರ್ವರ್ ಕನೆಕ್ಷನ್ ಎರರ್!");
    } finally {
      setLoading(false);
    }
  };

  // ❌ ಪ್ರಾಡಕ್ಟ್ ಡಿಲೀಟ್ ಮಾಡೋ ಫಂಕ್ಷನ್
  const handleDeleteProduct = async (productId) => {
    if (!productId || productId === "undefined") {
      alert("❌ Invalid Product ID!");
      return;
    }
    if (!window.confirm("Jeevan, ಈ ಪ್ರಾಡಕ್ಟ್ ಅನ್ನು ವೆಬ್‌ಸೈಟ್‌ನಿಂದ ಖಂಡಿತ ಡಿಲೀಟ್ ಮಾಡಬೇಕೇ?")) return;

    try {
      const response = await fetch(`https://dolphin-trends-3.onrender.com/api/products/${productId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        alert("🗑️ Product ಯಶಸ್ವಿಯಾಗಿ ಡಿಲೀಟ್ ಆಗಿದೆ!");
        fetchProducts(); // Refresh list
        if (onProductAdded) onProductAdded();
      } else {
        alert("❌ ಡಿಲೀಟ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.");
      }
    } catch (error) {
      alert("❌ ಸರ್ವರ್ ಕನೆಕ್ಷನ್ ಎರರ್!");
    }
  };

  return (
    <div className="admin-container" style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      
      {/* ─── 👗 ಸೆಕ್ಷನ್ 1: ಆಡ್ / ಎಡಿಟ್ ಪ್ರಾಡಕ್ಟ್ ಫಾರ್ಮ್ ─── */}
      <div className="admin-card" style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', marginBottom: '40px' }}>
        <h2>{editingProductId ? "📝 Admin Panel - Edit Product" : "🛠️ Admin Panel - Add Product"}</h2>
        <div className="form-section">
          <div className="input-group" style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>👗 Dress Photo</label>
            {!editingProductId && <input type="file" accept="image/*" ref={fileInputRef} onChange={handleImageChange} className="file-input" />}
            {preview && (
              <div className="image-preview">
                <img src={preview} alt="Preview" style={{ width: '120px', height: '140px', objectFit: 'cover', marginTop: '10px', borderRadius: '8px', border: '1px solid #ddd' }} />
              </div>
            )}
            {editingProductId && <p style={{ fontSize: '12px', color: 'gray', marginTop: '5px' }}>⚠️ Note: Image changes are handled via Telegram upload only.</p>}
          </div>

          <div className="input-group" style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Product Name</label>
            <input type="text" placeholder="eg: Silk Saree" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
          </div>

          <div className="input-group" style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Description</label>
            <textarea placeholder="Enter product details..." rows="3" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} />
          </div>

          <div className="input-row" style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
            <div className="input-group" style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Selling Price (₹)</label>
              <input type="number" placeholder="Selling Price" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} value={formData.price} onChange={(e) => setFormData({...formData, price: e.target.value})} />
            </div>
            <div className="input-group" style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Original Price (₹)</label>
              <input type="number" placeholder="Original Price" style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} value={formData.original_price} onChange={(e) => setFormData({...formData, original_price: e.target.value})} />
            </div>
          </div>

          <div className="input-group" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Category</label>
            <select style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
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

          {editingProductId ? (
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={handleUpdateProduct} disabled={loading} style={{ background: '#28a745', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                {loading ? "Updating..." : "💾 Save Changes"}
              </button>
              <button onClick={() => { setEditingProductId(null); setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' }); setPreview(null); }} style={{ background: '#6c757d', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          ) : (
            <button className="add-btn" onClick={handleAddProduct} disabled={loading} style={{ background: '#007bff', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', width: '100%' }}>
              {loading ? "Saving..." : "✅ Add Product"}
            </button>
          )}
        </div>
      </div>

      <hr style={{ border: '1px solid #ddd', margin: '40px 0' }} />

      {/* ─── 📥 ಸೆಕ್ಷನ್ 2: ಕಸ್ಟಮರ್ ಬುಕಿಂಗ್ಸ್ ಟೇಬಲ್ ─── */}
      <div className="admin-card" style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', marginBottom: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>📥 Customer Bookings List</h2>
          <button onClick={fetchBookings} style={{ padding: '6px 12px', cursor: 'pointer', borderRadius: '4px', background: '#007bff', color: 'white', border: 'none' }}>🔄 Refresh Bookings</button>
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
                        <a href={b.image_url} target="_blank" rel="noreferrer" style={{ color: '#007bff', textDecoration: 'none', fontWeight: 'bold' }}>View 📸</a>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', background: b.status === 'Pending' ? '#ffeaa7' : b.status === 'Approved-WaitingPayment' ? '#ffe0b2' : '#dfe6e9', color: b.status === 'Pending' ? '#b78103' : b.status === 'Approved-WaitingPayment' ? '#e65100' : '#2d3436' }}>
                          {b.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        {b.status === 'Pending' ? (
                          <>
                            <button onClick={() => handleBookingAction(b.booking_id, 'agree', b.customer_name)} style={{ background: '#28a745', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '8px', fontWeight: 'bold' }}>Agree</button>
                            <button onClick={() => handleBookingAction(b.booking_id, 'disagree', b.customer_name)} style={{ background: '#dc3545', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>Disagree</button>
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

      <hr style={{ border: '1px solid #ddd', margin: '40px 0' }} />

      {/* ─── 🛍️ ಸೆಕ್ಷನ್ 3: ಹೊಸದಾಗಿ ಸೇರಿಸಿರೋ ಮ್ಯಾನೇಜ್ ಪ್ರಾಡಕ್ಟ್ಸ್ ಟೇಬಲ್ (EDIT & DELETE) ─── */}
      <div className="admin-card" style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>🛍️ Manage Products Catalog ({products.length})</h2>
          <button onClick={fetchProducts} style={{ padding: '6px 12px', cursor: 'pointer', borderRadius: '4px', background: '#28a745', color: 'white', border: 'none' }}>🔄 Refresh List</button>
        </div>

        {productsLoading ? (
          <p>ಪ್ರಾಡಕ್ಟ್‌ಗಳು ಲೋಡ್ ಆಗುತ್ತಿವೆ ಜೀವನ್...</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
              <thead>
                <tr style={{ background: '#f4f4f4', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Image</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Product Name</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Category</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Price</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '20px', textAlign: 'center', color: 'gray' }}>ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಯಾವುದೇ ಪ್ರಾಡಕ್ಟ್ ಇಲ್ಲ!</td>
                  </tr>
                ) : (
                  products.map((p) => (
                    <tr key={p.product_id} style={{ borderBottom: '1px solid #ddd' }}>
                      <td style={{ padding: '12px' }}>
                        <img src={p.image} alt={p.name} style={{ width: '50px', height: '60px', objectFit: 'cover', borderRadius: '4px', border: '1px solid #eee' }} />
                      </td>
                      <td style={{ padding: '12px' }}><b>{p.name}</b></td>
                      <td style={{ padding: '12px' }}><span style={{ background: '#e1f5fe', color: '#0288d1', padding: '3px 8px', borderRadius: '4px', fontSize: '13px' }}>{p.category}</span></td>
                      <td style={{ padding: '12px', color: '#2e7d32', fontWeight: 'bold' }}>{p.price}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <button 
                          onClick={() => startEditProduct(p)} 
                          style={{ background: '#ffc107', color: 'black', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', marginRight: '8px', fontWeight: 'bold' }}
                        >
                          ✏️ Edit
                        </button>
                        <button 
                          onClick={() => handleDeleteProduct(p.product_id)} 
                          style={{ background: '#dc3545', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                        >
                          🗑️ Delete
                        </button>
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
