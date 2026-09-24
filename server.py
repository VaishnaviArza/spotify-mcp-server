from mcp.server.fastmcp import FastMCP
from spotify_client import (
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

sp = get_spotify_client()
mcp = FastMCP("spotify-mcp-server") #server's display name ""

@mcp.tool()
def spotify_get_current_playback() -> dict:
    """Get the currently playing track on Spotify, including whether playback is active, 
    the track name and artist name."""
    return get_current_playback(sp)

@mcp.tool()
def spotify_get_recently_played(limit: int = 10) -> list:
    """Get the most recently played songs. 
    Args:
        limit: Number of tracks to return. Must be an integer from 1 to 50.
    Returns the time played at, the track name, unique identifier of the track (track_uri) 
    and the artist name"""
    return get_recently_played(sp, limit)

@mcp.tool()
def spotify_get_available_devices() -> list:
    """Get all Spotify devices currently visible to this account. Returns a list of devices,
    each with id, name, type, is_active (bool), and volume_percent"""
    return get_available_devices(sp)

@mcp.tool()
def spotify_search_track(query: str, limit: int = 10) -> list:
    """Search Spotify for tracks matching a query. Use this whenever you need 
    to find a track's URI before playing it, queueing it, or adding it to a playlist.

    Args:
        query: Search text, e.g. a song title and/or artist name.
        limit: Number of results to return. Defaults to 10.
    
    Returns:
        A list of matching tracks, each with name, artist, and uri. The uri is 
        required as input for playback and playlist tools.
    """
    return search_track(sp, query, limit)

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
        confirm the action worked — a failed request does not raise an error, 
        it returns is_success: False with details in message.
    """
    return play(sp, track_uri=track_uri)


@mcp.tool()
def spotify_pause_track() -> dict:
    """Pause Spotify playback.
    
    Returns:
        A dict with is_success (bool) and message (str). Check is_success to 
        confirm the action worked.
    """
    return pause(sp)


@mcp.tool()
def spotify_skip_next() -> dict:
    """Skip to the next track in the current playback queue.
    
    Returns:
        A dict with is_success (bool) and message (str).
    """
    return skip_next(sp)

@mcp.tool()
def spotify_skip_previous() -> dict:
    """Skip to the previous track in the current playback queue.
    
    Returns:
        A dict with is_success (bool) and message (str).
    """
    return skip_previous(sp)

@mcp.tool()
def spotify_set_volume(volume_percent: int) -> dict:
    """Set Spotify playback volume.
    
    Args:
        volume_percent: Volume level from 0 to 100.
    
    Returns:
        A dict with is_success (bool) and message (str). If volume_percent is 
        outside 0-100, is_success will be False with an explanatory message.
    """
    return set_volume(sp, volume_percent)

@mcp.tool()
def spotify_add_to_queue(track_uri: str) -> dict:
    """Add a track to the end of the current Spotify playback queue.
    Requires a track uri — use spotify_search_track first to find one.
    Args:
        track_uri: The Spotify URI of the track to queue, from spotify_search_track.
    Returns:
        A dict with is_success (bool) and message (str).
    """
    return add_to_queue(sp, track_uri)


@mcp.tool()
def spotify_get_user_playlists() -> list:
    """Get all playlists owned by or followed by the current user.
    
    Returns:
        A list of playlists, each with id, name, and track_count. The id is 
        required as input for other playlist tools (getting tracks, adding 
        tracks, removing tracks).
    """
    return get_user_playlists(sp)

@mcp.tool()
def spotify_get_playlist_tracks(playlist_id: str) -> list:
    """Get all tracks in a specific Spotify playlist.
    Requires a playlist id — use spotify_get_user_playlists first to find one.
    Args:
        playlist_id: The Spotify ID of the playlist, from spotify_get_user_playlists.
    Returns:
        A list of tracks, each with name, uri, and artist.
    """
    return get_playlist_tracks(sp, playlist_id)

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
        to this playlist afterward.
    """
    return create_playlist(sp, name, description=description, public=public, 
                           collaborative=collaborative)

@mcp.tool()
def spotify_add_tracks_to_playlist(playlist_id: str, track_uris: list[str]) -> dict:
    """Add one or more tracks to a Spotify playlist.
    Requires a playlist id (from spotify_get_user_playlists or 
    spotify_create_playlist) and track uri(s) (from spotify_search_track).
    Args:
        playlist_id: The Spotify ID of the playlist to add tracks to.
        track_uris: A list of Spotify track URIs to add, even if adding just one track.
    
    Returns:
        A dict with is_success (bool) and message (str).
    """
    return add_tracks_to_playlist(sp, playlist_id, track_uris)


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
        A dict with is_success (bool) and message (str).
    """
    return remove_tracks_from_playlist(sp, playlist_id, track_uris)


if __name__ == "__main__":
    mcp.run()