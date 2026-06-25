"""Seed script to populate the database with sample music data for development."""
import uuid
import json
import random
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User, UserPreference
from app.models.music import Artist, Album, Song, Genre, Lyric, Podcast, PodcastEpisode
from app.models.playlist import Playlist, PlaylistSong, Like
from app.models.analytics import ListenHistory

app = create_app()

def seed():
    """Seed the database with sample data."""
    with app.app_context():
        # Check if already seeded
        if Artist.query.first():
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database...")

        # Create genres
        genres_data = [
            {'name': 'Pop', 'slug': 'pop', 'color': '#FF6B6B'},
            {'name': 'Hip Hop', 'slug': 'hip-hop', 'color': '#FFD93D'},
            {'name': 'Electronic', 'slug': 'electronic', 'color': '#6BCB77'},
            {'name': 'Rock', 'slug': 'rock', 'color': '#4D96FF'},
            {'name': 'R&B', 'slug': 'rnb', 'color': '#9B59B6'},
            {'name': 'Jazz', 'slug': 'jazz', 'color': '#E67E22'},
            {'name': 'Classical', 'slug': 'classical', 'color': '#1ABC9C'},
            {'name': 'Indie', 'slug': 'indie', 'color': '#E74C3C'},
            {'name': 'Lo-Fi', 'slug': 'lo-fi', 'color': '#8E44AD'},
            {'name': 'Ambient', 'slug': 'ambient', 'color': '#3498DB'},
        ]
        genres = {}
        for g in genres_data:
            genre = Genre(**g, description=f'{g["name"]} music genre')
            db.session.add(genre)
            genres[g['slug']] = genre
        db.session.flush()

        # Create artists
        artists_data = [
            {'name': 'Luna Waves', 'slug': 'luna-waves', 'verified': True, 'monthly_listeners': 4500000},
            {'name': 'Neon Pulse', 'slug': 'neon-pulse', 'verified': True, 'monthly_listeners': 3200000},
            {'name': 'Solar Drift', 'slug': 'solar-drift', 'verified': True, 'monthly_listeners': 2800000},
            {'name': 'Echo Valley', 'slug': 'echo-valley', 'verified': False, 'monthly_listeners': 1200000},
            {'name': 'Cosmic Rain', 'slug': 'cosmic-rain', 'verified': True, 'monthly_listeners': 5600000},
            {'name': 'Midnight Collective', 'slug': 'midnight-collective', 'verified': False, 'monthly_listeners': 890000},
            {'name': 'Aurora Beats', 'slug': 'aurora-beats', 'verified': True, 'monthly_listeners': 3400000},
            {'name': 'Starlight Symphony', 'slug': 'starlight-symphony', 'verified': True, 'monthly_listeners': 2100000},
        ]
        artists = {}
        for a in artists_data:
            artist = Artist(
                name=a['name'], slug=a['slug'],
                verified=a['verified'], monthly_listeners=a['monthly_listeners'],
                bio=f'{a["name"]} is an incredible musical artist making waves in the industry.'
            )
            db.session.add(artist)
            artists[a['slug']] = artist
        db.session.flush()

        # Create albums and songs
        moods = ['happy', 'chill', 'energetic', 'melancholic', 'romantic', 'focus', 'workout']
        keys = ['C', 'G', 'D', 'A', 'E', 'F', 'Bb', 'Eb']
        
        album_templates = [
            {'title': 'Midnight Dreams', 'type': 'album', 'tracks': 10},
            {'title': 'Electric Horizons', 'type': 'album', 'tracks': 8},
            {'title': 'Golden Hour', 'type': 'album', 'tracks': 12},
            {'title': 'Neon Nights', 'type': 'ep', 'tracks': 5},
            {'title': 'Summer Vibes', 'type': 'single', 'tracks': 1},
            {'title': 'Deep Blue', 'type': 'album', 'tracks': 10},
            {'title': 'Stellar Journey', 'type': 'album', 'tracks': 9},
            {'title': 'Urban Flow', 'type': 'ep', 'tracks': 4},
        ]

        songs_total = 0
        for artist_slug, artist in artists.items():
            num_albums = random.randint(1, 3)
            for _ in range(num_albums):
                tmpl = random.choice(album_templates)
                album = Album(
                    title=f"{tmpl['title']} - {artist.name}",
                    slug=f"{artist.slug}-{tmpl['title'].lower().replace(' ', '-')}-{random.randint(1,99)}",
                    artist_id=artist.id,
                    genre_id=random.choice(list(genres.values())).id,
                    album_type=tmpl['type'],
                    total_tracks=tmpl['tracks'],
                    release_date=datetime.now() - timedelta(days=random.randint(1, 365)),
                    description=f"{tmpl['title']} by {artist.name}"
                )
                db.session.add(album)
                db.session.flush()

                for t in range(1, tmpl['tracks'] + 1):
                    song = Song(
                        title=f"{tmpl['title']} Track {t}",
                        artist_id=artist.id,
                        album_id=album.id,
                        genre_id=random.choice(list(genres.values())).id,
                        duration=random.randint(150, 320),
                        track_number=t,
                        audio_url=f"/uploads/music/{artist.slug}-track-{t}.mp3",
                        plays=random.randint(1000, 10000000),
                        explicit=random.random() < 0.15,
                        mood=random.choice(moods),
                        bpm=random.randint(60, 180),
                        key=random.choice(keys),
                        is_featured=random.random() < 0.2,
                    )
                    db.session.add(song)
                    songs_total += 1

        db.session.flush()
        print(f"Created {songs_total} songs")

        # Create admin user
        admin = User(
            email='admin@honeymusic.com',
            username='admin',
            display_name='Admin',
            is_admin=True,
            is_verified=True,
            is_premium=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        prefs = UserPreference(user_id=admin.id)
        db.session.add(prefs)

        # Create demo user
        demo = User(
            email='demo@honeymusic.com',
            username='demo',
            display_name='Demo User',
            is_verified=True,
            is_premium=True
        )
        demo.set_password('demo123')
        db.session.add(demo)
        
        prefs2 = UserPreference(user_id=demo.id)
        db.session.add(prefs2)
        db.session.flush()

        # Create some playlists for demo user
        playlist_names = ['Chill Vibes', 'Workout Energy', 'Late Night Study', 'Weekend Party', 'Road Trip']
        for name in playlist_names:
            pl = Playlist(
                name=name,
                user_id=demo.id,
                description=f'A curated {name.lower()} playlist',
                is_public=True,
                color=random.choice(['#FF6B6B', '#1ED760', '#4D96FF', '#FFD93D', '#9B59B6'])
            )
            db.session.add(pl)
        db.session.flush()

        # Add likes for demo user
        all_songs = Song.query.all()
        for s in random.sample(all_songs, min(20, len(all_songs))):
            like = Like(user_id=demo.id, song_id=s.id)
            db.session.add(like)

        # Add listen history
        for _ in range(50):
            song = random.choice(all_songs)
            history = ListenHistory(
                user_id=demo.id,
                song_id=song.id,
                played_at=datetime.now() - timedelta(hours=random.randint(1, 168)),
                duration_played=random.randint(30, song.duration or 200),
                completed=random.random() < 0.4,
                source=random.choice(['library', 'search', 'recommendation', 'playlist'])
            )
            db.session.add(history)

        db.session.commit()
        print("Database seeded successfully!")
        print(f"Demo account: demo@honeymusic.com / demo123")
        print(f"Admin account: admin@honeymusic.com / admin123")

if __name__ == '__main__':
    seed()
