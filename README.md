# spotify-mcp-server

An MCP server that lets Claude Desktop control your Spotify. Ask it to play a song, queue something up, or build a playlist, and it happens on your real account.

It exposes 15 tools, 2 resources, and 2 prompts, and runs locally over stdio.

## What it can do

**Tools** (Claude decides when to call these)

| Category | Tools |
|---|---|
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

## Example things to say

- "What's playing right now?"
- "Play Mirrorball"
- "Queue up a few songs like it"
- "Create a playlist called Focus and add my last 5 played songs"
- "Pause, then turn the volume down to 30"

## How it's built

Two layers, kept separate on purpose:

```
spotify_client.py   talks to Spotify. Plain functions, no MCP code.
server.py           talks to Claude. Wraps those functions as MCP tools,
                    resources, and prompts.
```

Because `spotify_client.py` knows nothing about MCP, every function can be run and checked on its own from a terminal before Claude is involved. When something breaks, that tells you quickly whether the problem is "talking to Spotify" or "talking to Claude."

Auth is the OAuth 2.0 Authorization Code flow through [Spotipy](https://spotipy.readthedocs.io/). You log in once in the browser, and the tokens are cached and refreshed automatically.

Built on the `mcp` Python SDK, v2 (the `MCPServer` class).

```
spotify-mcp-server/
├── server.py           MCP server: tools, resources, prompts
├── spotify_client.py   Spotify auth and API functions
├── requirements.txt
├── .env                your credentials (not committed)
└── README.md
```

## Setup

You need Python 3.10 or newer, Claude Desktop, and a Spotify account. Playback control through Spotify's API needs Premium.

<!-- TODO: double-check Spotify's current rules for Development Mode apps (Premium on the app owner's account, 5-user cap) and state them accurately here -->

### 1. Create a Spotify app

Go to the [Spotify developer dashboard](https://developer.spotify.com/dashboard), create an app, and choose **Web API**. Set the Redirect URI to:

```
http://127.0.0.1:8765/callback
```

Use `127.0.0.1`, not `localhost`. The port can be anything free, but it has to match exactly in the dashboard and in your `.env`. (If you get a `WinError 10013` on Windows, the port you picked is probably reserved by the OS. Pick a different one.)

Copy your Client ID and Client Secret from the app's Settings page.

### 2. Install

```powershell
git clone https://github.com/<your-username>/spotify-mcp-server.git
cd spotify-mcp-server
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Add your credentials

Create a `.env` file in the project root:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8765/callback
```

Never commit this file. It's already in `.gitignore`, along with `.cache`, which holds your login tokens.

### 4. Log in once

Run this from the project folder:

```powershell
python spotify_client.py
```

Your browser opens to Spotify's consent page. Approve it, and your profile or current playback prints in the terminal. This creates a `.cache` file with your tokens. Do this step from a terminal first, because Claude Desktop starts the server in the background and may not show you a browser window.

### 5. Connect it to Claude Desktop

Open Claude Desktop's config file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

On Windows, if Claude Desktop was installed from the Microsoft Store/MSIX package, the real file may be in a redirected location instead:

```
%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
```

Add the server, using the full paths to your venv's Python and to `server.py`:

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

On macOS/Linux the command is `/path/to/spotify-mcp-server/venv/bin/python`. Backslashes in JSON paths must be doubled.

If the file already has an `mcpServers` section, add this as another entry inside it instead of making a second one.

Then **fully quit** Claude Desktop (system tray icon, Quit) and reopen it. Closing the window isn't enough, since the config is only read at startup. Start a regular chat and ask what's playing.

## Things to know

- **You need an active Spotify device.** Playback commands only work if Spotify is open and active somewhere (phone, desktop app, speaker). If nothing is, the tools say so.
- **Removing tracks is destructive.** `spotify_remove_tracks_from_playlist` removes every copy of a track, and Claude Desktop asks before running tools. Keep the approval on "ask every time" for that one.
- **Search returns at most 10 results per call.** That's why `build_playlist` runs several searches.
- **No recommendations or mood matching.** Spotify turned off its recommendations and audio-features endpoints for apps created after November 27, 2024, so tools built on them aren't possible here.
- **Local only.** It runs over stdio on your machine, so it works in Claude Desktop but not in claude.ai in the browser or the mobile app.

## Not built yet

Liked songs and saved albums, following artists, shuffle/repeat/seek, transferring playback between devices, and reordering playlist tracks.

## Troubleshooting

- **Server doesn't show up in Claude Desktop.** Check that both paths in the config are absolute and correct, then quit fully (tray icon) and reopen. Claude Desktop's logs are under Settings → Developer.
- **`ModuleNotFoundError` when it starts.** The config's `command` needs to point at the venv's Python, since that's where the packages are installed.
- **Spotify says the redirect URI is invalid.** It must match the dashboard and `.env` character for character.
- **Config file isn't where you expect on Windows.** See the redirected path in step 5.

## Trying the server without Claude

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) lets you call every tool, resource, and prompt directly in a browser:

```powershell
npx -y @modelcontextprotocol/inspector python server.py
```

It needs Node.js. Open the URL it prints and click Connect.

## License

<!-- TODO: choose a license (MIT is common) and add a LICENSE file -->
