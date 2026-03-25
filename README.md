# Marathon Training Tracker

A very simple beginner-friendly marathon training tracker that runs as a local web app in your browser.

## What it does

- Lets you log:
  - date
  - workout type
  - planned miles
  - actual miles
  - planned pace
  - actual pace
  - notes
- Shows a weekly summary:
  - total planned miles
  - total actual miles
  - number of runs completed
- Shows progress for your marathon plan by week
- Saves your data in a local `workouts.json` file through a tiny Python server

## Files

- `index.html` - the page
- `styles.css` - the design
- `app.js` - the app logic
- `server.py` - the tiny local server
- `workouts.json` - your saved workouts

The local server handles:
- manual workout saves through `/api/workouts`
- Garmin imports through `/api/import-workout`

## Semi-automatic Garmin helper

You can also run a small helper that watches a folder for new `.tcx` files and imports them automatically.

Default watch folder:

`/Users/elizabethshah/Documents/GarminExports`

### Run the helper

In a second Terminal window, after starting `server.py`, run:

```bash
cd /Users/elizabethshah/Documents/Workout/helper
python3 watch_garmin_folder.py
```

You can also watch a different folder:

```bash
cd /Users/elizabethshah/Documents/Workout/helper
python3 watch_garmin_folder.py /path/to/your/tcx-folder
```

How it works:
- The helper checks the folder every 15 seconds
- When it sees a new `.tcx` file, it parses it
- It posts the parsed workout to the local app server
- The app server stores it in `workouts.json`
- The helper keeps a small `import_state.json` file so it does not keep re-importing the same file

## Easiest way to run it

### Start the local app server

This app now uses a tiny local Python server so workouts are saved in `workouts.json`.

1. Open Terminal
2. Run:

```bash
cd /Users/elizabethshah/Documents/Workout
python3 server.py
```

3. Open this address in your browser:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

4. When you are done, go back to Terminal and press `Control + C`

## How to use the app

1. Open the app
2. Fill out the workout form
3. Click `Save Workout`
4. Review your weekly summary
5. Review the plan progress cards by week
6. Check the workout log below
7. Use `Delete` if you want to remove an entry

## Important note about saved data

Your workout data is saved in `/Users/elizabethshah/Documents/Workout/workouts.json` on your computer.

- If you refresh the page, your data stays
- If you use the same local folder and server, your data stays available
- If you delete `workouts.json`, your saved data will be removed

## No installation needed

You do not need to install npm, packages, or any extra tools for this app.
# Marathon
