# Honey Music 🍯

A premium, production-ready music streaming web application with a modern dark UI, glassmorphism effects, and vibrant green accent theme.

## Features

- **Authentication**: Email/password + Google OAuth with JWT tokens
- **Music Streaming**: Play, pause, seek, volume control, crossfade, gapless playback
- **Library Management**: Playlists (CRUD), liked songs, recently played, listening history
- **Discovery**: Trending, new releases, personalized recommendations, genre browsing
- **Search**: Live suggestions, full-text search across songs, albums, artists
- **Player**: Mini player bar, fullscreen player, audio visualizer, animated equalizer
- **Podcasts**: Podcast and episode management
- **Admin Dashboard**: User analytics, play stats, content management
- **Settings**: Profile, playback preferences, theme toggle (dark/light)
- **PWA**: Service worker, offline support, installable
- **Responsive**: Desktop, tablet, and mobile layouts
- **Accessibility**: Keyboard shortcuts, ARIA labels, semantic HTML

## Tech Stack

### Frontend
- Vanilla JavaScript (ES Modules) - no frameworks
- Web Audio API for playback and visualization
- CSS3 with custom properties, glassmorphism, animations
- PWA with service worker caching

### Backend
- Python Flask - REST API
- PostgreSQL - database
- SQLAlchemy - ORM
- Flask-JWT-Extended - authentication
- Flask-Bcrypt - password hashing
- Flask-CORS - cross-origin support
- Gunicorn - production WSGI server

## Project Structure
