import React, { useState, useEffect, useRef } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function ChatBox({ product, onClose }) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedSize, setSelectedSize] = useState(product?.selectedSize || 'M');
  const [message, setMessage] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [chatStatus, setChatStatus] = useState('pending');
  const [hasNewMessage, setHasNewMessage] = useState(false);
  
  const pollingRef = useRef(null);
  const lastMessageCount = useRef(0);
  
  const sizes = ['S', 'M', 'L', 'XL', 'XXL'];

  // 🔔 Request Push Notification Permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(perm => {
        console.log('🔔 Notification permission:', perm);
      }).catch(err => {
        console.log('Notification error:', err);
      });
    }
  }, []);

  // 🔄 Polling for live updates
  useEffect(() => {
    if (!chatId) return;

    const poll = async () => {
      try {
        const response = await fetch(`${API}/api/chat/${chatId}/messages`);
        const data = await response.json();
        
        if (data.messages && data.messages.length > lastMessageCount.current) {
          lastMessageCount.current = data.messages.length;
          setMessages(data.messages);
          setChatStatus(data.status);
          
          const lastMsg = data.messages[data.messages.length - 1];
          if (lastMsg && lastMsg.from === 'admin') {
            setHasNewMessage(true);
            showBrowserNotification(lastMsg.message, data.status);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    pollingRef.current = setInterval(poll, 3000);
    poll();

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [chatId]);

  // 🔔 Browser Push Notification
  const showBrowserNotification = (message, status) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      const title = status === 'approved' ? '✅ Order Approved!' :
                    status === 'rejected' ? '❌ Out of Stock' :
                    status === 'size_no_stock' ? '📏 Size Not Available' :
                    '🐬 Dolphin Trends Update';
      
      try {
        new Notification(title, {
          body: message.replace(/\*/g, '').replace(/\n/g, ' ').substring(0, 100),
          icon: '/dolphin.jpg',
          badge: '/dolphin.jpg',
          tag: 'dolphin-chat',
          requireInteraction: true
        });
      } catch (e) {
        console.log('Notification error:', e);
      }
    }
  };

  // ✅ Submit - All fields at once
  const handleSubmit = async () => {
    if (!name.trim()) {
      alert('⚠️ Please enter your Name!');
      return;
    }
    if (!phone || phone.length !== 10) {
      alert('⚠️ Please enter valid 10-digit WhatsApp number!');
      return;
    }
    if (!selectedSize) {
      alert('⚠️ Please select a Size!');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('customer_name', name.trim());
      formData.append('customer_phone', phone);
      formData.append('product_name', product?.name || 'General Inquiry');
      formData.append('product_image', product?.image || '');
      formData.append('size', selectedSize);
      formData.append('price', product?.price || '0');
      formData.append('message', message.trim() || `Hi, I'm interested in ${product?.name}`);

      const response = await fetch(`${API}/api/chat-box`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setChatId(data.customer_chat_id);
        
        // ✅ Show welcome message IMMEDIATELY
        const welcomeMsg = {
          from: 'admin',
          message: data.welcome_message,
          timestamp: Date.now() / 1000
        };
        setMessages([welcomeMsg]);
        lastMessageCount.current = 1;
        
        setStep(2);
      } else {
        alert('❌ Failed to send. Please try again.');
      }
    } catch (err) {
      console.error('Error:', err);
      alert('❌ Server connection error!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}>
      <div style={styles.chatBox}>
        {/* Header */}
        <div style={styles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.5rem' }}>🐬</span>
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>Dolphin Trends</div>
              <div style={{ fontSize: '0.7rem', opacity: 0.85 }}>
                {chatStatus === 'pending' && '⏳ Waiting for admin...'}
                {chatStatus === 'approved' && '✅ Order Approved'}
                {chatStatus === 'rejected' && '❌ Out of Stock'}
                {chatStatus === 'size_no_stock' && '📏 Size Not Available'}
              </div>
            </div>
          </div>
          {hasNewMessage && (
            <span style={{ 
              animation: 'pulse 1s infinite', 
              fontSize: '1.2rem',
              marginRight: '8px'
            }}>🔔</span>
          )}
          <button 
            onClick={onClose} 
            style={styles.closeBtn}
            aria-label="Close chat"
          >
            ✕
          </button>
        </div>

        {/* Product Info */}
        {product && product.name && (
          <div style={styles.productInfo}>
            <img 
              src={product.image} 
              style={styles.productImg} 
              alt={product.name}
              onError={(e) => e.target.style.display = 'none'}
            />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>
                {product.name}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#7a85a0' }}>
                {product.price}
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Combined Form (Name + Phone + Size + Message) */}
        {step === 1 && (
          <div style={styles.formBody}>
            <h3 style={{ 
              marginTop: 0, 
              fontSize: '1.1rem',
              marginBottom: '15px',
              color: '#fff'
            }}>
              📝 Your Details
            </h3>

            {/* Name */}
            <input
              type="text"
              placeholder="👤 Your Name"
              value={name}
              onChange={e => setName(e.target.value)}
              style={styles.input}
              maxLength={50}
            />

            {/* Phone with +91 prefix */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ 
                padding: '12px', 
                background: '#0a0f1a', 
                border: '1px solid rgba(26,108,255,0.3)', 
                borderRight: 'none', 
                borderRadius: '10px 0 0 10px', 
                color: '#7a85a0', 
                fontSize: '0.9rem',
                fontWeight: 'bold'
              }}>+91</span>
              <input
                type="tel"
                placeholder="WhatsApp Number"
                value={phone}
                maxLength={10}
                onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
                style={{ 
                  ...styles.input, 
                  marginBottom: 0, 
                  borderRadius: '0 10px 10px 0', 
                  flex: 1 
                }}
              />
            </div>

            {/* Size Selection */}
            <div style={{ marginBottom: '12px' }}>
              <label style={{ 
                fontSize: '0.85rem', 
                color: '#7a85a0', 
                display: 'block', 
                marginBottom: '8px' 
              }}>
                📏 Select Size
              </label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {sizes.map(size => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => setSelectedSize(size)}
                    style={selectedSize === size ? styles.sizeBtnSelected : styles.sizeBtn}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* Message */}
            <textarea
              placeholder="💬 Message (optional)"
              value={message}
              onChange={e => setMessage(e.target.value)}
              rows={3}
              style={styles.textarea}
              maxLength={500}
            />

            <button 
              onClick={handleSubmit} 
              disabled={loading} 
              style={{
                ...styles.sendBtn,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? '⏳ Submitting...' : '✅ Book Now'}
            </button>

            <p style={{
              fontSize: '0.7rem',
              color: '#7a85a0',
              textAlign: 'center',
              marginTop: '12px',
              marginBottom: 0
            }}>
              🔒 Your info is secure with us
            </p>
          </div>
        )}

        {/* Step 2: Live Chat */}
        {step === 2 && (
          <div style={styles.chatBody}>
            {/* Live indicator */}
            <div style={styles.liveIndicator}>
              <span style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                background: chatStatus === 'pending' ? '#f59e0b' : '#10b981',
                borderRadius: '50%',
                marginRight: '6px',
                animation: 'pulse 1.5s infinite'
              }}></span>
              {chatStatus === 'pending' ? '🔴 Live updates active' : '✅ Conversation closed'}
            </div>

            {/* Messages List */}
            <div style={styles.messageList}>
              {messages.map((msg, i) => (
                <div 
                  key={i} 
                  style={{
                    ...styles.message,
                    background: msg.from === 'admin' 
                      ? 'linear-gradient(135deg, #1a6cff, #004ecc)' 
                      : '#2a3a5f',
                    alignSelf: msg.from === 'customer' ? 'flex-end' : 'flex-start',
                    borderTopLeftRadius: msg.from === 'admin' ? '4px' : '12px',
                    borderTopRightRadius: msg.from === 'customer' ? '4px' : '12px'
                  }}
                >
                  <div style={{ 
                    fontSize: '0.7rem', 
                    opacity: 0.85, 
                    marginBottom: '4px',
                    fontWeight: 'bold'
                  }}>
                    {msg.from === 'admin' ? '🐬 Dolphin Trends' : '👤 You'}
                  </div>
                  <div style={{ 
                    fontSize: '0.85rem', 
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.4',
                    wordBreak: 'break-word'
                  }}>
                    {msg.message}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {chatStatus === 'pending' && messages.length > 0 && (
                <div style={styles.typing}>
                  <span>●</span>
                  <span>●</span>
                  <span>●</span>
                  <span style={{marginLeft: '8px', fontSize: '0.75rem'}}>Admin is typing...</span>
                </div>
              )}
            </div>

            {/* Close button when done */}
            {chatStatus !== 'pending' && (
              <button 
                onClick={onClose} 
                style={{
                  ...styles.sendBtn,
                  margin: '10px 15px 15px',
                  background: chatStatus === 'approved' 
                    ? 'linear-gradient(135deg, #10b981, #059669)' 
                    : 'linear-gradient(135deg, #6b7280, #4b5563)'
                }}
              >
                {chatStatus === 'approved' ? '✅ Continue Shopping' : '✅ Done'}
              </button>
            )}
          </div>
        )}

        <style>{`
          @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.5; }
          }
          @keyframes typing {
            0%, 60%, 100% { opacity: 0.3; }
            30% { opacity: 1; }
          }
          @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          @keyframes slideUp {
            from { transform: translateY(30px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
          }
        `}</style>
      </div>
    </div>
  );
}

const styles = {
  // ✅ Full screen overlay
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.75)',
    backdropFilter: 'blur(5px)',
    WebkitBackdropFilter: 'blur(5px)',
    zIndex: 10000,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '15px',
    animation: 'fadeIn 0.3s ease'
  },
  // ✅ Chat box - centered, full screen style
  chatBox: {
    width: '100%',
    maxWidth: '480px',
    height: '90vh',
    maxHeight: '700px',
    background: '#0f1a35',
    border: '2px solid #1a6cff',
    borderRadius: '20px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
    color: '#fff',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    animation: 'slideUp 0.3s ease-out'
  },
  header: {
    background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
    padding: '12px 15px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexShrink: 0
  },
  closeBtn: {
    background: 'rgba(255,255,255,0.15)',
    border: 'none',
    color: '#fff',
    fontSize: '1.3rem',
    cursor: 'pointer',
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  productInfo: {
    background: '#0b1329',
    padding: '10px 15px',
    margin: '10px',
    borderRadius: '10px',
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
    flexShrink: 0,
    border: '1px solid rgba(26,108,255,0.2)'
  },
  productImg: {
    width: '55px',
    height: '55px',
    borderRadius: '8px',
    objectFit: 'cover',
    flexShrink: 0
  },
  // ✅ Form body with scroll
  formBody: {
    padding: '15px',
    overflowY: 'auto',
    flex: 1
  },
  input: {
    width: '100%',
    padding: '12px 14px',
    marginBottom: '12px',
    borderRadius: '10px',
    border: '1px solid rgba(26,108,255,0.3)',
    background: '#060a15',
    color: '#fff',
    fontSize: '0.95rem',
    boxSizing: 'border-box',
    outline: 'none'
  },
  textarea: {
    width: '100%',
    padding: '12px 14px',
    marginBottom: '12px',
    borderRadius: '10px',
    border: '1px solid rgba(26,108,255,0.3)',
    background: '#060a15',
    color: '#fff',
    fontSize: '0.9rem',
    resize: 'none',
    fontFamily: 'sans-serif',
    boxSizing: 'border-box',
    outline: 'none'
  },
  sizeBtn: {
    padding: '8px 16px',
    background: '#2a3a5f',
    color: '#fff',
    border: '1px solid rgba(26,108,255,0.3)',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: 'bold',
    minWidth: '50px',
    transition: 'all 0.2s'
  },
  sizeBtnSelected: {
    padding: '8px 16px',
    background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: 'bold',
    minWidth: '50px',
    boxShadow: '0 4px 12px rgba(26,108,255,0.4)',
    transform: 'scale(1.05)'
  },
  sendBtn: {
    width: '100%',
    padding: '14px',
    background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
    color: '#fff',
    border: 'none',
    borderRadius: '10px',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '1rem',
    transition: 'transform 0.2s'
  },
  chatBody: {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    minHeight: 0,
    padding: 0
  },
  liveIndicator: {
    textAlign: 'center',
    fontSize: '0.75rem',
    color: '#7a85a0',
    margin: '10px 15px',
    padding: '8px',
    background: 'rgba(26,108,255,0.1)',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  messageList: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    padding: '5px 15px',
    minHeight: '200px'
  },
  message: {
    padding: '10px 14px',
    borderRadius: '12px',
    maxWidth: '85%',
    fontSize: '0.85rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    wordWrap: 'break-word',
    whiteSpace: 'pre-wrap'
  },
  typing: {
    padding: '8px 14px',
    background: '#2a3a5f',
    borderRadius: '12px',
    fontSize: '0.85rem',
    color: '#7a85a0',
    alignSelf: 'flex-start',
    display: 'flex',
    alignItems: 'center',
    gap: '4px'
  }
};

export default ChatBox;
