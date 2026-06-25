from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.music import Song, Album, Artist, Genre, Podcast, PodcastEpisode
from app.models.playlist import Like
from app.services.music_service import MusicService
from app.utils.helpers import create_response, paginate

music_bp = Blueprint('api.music', __name__)

@music_bp.route('/songs', methods=['GET'])
def get_songs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    genre = request.args.get('genre')
    artist = request.args.get('artist')
    album = request.args.get('album')

    query = Song.query.filter(Song.is_podcast == False)
    if genre:
        query = query.join(Genre).filter(Genre.slug == genre)
    if artist:
        query = query.filter(Song.artist_id == artist)
    if album:
        query = query.filter(Song.album_id == album)

    result = paginate(query.order_by(Song.created_at.desc()), page, per_page)
    return create_response(data=result)

@music_bp.route('/songs/<song_id>', methods=['GET'])
def get_song(song_id):
    song = Song.query.get(song_id)
    if not song:
        return create_response(error='Song not found', status=404)
    return create_response(data=song.to_dict())

@music_bp.route('/albums', methods=['GET'])
def get_albums():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    query = Album.query.order_by(Album.release_date.desc())
    result = paginate(query, page, per_page)
    return create_response(data=result)

@music_bp.route('/albums/<album_id>', methods=['GET'])
def get_album(album_id):
    album = Album.query.get(album_id)
    if not album:
        return create_response(error='Album not found', status=404)
    songs = album.songs.order_by(Song.track_number).all()
    data = album.to_dict()
    data['songs'] = [s.to_dict() for s in songs]
    return create_response(data=data)

@music_bp.route('/artists', methods=['GET'])
def get_artists():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    query = Artist.query.order_by(Artist.monthly_listeners.desc())
    result = paginate(query, page, per_page)
    return create_response(data=result)

@music_bp.route('/artists/<artist_id>', methods=['GET'])
def get_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return create_response(error='Artist not found', status=404)
    data = artist.to_dict()
    data['albums'] = [a.to_dict() for a in artist.albums.order_by(Album.release_date.desc()).all()]
    data['top_songs'] = [s.to_dict() for s in artist.songs.order_by(Song.plays.desc()).limit(10).all()]
    return create_response(data=data)

@music_bp.route('/genres', methods=['GET'])
def get_genres():
    genres = Genre.query.all()
    return create_response(data=[g.to_dict() for g in genres])

@music_bp.route('/genres/<genre_slug>', methods=['GET'])
def get_genre(genre_slug):
    genre = Genre.query.filter_by(slug=genre_slug).first()
    if not genre:
        return create_response(error='Genre not found', status=404)
    songs = genre.songs.order_by(Song.plays.desc()).limit(50).all()
    data = genre.to_dict()
    data['songs'] = [s.to_dict() for s in songs]
    return create_response(data=data)

@music_bp.route('/trending', methods=['GET'])
def trending():
    page = request.args.get('page', 1, type=int)
    result = MusicService.get_trending(page=page)
    return create_response(data=result)

@music_bp.route('/new-releases', methods=['GET'])
def new_releases():
    page = request.args.get('page', 1, type=int)
    result = MusicService.get_new_releases(page=page)
    return create_response(data=result)

@music_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def recommendations():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 20, type=int)
    result = MusicService.get_recommendations(user_id, limit)
    return create_response(data=result)

@music_bp.route('/like/<song_id>', methods=['POST', 'DELETE'])
@jwt_required()
def toggle_like(song_id):
    user_id = get_jwt_identity()
    song = Song.query.get(song_id)
    if not song:
        return create_response(error='Song not found', status=404)

    existing = Like.query.filter_by(user_id=user_id, song_id=song_id).first()
    
    if request.method == 'POST':
        if existing:
            return create_response(message='Song already liked')
        like = Like(user_id=user_id, song_id=song_id)
        db.session.add(like)
        db.session.commit()
        return create_response(message='Song liked', status=201)
    else:
        if existing:
            db.session.delete(existing)
            db.session.commit()
        return create_response(message='Song unliked')

@music_bp.route('/liked', methods=['GET'])
@jwt_required()
def get_liked_songs():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    likes = Like.query.filter_by(user_id=user_id)\
        .order_by(Like.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
  items = []
    for like in likes.items:
        item = like.to_dict()
        if like.song:
            item['song'] = like.song.to_dict()
        items.append(item)
    
    return create_response(data={
        'items': items,
        'page': likes.page,
        'per_page': likes.per_page,
        'total': likes.total,
        'pages': likes.pages,
    })

@music_bp.route('/listen', methods=['POST'])
@jwt_required()
def record_listen():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'song_id' not in data:
        return create_response(error='song_id required', status=400)
    
    result = MusicService.record_listen(
        user_id, data['song_id'],
        data.get('duration_played', 0),
        data.get('completed', False),
        data.get('source', 'library')
    )
    if not result:
        return create_response(error='Song not found', status=404)
    return create_response(data=result)

@music_bp.route('/podcasts', methods=['GET'])
def get_podcasts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    podcasts = Podcast.query.order_by(Podcast.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    return create_response(data=paginate(podcasts.query, page, per_page))

@music_bp.route('/podcasts/<podcast_id>', methods=['GET'])
def get_podcast(podcast_id):
    podcast = Podcast.query.get(podcast_id)
    if not podcast:
        return create_response(error='Podcast not found', status=404)
    data = podcast.to_dict()
    episodes = podcast.episodes.order_by(PodcastEpisode.episode_number.desc()).all()
    data['episodes'] = [e.to_dict() for e in episodes]
    return create_response(data=data)

@music_bp.route('/lyrics/<song_id>', methods=['GET'])
def get_lyrics(song_id):
    from app.models.music import Lyric
    lyric = Lyric.query.filter_by(song_id=song_id).first()
    if not lyric:
        return create_response(error='Lyrics not available', status=404)
    return create_response(data={
        'lyrics': lyric.lyrics_text,
        'synced_lyrics': lyric.synced_lyrics,
        'source': lyric.source,
        'language': lyric.language,
    })
