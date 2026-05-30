import React, { useState, useEffect } from 'react';
import './App.css';
import Admin from './Admin';
import ProductPage from './ProductPage';
import dolphin from './assets/dolphin.png';
import heroVideo from './assets/hero-video.mp4';

// 🏪 ಜೀವನ್, ಇಲ್ಲಿ ನಿಮ್ಮ ಫೋಟೋಗಳ ಎಕ್ಸ್‌ಟೆನ್ಶನ್ ಅನ್ನು .jpeg ಗೆ ಪಕ್ಕಾ ಚೇಂಜ್ ಮಾಡಲಾಗಿದೆ!
import shop1 from './assets/shop-1..jpeg';
import shop2 from './assets/shop-2..jpeg';
import shop3 from './assets/shop-3..jpeg';
import shop4 from './assets/shop-4..jpeg';
import shop5 from './assets/shop-5..jpeg';

const API = 'https://dolphin-trends-3.onrender.com';

function App() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [activePage, setActivePage] = useState('shop');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);
  const [viewProduct, setViewProduct] = useState(null);
  const [fullScreenImage, setFullScreenImage] = useState(null);

  const shopImages = [shop1, shop2, shop3, shop4, shop5];
  const [currentImgIndex, setCurrentImgIndex] = useState(0);

  const nextShopImage = () => setCurrentImgIndex((prev) => (prev + 1) % shopImages.length);
  const prevShopImage = () => setCurrentImgIndex((prev) => (prev - 1 + shopImages.length) % shopImages.length);

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

  useEffect(() => { fetchProducts(); }, []);

  const filtered = activeCategory === 'All' ? products : products.filter(p => p.category === activeCategory);

  return (
    <div className="App">
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
          <button className="admin-btn" onClick={() => isAdminLoggedIn ? (setIsAdminLoggedIn(false) || setShowAdmin(false) || fetchProducts()) : setShowAdmin(!showAdmin)}>
            {isAdminLoggedIn ? '🔓 Logout' : '🛠️ Admin'}
          </button>
        </div>
      </nav>

      {/* ─── 🔥 ಅಡ್ಮಿನ್ ಸೆಕ್ಷನ್ ಫಿಕ್ಸ್ ─── */}
      {showAdmin ? (
        isAdminLoggedIn ? (
          <Admin onProductAdded={fetchProducts} setFullScreenImage={setFullScreenImage} />
        ) : (
          <div style={{ background: '#0b1329', padding: '40px 20px', minHeight: '60vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <div style={{ background: '#1a233d', padding: '30px', borderRadius: '12px', width: '100%', maxWidth: '400px', textAlign: 'center' }}>
              <h2 style={{ color: '#fff', marginBottom: '20px' }}>🔐 Admin Login</h2>
              <button onClick={() => setIsAdminLoggedIn(true)} style={{ background: '#007bff', color: 'white', border: 'none', padding: '12px 25px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', width: '100%' }}>
                Enter Dashboard
              </button>
            </div>
          </div>
        )
      ) : (
        <>
          {activePage === 'shop' && (
            <div>
              <div className="hero"><video autoPlay muted loop playsInline className="hero-video"><source src={heroVideo} type="video/mp4" /></video><div className="hero-overlay"></div><div className="hero-content"><h2>✨ New Arrivals Every Day!</h2><p>Fresh styles just for you 🌸</p></div></div>
              <div className="categories">{categories.map(cat => <button key={cat} className={cat === activeCategory ? 'cat-btn active' : 'cat-btn'} onClick={() => setActiveCategory(cat)}>{cat}</button>)}</div>
              <div className="products-section">
                <h3>{activeCategory === 'All' ? 'All Products' : activeCategory}</h3>
                {loading ? <div className="loading">Loading... <div className="spinner"></div></div> : filtered.length === 0 ? <div className="no-products">😊 ಇನ್ನೂ products ಇಲ್ಲ — ಶೀಘ್ರದಲ್ಲೇ ಬರ್ತಿವೆ!</div> : (
                  <div className="products-grid">
                    {filtered.map(product => (
                      <div className={product.available === false ? 'product-card not-available' : 'product-card'} key={product.product_id || product.id}>
                        <div className="product-card-img-wrap" onClick={() => setFullScreenImage(product.image)} style={{cursor: 'zoom-in'}}><img src={product.image} alt={product.name} onError={e => e.target.src='https://via.placeholder.com/300x400?text=No+Image'} /></div>
                        <div className="product-info"><span className="category-tag">{product.category}</span><h4>{product.name}</h4><p className="price">{product.price}</p>{product.available !== false && <button className="buy-btn" onClick={() => setViewProduct(product)}>🛍️ Buy Now</button>}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activePage === 'branches' && (
            <div className="section-page">
              <div className="section-page-header"><h2>🏪 Our Branches</h2><p>Dolphin Trends — Bangalore ಅಲ್ಲಿ ನಮ್ಮ ಅಂಗಡಿಗಳು</p></div>
              <div className="branch-grid">
                {[
                  { tag:'Main Branch', name:'Rajgopalnagar', addr:'Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore — 560058', phone:'📞 +91 7795800741' },
                  { tag:'Branch 2', name:'Laggere', addr:'Anikethana Kishore Kendra Laggere, Bangalore — 560058', phone:'📞 +91 9353838835' },
                ].map((b, i) => <div className="branch-card" key={i}><span className="branch-tag">{b.tag}</span><h3>{b.name}</h3><p>{b.addr}</p><p className="branch-phone">{b.phone}</p></div>)}
              </div>
            </div>
          )}

          {activePage === 'location' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>📍 Our Locations</h2>
                <p>Dolphin Trends — ನಮ್ಮ ಅಂಗಡಿಗಳ ವಿಳಾಸ</p>
              </div>

              {/* Main Branch */}
              <div className="map-embed" style={{ marginBottom: '40px' }}>
                <h3 style={{ color: '#4d9fff', marginBottom: '15px', fontSize: '1.4rem' }}>⭐ Main Branch — Rajgopalnagar</h3>
                
                <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '15px', padding: '25px', marginBottom: '15px' }}>
                  <p style={{ color: '#f0f4ff', marginBottom: '10px' }}>📍 Rajgopal Nagar, Main Road, Peenya 2nd Stage, Bangalore — 560058</p>
                  <p style={{ color: '#7a85a0', marginBottom: '15px' }}>⏰ Mon–Sun: 11:00 AM – 10:00 PM</p>
                  <a href="https://maps.app.goo.gl/tJQ47jqAsoLRQ1Ua7" target="_blank" rel="noreferrer"
                    style={{ display: 'inline-block', padding: '12px 24px', background: '#1a6cff', color: '#fff', borderRadius: '10px', textDecoration: 'none', fontWeight: 'bold' }}>
                    🗺️ Open in Google Maps
                  </a>
                </div>

                {/* Shop Photos */}
                <h4 style={{ color: '#7a85a0', marginBottom: '10px', textAlign: 'center' }}>📸 Our Shop</h4>
                <div style={{ position: 'relative', width: '100%', maxWidth: '500px', height: '380px', margin: '0 auto', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(26,108,255,0.2)' }}>
                  <img src={shopImages[currentImgIndex]} alt="Shop" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <button onClick={prevShopImage} style={{ position: 'absolute', top: '50%', left: '10px', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', width: '36px', height: '36px', borderRadius: '50%', cursor: 'pointer', fontSize: '18px' }}>‹</button>
                  <button onClick={nextShopImage} style={{ position: 'absolute', top: '50%', right: '10px', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', width: '36px', height: '36px', borderRadius: '50%', cursor: 'pointer', fontSize: '18px' }}>›</button>
                  <div style={{ position: 'absolute', bottom: '12px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '6px' }}>
                    {shopImages.map((_, idx) => (
                      <span key={idx} onClick={() => setCurrentImgIndex(idx)}
                        style={{ width: '8px', height: '8px', borderRadius: '50%', background: currentImgIndex === idx ? '#1a6cff' : 'rgba(255,255,255,0.5)', cursor: 'pointer' }} />
                    ))}
                  </div>
                </div>
              </div>

              {/* Branch 2 */}
              <div className="map-embed">
                <h3 style={{ color: '#4d9fff', marginBottom: '15px', fontSize: '1.4rem' }}>🏪 Branch 2 — Laggere</h3>
                <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '15px', padding: '25px' }}>
                  <p style={{ color: '#f0f4ff', marginBottom: '10px' }}>📍 Anikethana Kishore Kendra, Laggere, Bangalore — 560058</p>
                  <p style={{ color: '#7a85a0', marginBottom: '15px' }}>⏰ Mon–Sun: 11:00 AM – 10:00 PM</p>
                  <a href="https://maps.app.goo.gl/amrkmppGsdgprtx27" target="_blank" rel="noreferrer"
                    style={{ display: 'inline-block', padding: '12px 24px', background: '#1a6cff', color: '#fff', borderRadius: '10px', textDecoration: 'none', fontWeight: 'bold' }}>
                    🗺️ Open in Google Maps
                  </a>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <footer><p><strong>🐬 Dolphin Trends</strong> | Developed by Jeevan JD</p></footer>

      {fullScreenImage && <div onClick={() => setFullScreenImage(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}><img src={fullScreenImage} alt="Full" style={{ maxWidth: '95%', maxHeight: '90vh' }} /></div>}
      {viewProduct && <ProductPage product={viewProduct} allProducts={products} onClose={() => setViewProduct(null)} onBook={p => setViewProduct(p)} />}
    </div>
  );
}

export default App;
