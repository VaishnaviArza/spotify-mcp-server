import os
import dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

dotenv.load_dotenv()

scopes = "user-read-playback-state user-modify-playback-state user-read-currently-playing " \
"user-read-recently-played playlist-read-private playlist-modify-public playlist-modify-private"

def get_spotify_client():
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "")
    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                 scope=scopes)
    return spotipy.Spotify(auth_manager=auth_manager)

def get_current_playback(sp):
    result = sp.current_playback()

    if result is None:
        return {"is_playing": False, "track": None, "artist": None}

    artist_name = result['item']['artists'][0]['name']
    track_name = result['item']['name']

    return {'is_playing': result['is_playing'], 'track': track_name, 'artist': artist_name}

def get_recently_played(sp, limit):
    result = sp.current_user_recently_played(limit=limit)
    items = result['items']
    recently_played = []
    for item in items:
        recently_played.append({"played_at": item['played_at'],
                                "track_name": item['track']['name'],
                                "track_uri": item['track']['uri'],
                                "artist_name": item['track']['artists'][0]['name']})
    return recently_played

def get_available_devices(sp):
    result = sp.devices()
    return result['devices']

def get_active_device_id(sp):
    devices = get_available_devices(sp)
    for device in devices:
        if device['is_active']:
            return device['id']
    return None

def search_track(sp, query, limit):
    result = sp.search(q=query, type='track', limit=limit)
    items = result['tracks']['items']
    tracks = []
    for item in items:
        tracks.append({'name': item['name'],
                       'artist': item['artists'][0]['name'],
                       'uri': item['uri']})
    return tracks

def play(sp, track_uri=None, device_id=None):
    if device_id is None:
        device_id = get_active_device_id(sp)
    if device_id is None:
        return {"is_success": False, "message": "No active Spotify device found"}
    try:
        if track_uri:
            sp.start_playback(device_id=device_id, uris=[track_uri])
        else:
            sp.start_playback(device_id=device_id)
        return {"is_success": True, "message": "Playback started"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def pause(sp, device_id=None):
    if device_id is None:
        device_id = get_active_device_id(sp)
    if device_id is None:
        return {"is_success": False, "message": "No active spotify device found"}
    try:
        sp.pause_playback(device_id=device_id)
        return {"is_success": True, "message": "Playback paused"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def skip_next(sp, device_id=None):
    if device_id is None:
        device_id = get_active_device_id(sp)
    if device_id is None:
        return {"is_success": False, "message": "No active spotify device found"}
    try:
        sp.next_track(device_id=device_id)
        return {"is_success": True, "message": "Skipped to next track"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def skip_previous(sp, device_id=None):
    if device_id is None:
        device_id = get_active_device_id(sp)
    if device_id is None:
        return {"is_success": False, "message": "No active spotify device found"}
    try:
        sp.previous_track(device_id=device_id)
        return {"is_success": True, "message": "Skipped to previous track"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def set_volume(sp, volume_percent, device_id=None):
    if not (0 <= volume_percent <= 100):
        return {"is_success": True, "message": "Volume must be between 0 and 100"}
    if device_id is None:
        device_id = get_active_device_id(sp)
    if device_id is None:
        return {"is_success": False, "message": "No active spotify device found"}
    try:
        sp.volume(volume_percent=volume_percent, device_id=device_id)
        return {"is_success": True, "message": f"Volume set to {volume_percent}"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def add_to_queue(sp, track_uri, device_id=None):
    if device_id is None:
        device_id = get_active_device_id(sp)
    if device_id is None:
        return {"is_success": False, "message": "No active Spotify device found"}
    try:
        sp.add_to_queue(uri=track_uri, device_id=device_id)
        return {"is_success": True, "message": "Added to queue"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def get_user_playlists(sp):
    result = sp.current_user_playlists()
    items = result['items']
    playlists = []
    for item in items:
        playlists.append({"id": item['id'], "name": item['name'], 
                          "track_count": item['items']['total']})
    return playlists

def get_playlist_tracks(sp, playlist_id):
    result = sp.playlist_items(playlist_id=playlist_id)
    items = result['items']
    playlist_tracks = []
    for item in items:
        playlist_tracks.append({"name": item['item']['name'],
                                "track_uri": item['item']['uri'],
                                "artist_name": item['item']['artists'][0]['name']})
    return playlist_tracks

def create_playlist(sp, name, public=False, collaborative=False, description=""):
    try:
        result = sp.current_user_playlist_create(name=name, public=public, 
                                                 collaborative=collaborative,
                                                 description=description)
        return {"is_success": True, "playlist_id": result['id'], 
                "message": f"Created playlist '{name}'"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def add_tracks_to_playlist(sp, playlist_id, track_uris):
    if not isinstance(track_uris, list):
        return {"is_success": False, "message": "Please make sure to send tracks uris as a list"}
    try:
        sp.playlist_add_items(playlist_id=playlist_id, items=track_uris)
        return {"is_success": True, "message": f"Added {len(track_uris)} track(s) to playlist"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}

def remove_tracks_from_playlist(sp, playlist_id, track_uris):
    if not isinstance(track_uris, list):
        return {"is_success": False, "message": "Please make sure to send tracks uris as a list"}
    try:
        sp.playlist_remove_all_occurrences_of_items(playlist_id=playlist_id, items=track_uris)
        return {"is_success": True, "message": f"Removed {len(track_uris)} track(s) from playlist"}
    except spotipy.SpotifyException as e:
        return {"is_success": False, "message": str(e)}



# if __name__ == "__main__":
#     sp = get_spotify_client()
#     import json
#     result = sp.current_user_recently_played(limit=5)
#     print(get_recently_played(sp))


