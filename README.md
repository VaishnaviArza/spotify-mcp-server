# spotify-mcp-server

An MCP server that lets Claude Desktop control your Spotify. Ask it to play a song, queue something up, or build a playlist, and it happens on your real account.

It has 16 tools, 2 resources, and 2 prompts. It runs locally on your machine, and the only network calls it makes are to Spotify.

## What it can do

**Tools** (Claude decides when to call these)

| Category | Tools |
|---|---|
| Login | `spotify_login` |
| Playback state | `spotify_get_current_playback`, `spotify_get_recently_played`, `spotify_get_available_devices` |
| Search | `spotify_search_track` |
| Playback control | `spotify_play`, `spotify_pause`, `spotify_skip_next`, `spotify_skip_previous`, `spotify_set_volume`, `spotify_add_to_queue` |
| Playlists | `spotify_get_user_playlists`, `spotify_get_playlist_tracks`, `spotify_create_playlist`, `spotify_add_tracks_to_playlist`, `spotify_remove_tracks_from_playlist` |

**Resources** (read-only context you can attach to a chat)

- `spotify://playlists` lists your playlists with their ids
- `spotify://playlists/{playlist_id}` lists the tracks in one playlist

**Prompts** (workflows you pick from the chat's + menu)

- `build_playlist(theme, track_count=15)` runs several varied searches, creates a private playlist, and adds the tracks
- `cleanup_playlist(playlist_name)` finds duplicates, proposes what to remove, and waits for your approval before changing anything

## Install

You need Claude Desktop and a Spotify account. Playback control through Spotify's API needs Premium. Every user needs their own Spotify developer app, because Spotify's API credentials can't be shared. That takes a few minutes.

### 1. Create a Spotify app

Go to the [Spotify developer dashboard](https://developer.spotify.com/dashboard), create an app, and choose **Web API**. Set the Redirect URI to:

```
http://127.0.0.1:8765/callback
```

The port can be anything, but it has to match the install form below.

Copy your Client ID and Client Secret from the app's Settings page.

### 2. Install the extension

Download `spotify-mcp-server.mcpb` from the [latest release](https://github.com/VaishnaviArza/spotify-mcp-server/releases/latest) and open it. Claude Desktop shows an install screen with a form for your Client ID, Client Secret, and Redirect URI. Fill it in and install.


### 3. Log in

In a regular chat, ask Claude something like "what's playing on Spotify?" The first time, it will tell you that you're not logged in and call `spotify_login`. A browser window opens for you to approve access (if you're already logged in to Spotify and have approved before, it may flash by and close on its own). Then Claude retries what you asked.


### Installing from source instead

If you'd rather run it directly, or want to change the code:

```powershell
git clone https://github.com/VaishnaviArza/spotify-mcp-server.git
cd spotify-mcp-server
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8765/callback
```

Then add the server to Claude Desktop's config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

On Windows, if Claude Desktop came from the Microsoft Store/MSIX package, the real file may be in a redirected location instead:

```
%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
```

```json
{
  "mcpServers": {
    "spotify-mcp-server": {
      "command": "C:\\path\\to\\spotify-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\spotify-mcp-server\\server.py"]
    }
  }
}
```

On macOS/Linux the command is `/path/to/spotify-mcp-server/venv/bin/python`. If the file already has an `mcpServers` section, add this as another entry inside it. Then fully quit Claude Desktop and reopen it, since the config is only read at startup.

To build the `.mcpb` yourself, run `.\build_bundle.ps1` from the project root. It copies the files the bundle needs into a folder, validates the manifest, and packs it into `dist\`. Needs Node.js.

## How it's built

Two layers:

```
spotify_client.py   talks to Spotify. Plain functions.
server.py           talks to Claude. Wraps those functions as MCP tools,
                    resources, and prompts.
```


**Login.** Auth is the OAuth 2.0 Authorization Code flow through [Spotipy](https://spotipy.readthedocs.io/). The server runs in the background with no terminal, so it never starts a login on its own. Every tool first checks for a usable token. If there isn't one, it raises an error telling Claude to call `spotify_login`. That tool starts the browser flow in a background thread and returns right away, so it doesn't hit a request timeout while you approve. Tokens are cached in `.spotify-mcp-server/token.json` in your home folder.

**Errors.** Failed actions raise errors that Claude can read (for example "No active Spotify device found") instead of returning a message that looks like success. Unexpected crashes stay hidden from the model and are logged on the server.

**Details.** Playlists and playlist tracks are fetched across all of Spotify's pages, so long playlists aren't cut off. Inputs like `limit` are checked before any Spotify call. Built on the `mcp` Python SDK, v2 (the `MCPServer` class).

```
spotify-mcp-server/
├── server.py            MCP server: tools, resources, prompts
├── spotify_client.py    Spotify auth and API functions
├── bundle/              manifest.json, pyproject.toml, uv.lock for the .mcpb
├── build_bundle.ps1     builds the .mcpb from a clean staging folder
├── requirements.txt     for running from source
└── README.md
```

## Things to know

- **You need an active Spotify device.** Playback commands only work if Spotify is open and active somewhere (phone, desktop app, speaker). If nothing is, the tools say so.
- **Removing tracks is destructive.** `spotify_remove_tracks_from_playlist` removes every copy of a track. Claude Desktop asks before running tools, so keep the approval on "ask every time" for that one.
- **Search returns at most 10 results per call**, and recently played at most 50. That's why `build_playlist` runs several searches.
- **No recommendations or mood matching.** Spotify turned off its recommendations and audio-features endpoints for apps created after November 27, 2024, so tools built on them aren't possible here.
- **Local only.** It runs on your machine, so it works in Claude Desktop but not in claude.ai in the browser or the mobile app.
- **Tested on Windows.** The code has nothing OS-specific that I know of, but I haven't tried macOS or Linux.

## Not built yet

Liked songs and saved albums, following artists, shuffle/repeat/seek, transferring playback between devices, and reordering playlist tracks.

## Troubleshooting

- **The extension doesn't start.** Check Claude Desktop's logs under Settings → Developer, and look for an error on the extension's page.
- **Spotify says the redirect URI is invalid.** It must match the Spotify dashboard and the install form character for character..
- **"Not logged in" even after approving.** Ask Claude to log in again. If a window was closed partway, use the link it gives you.
- **The login window opens and closes right away.** That's normal if you're already logged in to Spotify and have approved this app before.
- **Config file isn't where you expect on Windows** (source install only). See the redirected path above.

## Trying the server without Claude

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) lets you call every tool, resource, and prompt directly in a browser:

```powershell
npx -y @modelcontextprotocol/inspector python server.py
```

It needs Node.js. Open the URL it prints and click Connect.