# Rouvia Styling Guide

## Design Philosophy

Rouvia follows a modern, minimalist design approach focused on driver safety and ease of use. The interface prioritizes clarity, accessibility, and hands-free operation while maintaining a professional and trustworthy aesthetic.

## Design Principles

### Safety First
- Large, easily readable text and buttons
- High contrast colors for visibility in various lighting conditions
- Minimal cognitive load to reduce driver distraction
- Clear visual hierarchy for quick information scanning

### Accessibility
- WCAG 2.1 AA compliance
- Support for screen readers
- Keyboard navigation support
- High contrast mode support
- Voice-first interface design

### Modern Minimalism
- Clean, uncluttered interface
- Generous white space
- Subtle animations and transitions
- Consistent visual language across all components

## Color Palette

### Primary Colors
```css
/* Primary Blue - Trust, Technology, Navigation */
--primary-50: #eff6ff;
--primary-100: #dbeafe;
--primary-200: #bfdbfe;
--primary-300: #93c5fd;
--primary-400: #60a5fa;
--primary-500: #3b82f6;  /* Main primary */
--primary-600: #2563eb;
--primary-700: #1d4ed8;
--primary-800: #1e40af;
--primary-900: #1e3a8a;
```

### Secondary Colors
```css
/* Success Green - Confirmation, Go */
--success-50: #f0fdf4;
--success-100: #dcfce7;
--success-200: #bbf7d0;
--success-300: #86efac;
--success-400: #4ade80;
--success-500: #22c55e;  /* Main success */
--success-600: #16a34a;
--success-700: #15803d;
--success-800: #166534;
--success-900: #14532d;
```

### Warning Colors
```css
/* Warning Orange - Caution, Attention */
--warning-50: #fffbeb;
--warning-100: #fef3c7;
--warning-200: #fde68a;
--warning-300: #fcd34d;
--warning-400: #fbbf24;
--warning-500: #f59e0b;  /* Main warning */
--warning-600: #d97706;
--warning-700: #b45309;
--warning-800: #92400e;
--warning-900: #78350f;
```

### Error Colors
```css
/* Error Red - Stop, Error, Danger */
--error-50: #fef2f2;
--error-100: #fee2e2;
--error-200: #fecaca;
--error-300: #fca5a5;
--error-400: #f87171;
--error-500: #ef4444;  /* Main error */
--error-600: #dc2626;
--error-700: #b91c1c;
--error-800: #991b1b;
--error-900: #7f1d1d;
```

### Neutral Colors
```css
/* Grays - Text, Backgrounds, Borders */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;
```

## Typography

### Font Stack
```css
/* Primary Font - Inter (Modern, Readable) */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Monospace Font - JetBrains Mono (Code, Technical) */
font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', monospace;
```

### Font Sizes
```css
/* Mobile First Approach */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */
```

### Font Weights
```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

## Spacing System

### Spacing Scale
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

## Component Styles

### Buttons

#### Primary Button
```css
.btn-primary {
  background-color: var(--primary-500);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: 0.5rem;
  font-weight: var(--font-medium);
  font-size: var(--text-base);
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background-color: var(--primary-600);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: translateY(0);
}
```

#### Voice Button (Special)
```css
.btn-voice {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
  color: white;
  padding: var(--space-4) var(--space-8);
  border-radius: 50%;
  width: 80px;
  height: 80px;
  font-size: var(--text-xl);
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
}

.btn-voice:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.btn-voice.listening {
  animation: pulse 1.5s infinite;
}
```

### Cards

#### Route Card
```css
.route-card {
  background: white;
  border-radius: 1rem;
  padding: var(--space-6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--gray-200);
  transition: all 0.2s ease;
}

.route-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}
```

### Chat Interface

#### Chat Container
```css
.chat-container {
  background: var(--gray-50);
  border-radius: 1rem;
  padding: var(--space-6);
  max-height: 400px;
  overflow-y: auto;
}

.chat-message {
  margin-bottom: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: 0.75rem;
  max-width: 80%;
}

.chat-message.user {
  background: var(--primary-100);
  color: var(--primary-800);
  margin-left: auto;
}

.chat-message.assistant {
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-200);
}
```

## Map Styling

### Mapbox Theme
```javascript
const mapStyle = {
  version: 8,
  sources: {
    'rouvia-style': {
      type: 'raster',
      tiles: ['https://api.mapbox.com/styles/v1/mapbox/light-v10/tiles/{z}/{x}/{y}?access_token=YOUR_TOKEN'],
      tileSize: 256
    }
  },
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: {
        'background-color': '#f8fafc'
      }
    }
  ]
};
```

### Route Styling
```css
.route-line {
  stroke: var(--primary-500);
  stroke-width: 4;
  stroke-opacity: 0.8;
  stroke-dasharray: 5, 5;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}
```

## Responsive Design

### Breakpoints
```css
/* Mobile First */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

### Mobile Optimizations
- Touch-friendly button sizes (minimum 44px)
- Large text for readability while driving
- Simplified navigation for one-handed use
- Voice-first interface reduces need for touch

## Dark Mode Support

### Dark Theme Colors
```css
:root[data-theme="dark"] {
  --background: var(--gray-900);
  --surface: var(--gray-800);
  --text-primary: var(--gray-100);
  --text-secondary: var(--gray-300);
  --border: var(--gray-700);
}
```

## Animation Guidelines

### Micro-interactions
- Button hover: 0.2s ease
- Card hover: 0.3s ease
- Voice button pulse: 1.5s infinite
- Route animation: 1s linear infinite

### Performance
- Use `transform` and `opacity` for animations
- Avoid animating `width`, `height`, `top`, `left`
- Use `will-change` sparingly
- Prefer CSS animations over JavaScript

## Accessibility

### Focus States
```css
.focusable:focus {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
}
```

### Screen Reader Support
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## Implementation Notes

### Tailwind CSS Configuration
```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          // ... rest of primary colors
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      }
    }
  },
  plugins: []
};
```

### CSS Custom Properties
All colors and spacing values are defined as CSS custom properties for easy theming and consistency across components.
