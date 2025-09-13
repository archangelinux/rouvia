# Rouvia 🚀

A modern full-stack web application built with Next.js and FastAPI, featuring a clean monorepo structure with Docker support for both development and production environments.

## 📋 Overview

Rouvia is a full-stack application that demonstrates modern web development practices:

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python 3.11
- **Database**: In-memory storage (easily extensible to PostgreSQL/MongoDB)
- **Containerization**: Docker with multi-stage builds
- **Reverse Proxy**: Nginx for production deployments
- **Development**: Hot reload for both frontend and backend

## 🏗️ Architecture

```
rouvia/
├── client/                 # Next.js frontend application
│   ├── src/app/           # Next.js 13+ app directory
│   ├── public/            # Static assets
│   ├── Dockerfile         # Frontend container configuration
│   └── package.json       # Frontend dependencies
├── server/                # FastAPI backend application
│   ├── main.py           # FastAPI application entry point
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile        # Backend container configuration
│   └── package.json      # Backend scripts
├── docker-compose.yml     # Production Docker setup
├── docker-compose.dev.yml # Development Docker setup
├── nginx.conf            # Reverse proxy configuration
└── package.json          # Root workspace scripts
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** >= 18.0.0
- **npm** >= 8.0.0
- **Python** >= 3.11
- **Docker** (optional, for containerized deployment)

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/archangelinux/rouvia.git
   cd rouvia
   ```

2. **Install dependencies**
   ```bash
   npm run install:all
   ```

3. **Start the services**
   ```bash
   # Terminal 1 - Frontend
   npm run dev:client
   
   # Terminal 2 - Backend
   npm run dev:server
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Docker Development

1. **Start development containers**
   ```bash
   npm run docker:up-dev
   ```

2. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Option 3: Docker Production

1. **Build and start production containers**
   ```bash
   npm run docker:build
   npm run docker:up
   ```

2. **Access the application**
   - Application: http://localhost (Nginx reverse proxy)
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🛠️ Available Scripts

### Root Level Commands

```bash
# Development
npm run dev:client          # Start Next.js frontend
npm run dev:server          # Start FastAPI backend
npm run install:all         # Install all dependencies

# Building
npm run build:client        # Build Next.js for production
npm run build:server        # Install Python dependencies

# Docker
npm run docker:build        # Build all Docker images
npm run docker:up           # Start production containers
npm run docker:up-dev       # Start development containers
npm run docker:down         # Stop all containers
npm run docker:logs         # View container logs
npm run docker:clean        # Clean up Docker resources
```

### Client Commands (in `client/` directory)

```bash
npm run dev                 # Start development server
npm run build              # Build for production
npm run start              # Start production server
npm run lint               # Run ESLint
```

### Server Commands (in `server/` directory)

```bash
npm run dev                 # Start FastAPI with hot reload
npm run start               # Start FastAPI server
```

## 🔧 API Endpoints

The FastAPI backend provides the following endpoints:

- `GET /` - Welcome message
- `GET /api/health` - Health check
- `GET /api/users` - Get all users
- `POST /api/users` - Create a new user
- `GET /api/users/{user_id}` - Get user by ID
- `DELETE /api/users/{user_id}` - Delete user by ID

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Docker Configuration

### Development Setup

The development Docker setup includes:
- Volume mounts for hot reload
- Development environment variables
- Live reload for both frontend and backend

### Production Setup

The production Docker setup includes:
- Multi-stage builds for optimization
- Nginx reverse proxy
- Health checks and restart policies
- Non-root user execution for security

## 🔒 Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)
```bash
PYTHONPATH=/app
```

## 📦 Dependencies

### Frontend
- **Next.js 15.5.3** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **ESLint** - Code linting

### Backend
- **FastAPI 0.104.1** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Python-multipart** - File upload support

## 🚀 Deployment

### Production Deployment

1. **Build the application**
   ```bash
   npm run docker:build
   ```

2. **Deploy with Docker Compose**
   ```bash
   npm run docker:up
   ```

3. **Access via Nginx**
   - Application: http://your-domain.com
   - API: http://your-domain.com/api/

### Environment-Specific Configuration

For production deployments, consider:
- Setting up environment variables
- Configuring a production database
- Setting up SSL certificates
- Configuring proper logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the ISC License.

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill processes on ports 3000 and 8000
   lsof -ti:3000 | xargs kill -9
   lsof -ti:8000 | xargs kill -9
   ```

2. **Docker build fails**
   ```bash
   # Clean Docker cache
   npm run docker:clean
   ```

3. **Python virtual environment issues**
   ```bash
   # Recreate virtual environment
   cd server
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Getting Help

- Check the [Issues](https://github.com/archangelinux/rouvia/issues) page
- Review the API documentation at http://localhost:8000/docs
- Check Docker logs: `npm run docker:logs`

---

**Happy coding! 🎉**