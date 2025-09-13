# Rouvia Architecture

## System Overview

Rouvia is a smart hands-free driver assistance system that uses natural language processing and AI to create optimal routes for users. The system combines voice input, AI-powered intent parsing, and real-time mapping to provide intelligent navigation assistance.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Mapbox UI     │    │ • Voice API     │    │ • OpenAI Whisper│
│ • Chat Interface│    │ • LLM Gateway   │    │ • Google Gemini │
│ • Voice Controls│    │ • Route Engine  │    │ • Google Places │
│ • Route Display │    │ • Data Manager  │    │ • Google Routes │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Architecture

### Frontend Components (Next.js)

#### Core Components
- **MapboxContainer**: Main map display with route visualization
- **ChatInterface**: Voice and text input interface
- **RouteDisplay**: Shows generated routes and destinations
- **VoiceControls**: Handles voice input and feedback
- **DestinationEditor**: Allows manual editing of destinations

#### State Management
- **Route State**: Current route, destinations, constraints
- **Voice State**: Recording status, transcription results
- **UI State**: Map view, chat interface, loading states
- **User State**: Preferences, saved locations, history

### Backend Services (FastAPI)

#### Core Services
- **VoiceService**: Handles Whisper integration for speech-to-text
- **LLMService**: Manages Gemini integration for intent parsing
- **PlacesService**: Interfaces with Google Places API
- **RoutingService**: Manages Google Directions API integration
- **ConstraintService**: Handles distance, time, and preference constraints
- **UserDataService**: Manages user preferences and location history

#### API Endpoints
```
POST /api/voice/transcribe     # Convert speech to text
POST /api/llm/parse-intent     # Parse user intent from text
GET  /api/places/search        # Search for places
POST /api/routes/generate      # Generate optimal route
GET  /api/routes/{id}          # Get specific route
POST /api/constraints/apply    # Apply user constraints
GET  /api/user/preferences     # Get user preferences
POST /api/user/preferences     # Update user preferences
```

## Data Flow

### Voice-to-Route Pipeline

1. **Voice Input** → Whisper API → Text Transcription
2. **Text** → Gemini LLM → Intent Parsing
3. **Intent** → Google Places API → Place Options
4. **Places** → Gemini LLM → Optimal Destination Selection
5. **Destinations** → Google Directions API → Route Generation
6. **Route** → Frontend → Map Display

### Constraint Application

```
User Constraints (distance, time, preferences)
         ↓
Constraint Engine
         ↓
Filtered Place Options
         ↓
Optimized Route Selection
```

## Technology Stack

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type safety and better development experience
- **Tailwind CSS**: Utility-first styling
- **Mapbox GL JS**: Interactive maps and route visualization
- **Web Speech API**: Browser-based voice input
- **React Query**: Server state management

### Backend
- **FastAPI**: Modern Python web framework
- **Python 3.11**: Runtime environment
- **Pydantic**: Data validation and serialization
- **LangGraph**: AI workflow orchestration
- **Uvicorn**: ASGI server

### External Services
- **OpenAI Whisper**: Speech-to-text transcription
- **Google Gemini**: Large language model for intent parsing
- **Google Places API**: Location and business information
- **Google Directions API**: Route calculation and optimization
- **Mapbox API**: Map tiles and geocoding

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy and load balancing
- **PostgreSQL**: User data and preferences storage
- **Redis**: Caching and session management

## Security Considerations

### Data Protection
- Voice data is processed in real-time and not stored
- User location data is encrypted and anonymized
- API keys are stored securely using environment variables
- HTTPS enforcement for all communications

### Privacy
- User preferences are stored locally when possible
- Location history is opt-in and can be deleted
- No personal data is shared with third parties without consent

## Scalability

### Horizontal Scaling
- Stateless backend services
- Load balancer with Nginx
- Database read replicas
- CDN for static assets

### Performance Optimization
- Route caching for common destinations
- Lazy loading of map components
- Voice processing optimization
- API response compression

## Development Workflow

### Local Development
- Docker Compose for service orchestration
- Hot reload for both frontend and backend
- Mock services for external APIs during development
- Comprehensive logging and debugging tools

### Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- E2E tests for voice-to-route workflow
- Performance testing for route generation

## Future Enhancements

### Planned Features
- **Sidequest Mode**: Spontaneous route suggestions
- **Network Integration**: Connect with user's social networks
- **Predictive Routing**: ML-based route optimization
- **Multi-modal Transport**: Support for walking, cycling, transit
- **Real-time Updates**: Live traffic and incident data

### Technical Improvements
- **Offline Support**: Cached routes for areas with poor connectivity
- **Progressive Web App**: Mobile app-like experience
- **Advanced Analytics**: Route performance and user behavior insights
- **API Versioning**: Backward compatibility for client updates
