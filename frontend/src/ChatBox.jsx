import React, { useState, useEffect, useRef } from 'react';

function ChatBox({ orderTrigger, clearOrderTrigger }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! Welcome to Dolphin Trends. 👋", isUser: false, time: 'Just now' }
  ]);
  const [inputText, setInputText] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);

  // ಬ್ರೌಸರ್ ಟ್ಯಾಬ್ ಆಕ್ಟಿವ್ ಆಗಿದೆಯಾ ಇಲ್ವಾ ಅಂತ ಚೆಕ್ ಮಾಡೋದು (Red Dot ಅಲರ್ಟ್‌ಗಾಗಿ)
  useEffect(() => {
    if (isOpen && !document.hidden) {
      setUnreadCount(0);
    }
  }, [isOpen, messages]);

  // ಕಸ್ಟಮರ್ ಬೇರೆ ಟ್ಯಾಬ್‌ನಲ್ಲಿದ್ದಾಗ ಮೆಸೇಜ್ ಬಂದ್ರೆ Red Badge ಕೌಂಟ್ ಜಾಸ್ತಿ ಮಾಡೋದು
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isOpen) {
        setUnreadCount(0);
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [isOpen]);

  // 🛍️ ಕಸ್ಟಮರ್ ಆರ್ಡರ್ ಕನ್ಫರ್ಮ್ ಮಾಡಿದ ತಕ್ಷಣ ಆಟೋಮ್ಯಾಟಿಕ್ ಆಗಿ ಚಾಟ್ ಬಾಕ್ಸ್ ಓಪನ್ ಆಗೋ ಲಾಜಿಕ್
  useEffect(() => {
    if (orderTrigger) {
      setIsOpen(true);
      
      // ಆಟೋಮ್ಯಾಟಿಕ್ ಬುಕಿಂಗ್ ರಿಸೀವ್ಡ್ ಮೆಸೇಜ್ ಆಡ್ ಮಾಡೋದು
      const systemMsg = {
        id: Date.now(),
        text: `📦 Booking Request Received!\n\nProduct: ${orderTrigger.productName}\nSize: ${orderTrigger.size}\nPrice: ${orderTrigger.price}\n\nOur team will review this and update you shortly. 😊`,
        isUser: false,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, systemMsg]);
      clearOrderTrigger(); // ಟ್ರಿಗರ್ ಕ್ಲಿಯರ್ ಮಾಡೋದು
    }
  }, [orderTrigger, clearOrderTrigger]);

  // ಸ್ಕ್ರಾಲ್ ಆಟೋಮ್ಯಾಟಿಕ್ ಆಗಿ ಕೆಳಗೆ ಹೋಗೋಕೆ
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ಕಸ್ಟಮರ್ ನಾರ್ಮಲ್ ಚಾಟ್ ಮೆಸೇಜ್ ಕಳಿಸಿದಾಗ (Hi, Hello ಇತ್ಯಾದಿ)
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMsg = {
      id: Date.now(),
      text: inputText,
      isUser: true,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, newMsg]);
    setInputText('');

    // 🔗 TODO: ಇಲ್ಲಿ ಮುಂದೆ ನಾವು ಬ್ಯಾಕೆಂಡ್ ಮತ್ತು ಟೆಲಿಗ್ರಾಮ್ ಬಾಟ್‌ಗೆ ಈ ಮೆಸೇಜ್ ಕಳಿಸೋ ಸಾಕೆಟ್ ಕೋಡ್ ಬರೀತೀವಿ
    console.log("Sending to backend/telegram:", inputText);
  };

  return (
    <>
      <style>{chatBoxStyles}</style>
      
      <div className="chatbox-system-container">
        {/* ಚಾಟ್ ವಿಂಡೋ ಯುಐ */}
        {isOpen && (
          <div className="chatbox-window-box">
            <div className="chatbox-window-header">
              <div className="chatbox-admin-avatar">
                <span className="chatbox-online-green-dot"></span>
                🐬
              </div>
              <div className="chatbox-header-info">
                <h4>Dolphin Trends Support</h4>
                <p>Online | Real-time helper</p>
              </div>
              <button className="chatbox-close-x-btn" onClick={() => setIsOpen(false)}>✕</button>
            </div>

            {/* ಮೆಸೇಜ್ ಲಿಸ್ಟ್ */}
            <div className="chatbox-messages-body">
              {messages.map((msg) => (
                <div key={msg.id} className={`chatbox-message-row ${msg.isUser ? 'user-side' : 'admin-side'}`}>
                  <div className="chatbox-text-bubble">
                    {msg.text.split('\n').map((line, i) => <div key={i}>{line}</div>)}
                    <span className="chatbox-time-stamp">{msg.time}</span>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* ಇನ್‌ಪುಟ್ ಫೀಲ್ಡ್ */}
            <form className="chatbox-input-footer" onSubmit={handleSendMessage}>
              <input 
                type="text" 
                placeholder="Type a message (e.g., Hi, Hello)..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
              />
              <button type="submit">🕊️</button>
            </form>
          </div>
        )}

        {/* ಮೇನ್ ಫ್ಲೋಟಿಂಗ್ ಬಟನ್ ವಿತ್ ರೆಡ್ ಬ್ಯಾಡ್ಜ್ */}
        <button className={`chatbox-floating-trigger ${isOpen ? 'active-red' : ''}`} onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? '✕' : '💬'}
          {unreadCount > 0 && !isOpen && <span className="chatbox-red-badge-dot">{unreadCount}</span>}
        </button>
      </div>
    </>
  );
}

// ಪ್ರೀಮಿಯಂ ಬ್ಲೂ ಥೀಮ್ ಸಿಎಸ್ಎಸ್
const chatBoxStyles = `
  .chatbox-system-container { position: fixed; bottom: 25px; right: 25px; z-index: 999999; font-family: system-ui, -apple-system, sans-serif; }
  .chatbox-floating-trigger { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #1a6cff, #004ecc); color: #fff; border: 1px solid rgba(255,255,255,0.2); font-size: 26px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(26,108,255,0.4); position: relative; transition: all 0.3s; }
  .chatbox-floating-trigger.active-red { background: #ef4444; box-shadow: 0 4px 15px rgba(239,68,68,0.4); font-size: 20px; }
  .chatbox-red-badge-dot { position: absolute; top: -2px; right: -2px; background: #ef4444; color: white; border-radius: 50%; padding: 4px 8px; font-size: 11px; font-weight: bold; border: 2px solid #0a1428; }
  
  .chatbox-window-box { width: 340px; height: 450px; background: linear-gradient(135deg, #0f1a35 0%, #0a1428 100%); border: 1px solid rgba(26, 108, 255, 0.3); border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); margin-bottom: 15px; display: flex; flex-direction: column; overflow: hidden; animation: chatboxPopIn 0.3s cubic-bezier(0.16, 1, 0.3, 1); color: #fff; }
  .chatbox-window-header { background: rgba(26, 108, 255, 0.15); padding: 15px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid rgba(26, 108, 255, 0.2); position: relative; }
  .chatbox-admin-avatar { width: 40px; height: 40px; background: rgba(26,108,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; position: relative; border: 1px solid #1a6cff; }
  .chatbox-online-green-dot { width: 10px; height: 10px; background: #10b981; border-radius: 50%; position: absolute; bottom: 0; right: 0; border: 2px solid #0a1428; }
  .chatbox-header-info h4 { margin: 0; font-size: 14px; font-weight: 700; }
  .chatbox-header-info p { margin: 0; font-size: 11px; color: #a0b3d6; }
  .chatbox-close-x-btn { position: absolute; top: 18px; right: 15px; background: none; border: none; color: #a0b3d6; cursor: pointer; font-size: 16px; }
  
  .chatbox-messages-body { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: rgba(0,0,0,0.2); }
  .chatbox-message-row { display: flex; width: 100%; }
  .chatbox-message-row.user-side { justify-content: flex-end; }
  .chatbox-message-row.admin-side { justify-content: flex-start; }
  
  .chatbox-text-bubble { padding: 10px 14px; border-radius: 14px; font-size: 13px; line-height: 1.4; max-width: 80%; position: relative; }
  .user-side .chatbox-text-bubble { background: #1a6cff; color: white; border-radius: 14px 14px 0px 14px; }
  .admin-side .chatbox-text-bubble { background: rgba(26,108,255,0.15); color: #c8d6e5; border: 1px solid rgba(26,108,255,0.2); border-radius: 14px 14px 14px 0px; }
  .chatbox-time-stamp { display: block; font-size: 9px; color: #7a85a0; margin-top: 4px; text-align: right; }
  
  .chatbox-input-footer { padding: 12px; display: flex; gap: 8px; border-top: 1px solid rgba(26,108,255,0.2); background: rgba(0,0,0,0.3); }
  .chatbox-input-footer input { flex: 1; padding: 10px 12px; background: rgba(0,0,0,0.4); border: 1px solid rgba(26, 108, 255, 0.2); border-radius: 8px; color: white; outline: none; font-size: 13px; }
  .chatbox-input-footer input:focus { border-color: #1a6cff; }
  .chatbox-input-footer button { padding: 0 14px; background: #1a6cff; border: none; border-radius: 8px; color: white; cursor: pointer; font-size: 16px; }

  @keyframes chatboxPopIn { from { transform: scale(0.9) translateY(15px); opacity: 0; } to { transform: scale(1) translateY(0); opacity: 1; } }
`;

export default ChatBox;
