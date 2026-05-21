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

  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
  const shopAddress = "Dolphin Trends, Rajagopala Nagar, Peenya 2nd Stage, Bangalore - 560058";
  const shopLocation = "https://maps.app.goo.gl/zQeV2fcEv2fY625Z7";
  const ownerPhone = "919353838835";

  const discount = product.original_price
    ? Math.round((1 - parseInt(product.price.replace('₹','')) / parseInt(product.original_price.replace('₹',''))) * 100)
    : 0;

  const similarProducts = allProducts
    ? allProducts.filter(p => p.category === product.category && p.id !== product.id)
    : [];

  useEffect(() => {
    fetch('https://dolphin-trends-3.onrender.com/reviews/' + product.id)
     .then(res => res.json())
.then(data => {
   setReviews(Array.isArray(data) ? data : [])
})
.catch(err => console.error(err));

  const handleBuyNow = () => {
    if (!selectedSize) { alert('⚠️ Please select a size!'); return; }
    if (!customerName || !customerPhone) { alert('⚠️ Name ಮತ್ತು Phone ಹಾಕಿ!'); return; }

    const customerMsg = "🎉 *Welcome to Dolphin Trends!* 🐬\n\nHi " + customerName + "!\n\nYou have selected:\n👗 *" + product.name + "*\n📏 Size: " + selectedSize + "\n💰 Price: " + product.price + "\n\nPlease visit our shop:\n📍 " + shopAddress + "\n🗺️ " + shopLocation + "\n\n⏰ Timings: 10AM - 9PM\n📞 Contact: 7411255628\n\nSee you soon! 😊🛍️";
    window.open("https://wa.me/91" + customerPhone + "?text=" + encodeURIComponent(customerMsg), '_blank');

    const ownerMsg = "🛍️ *New Buy Request!*\n\n👗 " + product.name + "\n📏 Size: " + selectedSize + "\n💰 " + product.price + "\n👤 " + customerName + "\n📱 " + customerPhone;
    window.open("https://wa.me/" + ownerPhone + "?text=" + encodeURIComponent(ownerMsg), '_blank');

    setShowBuyForm(false);
  };

  const handleAddReview = async () => {
    if (!reviewName || !reviewText) { alert('⚠️ Name ಮತ್ತು Review ಹಾಕಿ!'); return; }
    const review = { product_id: product.id, name: reviewName, text: reviewText, rating: reviewRating };
    const res = await fetch('https://dolphin-trends-3.onrender.com/reviews', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(review)
    });
    const data = await res.json();
    setReviews([...reviews, data]);
    setReviewName(''); setReviewText(''); setReviewRating(5);
  };

  return (
    <div className="product-page-overlay" onClick={onClose}>
      <div className="product-page-box animate-pop" onClick={e => e.stopPropagation()}>
        <button className="pp-close-btn" onClick={onClose}>✕</button>

        {/* Top Section */}
        <div className="pp-top">

          {/* Left - Image */}
          <div className="pp-img-box">
            <img src={product.image} alt={product.name} />
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
                  >{size}</button>
                ))}
              </div>
            </div>

            {/* Buy Now */}
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
                    <button className="confirm-buy-btn" onClick={handleBuyNow}>✅ Confirm</button>
                    <button className="cancel-buy-btn" onClick={() => setShowBuyForm(false)}>Cancel</button>
                  </div>
                </div>
              )
            ) : (
              <div style={{padding:'15px', background:'rgba(255,59,92,0.1)', borderRadius:'10px', color:'#ff3b5c', textAlign:'center', border:'1px solid rgba(255,59,92,0.3)', margin:'15px 0'}}>
                ❌ Not Available
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
            <p style={{color:'#7a85a0', textAlign:'center', padding:'20px'}}>😊 ಇನ್ನೂ reviews ಇಲ್ಲ!</p>
          ) : (
            reviews.map(review => (
              <div key={review.id} style={{background:'#0f0f1e', border:'1px solid #1a4fff44', borderRadius:'12px', padding:'15px', marginBottom:'12px'}}>
                <div style={{display:'flex', justifyContent:'space-between', marginBottom:'8px'}}>
                  <strong style={{color:'#f0f4ff'}}>{review.name}</strong>
                  <span>{'⭐'.repeat(review.rating)}</span>
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
              {similarProducts.map(p => (
                <div key={p.id}
                  onClick={() => onBook(p)}
                  style={{cursor:'pointer', background:'#0f0f1e', border:'1px solid #1a4fff44', borderRadius:'12px', padding:'10px', textAlign:'center', transition:'all 0.2s'}}
                >
                  <img src={p.image} alt={p.name} style={{width:'100%', height:'110px', objectFit:'cover', borderRadius:'8px', marginBottom:'8px'}} />
                  <p style={{color:'#f0f4ff', fontSize:'0.8rem', marginBottom:'4px'}}>{p.name}</p>
                  <p style={{color:'#4d9fff', fontSize:'0.85rem', fontWeight:'bold'}}>{p.price}</p>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default ProductPage;
