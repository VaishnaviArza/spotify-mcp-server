from os import name

from mcp.server.mcpserver import MCPServer
from spotify_client import (
    get_auth_manager,
    is_logged_in,
    start_login,
    login_in_progress,
    get_login_error,
    missing_credentials,
    get_spotify_client,
    get_current_playback,
    get_recently_played,
    get_available_devices,
    search_track,
    play,
    pause,
    skip_next,
    skip_previous,
    set_volume,
    add_to_queue,
    get_user_playlists,
    get_playlist_tracks,
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist
)
import spotipy
from mcp.server.mcpserver.exceptions import ResourceError, ResourceNotFoundError, ToolError

# sp = get_spotify_client()
mcp = MCPServer("spotify-mcp-server") #server's display name ""
_auth_manager = None
_sp = None

def _manager(error=ToolError):
    global _auth_manager
    missing = missing_credentials()
    if missing:
        raise error("Spotify credentials are not configured. Missing: " + ", ".join(missing))
    if _auth_manager is None:
        _auth_manager = get_auth_manager()
    return _auth_manager

def get_sp(error=ToolError):
    """Return a logged-in Spotify client, or raise a clear error. Never starts a login."""
    global _sp
    manager = _manager(error)
    if not is_logged_in(manager):
        if login_in_progress():
            raise error("Spotify login is waiting for approval in the browser. "
                        "Ask the user to finish it, then retry.")
        detail = f" (last login error: {get_login_error()})" if get_login_error() else ""
        raise error("Not logged in to Spotify. Call spotify_login, then retry." + detail)
    if _sp is None:
        _sp = get_spotify_client(manager)
    return _sp

def _unwrap(result):
    if isinstance(result, dict) and 'is_success' in result:
        if not result['is_success']:
            raise ToolError(result['message'])
        return result
    return result

@mcp.tool()
def spotify_login() -> str:
    """Log in to Spotify. Call this when another Spotify tool says the user is not
    logged in. It opens a browser window where the user approves access. After
    calling it, ask the user to approve in the browser, then retry their original request.
    """
    manager = _manager()
    status = start_login(manager)
    if status == "already_logged_in":
        return "Already logged in to Spotify."
    if status == "in_progress":
        return ("A login is already waiting for approval. Ask the user to open this URL "
                f"and approve access: {manager.get_authorize_url()}")
    return ("A browser window should have opened for Spotify. Ask the user to approve "
            "access there, then retry their original request. If no window opened, "
            f"they can open this URL: {manager.get_authorize_url()}")

@mcp.tool()
def spotify_get_current_playback() -> dict:
    """Get the currently playing track on Spotify, including whether playback is active, 
    the track name and artist name."""
    return get_current_playback(get_sp())

@mcp.tool()
def spotify_get_recently_played(limit: int = 10) -> list:
    """Get the most recently played songs. 
    Args:
        limit: Number of tracks to return. Must be an integer from 1 to 50.
    Returns the time played at, the track name, unique identifier of the track (track_uri) 
    and the artist name"""
    try:
        return get_recently_played(get_sp(), limit)
    except ValueError as e:
        raise ToolError(str(e)) from e

@mcp.tool()
def spotify_get_available_devices() -> list:
    """Get all Spotify devices currently visible to this account. Returns a list of devices,
    each with id, name, type, is_active (bool), and volume_percent"""
    return get_available_devices(get_sp())

@mcp.tool()
def spotify_search_track(query: str, limit: int = 10) -> list:
    """Search Spotify for tracks matching a query. Use this whenever you need 
    to find a track's URI before playing it, queueing it, or adding it to a playlist.

    Args:
        query: Search text, e.g. a song title and/or artist name.
        limit: Number of results to return. Must be an integer from 1 to 10. Default is 10.
    
    Returns:
        A list of matching tracks, each with name, artist, and uri. The uri is 
        required as input for playback and playlist tools.
    """
    try:
        return search_track(get_sp(), query, limit)
    except ValueError as e:
        raise ToolError(str(e)) from e

@mcp.tool()
def spotify_play(track_uri: str = None) -> dict:
    """Start or resume playback on Spotify.
    
    Call with no arguments to resume whatever is currently paused. To play a 
    specific track, first use spotify_search_track to find its uri, then pass 
    that uri here.
    
    Args:
        track_uri: The Spotify URI of a track to play, obtained from 
            spotify_search_track. Leave unset to just resume playback.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to 
        confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(play(get_sp(), track_uri=track_uri))


@mcp.tool()
def spotify_pause() -> dict:
    """Pause Spotify playback.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to 
        confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(pause(get_sp()))


@mcp.tool()
def spotify_skip_next() -> dict:
    """Skip to the next track in the current playback queue.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to 
        confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(skip_next(get_sp()))

@mcp.tool()
def spotify_skip_previous() -> dict:
    """Skip to the previous track in the current playback queue.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to 
        confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(skip_previous(get_sp()))

@mcp.tool()
def spotify_set_volume(volume_percent: int) -> dict:
    """Set Spotify playback volume.
    
    Args:
        volume_percent: Volume level from 0 to 100.
    
    Returns:
        A dict with is_success (bool) and message (str). If volume_percent is 
        outside 0-100, is_success is True and the message explains the valid range. Otherwise, check is_success to confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(set_volume(get_sp(), volume_percent))

@mcp.tool()
def spotify_add_to_queue(track_uri: str) -> dict:
    """Add a track to the end of the current Spotify playback queue.
    Requires a track uri — use spotify_search_track first to find one.
    Args:
        track_uri: The Spotify URI of the track to queue, from spotify_search_track.
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to 
        confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(add_to_queue(get_sp(), track_uri))


@mcp.tool()
def spotify_get_user_playlists() -> list:
    """Get all playlists owned by or followed by the current user.
    
    Returns:
        A list of playlists, each with id, name, and track_count. The id is 
        required as input for other playlist tools (getting tracks, adding 
        tracks, removing tracks).
    """
    return get_user_playlists(get_sp())

@mcp.tool()
def spotify_get_playlist_tracks(playlist_id: str) -> list:
    """Get all tracks in a specific Spotify playlist.
    Requires a playlist id — use spotify_get_user_playlists first to find one.
    Args:
        playlist_id: The Spotify ID of the playlist, from spotify_get_user_playlists.
    Returns:
        A list of tracks, each with name, uri, and artist.
    """
    try:
        return get_playlist_tracks(get_sp(), playlist_id)
    except spotipy.SpotifyException as e:
        if e.http_status in (400, 404):
            raise ToolError(f"Playlist with id '{playlist_id}' not found") from e
        raise


@mcp.tool()
def spotify_create_playlist(name: str, description: str = "", public: bool = False, 
                            collaborative: bool = False) -> dict:
    """Create a new Spotify playlist for the current user.
    Args:
        name: Name of the new playlist.
        description: Optional playlist description.
        public: Whether the playlist is publicly visible. Defaults to False.
        collaborative: Whether other users can edit the playlist. Defaults to False.
    Returns:
        A dict with is_success (bool), playlist_id (str, the newly created 
        playlist's id), and message (str). playlist_id is needed to add tracks 
        to this playlist afterward. Check is_success to confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(create_playlist(get_sp(), name, description=description, public=public, 
                           collaborative=collaborative))

@mcp.tool()
def spotify_add_tracks_to_playlist(playlist_id: str, track_uris: list[str]) -> dict:
    """Add one or more tracks to a Spotify playlist.
    Requires a playlist id (from spotify_get_user_playlists or 
    spotify_create_playlist) and track uri(s) (from spotify_search_track).
    Args:
        playlist_id: The Spotify ID of the playlist to add tracks to.
        track_uris: A list of Spotify track URIs to add, even if adding just one track.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(add_tracks_to_playlist(get_sp(), playlist_id, track_uris))


@mcp.tool()
def spotify_remove_tracks_from_playlist(playlist_id: str, track_uris: list[str]) -> dict:
    """Remove one or more tracks from a Spotify playlist. Removes every occurrence of each given
    track if it appears more than once in the playlist.

    This is a destructive action — confirm with the user which playlist and which track(s) 
    before calling this.
    
    Args:
        playlist_id: The Spotify ID of the playlist to remove tracks from.
        track_uris: A list of Spotify track URIs to remove, even if removing just one track.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to confirm the action worked. The tool raises an error on failure and returns the confirmation message on success.
    """
    return _unwrap(remove_tracks_from_playlist(get_sp(), playlist_id, track_uris))

@mcp.resource("spotify://playlists", mime_type="application/json")
def spotify_playlists() -> list:
    """Get all playlists owned by or followed by the current user.
    Returns:
        A list of playlists, each with id, name, and track_count.
    """
    return get_user_playlists(get_sp())

@mcp.resource("spotify://playlists/{playlist_id}", mime_type="application/json")
def spotify_playlist_tracks(playlist_id: str) -> list:
    """Get all tracks in a specific Spotify playlist.
    Returns:
        A list of tracks, each with name, uri, and artist.
    """
    try:
        return get_playlist_tracks(get_sp(), playlist_id)
    except spotipy.SpotifyException as e:
        if e.http_status in (400, 404):
            raise ResourceNotFoundError(f"Playlist with id '{playlist_id}' not found") from e
        raise

@mcp.prompt()
def build_playlist(theme: str, track_count: int = 15) -> str:
    """Build a new spotify playlist around a theme or a mood."""
    return (
        f"Build a new Spotify playlist around the theme '{theme}' with {track_count} tracks. "
        "Follow these steps in order, since each depends on the one before it. "
        "1) Use spotify_search_track several times, with different queries that approach "
        "the theme from different angles (moods, genres, artists, eras), until you have "
        "enough distinct tracks. A single search returns at most 10 results, so one search "
        "is not enough. Avoid duplicates and avoid filling the playlist with one artist. "
        "2) Use spotify_create_playlist to create a private playlist with a fitting name. "
        "3) Use spotify_add_tracks_to_playlist with the new playlist's id and the track uris "
        "from your searches. "
        "After each action tool call, check is_success in the result. If anything failed, "
        "stop and tell me what went wrong. "
        f"If you cannot find {track_count} suitable tracks, add what you found and tell me the shortfall. "
        "On success, reply with only the playlist name, its id, and the track list, "
        "with no other text."
    )

@mcp.prompt()
def cleanup_playlist(playlist_name: str) -> str:
    """Find duplicate tracks in a Spotify playlist and clean them up after confirmation."""
    return (
        f"Help me clean up duplicate tracks in my Spotify playlist named '{playlist_name}'. "
        "Work in two phases, and do not change anything until I approve. "
        "PHASE 1 (read only): "
        "1) Use spotify_get_user_playlists to find the playlist by name. If there is no match "
        "or more than one, ask me which one I mean. Note its track_count. "
        "2) Use spotify_get_playlist_tracks to read its tracks. If fewer tracks come back than "
        "track_count, warn me that the list is incomplete and that you can only check what you can see. "
        "3) Find exact duplicates: the same uri appearing more than once. "
        "4) Find possible near-duplicates: different uris with the same or very similar name and artist, "
        "such as an album version and a single. Flag version differences like live, remastered, or remix "
        "instead of treating them as duplicates. "
        "5) Show me a proposal listing what you would remove and what you would keep, then stop. "
        "Tell me that removing an exact duplicate takes out every copy, so you would add one copy back, "
        "and that this copy will end up at the end of the playlist. "
        "Wait for my explicit approval before continuing. "
        "PHASE 2 (only after I approve): "
        "6) For each approved exact duplicate, use spotify_remove_tracks_from_playlist with its uri, "
        "then spotify_add_tracks_to_playlist with that same uri once. Do not re-add any track that was not removed. "
        "7) For each approved near-duplicate, use spotify_remove_tracks_from_playlist with only the uri "
        "of the copy I chose to remove. "
        "8) After each action tool call, check is_success. If anything failed, stop and tell me what went wrong. "
        "9) Use spotify_get_playlist_tracks again to verify, then reply with the before and after track counts "
        "and the name and uri of every track you removed, so I can undo a mistake."
    )

if __name__ == "__main__":
    mcp.run()