# AIO Application Changelog

### v2.8.4 (The Connectivity Fix)
*   **Update Fix**: Resolved SSL certificate verification issues on macOS that were preventing the auto-updater from checking GitHub.

### v2.8.3 (The Seamless Update Release)
*   **Update Intelligence**: Fixed auto-update logic to correctly detect OS-specific builds (Mac vs Windows).
*   **Workflow**: Added automatic "Reveal in Finder/Explorer" after the update download completes.
*   **Quality**: Refined GitHub Actions for independent OS releases.
*   **Windows Compatibility**: Added full support for Windows OS.
*   **OS-Native logic**: Automatically switches between Finder (macOS) and Explorer (Windows).
*   **Keyboard Shortcuts**: Added support for standard modifier keys (Ctrl+C/V/X/A on Windows/Linux, Command keys on macOS).
*   **Automated Deployment**: Updated GitHub Actions to automatically build both macOS `.app` and Windows `.exe` versions on every release tag.

### v2.8.0 (Auto-Update Release)
*   **Intelligence**: Added an automatic update checker that notifies users of new releases on startup.
*   **Direct Download**: Users can now download updates directly through the app interface.

### v2.6 (Data Harmonization)
*   **New Tool**: Introduced the **Date Harmonizer** for cross-batch date consistency.
*   **Intelligence**: Automatic parsing of US/EU date ambiguities and support for fuzzy date matching.
*   **Targeting**: Support for various output formats (e.g., YYYY-MM-DD for Database sync).
*   **Stability**: Added error-tracking for unparseable dates within the Activity Log.

### v2.5 (Log Intelligence & Quality of Life)
*   **Live Monitoring**: Added **Error & Warning counters** in the log header for instant health checks.
*   **Log Persistence**: Added a **"Save"** button to export the entire session log to a `.txt` file.
*   **UI Flex**: Added a **Minimize/Expand toggle** (▼/▲) to collapse the log panel.
*   **Smart Interaction**: Added **Double-Click to Copy** (optimized for per-line snippet capture).
*   **Polished Workflow**: Removed secondary log clutter for a cleaner focus.

### v2.4 (Rich Visuals & Aesthetics)
*   **Color-Coding System**: Implemented context-aware logging colors (Green, Yellow, Red, Pink).
*   **Theming**: Refined UI tags and colors for professional dark/light mode compatibility.

### v2.3 (Data Integrity & Insights)
*   **Concatenator Intelligence**: Detects "Disconnected Files" and common column intersections.
*   **Data Janitor**: Automatic **NULL Column Dropper** for unique/empty columns.
*   **File Stats**: Live **Row/Column counters** and Excel **Sheet Selection**.

### v2.2 (Foundation & OS Integration)
*   **Workflow Integration**: "Reveal in Finder" links and **Smart Naming** logic.
*   **Extended Toolset**: Integrated Excel to CSV converter and initial column detection.
