<!-- Improved compatibility of back to top link -->
<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<img width="1440" height="777" alt="rouvia" src="https://github.com/user-attachments/assets/8517a75c-d8ae-4f77-82e2-089afbfe2406" />

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h1 align="center">Rouvia</h1>

  <p align="center">
    AI voice assistant for your everyday travels  
    <br />
    <a href="https://youtu.be/BBaWlYHI5M0" target="_blank"><strong>View Demo »</strong></a>
    <br />
  </p>
</div>

---

## 📖 About The Project

Rouvia is a smart, hands-free travel assistant that turns navigation into a conversation.  
Instead of manually typing and juggling multiple apps, users can simply **talk or text** their plans.  
Rouvia processes natural language, understands complex multi-stop requests, and builds optimized routes—making travel both **safer** and **more enjoyable**.

### Inspiration
Navigation apps today aren’t built for how humans actually communicate. Drivers are forced into rigid commands, creating unsafe distractions. We imagined: *what if trip planning was as natural as talking to a friend who knows the area?*  

That idea became Rouvia.

---

## ✨ Features

- **Smart Map & Route Planning**  
  Context-aware intent parsing using Google Gemini. Handles multi-destination requests.
- **Voice-First Navigation**  
  Hands-free control with OpenAI Whisper transcription + natural language processing.
- **Unstructured Data Processing**  
  Converts messy or incomplete speech into structured navigation data. Confidence scoring & fallback mechanisms ensure reliability.
- **Intelligent Route Optimization**  
  Real-time constraints (time, distance, preferences). Integration with Google Directions API.
- **Sidequest Mode**  
  Generates spontaneous activity-based routes based on mood, budget, and interests.
- **Personalized Experience**  
  Learns from behavior patterns, saves places like *Home, Work, Gym*, and adapts over time.

---

## 🛠️ How We Built It

Rouvia is a **modern full-stack AI application** powered by a multi-stage processing pipeline.

### Frontend
- **Next.js 15**, **React**, **TypeScript**
- **Tailwind CSS** for styling
- **Mapbox GL JS** for interactive maps
- **React Query** for server state
- **Web Speech API** for browser-based voice input

### Backend
- **FastAPI** with Python 3.11
- **Pydantic** for validation
- **LangGraph** for orchestrating AI workflows
- **Uvicorn** for async performance

### External AI & APIs
- **OpenAI Whisper** → voice transcription  
- **Google Gemini** → natural language intent parsing  
- **Google Places & Directions APIs** → business info + routing  
- **Cohere** → trendiness scoring and multimodal analysis  

### Infrastructure
- **Docker** for containerization
- **Nginx** reverse proxy
- **MongoDB** for user data & preferences
- **Redis** for caching & session management
- **Kubernetes** for scalability (future-ready)
