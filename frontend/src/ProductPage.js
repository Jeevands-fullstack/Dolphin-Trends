import React, { useState, useEffect } from 'react';

function ProductPage({ product, onClose, onBook, allProducts }) {
  const [reviews, setReviews] = useState([]);
  const [reviewName, setReviewName] = useState('');
  const [reviewText, setReviewText] = useState('');
  const [reviewRating, setReviewRating] = useState(5);
  const [selectedSize, setSelectedSize] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [showBuyForm, setShowBuyForm] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const shopAddress = "Dolphin Trends, Rajagopala Nagar, Peenya 2nd Stage, Bangalore - 560058";
  const shopLocation = "https://maps.app.goo.gl/zQeV2fcEv2fY625Z7";

  // Safe fallback for ID matching
  const currentId = product.product_id || product.id;

  const cleanPrice = (priceStr) => {
    if (!priceStr) return 0;
    return parseInt(priceStr.replace(/[^\d]/g, '')) || 0;
  };

  const discount = product.original_price
    ? Math.round((1 - cleanPrice(product.price) / cleanPrice(product.original_price)) * 100)
    : 0;

  const similarProducts = allProducts
    ? allProducts.filter(p => p.category === product.category && (p.product_id || p.id) !== currentId).reverse()
    : [];

  // Fetch reviews safely using currentId
  useEffect(() => {
    if (!currentId || currentId === "undefined") return;
    fetch('https://dolphin-trends-3.onrender.com/reviews/' + currentId)
      .then(res => res.json())
      .then(data => {
        setReviews(Array.isArray(data) ? data : []);
      })
      .catch(err => {
        console.error("Reviews fetch error:", err);
        setReviews([]);
      });
  }, [currentId]); 

  const handleBuyNow = async () => {
    if (!selectedSize) { alert('⚠️ Please select a size!'); return; }
    if (!customerName || !customerPhone) { alert('⚠️ Name mattu Phone haki!'); return; }

    setBookingLoading(true);

    const bookingPayload = {
      customer_name: customerName,
      customer_phone: customerPhone,
      product_name: product.name,
      image_url: product.image,
      size: selectedSize,
      price: product.price
    };

    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingPayload)
      });

      if (response.ok) {
        // ✅ ಹಳೇ window.open(wa.me) ಲೈನ್‌ಗಳನ್ನು ಪೂರ್ತಿಯಾಗಿ ತೆಗೆದುಹಾಕಲಾಗಿದೆ!
        // ಈಗ ಬ್ಯಾಕೆಂಡ್ ಹಿನ್ನೆಲೆಯಲ್ಲಿ ಕಸ್ಟಮರ್‌ಗೆ ಮತ್ತು ಅಡ್ಮಿನ್‌ಗೆ ಇಬ್ಬರಿಗೂ ವಾಟ್ಸಾಪ್ ಮೆಸೇಜ್ ಕಳಿಸುತ್ತದೆ.
        
        setShowBuyForm(false);
        setCustomerName('');
        setCustomerPhone('');
        setSelectedSize('');
        alert("🎉 Order Request Sent Successfully!\nCheck your WhatsApp for confirmation details shortly. 😊");
      } else {
        alert("❌ Failed to register booking on server. Try again.");
      }
    } catch (err) {
      console.error("Booking error:", err);
      alert("❌ Server Error while booking.");
    } finally {
      setBookingLoading(false);
    }
  };

  const handleAddReview = async () => {
    if (!reviewName || !reviewText) { alert('⚠️ Name mattu Review haki!'); return; }
    try {
      const review = { product_id: currentId, name: reviewName, text: reviewText, rating: reviewRating };
      const res = await fetch('https://dolphin-trends-3.onrender.com/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(review)
      });
      const data = await res.json();
      
      if (data && !data.error) {
        setReviews(prev => [...prev, data]);
      }
      setReviewName(''); setReviewText(''); setReviewRating(5);
    } catch (err) {
      console.error("Add review error:", err);
    }
  };

  return (
    <div className="product-page-overlay" onClick={onClose}>
      <div className="product-page-box animate-pop" onClick={e => e.stopPropagation()}>
        <button className="pp-close-btn" onClick={onClose}>✕</button>

        {/* Top Section */}
        <div className="pp-top">
          
          {/* Left - Image Box */}
          <div className="pp-img-box" style={{ 
            position: 'relative', 
            overflow: 'hidden', 
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            minHeight: '350px'
          }}>
            <img 
              src={product.image} 
              alt={product.name} 
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                filter: product.available === false ? 'brightness(60%) grayscale(30%)' : 'none', 
                transition: 'all 0.3s'
              }}
            />
            
            {/* 🔴 Out of stock banner */}
            {product.available === false && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                zIndex: 5,
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                pointerEvents: 'none'
              }}>
                <span style={{
                  background: '#ef4444',
                  color: '#fff',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontWeight: 'bold',
                  fontSize: '16px',
                  textTransform: 'uppercase',
                  boxShadow: '0 4px 20px rgba(239,68,68,0.7)',
                  letterSpacing: '1.5px',
                  border: '1px solid rgba(255,255,255,0.3)',
                  whiteSpace: 'nowrap'
                }}>
                  🛑 Out of Stock
                </span>
              </div>
            )}
          </div>

          {/* Right - Details */}
          <div className="pp-details">
            <span className="category-tag">{product.category}</span>
            <h2 className="pp-title">{product.name}</h2>

            {/* Price */}
            <div className="pp-price-row">
              <span className="pp-price">{product.price}</span>
              {product.original_price && (
                <>
                  <span className="pp-original">{product.original_price}</span>
                  <span className="pp-discount">{discount}% OFF</span>
                </>
              )}
            </div>

            {/* Description */}
            {product.description && (
              <div className="pp-desc">{product.description}</div>
            )}

            {/* Size */}
            <div className="size-section">
              <p style={{color:'#7a85a0', fontSize:'0.85rem', marginBottom:'10px'}}>📏 Select Size</p>
              <div className="size-options">
                {sizes.map(size => (
                  <button
                    key={size}
                    className={selectedSize === size ? 'size-btn selected' : 'size-btn'}
                    onClick={() => setSelectedSize(size)}
                    disabled={product.available === false}
                  >{size}</button>
                ))}
              </div>
            </div>

            {/* Buy Now / Out of stock message */}
            {product.available !== false ? (
              !showBuyForm ? (
                <button className="main-buy-btn" onClick={() => setShowBuyForm(true)}>
                  🛍️ Buy Now
                </button>
              ) : (
                <div className="buy-form-container animate-fade">
                  <div className="large-input-group">
                    <label>👤 Your Name</label>
                    <input type="text" placeholder="Enter your name" value={customerName} onChange={e => setCustomerName(e.target.value)} />
                  </div>
                  <div className="large-input-group">
                    <label>📱 Phone Number</label>
                    <input type="number" placeholder="Enter phone number" value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} />
                  </div>
                  <div className="buy-actions-row">
                    <button className="confirm-buy-btn" onClick={handleBuyNow} disabled={bookingLoading}>
                      {bookingLoading ? "Booking..." : "✅ Confirm"}
                    </button>
                    <button className="cancel-buy-btn" onClick={() => setShowBuyForm(false)}>Cancel</button>
                  </div>
                </div>
              )
            ) : (
              <div style={{
                padding: '14px', 
                background: 'rgba(239,68,68,0.1)', 
                borderRadius: '10px', 
                color: '#ef4444', 
                textAlign: 'center', 
                border: '1px solid rgba(239,68,68,0.25)', 
                margin: '15px 0',
                fontWeight: 'bold',
                fontSize: '15px'
              }}>
                🛑 This Product is Currently Out of Stock
              </div>
            )}

            {/* Shop Info */}
            <div className="pp-shop-info">
              <p>📍 {shopAddress}</p>
              <a href={shopLocation} target="_blank" rel="noreferrer" style={{color:'#4d9fff', textDecoration:'none', fontWeight:'600'}}>
                🗺️ View on Google Maps
              </a>
            </div>
          </div>
        </div>

        {/* Reviews */}
        <div className="pp-reviews">
          <h3 style={{color:'#4d9fff', marginBottom:'20px', fontFamily:'Playfair Display, serif'}}>⭐ Customer Reviews</h3>

          {reviews.length === 0 ? (
            <p style={{color:'#7a85a0', textAlign:'center', padding:'20px'}}>😊 Innu reviews illa!</p>
          ) : (
            <reviews.map((review, idx) => (
              <div key={review.id || idx} style={{background:'#0f0f1e', border:'1px solid #1a4fff44', borderRadius:'12px', padding:'15px', marginBottom:'12px'}}>
                <div style={{display:'flex', justifyContent:'space-between', marginBottom:'8px'}}>
                  <strong style={{color:'#f0f4ff'}}>{review.name}</strong>
                  <span>{'⭐'.repeat(review.rating || 5)}</span>
                </div>
                <p style={{color:'#7a85a0', fontSize:'0.9rem'}}>{review.text}</p>
              </div>
            ))
          )}

          {/* Add Review */}
          <div className="add-review-box animate-slide">
            <h4 style={{color:'#4d9fff', marginBottom:'15px'}}>✍️ Write a Review</h4>
            <div className="review-form">
              <input className="rev-input" type="text" placeholder="Your Name" value={reviewName} onChange={e => setReviewName(e.target.value)} />
              <textarea className="rev-text" placeholder="Your Review..." value={reviewText} onChange={e => setReviewText(e.target.value)} rows={3} />
              <div className="rev-footer">
                <select className="rev-select" value={reviewRating} onChange={e => setReviewRating(parseInt(e.target.value))}>
                  <option value={5}>⭐⭐⭐⭐⭐ 5</option>
                  <option value={4}>⭐⭐⭐⭐ 4</option>
                  <option value={3}>⭐⭐⭐ 3</option>
                  <option value={2}>⭐⭐ 2</option>
                  <option value={1}>⭐ 1</option>
                </select>
                <button className="submit-btn" onClick={handleAddReview}>✅ Submit</button>
              </div>
            </div>
          </div>
        </div>

        {/* Similar Products */}
        {similarProducts.length > 0 && (
          <div style={{borderTop:'1px solid #1a4fff44', paddingTop:'25px', marginTop:'20px'}}>
            <h3 style={{color:'#4d9fff', marginBottom:'20px', fontFamily:'Playfair Display, serif'}}>👗 Similar Products</h3>
            <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(130px, 1fr))', gap:'15px'}}>
              {similarProducts.map(p => {
                const simId = p.product_id || p.id;
                return (
                  <div key={simId}
                    onClick={() => onBook(p)}
                    style={{
                      cursor:'pointer', 
                      background:'#0f0f1e', 
                      border:'1px solid #1a4fff44', 
                      borderRadius:'12px', 
                      padding:'10px', 
                      textAlign:'center', 
                      transition:'all 0.2s',
                      position: 'relative',
                      opacity: p.available === false ? 0.75 : 1
                    }}
                  >
                    <img src={p.image} alt={p.name} style={{width:'100%', height:'110px', objectFit:'cover', borderRadius:'8px', marginBottom:'8px', filter: 'none'}} />
                    
                    {p.available === false && (
                      <span style={{position:'absolute', top:'45px', left:'50%', transform:'translateX(-50%)', background:'#ef4444', color:'#fff', fontSize:'9px', padding:'3px 6px', borderRadius:'4px', fontWeight:'bold', whiteSpace:'nowrap'}}>OUT OF STOCK</span>
                    )}
                    
                    <p style={{color:'#f0f4ff', fontSize:'0.8rem', marginBottom:'4px'}}>{p.name}</p>
                    <p style={{color:'#4d9fff', fontSize:'0.85rem', fontWeight:'bold'}}>{p.price}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default ProductPage;
