<p align="center"><img src="assets/icon.png" alt="Unhoused Reader Pro icon" width="128"></p>

<h1 align="center">Unhoused Reader Pro</h1>

A Mac app for reading and relaunching **HOBO U23-001A (U23 Pro v2 Temp/RH)** data loggers over Onset's optical USB base station, without HOBOware. Read the data off a logger, save it as a clean CSV, and start it logging again!

## Install

1. [**Download Unhoused Reader Pro (.dmg)**](https://github.com/jstrand894/unhoused_app/releases/latest/download/Unhoused-Reader-Pro.dmg)
2. Open it and drag **Unhoused Reader Pro** onto **Applications**.
3. First launch only: the app isn't notarized, so macOS blocks it. Open it once, then go to **System Settings, Privacy & Security** and click **Open Anyway**. (Older macOS: right-click the app, Open, Open.)
4. Optional: right-click its Dock icon, then **Options, Keep in Dock**. In **Settings** (the gear) you can turn on *Open this app when a logger is plugged in*.

You also need a HOBO U23-001A logger and its Onset optical USB base station (BASE-U-4) with the logger coupler. Other base stations and loggers will probably work. Haven't tested though. 

## Before you start

**Close HOBOware.** Only one program can use the USB device at a time. Plug in the base station and seat the logger in its coupler. When the logger is found, the dot at the top turns green and the Logger card fills in.

## Using the app

The three numbered buttons are the workflow, and the checklist on the right ticks them off as you go. The button for the next sensible step is highlighted in blue.

1. **Readout device** stops the logger if it is logging (after you confirm), reads all its data into the app, and plots it. Hover the plot for exact values, drag to zoom, double-click to reset.
2. **Save readout** writes a CSV (temperatures are always in °C) and, if turned on in Settings, the raw `.hobo` file.
3. **Launch** drops a settings panel down inside the Logger card: name, interval, and an estimate of how long the memory will last. **Start logging** restarts the logger. If you haven't saved this logger's data, it warns you that launching erases it and asks you to confirm.

Other controls:

- **Stop logging** stops a logger without reading it out (for a logger that will just sit on a desk). The recorded data stays on it.
- **Refresh** re-reads the logger. **Open file…** loads a saved `.hobo` file so you can look at it or export it to CSV, no logger needed.
- The **°F / °C** rocker changes the units shown in the app. Saved CSV files are always in °C.
- **Settings** (gear): save a `.hobo` file alongside the CSV, ask where to save each time or use one folder, and open the app when a logger is plugged in.
- Shortcuts: ⌘O open, ⌘R refresh, ⌘D readout, ⌘S save, ⌘L launch, ⌘. stop, ⌘, settings.
- Warning strips appear if the battery is fair or low, or the logger's memory is nearly full. The app follows the system light or dark mode.
