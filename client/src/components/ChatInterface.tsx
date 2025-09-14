"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Send, MessageCircle, Sparkles } from "lucide-react";
import FilterPanel from "./FilterPanel";
import { useRoute, type PlaceStop } from "@/components/context/route-context";
import { useAuth } from "@/contexts/AuthContext";

interface ChatMessage {
  id: string;
  text: string;
  timestamp: Date;
  role?: "user" | "assistant" | "system";
}

async function getUserLocation(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      ({ coords }) =>
        resolve({ latitude: coords.latitude, longitude: coords.longitude }),
      (error) => reject(error),
      { enableHighAccuracy: true }
    );
  });
}

interface ChatInterfaceProps {
  userSub?: string | null;
}

export default function ChatInterface({ userSub }: ChatInterfaceProps) {
  const { setStops, setWaypoints, setUserLocation } = useRoute();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<"chat" | "filters">("chat");

  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null
  );
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const API_URL_AUDIO = "http://localhost:8000/plan-route-audio";
  const API_URL_TEXT = "http://localhost:8000/plan-route-text";

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

  const pushStopsToContext = (stops: PlaceStop[] | unknown) => {
    if (!Array.isArray(stops)) return;
    const typed = stops as PlaceStop[];
    setStops(typed);
    // Mapbox expects [lng, lat]
    setWaypoints(typed.map((s) => [s.lng, s.lat] as [number, number]));
  };

  const loadingMessages = [
    "Analyzing your request...",
    "Optimizing route...",
    "Maximizing ratings...",
    "Calling Sam Altman...",
    "Finding the perfect spots...",
    "Calculating optimal path...",
    "Asking Mr.Goose for directions...",
    "Crunching travel data...",
    "Polishing your adventure..."
  ];

  const getRandomLoadingMessage = () => {
    return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
  };

  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const loadingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const createLoadingMessage = () => {
    const loadingId = appendMessage({ 
      text: getRandomLoadingMessage(), 
      role: "assistant" 
    });
    
    // Start cycling through messages
    setLoadingMessageIndex(0);
    loadingIntervalRef.current = setInterval(() => {
      setLoadingMessageIndex(prev => (prev + 1) % loadingMessages.length);
    }, 1500); // Change message every 1.5 seconds
    
    return loadingId;
  };

  const removeLoadingMessage = (loadingId: string) => {
    // Stop the interval
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current);
      loadingIntervalRef.current = null;
    }
    
    // Remove the loading message
    setMessages(prev => prev.filter(m => m.id !== loadingId));
  };

  // Typed message -> POST /plan-route-text (JSON) or enhanced endpoint
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    appendMessage({ text: message.trim(), role: "user" });
    const outbound = message.trim();
    setMessage("");

    // Add loading message
    const loadingId = createLoadingMessage();

    let location: { latitude: number; longitude: number } | null = null;
    try {
      location = await getUserLocation();
      if (location) setUserLocation(location);
    } catch {
      /* optional */
    }

    const payload = {
      text: outbound,
      // backend accepts {latitude, longitude} OR {lat, lng}
      location: location
        ? { latitude: location.latitude, longitude: location.longitude }
        : null,
      user_id: userSub,  // Use userSub from props
    };

    try {
      const res = await fetch(API_URL_TEXT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await res.json();

      // Remove loading message
      removeLoadingMessage(loadingId);

      pushStopsToContext(result.stops);

      // Enhanced response handling
      let botReply = result.reply || result.response || result.message || result.text;
      
      if (result.enhanced_metadata) {
        const metadata = result.enhanced_metadata;
        const personalLocations = metadata.personal_locations || [];
        const suggestions = metadata.unmatched_suggestions || [];
        
        if (personalLocations.length > 0) {
          botReply += `\n\n🎯 Found ${personalLocations.length} personal location(s): ${personalLocations.map(loc => loc.name).join(', ')}`;
        }
        
        if (suggestions.length > 0) {
          botReply += `\n\n💡 Suggestions: ${suggestions.map(s => s.suggestion).join('; ')}`;
        }
      }
      
      if (botReply)
        appendMessage({ text: String(botReply), role: "assistant" });
    } catch (err) {
      // Replace loading message with error
      removeLoadingMessage(loadingId);
      appendMessage({
        text: "Failed to send message to server.",
        role: "system",
      });
      console.error(err);
    }
  };

  // Voice -> POST /plan-route-audio (multipart/form-data)
  const handleVoiceClick = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream; // Store stream reference
        
        const recorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm' // More widely supported than wav
        });

        // Clear previous chunks
        audioChunksRef.current = [];

        recorder.ondataavailable = (e) => {
          console.log("📊 Data available:", e.data.size, "bytes");
          if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        recorder.onstop = async () => {
          console.log("🎙️ Recording stopped");
          console.log("🎙️ Audio chunks:", audioChunksRef.current.length);
          
          const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          console.log("🎙️ Blob size:", blob.size, "bytes");
          console.log("🎙️ Blob type:", blob.type);

          if (blob.size === 0) {
            console.error("❌ Empty audio blob! Recording may have been too short.");
            appendMessage({
              text: "Recording was too short or empty. Please hold the microphone button longer.",
              role: "system",
            });
            return;
          }

          const placeholderId = appendMessage({
            text: "Transcribing your voice...",
            role: "user",
          });

          // Add loading message for processing
          const loadingId = createLoadingMessage();

          let location: { latitude: number; longitude: number } | null = null;
          try {
            location = await getUserLocation();
            if (location) setUserLocation(location);
          } catch {
            /* optional */
          }

          const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
          const filename = `voice-${timestamp}.webm`;

          const formData = new FormData();
          formData.append("audio", blob, filename);
          if (location) formData.append("location", JSON.stringify(location));
          if (userSub) formData.append("user_id", userSub);  // Use userSub from props

          console.log("📤 Sending FormData with blob size:", blob.size);

          try {
            const res = await fetch(API_URL_AUDIO, {
              method: "POST",
              body: formData,
            });
            
            if (!res.ok) {
              const errorText = await res.text();
              console.error("Server error:", errorText);
              throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            
            const result = await res.json();

            const transcript: string = result.transcribed_text || "";
            replaceMessageText(
              placeholderId,
              transcript || "(No transcript returned)"
            );

            // Remove loading message
            removeLoadingMessage(loadingId);

            pushStopsToContext(result.stops);

            // Enhanced response handling for voice
            let botReply: string = result.message || "";
            
            if (result.enhanced_metadata) {
              const metadata = result.enhanced_metadata;
              const personalLocations = metadata.personal_locations || [];
              const suggestions = metadata.unmatched_suggestions || [];
              
              if (personalLocations.length > 0) {
                botReply += `\n\n🎯 Found ${personalLocations.length} personal location(s): ${personalLocations.map(loc => loc.name).join(', ')}`;
              }
              
              if (suggestions.length > 0) {
                botReply += `\n\n💡 Suggestions: ${suggestions.map(s => s.suggestion).join('; ')}`;
              }
            }
            
            if (botReply) appendMessage({ text: botReply, role: "assistant" });
          } catch (err) {
            replaceMessageText(
              placeholderId,
              "Transcription failed. Please try again."
            );
            // Remove loading message and show error
            removeLoadingMessage(loadingId);
            appendMessage({
              text: "Processing failed. Please try again.",
              role: "system",
            });
            console.error("Failed to send audio:", err);
          }

          // Clean up
          audioChunksRef.current = [];
        };

        // Start recording with timeslice to ensure regular data events
        recorder.start(100); // Request data every 100ms
        setMediaRecorder(recorder);
        setIsRecording(true);
        
        console.log("🎙️ Recording started");
        
      } catch (err) {
        console.error("❌ Failed to start recording:", err);
        appendMessage({
          text: "Could not access microphone. Please check permissions.",
          role: "system",
        });
      }
    } else {
      // Stop recording if active
      console.log("⏹️ Stopping recording...");
      if (mediaRecorder && mediaRecorder.state === "recording") {
        // Don't call requestData(), just stop
        mediaRecorder.stop();
      }
      
      // Clean up stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="bg-white rounded-tl-2xl rounded-tr-2xl rounded-br-2xl rounded-bl-2xl shadow-lg border border-gray-200 flex flex-col max-h-[40vh]">
      {/* Mode Toggle */}
      <div className="flex border-b border-gray-100">
        <button
          onClick={() => setMode("chat")}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors rounded-tl-2xl ${
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
          <Sparkles size={16} className="inline mr-2" />
          Sidequest
        </button>
      </div>


      {/* Content based on mode */}
      {mode === "chat" ? (
        <>
          {/* Messages Container */}
          <div className="max-h-100 overflow-y-auto p-4 space-y-3 min-h-0">
            {messages.map((msg, index) => {
              const isRecent = index >= messages.length - 3;
              const opacity = isRecent
                ? 1
                : Math.max(0.3, 1 - (messages.length - index) * 0.1);

              const isLoadingMessage = msg.role === "assistant" && 
                (msg.text.includes("Analyzing") || msg.text.includes("Optimizing") || 
                 msg.text.includes("Maximizing") || msg.text.includes("Calling") ||
                 msg.text.includes("Finding") || msg.text.includes("Calculating") || 
                 msg.text.includes("Asking") || msg.text.includes("Crunching") || 
                 msg.text.includes("Polishing"));

              return (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-left`}
                  style={{ opacity }}
                >
                  <div className={`rounded-lg px-4 py-2 max-w-[80%] break-words ${
                    msg.role === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200'
                  }`}>
                    <div className={`text-sm leading-relaxed font-light whitespace-pre-wrap break-words ${
                      msg.role === 'user' ? 'text-white' : 'text-gray-800'
                    }`}>
                      {isLoadingMessage ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin">⟳</span>
                          <span key={loadingMessageIndex} className="animate-pulse">
                            {loadingMessages[loadingMessageIndex]}
                          </span>
                        </span>
                      ) : (
                        msg.text.split('').map((char, charIndex) => (
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
                        ))
                )}
                    </div>
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
                    ? "bg-red-500 text-white animate-pulse"
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