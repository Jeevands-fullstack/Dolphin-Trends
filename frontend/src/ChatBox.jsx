import React, { useState, useEffect, useRef } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function ChatBox({ product, onClose }) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [chatStatus, setChatStatus] = useState('pending');
  const [hasNewMessage, setHasNewMessage] = useState(false);
  
  const pollingRef = useRef(null);
  const lastMessageCount = useRef(0);

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
          
          // 🔔 Check if last message is from admin
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

    // Poll every 3 seconds
    pollingRef.current = setInterval(poll, 3000);
    poll(); // Initial poll

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

  // 🚀 Step 1: Open Chat
  const handleOpenChat = async () => {
    // Validation
    if (!name.trim()) {
      alert('⚠️ Please enter your Name!');
      return;
    }

    if (!phone || phone.length !== 10 || !/^\d{10}$/.test(phone)) {
      alert('⚠️ Please enter valid 10-digit WhatsApp number!');
      return;
    }
    
    setLoading(true);
    
    try {
      // Try to get push subscription
      let pushSub = null;
      if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
          const registration = await navigator.serviceWorker.ready;
          // Optional: Subscribe to push (requires VAPID key)
        } catch (e) {
          console.log('Service worker not ready:', e);
        }
      }

      const formData = new FormData();
      formData.append('customer_name', name.trim());
      formData.append('customer_phone', phone);
      formData.append('product_name', product?.name || 'General Inquiry');
      formData.append('product_image', product?.image || '');
      formData.append('size', product?.selectedSize || 'M');
      formData.append('price', product?.price || '0');
      formData.append('message', message.trim() || `Hi, I'm interested in ${product?.name}`);
      if (pushSub) formData.append('push_subscription', pushSub);

      const response = await fetch(`${API}/api/chat-box`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setChatId(data.customer_chat_id);
        setStep(2); // Move to chat screen
        
        // Add user's initial message
        if (message.trim()) {
          setMessages([{
            from: 'customer',
            message: message.trim(),
            timestamp: Date.now() / 1000
          }]);
        } else {
          // Show welcome message immediately
          setMessages([{
            from: 'admin',
            message: data.welcome_message,
            timestamp: Date.now() / 1000
          }]);
        }
      } else {
        const err = await response.json().catch(() => ({}));
        alert(`❌ Failed: ${err.detail || 'Please try again'}`);
      }
    } catch (err) {
      console.error('Chat Error:', err);
      alert('❌ Server connection error!');
    } finally {
      setLoading(false);
    }
  };

  return (
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

      {/* Step 1: Form */}
      {step === 1 && (
        <div style={{ padding: '20px' }}>
          <h3 style={{ 
            marginTop: 0, 
            fontSize: '1.1rem',
            marginBottom: '15px',
            color: '#fff'
          }}>
            📝 Your Details
          </h3>
          
          <input
            type="text"
            placeholder="👤 Your Name"
            value={name}
            onChange={e => setName(e.target.value)}
            style={styles.input}
            maxLength={50}
          />
          
          <input
            type="tel"
            placeholder="📱 WhatsApp Number (10 digits)"
            value={phone}
            maxLength={10}
            onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
            style={styles.input}
          />
          
          <textarea
            placeholder="💬 Message (optional)"
            value={message}
            onChange={e => setMessage(e.target.value)}
            rows={3}
            style={styles.textarea}
            maxLength={500}
          />
          
          <button 
            onClick={handleOpenChat} 
            disabled={loading} 
            style={{
              ...styles.sendBtn,
              opacity: loading ? 0.6 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '⏳ Opening Chat...' : '💬 Open Chat'}
          </button>
          
          <p style={{
            fontSize: '0.7rem',
            color: '#7a85a0',
            textAlign: 'center',
            marginTop: '12px'
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
            {messages.length === 0 && (
              <div style={{ 
                textAlign: 'center', 
                color: '#7a85a0', 
                padding: '20px',
                fontSize: '0.85rem'
              }}>
                ⏳ Loading messages...
              </div>
            )}
            
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
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
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
                <div style={{
                  fontSize: '0.65rem',
                  opacity: 0.6,
                  marginTop: '4px',
                  textAlign: 'right'
                }}>
                  {msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : ''}
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

          {/* Action Buttons */}
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
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

const styles = {
  chatBox: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    width: '380px',
    maxWidth: '95vw',
    height: '600px',
    maxHeight: '85vh',
    background: '#0f1a35',
    border: '2px solid #1a6cff',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
    zIndex: 9999,
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
    background: 'none',
    border: 'none',
    color: '#fff',
    fontSize: '1.3rem',
    cursor: 'pointer',
    padding: '4px 8px',
    lineHeight: 1,
    borderRadius: '4px'
  },
  productInfo: {
    background: '#0b1329',
    padding: '10px 12px',
    margin: '10px',
    borderRadius: '8px',
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
    flexShrink: 0
  },
  productImg: {
    width: '50px',
    height: '50px',
    borderRadius: '6px',
    objectFit: 'cover',
    flexShrink: 0
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    marginBottom: '10px',
    borderRadius: '8px',
    border: '1px solid rgba(26,108,255,0.3)',
    background: '#060a15',
    color: '#fff',
    fontSize: '0.9rem',
    boxSizing: 'border-box',
    outline: 'none'
  },
  textarea: {
    width: '100%',
    padding: '10px 12px',
    marginBottom: '10px',
    borderRadius: '8px',
    border: '1px solid rgba(26,108,255,0.3)',
    background: '#060a15',
    color: '#fff',
    fontSize: '0.9rem',
    resize: 'vertical',
    fontFamily: 'sans-serif',
    boxSizing: 'border-box',
    outline: 'none'
  },
  sendBtn: {
    width: '100%',
    padding: '12px',
    background: 'linear-gradient(135deg, #1a6cff, #004ecc)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '0.95rem',
    transition: 'transform 0.2s'
  },
  chatBody: {
    padding: '0 15px 15px',
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    minHeight: 0
  },
  liveIndicator: {
    textAlign: 'center',
    fontSize: '0.75rem',
    color: '#7a85a0',
    marginBottom: '10px',
    padding: '6px 10px',
    background: 'rgba(26,108,255,0.1)',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  messageList: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '5px 0',
    minHeight: '200px',
    maxHeight: '400px'
  },
  message: {
    padding: '10px 12px',
    borderRadius: '12px',
    maxWidth: '85%',
    fontSize: '0.85rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    wordWrap: 'break-word'
  },
  typing: {
    padding: '8px 12px',
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
