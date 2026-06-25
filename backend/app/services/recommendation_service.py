from datetime import datetime, timedelta
from sqlalchemy import desc, func
from app.extensions import db
from app.models.music import Song, Genre
from app.models.analytics import ListenHistory
from app.models.playlist import Like

class RecommendationService:
    @staticmethod
    def get_mood_playlists(mood, limit=20):
        """Get songs matching a specific mood."""
        mood_songs = Song.query.filter(
            Song.mood == mood.lower(),
            Song.is_podcast == False
        ).order_by(desc(Song.plays)).limit(limit).all()
        return [song.to_dict() for song in mood_songs]

    @staticmethod
    def get_genre_mix(genre_slug, limit=30):
        """Get a mix of songs from a specific genre."""
        genre = Genre.query.filter_by(slug=genre_slug).first()
        if not genre:
            return []
        songs = Song.query.filter_by(
            genre_id=genre.id,
            is_podcast=False
        ).order_by(
            func.random(),
            desc(Song.plays)
        ).limit(limit).all()
        return [song.to_dict() for song in songs]

    @staticmethod
    def get_user_mix(user_id, limit=30):
        """Create a personalized mix based on listening patterns."""
        # Most played genres
        top_genres = db.session.query(
            Song.genre_id,
            func.count(ListenHistory.id).label('count')
        ).join(
            ListenHistory, ListenHistory.song_id == Song.id
        ).filter(
            ListenHistory.user_id == user_id
        ).group_by(Song.genre_id).order_by(desc('count')).limit(3).all()

        if not top_genres:
            return []

        genre_ids = [g[0] for g in top_genres if g[0]]

        # Get songs from these genres, excluding recently played
        recent = db.session.query(ListenHistory.song_id).filter(
            ListenHistory.user_id == user_id,
            ListenHistory.played_at >= datetime.utcnow() - timedelta(days=1)
        ).subquery()

        mix = Song.query.filter(
            Song.genre_id.in_(genre_ids),
            ~Song.id.in_(recent),
            Song.is_podcast == False
        ).order_by(func.random()).limit(limit).all()

        return [song.to_dict() for song in mix]
