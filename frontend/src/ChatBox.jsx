import React, { useState, useEffect, useRef } from 'react';

const API = 'https://dolphin-trends-3.onrender.com';

function ChatBox({ orderTrigger, clearOrderTrigger }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! Welcome to Dolphin Trends. 👋", isUser: false, time: 'Just now', timestamp: Date.now() / 1000 }
  ]);
  const [inputText, setInputText] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);
  const [customerChatId, setCustomerChatId] = useState(null);
  const [lastTimestamp, setLastTimestamp] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [bookingStatus, setBookingStatus] = useState('pending');
  const messagesEndRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // 🆕 Load customer_chat_id from localStorage on mount
  useEffect(() => {
    const savedChatId = localStorage.getItem('dolphin_chat_id');
    const savedMessages = localStorage.getItem('dolphin_chat_messages');
    
    if (savedChatId) {
      setCustomerChatId(savedChatId);
      // Fetch latest messages from server
      pollMessages(savedChatId, 0);
    }
    
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        if (parsed.length > 0) {
          setMessages(parsed);
        }
      } catch (e) {
        console.error('Failed to parse saved messages', e);
      }
    }
  }, []);

  // 🆕 When customer books → save chat_id and open chatbox
  useEffect(() => {
    if (orderTrigger && orderTrigger.customer_chat_id) {
      const chatId = orderTrigger.customer_chat_id;
      setCustomerChatId(chatId);
      localStorage.setItem('dolphin_chat_id', chatId);
      setIsOpen(true);

      const systemMsg = {
        id: Date.now(),
        text: `📦 Booking Request Received!\n\nProduct: ${orderTrigger.productName}\nSize: ${orderTrigger.size}\nPrice: ${orderTrigger.price}\n\nOur team will review this and update you shortly. 😊`,
        isUser: false,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: Date.now() / 1000
      };

      setMessages(prev => [...prev, systemMsg]);
      clearOrderTrigger();
    }
  }, [orderTrigger, clearOrderTrigger]);

  // 🆕 Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('dolphin_chat_messages', JSON.stringify(messages));
    }
  }, [messages]);

  // 🆕 Poll for new messages every 4 seconds when chatbox is open AND we have a chat_id
  useEffect(() => {
    if (isOpen && customerChatId) {
      pollMessages(customerChatId, lastTimestamp);
      pollIntervalRef.current = setInterval(() => {
        pollMessages(customerChatId, lastTimestamp);
      }, 4000);
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [isOpen, customerChatId, lastTimestamp]);

  // 🆕 Clear unread count when chatbox opens
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
    }
  }, [isOpen, messages]);

  // 🆕 Visibility change - reset unread when tab is active
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isOpen) {
        setUnreadCount(0);
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [isOpen]);

  // 🆕 Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 🆕 Poll messages from backend
  const pollMessages = async (chatId, since) => {
    try {
      const response = await fetch(`${API}/api/chat/${chatId}/messages?since=${since}`);
      const data = await response.json();

      if (data.status === 'success' && data.messages && data.messages.length > 0) {
        const newMsgs = data.messages.map(msg => ({
          id: msg.timestamp * 1000 + Math.random(),
          text: msg.message,
          isUser: msg.from === 'customer',
          time: new Date(msg.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          timestamp: msg.timestamp,
          type: msg.type
        }));

        setMessages(prev => [...prev, ...newMsgs]);

        // Update last timestamp
        const maxTimestamp = Math.max(...data.messages.map(m => m.timestamp));
        setLastTimestamp(maxTimestamp);

        // If admin sent a message and chat is closed → increment unread
        if (!isOpen) {
          const adminMsgs = newMsgs.filter(m => !m.isUser);
          if (adminMsgs.length > 0) {
            setUnreadCount(prev => prev + adminMsgs.length);
          }
        }
      }

      // Update booking status
      if (data.booking_status) {
        setBookingStatus(data.booking_status);
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  };

  // 🆕 Send customer message to backend
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // If no chat_id yet, create one by saving to local storage with temp ID
    // Actually, we need chat_id from a booking. If no booking, just show locally.
    if (!customerChatId) {
      alert('⚠️ Please book a product first to start chatting with us!');
      return;
    }

    setIsSending(true);
    const messageText = inputText;
    setInputText('');

    // Optimistic update - add message immediately
    const optimisticMsg = {
      id: Date.now(),
      text: messageText,
      isUser: true,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: Date.now() / 1000,
      sending: true
    };
    setMessages(prev => [...prev, optimisticMsg]);

    try {
      const formData = new FormData();
      formData.append('customer_chat_id', customerChatId);
      formData.append('message', messageText);

      const response = await fetch(`${API}/api/send-customer-message`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        // Mark message as sent
        setMessages(prev => prev.map(m => 
          m.id === optimisticMsg.id ? { ...m, sending: false } : m
        ));
      } else {
        alert('❌ Failed to send message. Please try again.');
        setMessages(prev => prev.filter(m => m.id !== optimisticMsg.id));
      }
    } catch (error) {
      console.error('Send error:', error);
      alert('❌ Network error. Please try again.');
      setMessages(prev => prev.filter(m => m.id !== optimisticMsg.id));
    } finally {
      setIsSending(false);
    }
  };

  // 🆕 Clear chat history
  const clearChat = () => {
    if (!window.confirm('Clear all chat history? Your booking will remain active.')) return;
    localStorage.removeItem('dolphin_chat_messages');
    localStorage.removeItem('dolphin_chat_id');
    setMessages([{
      id: 1,
      text: "Hello! Welcome to Dolphin Trends. 👋",
      isUser: false,
      time: 'Just now',
      timestamp: Date.now() / 1000
    }]);
    setCustomerChatId(null);
    setLastTimestamp(0);
    setUnreadCount(0);
    setBookingStatus('pending');
  };

  return (
    <>
      <style>{chatBoxStyles}</style>
      
      <div className="chatbox-system-container">
        {/* Chat Window */}
        {isOpen && (
          <div className="chatbox-window-box">
            <div className="chatbox-window-header">
              <div className="chatbox-admin-avatar">
                <span className="chatbox-online-green-dot"></span>
                🐬
              </div>
              <div className="chatbox-header-info">
                <h4>Dolphin Trends Support</h4>
                <p>
                  {customerChatId 
                    ? `Chat ID: ${customerChatId.slice(0, 6)}... • ${bookingStatus}` 
                    : 'Online | Real-time helper'}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px', position: 'absolute', top: '15px', right: '45px' }}>
                {customerChatId && (
                  <button 
                    onClick={clearChat} 
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#a0b3d6',
                      cursor: 'pointer',
                      fontSize: '14px',
                      padding: '4px'
                    }}
                    title="Clear chat"
                  >
                    🗑️
                  </button>
                )}
              </div>
              <button className="chatbox-close-x-btn" onClick={() => setIsOpen(false)}>✕</button>
            </div>

            {/* Messages List */}
            <div className="chatbox-messages-body">
              {messages.map((msg) => (
                <div 
                  key={msg.id} 
                  className={`chatbox-message-row ${msg.isUser ? 'user-side' : 'admin-side'}`}
                >
                  <div className="chatbox-text-bubble">
                    {msg.text.split('\n').map((line, i) => <div key={i}>{line}</div>)}
                    <span className="chatbox-time-stamp">
                      {msg.sending && '⏳ '}
                      {msg.time}
                    </span>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form className="chatbox-input-footer" onSubmit={handleSendMessage}>
              <input 
                type="text" 
                placeholder={customerChatId ? "Type your message..." : "Book a product first to chat..."}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isSending || !customerChatId}
              />
              <button type="submit" disabled={isSending || !customerChatId}>
                {isSending ? '⏳' : '🕊️'}
              </button>
            </form>
          </div>
        )}

        {/* Floating Button with Red Badge */}
        <button 
          className={`chatbox-floating-trigger ${isOpen ? 'active-red' : ''} ${unreadCount > 0 ? 'has-badge' : ''}`} 
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? '✕' : '💬'}
          {unreadCount > 0 && !isOpen && (
            <span className="chatbox-red-badge-dot">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>
      </div>
    </>
  );
}

const chatBoxStyles = `
  .chatbox-system-container { 
    position: fixed; bottom: 25px; right: 25px; z-index: 999999; 
    font-family: system-ui, -apple-system, sans-serif; 
  }
  
  .chatbox-floating-trigger { 
    width: 60px; height: 60px; border-radius: 50%; 
    background: linear-gradient(135deg, #1a6cff, #004ecc); 
    color: #fff; border: 1px solid rgba(255,255,255,0.2); 
    font-size: 26px; cursor: pointer; 
    display: flex; align-items: center; justify-content: center; 
    box-shadow: 0 4px 15px rgba(26,108,255,0.4); 
    position: relative; transition: all 0.3s; 
  }
  .chatbox-floating-trigger:hover { transform: scale(1.05); }
  .chatbox-floating-trigger.active-red { 
    background: #ef4444; box-shadow: 0 4px 15px rgba(239,68,68,0.4); 
    font-size: 20px; 
  }
  .chatbox-floating-trigger.has-badge { animation: chatboxPulse 1.5s infinite; }
  
  @keyframes chatboxPulse {
    0%, 100% { box-shadow: 0 4px 15px rgba(239,68,68,0.4); }
    50% { box-shadow: 0 4px 25px rgba(239,68,68,0.8), 0 0 0 8px rgba(239,68,68,0.2); }
  }
  
  .chatbox-red-badge-dot { 
    position: absolute; top: -2px; right: -2px; 
    background: #ef4444; color: white; border-radius: 50%; 
    padding: 4px 7px; font-size: 11px; font-weight: bold; 
    border: 2px solid #0a1428; min-width: 22px; text-align: center;
  }
  
  .chatbox-window-box { 
    width: 360px; height: 480px; 
    background: linear-gradient(135deg, #0f1a35 0%, #0a1428 100%); 
    border: 1px solid rgba(26, 108, 255, 0.3); 
    border-radius: 16px; 
    box-shadow: 0 10px 40px rgba(0,0,0,0.5); 
    margin-bottom: 15px; 
    display: flex; flex-direction: column; 
    overflow: hidden; 
    animation: chatboxPopIn 0.3s cubic-bezier(0.16, 1, 0.3, 1); 
    color: #fff; 
  }
  
  .chatbox-window-header { 
    background: rgba(26, 108, 255, 0.15); 
    padding: 15px; 
    display: flex; align-items: center; gap: 12px; 
    border-bottom: 1px solid rgba(26, 108, 255, 0.2); 
    position: relative; 
  }
  
  .chatbox-admin-avatar { 
    width: 40px; height: 40px; 
    background: rgba(26,108,255,0.2); 
    border-radius: 50%; 
    display: flex; align-items: center; justify-content: center; 
    font-size: 20px; position: relative; 
    border: 1px solid #1a6cff; 
  }
  
  .chatbox-online-green-dot { 
    width: 10px; height: 10px; 
    background: #10b981; border-radius: 50%; 
    position: absolute; bottom: 0; right: 0; 
    border: 2px solid #0a1428; 
    animation: greenPulse 2s infinite;
  }
  
  @keyframes greenPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
  
  .chatbox-header-info h4 { margin: 0; font-size: 14px; font-weight: 700; }
  .chatbox-header-info p { margin: 0; font-size: 10px; color: #a0b3d6; }
  
  .chatbox-close-x-btn { 
    position: absolute; top: 18px; right: 15px; 
    background: none; border: none; 
    color: #a0b3d6; cursor: pointer; 
    font-size: 16px; 
  }
  
  .chatbox-messages-body { 
    flex: 1; padding: 15px; 
    overflow-y: auto; 
    display: flex; flex-direction: column; gap: 10px; 
    background: rgba(0,0,0,0.2); 
  }
  
  .chatbox-message-row { display: flex; width: 100%; }
  .chatbox-message-row.user-side { justify-content: flex-end; }
  .chatbox-message-row.admin-side { justify-content: flex-start; }
  
  .chatbox-text-bubble { 
    padding: 10px 14px; border-radius: 14px; 
    font-size: 13px; line-height: 1.4; 
    max-width: 80%; position: relative; 
    word-wrap: break-word;
  }
  .user-side .chatbox-text-bubble { 
    background: #1a6cff; color: white; 
    border-radius: 14px 14px 0px 14px; 
  }
  .admin-side .chatbox-text-bubble { 
    background: rgba(26,108,255,0.15); color: #c8d6e5; 
    border: 1px solid rgba(26,108,255,0.2); 
    border-radius: 14px 14px 14px 0px; 
  }
  .chatbox-time-stamp { 
    display: block; font-size: 9px; color: #7a85a0; 
    margin-top: 4px; text-align: right; 
  }
  
  .chatbox-input-footer { 
    padding: 12px; display: flex; gap: 8px; 
    border-top: 1px solid rgba(26,108,255,0.2); 
    background: rgba(0,0,0,0.3); 
  }
  .chatbox-input-footer input { 
    flex: 1; padding: 10px 12px; 
    background: rgba(0,0,0,0.4); 
    border: 1px solid rgba(26, 108, 255, 0.2); 
    border-radius: 8px; color: white; 
    outline: none; font-size: 13px; 
  }
  .chatbox-input-footer input:focus { border-color: #1a6cff; }
  .chatbox-input-footer input:disabled { opacity: 0.5; cursor: not-allowed; }
  .chatbox-input-footer button { 
    padding: 0 14px; background: #1a6cff; 
    border: none; border-radius: 8px; 
    color: white; cursor: pointer; 
    font-size: 16px; 
  }
  .chatbox-input-footer button:disabled { opacity: 0.5; cursor: not-allowed; }
  
  @keyframes chatboxPopIn { 
    from { transform: scale(0.9) translateY(15px); opacity: 0; } 
    to { transform: scale(1) translateY(0); opacity: 1; } 
  }
  
  @media (max-width: 480px) {
    .chatbox-window-box { width: calc(100vw - 40px); height: 70vh; }
    .chatbox-system-container { right: 10px; bottom: 10px; }
  }
`;

export default ChatBox;
