"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Send, MessageCircle, Settings } from "lucide-react";
import FilterPanel from "./FilterPanel";

interface ChatMessage {
  id: string;
  text: string;
  timestamp: Date;
  // Optional role to style in future (user/assistant/system)
  role?: "user" | "assistant" | "system";
}

function getUserLocation(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        resolve({ latitude, longitude });
      },
      (error) => reject(error),
      { enableHighAccuracy: true }
    );
  });
}

export default function ChatInterface() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<"chat" | "filters">("chat");

  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null
  );
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);

  const API_URL = "http://localhost:8000/plan-route-audio";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const appendMessage = (partial: Omit<ChatMessage, "id" | "timestamp">) => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      ...partial,
    };
    setMessages((prev) => [...prev, msg]);
    return msg.id;
  };

  const replaceMessageText = (id: string, newText: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, text: newText } : m))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    // Show the user's typed message immediately
    appendMessage({ text: message.trim(), role: "user" });
    const outbound = message.trim();
    setMessage("");

    // Attach location and send as JSON
    let location: { latitude: number; longitude: number } | null = null;
    try {
      location = await getUserLocation();
    } catch (err) {
      console.warn("Location unavailable:", err);
    }

    const payload = {
      text: outbound,
      timestamp: new Date().toISOString(),
      location,
    };

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await res.json();

      // If your API returns a bot reply, show it
      const botReply =
        result.reply || result.response || result.message || result.text;
      if (botReply) {
        appendMessage({ text: String(botReply), role: "assistant" });
      }
    } catch (err) {
      appendMessage({
        text: "⚠️ Failed to send message to server.",
        role: "system",
      });
      console.error(err);
    }
  };

  const handleVoiceClick = async () => {
    if (!isRecording) {
      // Start recording
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        setAudioChunks((prev) => [...prev, e.data]);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        setAudioChunks([]);

        // Show a temporary placeholder in the chat while we transcribe
        const placeholderId = appendMessage({
          text: "🎙️ Transcribing…",
          role: "user",
        });

        // Try to get location (optional)
        let location: { latitude: number; longitude: number } | null = null;
        try {
          location = await getUserLocation();
        } catch (err) {
          console.warn("Location unavailable:", err);
        }

        // Create a unique filename and send to backend
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const filename = `voice-${timestamp}.wav`;

        const formData = new FormData();
        formData.append("audio", audioBlob, filename);
        if (location) {
          formData.append("location", JSON.stringify(location));
        }

        try {
          const res = await fetch(API_URL, { method: "POST", body: formData });
          const result = await res.json();

          // Flexible keys: transcript preferred; fallbacks for different server shapes
          const transcript = result.transcribed_text || "";

          if (transcript) {
            // Replace the placeholder with actual transcript so it looks like the user's message
            replaceMessageText(placeholderId, String(transcript));
          } else {
            // If server returns no transcript, keep placeholder but indicate issue
            replaceMessageText(placeholderId, "🎙️ (No transcript returned)");
          }

          // Optionally append an assistant/bot reply if provided
          const botReply = result.message || "";
          if (botReply) {
            appendMessage({ text: String(botReply), role: "assistant" });
          }
        } catch (err) {
          // Replace placeholder with error
          replaceMessageText(
            placeholderId,
            "⚠️ Transcription failed. Please try again."
          );
          console.error("Failed to send audio:", err);
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } else {
      // Stop recording
      mediaRecorder?.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 flex flex-col max-h-[40vh]">
      {/* Mode Toggle */}
      <div className="flex border-b border-gray-100">
        <button
          onClick={() => setMode("chat")}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            mode === "chat"
              ? "text-green-600 border-b-2 border-green-600 bg-green-50"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <MessageCircle size={16} className="inline mr-2" />
          Chat
        </button>
        <button
          onClick={() => setMode("filters")}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            mode === "filters"
              ? "text-green-600 border-b-2 border-green-600 bg-green-50"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <Settings size={16} className="inline mr-2" />
          Filters
        </button>
      </div>

      {/* Content based on mode */}
      {mode === "chat" ? (
        <>
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            {messages.map((msg, index) => {
              const isRecent = index >= messages.length - 3;
              const opacity = isRecent
                ? 1
                : Math.max(0.3, 1 - (messages.length - index) * 0.1);

              return (
                <div
                  key={msg.id}
                  className="animate-fade-in-left"
                  style={{ opacity }}
                >
                  <div className="text-gray-800 text-base leading-relaxed font-light">
                    {msg.text.split("").map((char, charIndex) => (
                      <span
                        key={charIndex}
                        className="animate-char-fade-in"
                        style={{
                          animationDelay: `${charIndex * 0.02}s`,
                          animationFillMode: "both",
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
            <form
              className="flex items-center space-x-4"
              onSubmit={handleSubmit}
            >
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your route here"
                className="flex-1 border rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 text-gray-800 placeholder-gray-500"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    (e.currentTarget.form as HTMLFormElement)?.requestSubmit();
                  }
                }}
              />

              {/* Voice Input Button */}
              <button
                type="button"
                onClick={handleVoiceClick}
                className={`rounded-full w-10 h-10 flex items-center justify-center transition-colors duration-150 ${
                  isRecording
                    ? "bg-red-500 text-white"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
                title={isRecording ? "Stop recording" : "Voice input"}
              >
                <Mic size={18} />
              </button>

              {/* Send Button */}
              <button
                type="submit"
                className="rounded-full w-10 h-10 flex items-center justify-center bg-black text-white hover:bg-gray-800 transition-colors duration-150"
                title="Send"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <FilterPanel />
        </div>
      )}
    </div>
  );
}
