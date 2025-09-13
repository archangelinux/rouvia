'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, Send } from 'lucide-react';

interface ChatMessage {
  id: string;
  text: string;
  timestamp: Date;
}

export default function ChatInterface() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      text: message.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setMessage('');
    
     try {
      const res = await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMessage),
      });

      const result = await res.json();
      console.log('Server response:', result);
      } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 flex flex-col max-h-[40vh]">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.map((msg, index) => {
          const isRecent = index >= messages.length - 3;
          const opacity = isRecent ? 1 : Math.max(0.3, 1 - (messages.length - index) * 0.1);
          
          return (
            <div
              key={msg.id}
              className="animate-fade-in-left"
              style={{ opacity }}
            >
              <div className="text-gray-800 text-base leading-relaxed font-light">
                {msg.text.split('').map((char, charIndex) => (
                  <span
                    key={charIndex}
                    className="animate-char-fade-in"
                    style={{ 
                      animationDelay: `${charIndex * 0.02}s`,
                      animationFillMode: 'both'
                    }}
                  >
                    {char}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Field */}
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your route here"
            className="flex-1 border rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 text-gray-800 placeholder-gray-500"
            onKeyPress={(e) => e.key === 'Enter' && handleSubmit(e)}
          />
          
          {/* Voice Input Button */}
          <button
            type="button"
            className="rounded-full w-10 h-10 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors duration-150"
            title="Voice input"
          >
            <Mic size={18} />
          </button>
          
          {/* Send Button */}
          <button
            type="submit"
            onClick={handleSubmit}
            className="rounded-full w-10 h-10 flex items-center justify-center bg-black text-white hover:bg-gray-800 transition-colors duration-150"
            title="Send"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
