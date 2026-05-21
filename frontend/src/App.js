import React, { useState, useEffect } from 'react';
import './App.css';
import Admin from './Admin';
import BookingModal from './BookingModal';
import Login from './Login';
import ProductPage from './ProductPage';
import dolphin from './assets/dolphin.png';
import heroVideo from './assets/hero-video.mp4';

function App() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [activePage, setActivePage] = useState('shop');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [viewProduct, setViewProduct] = useState(null);
  const [editProduct, setEditProduct] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [editLoading, setEditLoading] = useState(false);

  const categories = [
    'All', 'Leggings', 'Kurta Sets', 'Jeans',
    'Patiala Pants', 'Kurtha Top', 'Umbrella Sets', 'Frocks',
    'Western Wear', 'Gym Pants','250 Tops','350 Tops','Jeans Tops',
  ];

  const fetchProducts = () => {
    setLoading(true);
    fetch('https://dolphin-trends-3.onrender.com/products')
      .then(r => r.json())
      .then(d => { setProducts(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchProducts(); }, []);

  const filtered = activeCategory === 'All'
    ? products
    : products.filter(p => p.category === activeCategory);

  const handleAdminClick = () => {
    if (isAdminLoggedIn) {
      setIsAdminLoggedIn(false);
      setShowAdmin(false);
      fetchProducts();
    } else {
      setShowAdmin(!showAdmin);
    }
  };

  // ✅ FIX: Correct delete URL with /products/
  const handleDelete = (e, id) => {
    e.stopPropagation();
    if (!window.confirm('ಈ product delete ಮಾಡಬೇಕಾ?')) return;
    fetch('https://dolphin-trends-3.onrender.com/products/' + id, { method: 'DELETE' })
      .then(r => { if (r.ok) setProducts(p => p.filter(x => x.id !== id)); });
  };

  const handleEditOpen = (e, product) => {
    e.stopPropagation();
    setEditProduct(product);
    setEditForm({
      name: product.name || '',
      price: product.price || '',
      original_price: product.original_price || '',
      category: product.category || '',
      available: product.available !== false,
      image: product.image
    });
  };

  // ✅ FIX: Correct edit save URL with /products/
  const handleEditSave = () => {
    if (!editProduct) return;
    setEditLoading(true);
    fetch('https://dolphin-trends-3.onrender.com/products/' + editProduct.id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...editProduct, ...editForm }),
    })
      .then(r => r.json())
      .then(updated => {
        setProducts(p => p.map(x => x.id === updated.id ? updated : x));
        setEditProduct(null);
        setEditLoading(false);
      })
      .catch(() => { alert('Update ಆಗಲಿಲ್ಲ!'); setEditLoading(false); });
  };

  return (
    <div className="App">

      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-logo" onClick={() => { setActivePage('shop'); setShowAdmin(false); }} style={{cursor:'pointer'}}>
          <img src={dolphin} alt="Dolphin Trends Logo" />
          <div className="logo-text">
            <h1>🐬 Dolphin Trends</h1>
            <p>Women's Fashion · Bangalore</p>
          </div>
        </div>

        <ul className="navbar-links">
          <li><button className={activePage === 'shop' && !showAdmin ? 'active' : ''} onClick={() => { setActivePage('shop'); setShowAdmin(false); }}>🛍️ Shop</button></li>
          <li><button className={activePage === 'branches' ? 'active' : ''} onClick={() => { setActivePage('branches'); setShowAdmin(false); }}>🏪 Branches</button></li>
          <li><button className={activePage === 'contact' ? 'active' : ''} onClick={() => { setActivePage('contact'); setShowAdmin(false); }}>📞 Contact</button></li>
          <li><button className={activePage === 'location' ? 'active' : ''} onClick={() => { setActivePage('location'); setShowAdmin(false); }}>📍 Location</button></li>
        </ul>

        <div className="navbar-right">
          {isAdminLoggedIn && !showAdmin && (
            <button className="admin-btn" onClick={() => setShowAdmin(true)}>⚙️ Admin Panel</button>
          )}
          <button className="admin-btn" onClick={handleAdminClick}>
            {isAdminLoggedIn ? '🔓 Logout' : '🛠️ Admin'}
          </button>
        </div>
      </nav>

      {/* Admin Mode Badge */}
      {isAdminLoggedIn && (
        <div style={{textAlign:'center', padding:'6px', background:'rgba(26,108,255,0.1)', borderBottom:'1px solid rgba(26,108,255,0.2)', fontSize:'0.75rem'}}>
          <span className="admin-mode-badge">🔐 Admin Mode Active — Edit & Delete Enabled</span>
        </div>
      )}

      {/* Main Content */}
      {showAdmin ? (
        isAdminLoggedIn
          ? <Admin onProductAdded={fetchProducts} />
          : <Login onLogin={() => setIsAdminLoggedIn(true)} />
      ) : (
        <>
          {/* Shop Page */}
          {activePage === 'shop' && (
            <div>
              {/* Hero Video */}
              <div className="hero">
                <video autoPlay muted loop playsInline className="hero-video">
                  <source src={heroVideo} type="video/mp4" />
                </video>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                  <h2>✨ New Arrivals Every Day!</h2>
                  <p>Fresh styles just for you 🌸</p>
                </div>
              </div>

              {/* Categories */}
              <div className="categories">
                {categories.map(cat => (
                  <button
                    key={cat}
                    className={cat === activeCategory ? 'cat-btn active' : 'cat-btn'}
                    onClick={() => setActiveCategory(cat)}
                  >{cat}</button>
                ))}
              </div>

              {/* Products */}
              <div className="products-section">
                <h3>{activeCategory === 'All' ? 'All Products' : activeCategory}</h3>
                {loading ? (
                  <div className="loading">Loading... <div className="spinner"></div></div>
                ) : filtered.length === 0 ? (
                  <div className="no-products">😊 ಇನ್ನೂ products ಇಲ್ಲ — ಶೀಘ್ರದಲ್ಲೇ ಬರ್ತಿವೆ!</div>
                ) : (
                  <div className="products-grid">
                    {filtered.map(product => (
                      <div
                        className={product.available === false ? 'product-card not-available' : 'product-card'}
                        key={product.id}
                        onClick={() => setViewProduct(product)}
                      >
                        {product.available === false && (
                          <span className="not-available-badge">❌ Not Available</span>
                        )}

                        {isAdminLoggedIn && (
                          <div style={{position:'absolute', top:'10px', right:'10px', display:'flex', gap:'6px', zIndex:10}}>
                            <button onClick={e => handleEditOpen(e, product)} style={editBtnStyle}>✏️</button>
                            <button onClick={e => handleDelete(e, product.id)} style={deleteBtnStyle}>🗑️</button>
                          </div>
                        )}

                        <div className="product-card-img-wrap">
                          <img src={product.image} alt={product.name} />
                        </div>
                        <div className="product-info">
                          <span className="category-tag">{product.category}</span>
                          <h4>{product.name}</h4>
                          <p className="price">{product.price}</p>
                          {product.original_price && (
                            <p className="original-price-small"><s>{product.original_price}</s></p>
                          )}
                          {product.available !== false && (
                            <button className="buy-btn" onClick={e => { e.stopPropagation(); setViewProduct(product); }}>
                              🛍️ Buy Now
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Branches Page */}
          {activePage === 'branches' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>🏪 Our Branches</h2>
                <p>Dolphin Trends — Bangalore ಅಲ್ಲಿ ನಮ್ಮ ಅಂಗಡಿಗಳು</p>
              </div>
              <div className="branch-grid">
                {[
                  { tag:'Main Branch', name:'Laggere Main Road', addr:'Anikethana Kishore Kendra Laggere, Bangalore — 560058', phone:'📞 +91 7795800741', hours:'Mon–Sun: 11am – 10pm' },
                  { tag:'Branch 2', name:'Rajgopalnagar', addr:'Near Peenya 2nd Stage, Bangalore — 560091', phone:'📞 +91 9353838835', hours:'Mon–Sun: 11am – 10pm' },
                ].map((b, i) => (
                  <div className="branch-card" key={i}>
                    <span className="branch-tag">{b.tag}</span>
                    <h3>{b.name}</h3>
                    <p>{b.addr}</p>
                    <p className="branch-phone">{b.phone}</p>
                    <p style={{color:'#4d9fff', fontSize:'0.8rem', marginTop:'6px'}}>⏰ {b.hours}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contact Page */}
          {activePage === 'contact' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>📞 Contact Us</h2>
                <p>ನಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸಿ — ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಂತೋಷ!</p>
              </div>
              <div className="contact-grid">
                <div className="info-card">
                  <h3>📬 Get In Touch</h3>
                  {[
                    { icon:'📱', label:'WhatsApp', value:'+91 7795800741' },
                    { icon:'📧', label:'Email', value:'dolphintrends@gmail.com' },
                    { icon:'📸', label:'Instagram', value:'@dolphintrends_blr' },
                    { icon:'⏰', label:'Working Hours', value:'Mon – Sun: 11:00 AM – 10:00 PM' },
                  ].map((row, i) => (
                    <div className="contact-row" key={i}>
                      <div className="c-icon">{row.icon}</div>
                      <div>
                        <strong>{row.label}</strong>
                        <span>{row.value}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="info-card">
                  <h3>📍 Main Branch Address</h3>
                  {[
                    { icon:'🏪', label:'Shop Name', value:"Dolphin Trends — Women's Fashion Store" },
                    { icon:'📌', label:'Address', value:'Laggere Main Road, Bangalore — 560058' },
                    { icon:'🚇', label:'Nearest Metro', value:'Jalahalli Metro Station' },
                    { icon:'🚌', label:'Bus Stop', value:'Laggere Aladmara Bus Stop' },
                  ].map((row, i) => (
                    <div className="contact-row" key={i}>
                      <div className="c-icon">{row.icon}</div>
                      <div>
                        <strong>{row.label}</strong>
                        <span>{row.value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Location Page */}
          {activePage === 'location' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>📍 Our Location</h2>
                <p>Rajagopala Nagar, Peenya 2nd Stage, Bangalore</p>
              </div>
              <div className="map-embed">
                <iframe
                  title="Dolphin Trends Location"
                  src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3887.126425176161!2d77.5195431!3d13.0276313!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bae3d90680f4f9f%3A0x608e06385a49b28a!2sPeenya%202nd%20Stage%2C%20Bengaluru%2C%20Karnataka!5e0!3m2!1sen!2sin!4v1700000000000!5m2!1sen!2sin"
                  allowFullScreen=""
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                  style={{border:0, width:'100%', height:'400px', borderRadius:'15px'}}
                />
                <div className="map-label">
                  📍 Rajagopala Nagar, Peenya 2nd Stage, Bangalore — 560091
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <footer>
        <p><strong>🐬 Dolphin Trends</strong> | Women's Fashion Store | Bangalore</p>
        <p>📍 Laggere Main Road, Bangalore — 560058</p>
        <p>📱 +91 7795800741 | 📸 Developer by Jeevan JD</p>
      </footer>

      {/* Product Page */}
      {viewProduct && (
        <ProductPage
          product={viewProduct}
          allProducts={products}
          onClose={() => setViewProduct(null)}
          onBook={p => setViewProduct(p)}
        />
      )}

      {/* Booking Modal */}
      {selectedProduct && (
        <BookingModal product={selectedProduct} onClose={() => setSelectedProduct(null)} />
      )}

      {/* Edit Modal */}
      {editProduct && (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <h3 style={{color:'#4d9fff', marginBottom:'20px', fontFamily:'Playfair Display, serif'}}>✏️ Product Edit</h3>
            {[
              { label:'Product Name', key:'name', placeholder:'Product name' },
              { label:'Price (₹)', key:'price', placeholder:'₹500' },
              { label:'Original Price (optional)', key:'original_price', placeholder:'₹800' },
            ].map(f => (
              <div key={f.key}>
                <label style={labelStyle}>{f.label}</label>
                <input
                  value={editForm[f.key] || ''}
                  onChange={e => setEditForm({...editForm, [f.key]: e.target.value})}
                  style={inputStyle}
                  placeholder={f.placeholder}
                />
              </div>
            ))}

            <label style={labelStyle}>Category</label>
            <select
              value={editForm.category}
              onChange={e => setEditForm({...editForm, category: e.target.value})}
              style={inputStyle}
            >
              {categories.filter(c => c !== 'All').map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <label style={{...labelStyle, display:'flex', alignItems:'center', gap:'10px', marginTop:'8px', cursor:'pointer'}}>
              <input
                type="checkbox"
                checked={editForm.available}
                onChange={e => setEditForm({...editForm, available: e.target.checked})}
                style={{width:'18px', height:'18px', accentColor:'#1a6cff'}}
              />
              Available ✅
            </label>

            <div style={{display:'flex', gap:'10px', marginTop:'22px'}}>
              <button onClick={handleEditSave} disabled={editLoading}
                style={{flex:1, background:'#1a6cff', color:'#fff', border:'none', borderRadius:'10px', padding:'12px', fontWeight:'700', fontSize:'0.9rem', cursor:'pointer'}}>
                {editLoading ? 'Saving...' : '💾 Save'}
              </button>
              <button onClick={() => setEditProduct(null)}
                style={{flex:1, background:'#1a1a30', color:'#7a85a0', border:'1px solid #1a4fff44', borderRadius:'10px', padding:'12px', fontWeight:'600', fontSize:'0.9rem', cursor:'pointer'}}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

const editBtnStyle = { background:'#1a6cff', color:'#fff', border:'none', borderRadius:'7px', padding:'5px 10px', fontWeight:'700', fontSize:'0.75rem', cursor:'pointer' };
const deleteBtnStyle = { background:'#ff3b5c', color:'#fff', border:'none', borderRadius:'7px', padding:'5px 10px', fontWeight:'700', fontSize:'0.75rem', cursor:'pointer' };
const overlayStyle = { position:'fixed', inset:0, background:'rgba(0,0,0,0.75)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:2000 };
const modalStyle = { background:'#0f0f1e', border:'1px solid rgba(26,108,255,0.3)', borderRadius:'18px', padding:'30px', width:'90%', maxWidth:'420px', color:'#f0f4ff' };
const labelStyle = { fontSize:'0.78rem', color:'#7a85a0', display:'block', marginBottom:'4px' };
const inputStyle = { width:'100%', padding:'10px 13px', marginBottom:'13px', borderRadius:'9px', border:'1px solid rgba(26,108,255,0.25)', background:'#0b0b18', color:'#f0f4ff', boxSizing:'border-box' };

export default App;
