"use client";
import { useState } from "react";

type ChatboxProps = {
  open: boolean;
  onToggle: () => void;
};

export default function Chatbox({ open, onToggle }: ChatboxProps) {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, input]);
    setInput("");
  };

  return (
    <div className={`transition-all ${open ? "w-80" : "w-12"} h-[500px] bg-white shadow-xl rounded-xl overflow-hidden`}>
      {/* Header */}
      <div className="flex items-center justify-between p-2 bg-gray-200">
        <span className="font-bold">{open ? "Chatbot" : ""}</span>
        <button onClick={onToggle} className="px-2">≡</button>
      </div>

      {/* Messages */}
      {open && (
        <div className="flex flex-col h-full">
          <div className="flex-1 p-2 overflow-y-auto">
            {messages.map((msg, idx) => (
              <div key={idx} className="mb-2 bg-blue-100 p-2 rounded">{msg}</div>
            ))}
          </div>

          {/* Input */}
          <div className="p-2 border-t flex">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 border rounded px-2"
              placeholder="Type a message..."
            />
            <button onClick={handleSend} className="ml-2 px-3 bg-blue-500 text-white rounded">Send</button>
          </div>
        </div>
      )}
    </div>
  );
}