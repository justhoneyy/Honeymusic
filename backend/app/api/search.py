from flask import Blueprint, request
from sqlalchemy import or_
from app.models.music import Song, Album, Artist, Genre, Podcast
from app.utils.helpers import create_response

search_bp = Blueprint('api.search', __name__)

@search_bp.route('', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return create_response(data={
            'songs': [], 'albums': [], 'artists': [],
            'genres': [], 'podcasts': []
        })

    limit = request.args.get('limit', 10, type=int)
    
    # Songs
    songs = Song.query.filter(
        or_(
            Song.title.ilike(f'%{q}%'),
            Song.artist.has(Artist.name.ilike(f'%{q}%')),
            Song.album.has(Album.title.ilike(f'%{q}%'))
        ),
        Song.is_podcast == False
    ).limit(limit).all()

    # Albums
    albums = Album.query.filter(
        or_(
            Album.title.ilike(f'%{q}%'),
            Album.artist.has(Artist.name.ilike(f'%{q}%'))
        )
    ).limit(limit).all()

    # Artists
    artists = Artist.query.filter(
        Artist.name.ilike(f'%{q}%')
    ).limit(limit).all()

    # Genres
    genres = Genre.query.filter(
        Genre.name.ilike(f'%{q}%')
    ).limit(limit).all()

    # Podcasts
    podcasts = Podcast.query.filter(
        Podcast.title.ilike(f'%{q}%')
    ).limit(limit).all()

    return create_response(data={
        'songs': [s.to_dict() for s in songs],
        'albums': [a.to_dict() for a in albums],
        'artists': [a.to_dict() for a in artists],
        'genres': [g.to_dict() for g in genres],
        'podcasts': [p.to_dict() for p in podcasts],
        'query': q,
    })

@search_bp.route('/suggestions', methods=['GET'])
def suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return create_response(data=[])
    
    songs = Song.query.filter(
        Song.title.ilike(f'{q}%')
    ).limit(5).all()
    
    artists = Artist.query.filter(
        Artist.name.ilike(f'{q}%')
    ).limit(3).all()
    
    results = []
    results.extend([{'type': 'song', 'id': s.id, 'text': s.title, 'subtext': s.artist.name if s.artist else ''} for s in songs])
    results.extend([{'type': 'artist', 'id': a.id, 'text': a.name, 'subtext': 'Artist'} for a in artists])
    
    return create_response(data=results[:8])
