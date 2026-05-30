import React, { useState, useRef, useEffect } from 'react';

function Admin({ onProductAdded, setFullScreenImage }) {
  const [formData, setFormData] = useState({ name: '', description: '', price: '', original_price: '', category: 'Tops' });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const [bookings, setBookings] = useState([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);

  useEffect(() => { fetchBookings(); }, []);

  const fetchBookings = async () => {
    setBookingsLoading(true);
    try {
      const response = await fetch('https://dolphin-trends-3.onrender.com/api/admin/bookings');
      if (response.ok) {
        const data = await response.json();
        setBookings(data);
      }
    } catch (error) { console.error(error); } 
    finally { setBookingsLoading(false); }
  };

  const handleBookingAction = async (bookingId, action) => {
    if (!window.confirm(`Jeevan, do you want to proceed?`)) return;
    try {
      const response = await fetch(`https://dolphin-trends-3.onrender.com/api/admin/update-booking?booking_id=${bookingId}&action=${action}`, { method: 'POST' });
      if (response.ok) { alert(`✅ Success!`); fetchBookings(); }
    } catch (error) { alert("❌ Error!"); }
  };

  return (
    <div style={{ background: '#0b1329', padding: '20px', color: '#fff' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        
        {/* ಟೇಬಲ್ 1: ಸಿಂಗಲ್ ಬುಕಿಂಗ್ ಬಾಕ್ಸ್ ಮಾತ್ರ ಇಲ್ಲಿದೆ ಜೀವನ್ */}
        <div style={{ background: '#1a233d', padding: '20px', borderRadius: '12px' }}>
          <h2>📥 Customer Bookings List</h2>
          {bookingsLoading ? <p>Loading...</p> : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#24335c', borderBottom: '2px solid #475569' }}>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Photo</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Customer</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Phone</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Product</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.length === 0 ? <tr><td colSpan="6" style={{ padding: '20px', textAlign: 'center' }}>No bookings!</td></tr> : (
                    bookings.map((b) => (
                      <tr key={b.booking_id} style={{ borderBottom: '1px solid #24335c' }}>
                        <td style={{ padding: '12px' }}>
                          {b.product_image && <img src={b.product_image} alt="product" onClick={() => setFullScreenImage(b.product_image)} style={{ width: '50px', height: '65px', objectFit: 'cover', borderRadius: '4px', cursor: 'pointer' }} />}
                        </td>
                        <td style={{ padding: '12px' }}>{b.customer_name}</td>
                        <td style={{ padding: '12px' }}>{b.customer_phone}</td>
                        <td style={{ padding: '12px' }}>{b.product_name}</td>
                        <td style={{ padding: '12px', color: b.status === 'Pending' ? '#f59e0b' : '#10b981' }}>{b.status}</td>
                        <td style={{ padding: '12px' }}>
                          {b.status === 'Pending' && (
                            <div style={{ display: 'flex', gap: '5px' }}>
                              <button onClick={() => handleBookingAction(b.booking_id, 'agree')} style={{ background: '#28a745', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Agree</button>
                              <button onClick={() => handleBookingAction(b.booking_id, 'disagree')} style={{ background: '#dc3545', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}>Disagree</button>
                            </div>
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

      </div>
    </div>
  );
}

export default Admin;
