import React, { useState, useEffect } from 'react';
import './App.css';
import Admin from './Admin';
import BookingModal from './BookingModal';
import Login from './Login';
import ProductPage from './ProductPage';
import dolphin from './assets/dolphin.png';
import heroVideo from './assets/hero-video.mp4';
import shop1 from './assets/shop-1.jpg';
import shop2 from './assets/shop-2.jpg';
import shop3 from './assets/shop-3.jpg';
import shop4 from './assets/shop-4.jpg';
import shop5 from './assets/shop-5.jpg';

const API = 'https://dolphin-trends-3.onrender.com';

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
  const [fullScreenImage, setFullScreenImage] = useState(null);

  // 📸 ಶಾಪ್ ಇಮೇಜ್ ಸ್ಲೈಡರ್‌ಗಾಗಿ ಸ್ಟೇಟ್ಸ್
  const shopImages = [shop1, shop2, shop3, shop4, shop5];
  const [currentImgIndex, setCurrentImgIndex] = useState(0);

  const nextShopImage = () => {
    setCurrentImgIndex((prev) => (prev + 1) % shopImages.length);
  };

  const prevShopImage = () => {
    setCurrentImgIndex((prev) => (prev - 1 + shopImages.length) % shopImages.length);
  };

  const categories = [
    'All', 'Leggings', 'Kurta Sets', 'Jeans',
    'Patiala Pants', 'Kurtha Top', 'Umbrella Sets', 'Frocks',
    'Western Wear', 'Gym Pants','250 Tops','350 Tops','Jeans Tops',
  ];

  const fetchProducts = () => {
    setLoading(true);
    fetch(`${API}/products`)
      .then(r => r.json())
      .then(d => { 
        setProducts(Array.isArray(d) ? d.reverse() : []); 
        setLoading(false); 
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => { 
    fetchProducts(); 
  }, []);

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

  const handleEditOpen = (e, product) => {
    e.stopPropagation();
    setEditProduct(product);
    setEditForm({
      name: product.name || '',
      price: product.price || '',
      original_price: product.original_price || '',
      category: product.category || '',
      available: product.available !== false,
    });
  };

  const handleDelete = async (e, product) => {
    e.stopPropagation();
    const id = product.product_id || product.id;
    if (!id || id === 'undefined') {
      alert('❌ Product ID not found!');
      return;
    }
    if (!window.confirm('ಈ product delete ಮಾಡಬೇಕಾ?')) return;
    try {
      const response = await fetch(`${API}/products/${id}`, { method: 'DELETE' });
      if (response.ok) {
        setProducts(prev => prev.filter(p => (p.product_id || p.id) !== id));
        alert('✅ Product deleted');
      } else {
        alert('❌ Delete failed');
      }
    } catch (err) {
      alert('❌ Server error');
    }
  };

  const handleEditSave = async () => {
    if (!editProduct) return;
    setEditLoading(true)
    const productId = editProduct.product_id || editProduct.id;
    if (!productId || productId === 'undefined') {
      alert('❌ Product ID not found!');
      setEditLoading(false);
      return;
    }
    try {
      const response = await fetch(`${API}/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });
      if (response.ok) {
        setProducts(prev => prev.map(p =>
          (p.product_id || p.id) === productId ? { ...p, ...editForm } : p
        ));
        alert('✅ Product updated');
        setEditProduct(null);
      } else {
        alert('❌ Update failed');
      }
    } catch (err) {
      alert('❌ Server error');
    } finally {
      setEditLoading(false);
    }
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

      {isAdminLoggedIn && (
        <div style={{textAlign:'center', padding:'6px', background:'rgba(26,108,255,0.1)', borderBottom:'1px solid rgba(26,108,255,0.2)', fontSize:'0.75rem'}}>
          <span className="admin-mode-badge">🔐 Admin Mode Active — Edit & Delete Enabled</span>
        </div>
      )}

      {showAdmin ? (
        isAdminLoggedIn
          ? <Admin onProductAdded={fetchProducts} setFullScreenImage={setFullScreenImage} />
          : <Login onLogin={() => setIsAdminLoggedIn(true)} />
      ) : (
        <>
          {activePage === 'shop' && (
            <div>
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

              <div className="categories">
                {categories.map(cat => (
                  <button key={cat} className={cat === activeCategory ? 'cat-btn active' : 'cat-btn'} onClick={() => setActiveCategory(cat)}>{cat}</button>
                ))}
              </div>

              <div className="products-section">
                <h3>{activeCategory === 'All' ? 'All Products' : activeCategory}</h3>
                {loading ? (
                  <div className="loading">Loading... <div className="spinner"></div></div>
                ) : filtered.length === 0 ? (
                  <div className="no-products">😊 ಇನ್ನೂ products ಇಲ್ಲ — ಶೀಘ್ರದಲ್ಲೇ ಬರ್ತಿವೆ!</div>
                ) : (
                  <div className="products-grid">
                    {filtered.map(product => (
                      <div className={product.available === false ? 'product-card not-available' : 'product-card'} key={product.product_id || product.id}>
                        {product.available === false && (
                          <span className="not-available-badge">❌ Not Available</span>
                        )}
                        {isAdminLoggedIn && (
                          <div style={{position:'absolute', top:'10px', right:'10px', display:'flex', gap:'6px', zIndex:10}}>
                            <button onClick={e => handleEditOpen(e, product)} style={editBtnStyle}>✏️</button>
                            <button onClick={e => handleDelete(e, product)} style={deleteBtnStyle}>🗑️</button>
                          </div>
                        )}
                        
                        <div className="product-card-img-wrap" onClick={() => setFullScreenImage(product.image)} style={{cursor: 'zoom-in'}}>
                          <img src={product.image} alt={product.name} onError={e => e.target.src='https://via.placeholder.com/300x400?text=No+Image'} />
                        </div>
                        
                        <div className="product-info">
                          <span className="category-tag">{product.category}</span>
                          <h4>{product.name}</h4>
                          <p className="price">{product.price}</p>
                          {product.original_price && (
                            <p className="original-price-small"><s>{product.original_price}</s></p>
                          )}
                          {product.available !== false && (
                            <button className="buy-btn" onClick={() => setViewProduct(product)}>
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

          {activePage === 'branches' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>🏪 Our Branches</h2>
                <p>Dolphin Trends — Bangalore ಅಲ್ಲಿ ನಮ್ಮ ಅಂಗಡಿಗಳು</p>
              </div>
              <div className="branch-grid">
                {[
                  { tag:'Main Branch', name:'Rajgopalnagar', addr:'Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore — 560058', phone:'📞 +91 7795800741', hours:'Mon–Sun: 11am – 10pm' },
                  { tag:'Branch 2', name:'Laggere', addr:'Anikethana Kishore Kendra Laggere, Bangalore — 560058', phone:'📞 +91 9353838835', hours:'Mon–Sun: 11am – 10pm' },
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
                      <div><strong>{row.label}</strong><span>{row.value}</span></div>
                    </div>
                  ))}
                </div>
                <div className="info-card">
                  <h3>📍 Store Address</h3>
                  {[
                    { icon:'🏪', label:'Shop Name', value:"Dolphin Trends — Women's Fashion Store" },
                    { icon:'📌', label:'Address', value:'Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore' },
                    { icon:'🚇', label:'Nearest Metro', value:'Peenya Industry Metro Station' },
                  ].map((row, i) => (
                    <div className="contact-row" key={i}>
                      <div className="c-icon">{row.icon}</div>
                      <div><strong>{row.label}</strong><span>{row.value}</span></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

{activePage === 'location' && (
  <div className="section-page">
    <div className="section-page-header">
      <h2>📍 Our Locations</h2>
      <p>Dolphin Trends — ನಮ್ಮ ಅಂಗಡಿಗಳ ವಿಳಾಸ</p>
    </div>

    {/* Branch 1 */}
    <div className="map-embed" style={{marginBottom:'40px'}}>
      <h3 style={{color:'#4d9fff', marginBottom:'15px', fontSize:'1.4rem'}}>⭐ Main Branch — Rajgopalnagar</h3>
      <iframe
        title="Main Branch"
        src="https://maps.google.com/maps?q=12.997,77.5186&z=16&output=embed"
        allowFullScreen="" loading="lazy"
        style={{border:0, width:'100%', height:'350px', borderRadius:'15px'}}
      />
      <div className="map-label">📍 Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore — 560058</div>
      <a href="https://maps.app.goo.gl/tJQ47jqAsoLRQ1Ua7" target="_blank" rel="noreferrer"
        style={{display:'block', marginTop:'10px', color:'#4d9fff', fontWeight:'bold', textDecoration:'none'}}>
        🗺️ Open in Google Maps
      </a>

      {/* Shop Photos Slider */}
      <h4 style={{color:'#7a85a0', marginTop:'20px', marginBottom:'10px', textAlign:'center'}}>📸 Our Shop</h4>
      <div className="shop-slider-container" style={{position:'relative', width:'100%', maxWidth:'500px', height:'380px', margin:'0 auto', borderRadius:'12px', overflow:'hidden', border:'1px solid rgba(26,108,255,0.2)'}}>
        <img src={shopImages[currentImgIndex]} alt="Shop" style={{width:'100%', height:'100%', objectFit:'cover'}} />
        <button onClick={prevShopImage} style={{position:'absolute', top:'50%', left:'10px', transform:'translateY(-50%)', background:'rgba(0,0,0,0.6)', color:'#fff', border:'none', width:'36px', height:'36px', borderRadius:'50%', cursor:'pointer', fontSize:'18px'}}>‹</button>
        <button onClick={nextShopImage} style={{position:'absolute', top:'50%', right:'10px', transform:'translateY(-50%)', background:'rgba(0,0,0,0.6)', color:'#fff', border:'none', width:'36px', height:'36px', borderRadius:'50%', cursor:'pointer', fontSize:'18px'}}>›</button>
        <div style={{position:'absolute', bottom:'12px', left:'50%', transform:'translateX(-50%)', display:'flex', gap:'6px'}}>
          {shopImages.map((_, idx) => (
            <span key={idx} onClick={() => setCurrentImgIndex(idx)}
              style={{width:'8px', height:'8px', borderRadius:'50%', background: currentImgIndex===idx ? '#1a6cff' : 'rgba(255,255,255,0.5)', cursor:'pointer'}} />
          ))}
        </div>
      </div>
    </div>

    {/* Branch 2 */}
    <div className="map-embed">
      <h3 style={{color:'#4d9fff', marginBottom:'15px', fontSize:'1.4rem'}}>🏪 Branch 2 — Laggere</h3>
      <iframe
        title="Branch 2"
        src="https://maps.google.com/maps?q=13.021,77.5218&z=16&output=embed"
        allowFullScreen="" loading="lazy"
        style={{border:0, width:'100%', height:'350px', borderRadius:'15px'}}
      />
      <div className="map-label">📍 Anikethana Kishore Kendra Laggere, Bangalore — 560058</div>
      <a href="https://maps.app.goo.gl/amrkmppGsdgprtx27" target="_blank" rel="noreferrer"
        style={{display:'block', marginTop:'10px', color:'#4d9fff', fontWeight:'bold', textDecoration:'none'}}>
        🗺️ Open in Google Maps
      </a>
    </div>
  </div>
)}
  
<footer>
        <p><strong>🐬 Dolphin Trends</strong> | Women's Fashion Store | Bangalore</p>
        <p>📍 Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore</p>
        <p>📱 +91 7795800741 | 📸 Developed by Jeevan JD</p>
      </footer>

      {fullScreenImage && (
        <div onClick={() => setFullScreenImage(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, cursor: 'zoom-out' }}>
          <span style={{ position: 'absolute', top: '20px', right: '30px', color: '#fff', fontSize: '30px', fontWeight: 'bold', cursor: 'pointer' }}>✕</span>
          <img src={fullScreenImage} alt="Full Screen" style={{ maxWidth: '95%', maxHeight: '90vh', borderRadius: '8px' }} />
        </div>
      )}

      {viewProduct && (
        <ProductPage product={viewProduct} allProducts={products} onClose={() => setViewProduct(null)} onBook={p => setViewProduct(p)} />
      )}

      {selectedProduct && (
        <BookingModal product={selectedProduct} onClose={() => setSelectedProduct(null)} />
      )}

      {editProduct && (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <h3 style={{color:'#4d9fff', marginBottom:'20px'}}>✏️ Product Edit</h3>
            {[
              { label:'Product Name', key:'name', placeholder:'Product name' },
              { label:'Price (₹)', key:'price', placeholder:'₹500' },
              { label:'Original Price (optional)', key:'original_price', placeholder:'₹800' },
            ].map(f => (
              <div key={f.key}>
                <label style={labelStyle}>{f.label}</label>
                <input value={editForm[f.key] || ''} onChange={e => setEditForm({...editForm, [f.key]: e.target.value})} style={inputStyle} placeholder={f.placeholder} />
              </div>
            ))}
            <label style={labelStyle}>Category</label>
            <select value={editForm.category || ''} onChange={e => setEditForm({...editForm, category: e.target.value})} style={inputStyle}>
              {categories.filter(c => c !== 'All').map(c => (<option key={c} value={c}>{c}</option>))}
            </select>
            <label style={{...labelStyle, display:'flex', alignItems:'center', gap:'10px', marginTop:'8px', cursor:'pointer'}}>
              <input type="checkbox" checked={editForm.available !== false} onChange={e => setEditForm({...editForm, available: e.target.checked})} style={{width:'18px', height:'18px', accentColor:'#1a6cff'}} />
              Available ✅
            </label>
            <div style={{display:'flex', gap:'10px', marginTop:'22px'}}>
              <button onClick={handleEditSave} disabled={editLoading} style={{flex:1, background:'#1a6cff', color:'#fff', border:'none', borderRadius:'10px', padding:'12px', fontWeight:'700', cursor:'pointer'}}>
                {editLoading ? 'Saving...' : '💾 Save'}
              </button>
              <button onClick={() => setEditProduct(null)} style={{flex:1, background:'#1a1a30', color:'#7a85a0', border:'1px solid #1a4fff44', borderRadius:'10px', padding:'12px', cursor:'pointer'}}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const editBtnStyle = { background:'#1a6cff', color:'#fff', border:'none', borderRadius:'7px', padding:'5px 10px', cursor:'pointer' };
const deleteBtnStyle = { background:'#ff3b5c', color:'#fff', border:'none', borderRadius:'7px', padding:'5px 10px', cursor:'pointer' };
const overlayStyle = { position:'fixed', inset:0, background:'rgba(0,0,0,0.75)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:2000 };
const modalStyle = { background:'#0f0f1e', border:'1px solid rgba(26,108,255,0.3)', borderRadius:'18px', padding:'30px', width:'90%', maxWidth:'420px', color:'#f0f4ff' };
const labelStyle = { fontSize:'0.78rem', color:'#7a85a0', display:'block', marginBottom:'4px' };
const inputStyle = { width:'100%', padding:'10px 13px', marginBottom:'13px', borderRadius:'9px', border:'1px solid rgba(26,108,255,0.25)', background:'#0b0b18', color:'#f0f4ff', boxSizing:'border-box' };

export default App;
