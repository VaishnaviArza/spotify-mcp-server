$stage = "dist\staging"
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $stage | Out-Null

Copy-Item server.py, spotify_client.py $stage
Copy-Item bundle\manifest.json, bundle\pyproject.toml, bundle\uv.lock $stage

npx -y @anthropic-ai/mcpb validate "$stage\manifest.json"
npx -y @anthropic-ai/mcpb pack $stage "dist\spotify-mcp-server.mcpb"