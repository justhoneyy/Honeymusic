from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.extensions import db
from app.models.music import Song, Album, Artist, Genre, Podcast, PodcastEpisode
from app.models.playlist import Playlist, PlaylistSong, Like
from app.models.analytics import ListenHistory
from app.utils.helpers import paginate

class MusicService:
    @staticmethod
    def get_trending(page=1, per_page=20):
        """Get trending songs based on plays in last 7 days."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        trending = db.session.query(
            Song,
            func.count(ListenHistory.id).label('play_count')
        ).outerjoin(
            ListenHistory,
            db.and_(
                ListenHistory.song_id == Song.id,
                ListenHistory.played_at >= week_ago
            )
        ).group_by(Song.id).order_by(
            desc('play_count'),
            desc(Song.plays)
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [song[0].to_dict() for song in trending.items],
            'page': trending.page,
            'per_page': trending.per_page,
            'total': trending.total,
            'pages': trending.pages,
        }

    @staticmethod
    def get_new_releases(page=1, per_page=20):
        """Get recently released albums."""
        albums = Album.query.filter(
            Album.is_featured == True
        ).order_by(
            desc(Album.release_date),
            desc(Album.created_at)
        ).paginate(page=page, per_page=per_page, error_out=False)

        return paginate(albums.query, page, per_page)

    @staticmethod
    def get_recommendations(user_id, limit=20):
        """Get personalized recommendations based on listening history."""
        # Get user's liked genres
        liked_songs = db.session.query(Song.genre_id).join(
            Like, Like.song_id == Song.id
        ).filter(Like.user_id == user_id).subquery()

        # Get recent artists
        recent_artists = db.session.query(Song.artist_id).join(
            ListenHistory, ListenHistory.song_id == Song.id
        ).filter(ListenHistory.user_id == user_id).order_by(
            desc(ListenHistory.played_at)
        ).limit(10).subquery()

        # Recommend songs from similar genres/artists not recently played
        recently_played = db.session.query(ListenHistory.song_id).filter(
            ListenHistory.user_id == user_id,
            ListenHistory.played_at >= datetime.utcnow() - timedelta(days=7)
        ).subquery()

        recommendations = Song.query.filter(
            db.or_(
                Song.genre_id.in_(liked_songs),
                Song.artist_id.in_(recent_artists)
            ),
            ~Song.id.in_(recently_played),
            Song.is_podcast == False
        ).order_by(
            desc(Song.plays),
            func.random()
        ).limit(limit).all()

        return [song.to_dict() for song in recommendations]

    @staticmethod
    def record_listen(user_id, song_id, duration_played, completed=False, source='library'):
        """Record a listen event."""
        song = Song.query.get(song_id)
        if not song:
            return None

        history = ListenHistory(
            user_id=user_id,
            song_id=song_id,
            duration_played=duration_played,
            completed=completed,
            source=source
        )
        song.plays += 1
        db.session.add(history)
        db.session.commit()
        return history.to_dict()
