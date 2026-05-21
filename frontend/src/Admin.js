import React, { useState, useRef } from 'react';

function Admin({ onProductAdded }) {
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

  // ಫೋಟೋ ಆಯ್ದುಕೊಂಡಾಗ ಪ್ರಿವ್ಯೂ ತೋರಿಸಲು
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleAddProduct = async () => {
    const file = fileInputRef.current.files[0];

    // ವ್ಯಾಲಿಡೇಶನ್
    if (!formData.name || !formData.price || !file) {
      alert("⚠️ ದಯವಿಟ್ಟು ಫೋಟೋ, ಹೆಸರು ಮತ್ತು ಮಾರಾಟದ ಬೆಲೆಯನ್ನು ನಮೂದಿಸಿ!");
      return;
    }

    setLoading(true);

    // FastAPI ಬ್ಯಾಕೆಂಡ್‌ಗೆ ಕಳುಹಿಸಲು FormData ತಯಾರಿ
    const dataToSend = new FormData();
    dataToSend.append('name', formData.name);
    dataToSend.append('price', `₹${formData.price}`);
    dataToSend.append('original_price', formData.original_price ? `₹${formData.original_price}` : "");
    dataToSend.append('description', formData.description);
    dataToSend.append('category', formData.category);
    dataToSend.append('file', file);

    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com', {
        method: 'POST',
        body: dataToSend,
      });

      if (response.ok) {
        alert("✅ Product ಯಶಸ್ವಿಯಾಗಿ ಸೇವ್ ಆಗಿದೆ!");
        // ಫಾರ್ಮ್ ಅನ್ನು ಮೊದಲಿನ ಸ್ಥಿತಿಗೆ ತರುವುದು
        setFormData({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
        setPreview(null);
        fileInputRef.current.value = "";
        if (onProductAdded) onProductAdded();
      } else {
        alert("❌ ಸೇವ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ! ಬ್ಯಾಕೆಂಡ್ ಚೆಕ್ ಮಾಡಿ.");
      }
    } catch (error) {
      alert("❌ ಸರ್ವರ್ ಕನೆಕ್ಷನ್ ಎರರ್! FastAPI ರನ್ ಆಗುತ್ತಿದೆಯೇ ನೋಡಿ.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-container">
      <div className="admin-card">
        <h2>🛠️ Admin Panel</h2>
        <div className="form-section">
          
          {/* ಇಮೇಜ್ ಅಪ್‌ಲೋಡ್ ಸೆಕ್ಷನ್ */}
          <div className="input-group">
            <label>👗 Dress Photo</label>
            <input 
              type="file" 
              accept="image/*" 
              ref={fileInputRef} 
              onChange={handleImageChange} 
              className="file-input"
            />
            {preview && (
              <div className="image-preview">
                <img src={preview} alt="Preview" style={{width: '100px', marginTop: '10px', borderRadius: '8px'}} />
              </div>
            )}
          </div>

          {/* ಪ್ರಾಡಕ್ಟ್ ಹೆಸರು */}
          <div className="input-group">
            <label>Product Name</label>
            <input 
              type="text" 
              placeholder="eg: Silk Saree"
              value={formData.name} 
              onChange={(e) => setFormData({...formData, name: e.target.value})} 
            />
          </div>

          {/* ಡಿಸ್ಕ್ರಿಪ್ಷನ್ */}
          <div className="input-group">
            <label>Description</label>
            <textarea 
              placeholder="Enter product details..."
              rows="3"
              value={formData.description} 
              onChange={(e) => setFormData({...formData, description: e.target.value})} 
            />
          </div>

          {/* ಬೆಲೆಗಳ ಸೆಕ್ಷನ್ - ಇಲ್ಲಿ ಎರರ್ ಫಿಕ್ಸ್ ಮಾಡಲಾಗಿದೆ */}
          <div className="input-row">
            <div className="input-group">
              <label>Selling Price (₹)</label>
              <input 
                type="number" 
                placeholder="Selling Price" 
                value={formData.price} 
                onChange={(e) => setFormData({...formData, price: e.target.value})} 
              />
            </div>
            <div className="input-group">
              <label>Original Price (₹)</label>
              <input 
                type="number" 
                placeholder="Original Price" 
                value={formData.original_price} 
                onChange={(e) => setFormData({...formData, original_price: e.target.value})} 
              />
            </div>
          </div>

          {/* ಕೆಟಗರಿ ಸೆಲೆಕ್ಷನ್ */}
          <div className="input-group">
            <label>Category</label>
            <select value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})}>
              <option value="Tops">Tops</option>
              <option value="Kurthas Sets">Kurthas Sets</option>
              <option value="Jeans">Jeans</option>
              <option value=" Umbrella Sets"> Umbrella Sets</option>
              <option value="Western wear">Western wear</option>
              <option value="250 Tops">250 Tops</option>
              <option value="Kurtha Tops">Kurtha Tops</option>
              <option value="Jeans Tops">Jeans Tops</option>
              <option value="Leggins">Leggins</option>
              <option value="350 Sets">350 Sets</option>
              <option value="frocks">frocks</option>
            </select>
          </div>

          {/* ಸೇವ್ ಬಟನ್ */}
          <button className="add-btn" onClick={handleAddProduct} disabled={loading}>
            {loading ? "Saving..." : "✅ Add Product"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Admin;
