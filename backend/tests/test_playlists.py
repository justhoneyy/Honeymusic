"""Tests for playlist endpoints."""

def test_create_playlist(client, auth_headers):
    """Test creating a playlist."""
    response = client.post('/api/playlists', json={
        'name': 'My Test Playlist',
        'description': 'A test playlist'
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json['data']['name'] == 'My Test Playlist'

def test_get_playlists(client, auth_headers):
    """Test listing playlists."""
    client.post('/api/playlists', json={'name': 'Playlist 1'}, headers=auth_headers)
    response = client.get('/api/playlists', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['data']) >= 1

def test_delete_playlist(client, auth_headers):
    """Test deleting a playlist."""
    create = client.post('/api/playlists', json={'name': 'To Delete'}, headers=auth_headers)
    playlist_id = create.json['data']['id']
    response = client.delete(f'/api/playlists/{playlist_id}', headers=auth_headers)
    assert response.status_code == 200

def test_add_song_to_playlist(client, auth_headers):
    """Test adding a song to a playlist (needs seed data)."""
    # Create playlist
    create = client.post('/api/playlists', json={'name': 'Add Song Test'}, headers=auth_headers)
    playlist_id = create.json['data']['id']

    # Try adding to empty playlist (will fail gracefully without seed data)
    response = client.post(f'/api/playlists/{playlist_id}/songs', json={
        'song_id': 'nonexistent'
    }, headers=auth_headers)
    assert response.status_code == 404
