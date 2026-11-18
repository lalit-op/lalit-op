# Vistaar for Samsung Tizen — enhanced prototype

TV-first TizenBrew application module. This is web content, not an Android APK or signed Samsung WGT.

## Features
- Remote-friendly TV interface
- Live TV and Free TV browsing
- M3U playlist parsing using the India playlist by default
- Search, category filtering, favourites and recently watched
- HTML video player with retry
- Configurable playlist URL and autoplay
- Local persistence for settings and favourites

## Install
Use this branch-specific TizenBrew module identifier:
`lalit-op/lalit-op@vistaar-tizen`

## Compatibility limits
- Uses standard HTML video and does not assume Samsung AVPlay/Tizen APIs are exposed by TizenBrew.
- HLS playback depends on TV browser codecs, CORS and provider availability; some streams will fail.
- Jio sign-in, subscriber entitlements, private stream retrieval and DRM/Widevine are not implemented. They require authorized API/source access.
- Not yet tested on the Samsung T5500; exact model code and firmware are unconfirmed.
- Use only playlists and streams you are authorized to access.
