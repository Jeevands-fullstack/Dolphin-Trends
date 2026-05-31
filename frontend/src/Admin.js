import React, { useState, useEffect } from 'react';
import './Admin.css';

const API = 'https://dolphin-trends-3.onrender.com';

function Admin({ onProductAdded, editData, onCancelEdit }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [originalPrice, setOriginalPrice] = useState('');
  const [category, setCategory] = useState('Leggings');
  const [available, setAvailable] = useState(true);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // 📝 ಹಳೆಯ ಕ್ಯಾಟಗರಿ ಲಿಸ್ಟ್ ಜಾಗದಲ್ಲಿ ನಿನ್ನ ಲೈವ್ ಡೇಟಾಬೇಸ್‌ಗೆ ಮ್ಯಾಚ್ ಆಗುವ ಇತ್ತೀಚಿನ ಕ್ಯಾಟಗರಿಗಳು
  const categories = [
    'Leggings', 'Suit Set', 'Kurthas', 'Umbrella', 'Jeans',
    'Patiala Pants', 'Kurtha Top', 'Umbrella Sets', 'Frocks',
    'Western Wear', 'Gym Pants', '250 Tops', '350 Tops', 'Jeans Tops', 'Tops'
  ];

  // 🔄 ಎಡಿಟ್ ಮಾಡೋಕೆ ಕ್ಲಿಕ್ ಮಾಡಿದಾಗ ಹಳೆಯ ಡೇಟಾವನ್ನು ಫಾರ್ಮ್‌ಗೆ ಲೋಡ್ ಮಾಡುವುದು
  useEffect(() => {
    if (editData) {
      setName(editData.name || '');
      setDescription(editData.description || '');
      
      // ₹ ಸಿಂಬಲ್ ಇದ್ದರೆ ತೆಗೆದು ಬರೀ ನಂಬರ್ ಮಾತ್ರ ಇನ್‌ಪುಟ್‌ಗೆ ಸೆಟ್ ಮಾಡುವುದು
      const p = String(editData.price || '').replace('₹', '').trim();
      setPrice(p);
      
      const op = String(editData.original_price || '').replace('₹', '').trim();
      setOriginalPrice(op);
      
      setCategory(editData.category || 'Leggings');
      setAvailable(editData.available !== false);
      setImagePreview(editData.image || null);
      setImageFile(null); 
    } else {
      // ರೀಸೆಟ್ ಫಾರ್ಮ್
      setName('');
      setDescription('Beautiful design crafted with rich fabric.');
      setPrice('');
      setOriginalPrice('');
      setCategory('Leggings');
      setAvailable(true);
      setImagePreview(null);
      setImageFile(null);
    }
  }, [editData]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImageFile(file);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('description', description);
      formData.append('price', `₹${price}`);
      formData.append('original_price', originalPrice ? `₹${originalPrice}` : '');
      formData.append('category', category);
      formData.append('available', String(available));

      if (imageFile) {
        formData.append('image', imageFile);
      }

      let url = `${API}/products`;
      let method = 'POST';

      if (editData) {
        // ಎಡಿಟ್ ಮೋಡ್‌ನಲ್ಲಿದ್ದಾಗ ಆಯಾ ಪ್ರಾಡಕ್ಟ್ ಐಡಿಗೆ PUT ರಿಕ್ವೆಸ್ಟ್ ಹೋಗುತ್ತದೆ
        const pId = editData.product_id || editData.id;
        url = `${API}/products/${pId}`;
        method = 'PUT';
      }

      const response = await fetch(url, {
        method: method,
        body: formData,
      });

      if (response.ok) {
        alert(editData ? '✅ Product Updated Successfully!' : '✅ Product Added Successfully!');
        if (onProductAdded) onProductAdded();
      } else {
        const errText = await response.text();
        alert(`❌ Error: ${errText || 'Submission failed'}`);
      }
    } catch (err) {
      console.error(err);
      alert('❌ Server Error! ದಯವಿಟ್ಟು ನೆಟ್‌ವರ್ಕ್ ಚೆಕ್ ಮಾಡಿ.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="admin-container" style={{ maxWidth: '600px', margin: '30px auto', padding: '20px', background: '#0d162d', borderRadius: '15px', border: '1px solid rgba(26,108,255,0.2)', color: '#fff' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid rgba(26,108,255,0.1)', paddingBottom: '10px' }}>
        <h2 style={{ margin: 0, color: '#4d9fff' }}>
          {editData ? '🔄 Edit Product Details' : '➕ Add New Product'}
        </h2>
        {editData && (
          <button type="button" onClick={onCancelEdit} style={{ background: '#6b7c96', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
            Cancel Edit
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        
        {/* 👗 ಇಮೇಜ್ ಅಪ್ಲೋಡ್ ಸೆಕ್ಷನ್ */}
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: '#8fa0b7' }}>
            👗 Dress Photo {editData && '(Change madbekidre new file choose madi)'}
          </label>
          <input type="file" accept="image/*" onChange={handleFileChange} required={!editData} style={{ color: '#8fa0b7', marginBottom: '10px' }} />
          {imagePreview && (
            <div style={{ marginTop: '5px' }}>
              <img src={imagePreview} alt="Preview" style={{ width: '100px', height: '120px', objectFit: 'cover', borderRadius: '8px', border: '2px solid #1a6cff' }} />
            </div>
          )}
        </div>

        {/* 🏷️ ಪ್ರಾಡಕ್ಟ್ ಹೆಸರು - ಇವಾಗ ಪೂರ್ತಿ ಅನ್‌ಲಾಕ್ ಆಗಿದೆ, ಚೇಂಜ್ ಮಾಡಬಹುದು! */}
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: '#8fa0b7' }}>Product Name</label>
          <input 
            type="text" 
            value={name} 
            onChange={(e) => setName(e.target.value)} 
            placeholder="Enter Product Name (e.g., Premium Dress)" 
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(26,108,255,0.3)', background: '#060a15', color: '#fff', boxSizing: 'border-box' }}
            required 
          />
        </div>

        {/* 📝 ಡಿಸ್ಕ್ರಿಪ್ಷನ್ */}
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: '#8fa0b7' }}>Description</label>
          <textarea 
            value={description} 
            onChange={(e) => setDescription(e.target.value)} 
            rows="3"
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(26,108,255,0.3)', background: '#060a15', color: '#fff', boxSizing: 'border-box', fontFamily: 'sans-serif' }}
            required
          />
        </div>

        {/* 💰 ಪ್ರೈಸ್ ಸೆಕ್ಷನ್ */}
        <div style={{ display: 'flex', gap: '15px' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: '#8fa0b7' }}>Selling Price (₹)</label>
            <input 
              type="number" 
              value={price} 
              onChange={(e) => setPrice(e.target.value)} 
              placeholder="1500" 
              style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(26,108,255,0.3)', background: '#060a15', color: '#fff', boxSizing: 'border-box' }}
              required 
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: '#8fa0b7' }}>Original Price (₹)</label>
            <input 
              type="number" 
              value={originalPrice} 
              onChange={(e) => setOriginalPrice(e.target.value)} 
              placeholder="1999" 
              style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(26,108,255,0.3)', background: '#060a15', color: '#fff', boxSizing: 'border-box' }}
            />
          </div>
        </div>

        {/* 🗂️ ಕ್ಯಾಟಗರಿ ಸೆಲೆಕ್ಷನ್ */}
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: '#8fa0b7' }}>Category</label>
          <select 
            value={category} 
            onChange={(e) => setCategory(e.target.value)} 
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(26,108,255,0.3)', background: '#060a15', color: '#fff', boxSizing: 'border-box', cursor: 'pointer' }}
          >
            {categories.map(cat => (
              <option key={cat} value={cat} style={{ background: '#0d162d' }}>{cat}</option>
            ))}
          </select>
        </div>

        {/* 🚦 ಅವೈಲೆಬಿಲಿಟಿ ಸ್ಟೇಟಸ್ (In Stock / Out of Stock) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '5px' }}>
          <input 
            type="checkbox" 
            id="available" 
            checked={available} 
            onChange={(e) => setAvailable(e.target.checked)} 
            style={{ width: '18px', height: '18px', cursor: 'pointer' }}
          />
          <label htmlFor="available" style={{ fontSize: '0.95rem', color: '#fff', cursor: 'pointer', fontWeight: '500' }}>
            {available ? '🟢 In Stock (ಯಾವುದೇ ತೊಂದರೆ ಇಲ್ಲದೆ ಗ್ರಾಹಕರು ಖರೀದಿಸಬಹುದು)' : '🔴 Out of Stock (ಪ್ರಾಡಕ್ಟ್ ಮೇಲೆ ಬ್ಯಾನರ್ ತೋರಿಸು)'}
          </label>
        </div>

        {/* 🚀 ಸಬ್ಮಿಟ್ ಬಟನ್ */}
        <button 
          type="submit" 
          disabled={submitting}
          style={{ width: '100%', padding: '14px', borderRadius: '10px', border: 'none', background: 'linear-gradient(135deg, #1a6cff, #004ecc)', color: '#fff', fontWeight: 'bold', fontSize: '1rem', cursor: submitting ? 'not-allowed' : 'pointer', marginTop: '10px', boxShadow: '0 4px 15px rgba(26, 108, 255, 0.3)', transition: 'all 0.2s' }}
        >
          {submitting ? 'Processing...' : editData ? '🚀 Update Product Details' : '➕ Save & Publish Product'}
        </button>

      </form>
    </div>
  );
}

export default Admin;

