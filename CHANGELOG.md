# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]
- Future improvements TBD.

## [v7e] - 2025-09-12
### Added
- Automatic 30s refresh of online players list (plus manual Refresh button).
- Backup button refuses to run while the server is active, with warning message.
- Better layout for splash image and controls.

### Changed
- Backup logs are streamed into the GUI with `[backup]` prefix.
- Exit button now does `save-all`, clean stop, shows log, and delays 3 seconds before closing.

## [v7d] - 2025-09-11
### Added
- Backup button runs `backup.bat` and streams its output into the GUI log.

### Changed
- Splash image repositioned above Whitelist section for better layout.

## [v7c] - 2025-09-11
### Added
- Splash image support: IceFireYinYangTransparent.png can be displayed in the GUI.

### Changed
- Reorganized layout to reduce wasted space.

## [v7b] - 2025-09-10
### Added
- Whitelist panel: view, add, and remove players.
- Online players panel: manual refresh.

### Changed
- Exit button now performs graceful stop and cleans stop.flag.

## [v7a] - 2025-09-09
### Added
- Exit button that stops the server and closes the GUI after a delay.
- Save All button aligned with Start/Stop row.

## [v6] - 2025-09-08
### Added
- Command input box to send arbitrary commands to the server.

## [v5] - 2025-09-07
### Added
- Auto-start server when GUI opens.
- Whitelist Add prompt button.
- Save All button.
- Make stop.flag button.
- Command log window.

### Changed
- Runs as `.pyw` to avoid extra console window.

## [Earlier prototypes]
- Basic Tkinter GUI for Start/Stop and stop.flag support.
