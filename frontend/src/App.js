import React, { useState, useEffect } from 'react';
import './App.css';
import Admin from './Admin';
import ProductPage from './ProductPage';
import ChatBox from './ChatBox';  // 🆕 Chat Box import
import dolphin from './assets/dolphin.jpg';
import heroVideo from './assets/hero-video.mp4';

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
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(() => {
    return sessionStorage.getItem('admin_logged_in') === 'true';
  });
  const [viewProduct, setViewProduct] = useState(null);
  const [fullScreenImage, setFullScreenImage] = useState(null);
  const [editProductData, setEditProductData] = useState(null); 

  // 🆕 Chat Box States
  const [chatOpen, setChatOpen] = useState(false);
  const [chatProduct, setChatProduct] = useState(null);

  // 🔐 Admin Login States
  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  const shopImages = [shop1, shop2, shop3, shop4, shop5];
  const [currentImgIndex, setCurrentImgIndex] = useState(0);

  const nextShopImage = () => setCurrentImgIndex((prev) => (prev + 1) % shopImages.length);
  const prevShopImage = () => setCurrentImgIndex((prev) => (prev - 1 + shopImages.length) % shopImages.length);

  const categories = [
    'All', 
    'Suit Set',
    'Kurta Sets', 
    'Kurtha Top', 
    'Jeans',
    'Plazzo Pants', 
    'Umbrella Sets', 
    'Frocks',
    'Western Wear', 
    'Gym Pants',
    '250 Tops',
    '350 Tops',
    'Jeans Tops',
    'Leggings',
    'Formal Pants',
    'Formal Shirt'
  ];

  // 🔄 Products Fetch
  const fetchProducts = () => {
    setLoading(true);
    fetch(`${API}/products?_ts=${Date.now()}`)
      .then(r => r.json())
      .then(d => { 
        setProducts(Array.isArray(d) ? d.reverse() : []); 
        setLoading(false); 
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        setLoading(false);
      });
  };

  useEffect(() => { fetchProducts(); }, []);

  // 🔐 Admin Login
  const handleAdminLoginSubmit = (e) => {
    e.preventDefault();
    const ADMIN_USER = 'dolphin_admin';
    const ADMIN_PASS = 'dolphin@2024';
    
    if (adminUsername === ADMIN_USER && adminPassword === ADMIN_PASS) {
      setIsAdminLoggedIn(true);
      sessionStorage.setItem('admin_logged_in', 'true');
      setLoginError('');
      setAdminUsername('');
      setAdminPassword('');
      setShowAdmin(true); 
      setActivePage('shop');
    } else {
      setLoginError('❌ ತಪ್ಪು Username ಅಥವಾ Password!');
      setAdminPassword('');
    }
  };

  // 🔓 Logout
  const handleLogout = () => {
    setIsAdminLoggedIn(false);
    sessionStorage.removeItem('admin_logged_in');
    setShowAdmin(false);
    setEditProductData(null);
    fetchProducts();
  };

  // 🗑️ Delete Product
  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('⚠️ ನೀವು ಖಚಿತವಾಗಿ ಈ ಪ್ರಾಡಕ್ಟ್ ಅನ್ನು ಡಿಲೀಟ್ ಮಾಡಲು ಬಯಸುತ್ತೀರಾ?')) return;
    try {
      const r = await fetch(`${API}/products/${productId}`, { method: 'DELETE' });
      if (r.ok) {
        alert('🗑️ Product Deleted!');
        fetchProducts();
      } else {
        alert('❌ Delete failed!');
      }
    } catch (err) {
      alert('❌ Server Error!');
    }
  };

  // ✏️ Edit Product
  const handleEditClick = (product) => {
    setEditProductData(product);
    setShowAdmin(true); 
  };

  // 🎯 Product Added Success
  const handleProductAddedSuccess = () => {
    fetchProducts();
    setEditProductData(null);
    setShowAdmin(false);
    setActivePage('shop'); 
  };

  // 🛒 Buy Now Handler - 🆕 Chat Box open ಮಾಡುತ್ತದೆ
  const handleBuyNow = (product) => {
    if (product.available === false) {
      alert('❌ ಈ product ಸದ್ಯ ಲಭ್ಯವಿಲ್ಲ!');
      return;
    }
    // 🆕 Chat Box open ಮಾಡಿ
    setChatProduct(product);
    setChatOpen(true);
  };

  // 🆕 Chat Button Click - General Chat (product ಇಲ್ಲದೆ)
  const handleOpenChat = () => {
    setChatProduct(null);
    setChatOpen(true);
  };

  const filtered = activeCategory === 'All' 
    ? products 
    : products.filter(p => p.category === activeCategory);

  return (
    <div className="App">
      {/* 🔝 Navbar */}
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
          
          <li>
            <button 
              className="insta-nav-btn" 
              onClick={() => window.open('https://www.instagram.com/dolphin_trends_rajagopalanagar?igsh=MWJ4MGRybGFxOXdiYw==', '_blank')}
              style={{
                background: 'linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)',
                color: '#fff',
                border: 'none',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'transform 0.2s'
              }}
            >
              📸 Instagram
            </button>
          </li>
        </ul>
        
        <div className="navbar-right">
          <button 
            className="admin-btn" 
            onClick={() => isAdminLoggedIn 
              ? handleLogout() 
              : setShowAdmin(!showAdmin)
            }
          >
            {isAdminLoggedIn ? '🔓 Logout' : '🛠️ Admin'}
          </button>
        </div>
      </nav>

      {showAdmin ? (
        isAdminLoggedIn ? (
          <Admin 
            onProductAdded={handleProductAddedSuccess} 
            editData={editProductData} 
            onCancelEdit={() => { setEditProductData(null); setShowAdmin(false); setActivePage('shop'); }}
          />
        ) : (
          <div style={{ background: '#070b19', padding: '60px 20px', minHeight: '75vh', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
            
            <style>{`
              @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(40px); }
                to { opacity: 1; transform: translateY(0); }
              }
              .login-box {
                animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                background: #0d162d !important;
                border: 1px solid rgba(26, 108, 255, 0.35) !important;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6), 0 0 15px rgba(26, 108, 255, 0.1) !important;
                transition: all 0.3s ease;
              }
              .login-box:hover {
                border-color: rgba(26, 108, 255, 0.6) !important;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.7), 0 0 25px rgba(26, 108, 255, 0.2) !important;
              }
              .login-btn {
                background: linear-gradient(135deg, #1a6cff, #004ecc) !important;
                transition: all 0.25s ease !important;
              }
              .login-btn:hover {
                transform: scale(1.03);
                box-shadow: 0 5px 15px rgba(26,108,255,0.4);
              }
              .input-field:focus {
                border-color: #1a6cff !important;
                box-shadow: 0 0 8px rgba(26,108,255,0.3) !important;
              }
              .reviews-section {
                background: #0f1a35;
                border: 1px solid rgba(26, 108, 255, 0.2);
                border-radius: 15px;
                padding: 35px 20px;
                margin: 50px auto 20px auto;
                max-width: 1100px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
              }
              .rating-big {
                font-size: 3.5rem;
                font-weight: bold;
                color: #fff;
                margin-bottom: 5px;
                font-family: sans-serif;
              }
              .stars-gold {
                color: #f59e0b;
                font-size: 1.8rem;
                margin-bottom: 10px;
                letter-spacing: 2px;
              }
              .reviews-count {
                color: #7a85a0;
                font-size: 0.95rem;
                margin-bottom: 25px;
                font-weight: 500;
              }
              .review-btn {
                display: inline-block;
                padding: 13px 28px;
                background: linear-gradient(135deg, #1a6cff, #004ecc);
                color: #fff;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                transition: all 0.25s ease;
                box-shadow: 0 4px 15px rgba(26, 108, 255, 0.3);
                font-size: 0.95rem;
              }
              .review-btn:hover {
                transform: scale(1.03);
                box-shadow: 0 6px 20px rgba(26, 108, 255, 0.5);
                color: #fff;
              }
              .insta-nav-btn:hover {
                transform: scale(1.05);
                opacity: 0.9;
              }
            `}</style>

            <form onSubmit={handleAdminLoginSubmit} className="login-box" style={{ padding: '40px 35px', borderRadius: '20px', width: '100%', maxWidth: '390px', textAlign: 'center' }}>
              <div style={{ fontSize: '2.8rem', marginBottom: '12px', display: 'inline-block' }}>🔐</div>
              <h2 style={{ color: '#fff', marginBottom: '8px', fontSize: '1.6rem', fontWeight: '700', letterSpacing: '0.5px' }}>Admin Control</h2>
              <p style={{ color: '#6b7c96', fontSize: '0.85rem', marginBottom: '30px' }}>ದಯವಿಟ್ಟು ಮುಂದುವರಿಯಲು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ</p>
              
              <div style={{ textAlign: 'left', marginBottom: '18px' }}>
                <label style={{ fontSize: '0.8rem', color: '#8fa0b7', display: 'block', marginBottom: '6px', fontWeight: '500' }}>Username</label>
                <input 
                  type="text" 
                  placeholder="Enter Username" 
                  value={adminUsername}
                  onChange={(e) => setAdminUsername(e.target.value)}
                  className="input-field"
                  style={{ width: '100%', padding: '13px 15px', borderRadius: '10px', border: '1px solid rgba(26,108,255,0.2)', background: '#060a15', color: '#fff', outline: 'none', boxSizing: 'border-box', fontSize: '0.95rem', transition: 'all 0.2s' }}
                  required
                  autoComplete="username"
                />
              </div>

              <div style={{ textAlign: 'left', marginBottom: '22px' }}>
                <label style={{ fontSize: '0.8rem', color: '#8fa0b7', display: 'block', marginBottom: '6px', fontWeight: '500' }}>Password</label>
                <input 
                  type="password" 
                  placeholder="Enter Admin Password" 
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  className="input-field"
                  style={{ width: '100%', padding: '13px 15px', borderRadius: '10px', border: '1px solid rgba(26,108,255,0.2)', background: '#060a15', color: '#fff', outline: 'none', boxSizing: 'border-box', fontSize: '0.95rem', transition: 'all 0.2s' }}
                  required
                  autoComplete="current-password"
                />
              </div>

              {loginError && (
                <p style={{ color: '#ff4d4d', fontSize: '0.85rem', marginBottom: '18px', fontWeight: 'bold', background: 'rgba(255,77,77,0.1)', padding: '8px', borderRadius: '6px', border: '1px solid rgba(255,77,77,0.2)' }}>
                  {loginError}
                </p>
              )}

              <button type="submit" className="login-btn" style={{ color: 'white', border: 'none', padding: '14px 25px', borderRadius: '10px', cursor: 'pointer', fontWeight: 'bold', width: '100%', fontSize: '1rem', marginTop: '5px' }}>
                Verify & Enter Dashboard
              </button>
            </form>
          </div>
        )
      ) : (
        <>
          {activePage === 'shop' && (
            <div>
              {/* 🎬 Hero Section */}
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

              {/* 🏷️ Categories Filter */}
              <div className="categories">
                {categories.map(cat => (
                  <button 
                    key={cat} 
                    className={cat === activeCategory ? 'cat-btn active' : 'cat-btn'} 
                    onClick={() => setActiveCategory(cat)}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* 🛍️ Products Section */}
              <div className="products-section">
                <h3>{activeCategory === 'All' ? 'All Products' : activeCategory}</h3>
                
                {loading ? (
                  <div className="loading">
                    Loading... <div className="spinner"></div>
                  </div>
                ) : filtered.length === 0 ? (
                  <div className="no-products">
                    😊 ಇನ್ನೂ products ಇಲ್ಲ — ಶೀಘ್ರದಲ್ಲೇ ಬರ್ತಿವೆ!
                  </div>
                ) : (
                  <div className="products-grid">
                    {filtered.map(product => (
                      <div 
                        className={product.available === false ? 'product-card not-available' : 'product-card'} 
                        key={product.product_id || product.id} 
                        style={{ position: 'relative' }}
                      >
                        
                        {isAdminLoggedIn && (
                          <div style={{ 
                            position: 'absolute', 
                            top: '10px', 
                            right: '10px', 
                            display: 'flex', 
                            gap: '5px', 
                            zIndex: 10, 
                            background: 'rgba(11,19,41,0.85)', 
                            padding: '6px', 
                            borderRadius: '8px', 
                            boxShadow: '0 4px 10px rgba(0,0,0,0.3)' 
                          }}>
                            <button 
                              onClick={() => handleEditClick(product)} 
                              style={{ background: '#f59e0b', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '11px' }}
                            >
                              ✏️ Edit
                            </button>
                            <button 
                              onClick={() => handleDeleteProduct(product.product_id || product.id)} 
                              style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '11px' }}
                            >
                              🗑️ Del
                            </button>
                          </div>
                        )}

                        <div 
                          className="product-card-img-wrap" 
                          onClick={() => setFullScreenImage(product.image)} 
                          style={{
                            cursor: 'zoom-in', 
                            position: 'relative', 
                            overflow: 'hidden',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <img 
                            src={product.image} 
                            alt={product.name} 
                            onError={e => { e.target.onerror = null; e.target.src = dolphin; }} 
                            style={{
                              filter: product.available === false ? 'brightness(60%) grayscale(20%)' : 'none',
                              transition: 'all 0.3s'
                            }}
                          />

                          {product.available === false && (
                            <div style={{
                              position: 'absolute',
                              top: '50%',
                              left: '50%',
                              transform: 'translate(-50%, -50%)',
                              zIndex: 6,
                              background: '#ef4444',
                              color: '#fff',
                              padding: '8px 16px',
                              borderRadius: '6px',
                              fontWeight: 'bold',
                              fontSize: '13px',
                              textTransform: 'uppercase',
                              boxShadow: '0 4px 15px rgba(239,68,68,0.6)',
                              letterSpacing: '1px',
                              whiteSpace: 'nowrap',
                              pointerEvents: 'none',
                              border: '1px solid rgba(255,255,255,0.2)'
                            }}>
                              🛑 Out of Stock
                            </div>
                          )}
                        </div>

                        <div className="product-info">
                          <span className="category-tag">{product.category}</span>
                          <h4>{product.name}</h4>
                          <p className="price">{product.price}</p>
                          {product.available !== false && (
                            // 🆕 Buy Now → Chat Box Open
                            <button className="buy-btn" onClick={() => handleBuyNow(product)}>
                              💬 Chat & Book
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* ⭐ Google Reviews Section */}
              <div className="reviews-section">
                <h3 style={{ color: '#4d9fff', marginBottom: '8px', fontSize: '1.6rem', fontWeight: '600' }}>
                  ✨ What Our Customers Say
                </h3>
                <p style={{ color: '#7a85a0', marginBottom: '20px', fontSize: '0.95rem' }}>
                  ನಮ್ಮ ಗ್ರಾಹಕರ ನಂಬಿಕೆ ಮತ್ತು ಪ್ರೀತಿ 🌸
                </p>
                
                <div className="rating-big">4.9</div>
                <div className="stars-gold">⭐⭐⭐⭐⭐</div>
                <div className="reviews-count">Based on 12 Google Reviews</div>
                
                <p style={{ color: '#f0f4ff', maxWidth: '650px', margin: '0 auto 25px auto', fontSize: '0.95rem', lineHeight: '1.6', fontStyle: 'italic' }}>
                  "Dolphin Trends offers the best premium collection of Kurtis, Tops, and Western Wear in Bangalore at unbeatable prices!"
                </p>

                <a 
                  href="https://share.google/UPBRCnDCHS8m48ymt" 
                  target="_blank" 
                  rel="noreferrer" 
                  className="review-btn"
                >
                  🚀 View All Reviews on Google
                </a>
              </div>
            </div>
          )}

          {/* 🏪 Branches Page */}
          {activePage === 'branches' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>🏪 Our Branches</h2>
                <p>Dolphin Trends — Bangalore ಅಲ್ಲಿ ನಮ್ಮಂಗಡಿಗಳು</p>
              </div>
              <div className="branch-grid">
                {[
                  { tag:'Main Branch', name:'Laggere', addr:'Anikethana Kishore Kendra Laggere, Bangalore — 560058', phone:'📞 +91 7795800741' },
                  { tag:'Branch 2', name:'Rajgopal nagar', addr:'Rajgopal nagar main road ,Peenya 2nd stage, Bangalore — 560058', phone:'📞 +91 9353838835' },
                ].map((b, i) => (
                  <div className="branch-card" key={i}>
                    <span className="branch-tag">{b.tag}</span>
                    <h3>{b.name}</h3>
                    <p>{b.addr}</p>
                    <p className="branch-phone">{b.phone}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 📞 Contact Page */}
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
                    { icon:'📱', label:'WhatsApp', value:'+91 9353838835' },
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
                  <h3>📍 Main Branch Address</h3>
                  {[
                    { icon:'🏪', label:'Shop Name', value:"Dolphin Trends — Women's Fashion Store" },
                    { icon:'📌', label:'Address', value:'Laggere Main Road, Bangalore — 560058' },
                    { icon:'🚇', label:'Nearest Metro', value:'Jalahalli Metro Station' },
                    { icon:'🚌', label:'Bus Stop', value:'Laggere Aladmara Bus Stop' },
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

          {/* 📍 Location Page */}
          {activePage === 'location' && (
            <div className="section-page">
              <div className="section-page-header">
                <h2>📍 Our Locations</h2>
                <p>Dolphin Trends — ನಮ್ಮಂಗಡಿಗಳ ವಿಳಾಸ</p>
              </div>
              
              <div className="map-embed" style={{ marginBottom: '40px' }}>
                <h3 style={{ color: '#4d9fff', marginBottom: '15px', fontSize: '1.4rem' }}>⭐ Main Branch — Laggere</h3>
                <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '15px', padding: '25px', marginBottom: '15px' }}>
                  <p style={{ color: '#f0f4ff', marginBottom: '10px' }}>📍 Anikethana Kishore Kendra, Laggere, Bangalore — 560058</p>
                  <p style={{ color: '#7a85a0', marginBottom: '15px' }}>⏰ Mon–Sun: 11:00 AM – 10:00 PM</p>
                  <a 
                    href="https://maps.app.goo.gl/tJQ47jqAsoLRQ1Ua7" 
                    target="_blank" 
                    rel="noreferrer" 
                    style={{ display: 'inline-block', padding: '12px 24px', background: '#1a6cff', color: '#fff', borderRadius: '10px', textDecoration: 'none', fontWeight: 'bold' }}
                  >
                    🗺️ Open in Google Maps
                  </a>
                </div>
                <h4 style={{ color: '#7a85a0', marginBottom: '10px', textAlign: 'center' }}>📸 Our Shop</h4>
                <div style={{ position: 'relative', width: '100%', maxWidth: '500px', height: '380px', margin: '0 auto', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(26,108,255,0.2)' }}>
                  <img 
                    src={shopImages[currentImgIndex]} 
                    alt="Shop" 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                  />
                  <button 
                    onClick={prevShopImage} 
                    style={{ position: 'absolute', top: '50%', left: '10px', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', width: '36px', height: '36px', borderRadius: '50%', cursor: 'pointer', fontSize: '18px' }}
                  >
                    ‹
                  </button>
                  <button 
                    onClick={nextShopImage} 
                    style={{ position: 'absolute', top: '50%', right: '10px', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', width: '36px', height: '36px', borderRadius: '50%', cursor: 'pointer', fontSize: '18px' }}
                  >
                    ›
                  </button>
                  <div style={{ position: 'absolute', bottom: '12px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '6px' }}>
                    {shopImages.map((_, idx) => (
                      <span 
                        key={idx} 
                        onClick={() => setCurrentImgIndex(idx)} 
                        style={{ width: '8px', height: '8px', borderRadius: '50%', background: currentImgIndex === idx ? '#1a6cff' : 'rgba(255,255,255,0.5)', cursor: 'pointer' }} 
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div className="map-embed">
                <h3 style={{ color: '#4d9fff', marginBottom: '15px', fontSize: '1.4rem' }}>🏪 Branch 2 — Rajgopal nagar</h3>
                <div style={{ background: '#0f1a35', border: '1px solid rgba(26,108,255,0.2)', borderRadius: '15px', padding: '25px' }}>
                  <p style={{ color: '#f0f4ff', marginBottom: '10px' }}>📍 Rajgopal nagar,main road,peenya 2nd stage— 560058</p>
                  <p style={{ color: '#7a85a0', marginBottom: '15px' }}>⏰ Mon–Sun: 11:00 AM – 10:00 PM</p>
                  <a 
                    href="https://maps.app.goo.gl/amrkmppGsdgprtx27" 
                    target="_blank" 
                    rel="noreferrer" 
                    style={{ display: 'inline-block', padding: '12px 24px', background: '#1a6cff', color: '#fff', borderRadius: '10px', textDecoration: 'none', fontWeight: 'bold' }}
                  >
                    🗺️ Open in Google Maps
                  </a>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* 📄 Footer */}
      <footer>
        <p><strong>🐬 Dolphin Trends</strong> | Developed by Jeevan___JD</p>
      </footer>

      {/* 🔍 Full Screen Image Viewer */}
      {fullScreenImage && (
        <div 
          onClick={() => setFullScreenImage(null)} 
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, cursor: 'zoom-out' }}
        >
          <img 
            src={fullScreenImage} 
            alt="Full" 
            style={{ maxWidth: '95%', maxHeight: '90vh' }} 
          />
        </div>
      )}

      {/* 🛒 Product Page Modal */}
      {viewProduct && (
        <ProductPage 
          product={viewProduct} 
          allProducts={products} 
          onClose={() => setViewProduct(null)} 
          onBook={p => setViewProduct(p)} 
        />
      )}

      {/* 🆕 Floating Chat Button - ಎಲ್ಲಾ pages ನಲ್ಲೂ ಕಾಣಿಸುತ್ತದೆ */}
      {!showAdmin && (
        <button
          onClick={handleOpenChat}
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '65px',
            height: '65px',
            background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
            borderRadius: '50%',
            border: 'none',
            color: '#fff',
            fontSize: '30px',
            cursor: 'pointer',
            boxShadow: '0 4px 25px rgba(26,108,255,0.5)',
            zIndex: 9998,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'transform 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          aria-label="Open chat"
        >
          💬
        </button>
      )}

      {/* 🆕 Chat Box Modal - ಎಲ್ಲಾ pages ನಲ್ಲೂ available */}
      {chatOpen && (
        <ChatBox 
          product={chatProduct} 
          onClose={() => setChatOpen(false)} 
        />
      )}
    </div>
  );
}

export default App;
