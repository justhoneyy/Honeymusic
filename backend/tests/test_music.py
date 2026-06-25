"""Tests for music endpoints."""

from app.extensions import db
from app.models.music import Artist, Album, Song, Genre

def create_test_data():
    """Helper to create test music data."""
    genre = Genre(name='Test Genre', slug='test-genre')
    artist = Artist(name='Test Artist', slug='test-artist', verified=True)
    db.session.add_all([genre, artist])
    db.session.flush()

    album = Album(
        title='Test Album',
        slug='test-album',
        artist_id=artist.id,
        album_type='album',
        total_tracks=2
    )
    db.session.add(album)
    db.session.flush()

    songs = [
        Song(title='Song 1', artist_id=artist.id, album_id=album.id,
             genre_id=genre.id, duration=180, track_number=1,
             audio_url='/uploads/music/test1.mp3'),
        Song(title='Song 2', artist_id=artist.id, album_id=album.id,
             genre_id=genre.id, duration=200, track_number=2,
             audio_url='/uploads/music/test2.mp3')
    ]
    db.session.add_all(songs)
    db.session.commit()
    return genre, artist, album, songs

def test_get_songs(client):
    """Test listing songs."""
    create_test_data()
    response = client.get('/api/music/songs')
    assert response.status_code == 200
    assert len(response.json['data']['items']) >= 2

def test_get_song(client):
    """Test getting a single song."""
    _, _, _, songs = create_test_data()
    response = client.get(f'/api/music/songs/{songs[0].id}')
    assert response.status_code == 200
    assert response.json['data']['title'] == 'Song 1'

def test_get_album(client):
    """Test getting album with songs."""
    _, _, album, _ = create_test_data()
    response = client.get(f'/api/music/albums/{album.id}')
    assert response.status_code == 200
    assert response.json['data']['title'] == 'Test Album'
    assert len(response.json['data']['songs']) == 2

def test_get_artist(client):
    """Test getting artist with albums and top songs."""
    _, artist, _, _ = create_test_data()
    response = client.get(f'/api/music/artists/{artist.id}')
    assert response.status_code == 200
    assert response.json['data']['name'] == 'Test Artist'
    assert len(response.json['data']['albums']) == 1

def test_get_genres(client):
    """Test listing genres."""
    create_test_data()
    response = client.get('/api/music/genres')
    assert response.status_code == 200
    assert len(response.json['data']) >= 1

def test_search(client):
    """Test search endpoint."""
    create_test_data()
    response = client.get('/api/search?q=Song')
    assert response.status_code == 200
    assert len(response.json['data']['songs']) >= 1

def test_trending(client):
    """Test trending endpoint."""
    create_test_data()
    response = client.get('/api/music/trending')
    assert response.status_code == 200
