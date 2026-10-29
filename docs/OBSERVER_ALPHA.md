# Observer alpha — how to play, what to check, how to report a bug

The observer is the first usable interface: create or open a world, advance it, explore its history, and
hand us a saved world when something looks wrong. It is an alpha (plain pages, local only), built on the same
session and archive as everything else, not a separate engine.

## Start, stop, reopen (Windows)

1. Install Python 3.11 or newer from python.org (tick "Add Python to PATH"). Nothing else is needed.
2. Double-click **`RUN_OBSERVER_WINDOWS.bat`** in the Golf Legacy folder. A console window opens and your
   browser opens at `http://localhost:8765/`. Keep the console window open while you play.
3. **Stop**: the **Quit** button in the World library, or Ctrl-C in the console window. A running advance
   first finishes the week it is playing and saves every completed week. Closing the console window instead
   stops at once: the world stays at its last saved week, and the unfinished advance is reported when you
   next open the world.
4. **Reopen**: double-click the .bat again and press **Open** on your world.

From a terminal: `python tools/observer.py --open` (the library in `worlds/`), `python tools/observer.py
worlds/NAME` (open one world directly), `python tools/observer.py path/to/archive --read-only` (browse a
history archive), `--worlds DIR` for another library folder, `--port`, `--workers N`.

The observer listens on 127.0.0.1 only (this computer). Worlds are folders in `worlds/` (not tracked by git).

## Updating to a new version

1. Quit the observer.
2. On GitHub (Golf-Legacy, branch main) press **Code → Download ZIP** and unzip it.
3. Open the unzipped folder (`Golf-Legacy-main`), select everything in it, and copy it into your existing Golf
   Legacy folder, choosing **Replace the files in the destination**. Your `worlds` folder is not in the
   download, so your worlds stay exactly as they are.
4. Start `RUN_OBSERVER_WINDOWS.bat` again and Open your world.

The library shows whether each world can still be resumed ("this engine"): updates that change only the
observer, tools or the save code keep it so.

## What you can do

- **World library** (`/worlds`): every world with its date, seed, starting year, compatibility and state;
  **Remove…** moves a world to the trash (restore it, or delete it permanently by typing its name; never the
  open world or during an operation); **Create** (a name, a starting year,
  and a seed: the whole world is generated; a new seed is suggested each time -- the same seed always makes the
  same world and, shot for shot, the same history, a different seed a different one), **Open** (resume), **Browse history** (read-only), **Copy**
  (never changes the original), **Report a problem**, **Close**, **Quit**.
- **Advance**: *Advance week*, *4 weeks*, *To end of season*, or a number of seasons and *Advance seasons*
  (the rest of this season, then whole seasons), from the header of any page. The advance runs in the
  background with a progress bar; you can keep browsing (pages show the last saved week, which the footer
  names) and **Stop simulation** (it stops after the week being played; every completed week is kept). A
  multi-season advance saves and publishes each season as it ends, and the pages move on to it, so stopping
  or closing the window never loses a finished season. One operation at a time.
- **Explore**: Overview, Calendar (this season, played / scheduled / not held), Rankings (world, amateur),
  Golfers / Coaches / Caddies directories (filters: name, nation, tour, status; sorting), Courses, Nations,
  Tours, Tournaments (filters: tour, kind), Seasons and season recaps, Records & frivolities, Moments.
  Every person, edition, tournament, course, nation and tour links to its page; the browser's Back button
  keeps your filters.
- **Stats** and **Prize money** (Basketball GM style): a season (the current one so far, or any archived one) or
  all-time, all tours or one, sorted by any column (starts, wins, runner-up, top 2/5/10, cuts made, prize
  money); every number opens the results behind it. Definitions are under the table.
- **Shortlist**: ☆ Shortlist on any person, course, nation, tour, tournament or edition; the Shortlist page
  lists them. Kept with the world (it travels with copies and problem reports).
- **A person's page**: age (approximate: season year minus birth year) before the birth year; current ratings
  with the archetype and signed changes (this season, last season; "unavailable" where no earlier record
  exists); career honors (major, Premier Tour, Challenger, regional, mini tour, college national and
  postseason champion, college, amateur championship and other wins), with counts, first and latest years
  and links; a season-by-season table with age, every statistic linked to its results and *show each tour*
  for the per-tour rows; coaches show their current clients as rows and a season-by-season staff table.
  One identity with a tab per career — *Playing career* (seasons, wins, moments),
  *Results* (every start with the coach and caddie that week and how they got in), *Coaches & caddies*,
  *Coaching*, *Caddying* (each partnership with dates, starts together, wins and majors).
- **An edition** (one year of a tournament) is separate from the **tournament** (all its editions), and a
  **course layout** from its course. The current season's editions are linked as soon as they are played and
  read the same after the season is archived.

## Long runs (for example 100 seasons)

- Use its own Golf Legacy folder for a long run and keep that folder's code unchanged until the run ends;
  install updates into another folder (copy worlds across only when you want to open them with newer code).
- Note the world's name, seed and start year (the library shows the seed; the start year is 2027).
- Keep the laptop plugged in, and keep about 10 GB of disk free (a 50-season world with its history index
  takes about 1.3 GB; 100 seasons is larger, not yet measured).
- Type the number of seasons and press *Advance seasons*. You can browse meanwhile; *Stop simulation* stops
  after the current week. To continue later, Open the world and advance the remaining seasons.
- Report a problem and Copy wait for the running advance: stop it first.

## Saving

There is no Save button: every advance is saved (committed) when it ends -- one week, four weeks, the rest of
the season, or the weeks completed before you pressed Stop. Closing or quitting never loses a finished
advance, and the observer has nothing unsaved of its own. "Resume" is simply Open.

## How it keeps your world safe

- Every page comes from one saved ("committed") week and the history published with it. While an advance
  runs, nothing on screen comes from the half-played week.
- An advance form carries the world, the date it was drawn at and a one-time key: double clicks, refreshes,
  retries and reconnects never advance twice, and a form from before another advance does nothing.
- A failed advance shows its error and keeps the world at its last saved week; the error goes to the world's
  log (`observer.log` in its folder). If the observer stops mid-advance, nothing half-written is kept.
- If a world says it is **locked** ("being advanced by another program") and no other Golf Legacy window is
  open, tick the box and press **Release the lock** in the library (a lock left by a program that has died is
  normally taken over automatically).

## Supported saves

| Save | What the observer does |
|---|---|
| A world saved by **this engine** (format golf-legacy-session/1, schema 1) | Open and advance it. |
| A world saved by **another engine** (older code; e.g. the 50-season world, engine commit 7334ffe) | Browse its history read-only, or **Copy** it with "continue with this engine": the copy records which engine saved it and which continues it (`ENGINE_ACCEPTED.json`), and only the copy is opened. The original is never resumed or changed. Its history keeps what the older engine produced; everything after the copy is the new engine's. |
| A history archive without a session (a folder with `MANIFEST.json`, or `world.json` from before manifests) | Browse read-only. |
| An unknown save format or schema | Listed as unsupported; not opened. |

The "engine" is a fingerprint of the simulation code (`golfsim/`, not counting the save and archive code):
updates that change only the observer, tools or documentation do not change it, so your worlds stay
resumable. An update that changes the simulation makes existing worlds "another engine".

## Reporting a problem

**Report a problem** (on every page, and per world in the library) writes a zip to `worlds/_diagnostics/`:
the saved world (the current checkpoint and every history file it depends on), the world's log, versions
(save format, the engine that saved it and the one running), seed, date, generations, every file's size and
SHA-256, and your note (what happened, steps, what you expected). The history index and the previous
checkpoint are optional (the index is rebuilt from the season files when missing; on a 50-season world it is
about 1 GB of the 1.25 GB, so leave it out unless we ask). Local folder names are removed from the log. Nothing is uploaded:
send the zip yourself. Keep the world as it is until we have looked.

What we do with it: unzip into an empty folder, review it read-only first, note the last good checkpoint and
the failure, reproduce with the engine commit it names, and never change your original.

## Acceptance checklist (about 20 minutes)

1. Start the observer with the .bat; the library opens in the browser.
2. Create a world (any name, the suggested seed). The overview shows 2027, week 1 (1 January next).
3. *Advance week* twice quickly (double-click): one week is played (2027, week 2), not two.
4. *4 weeks*, and while it runs open a golfer and the calendar: the pages work and still show week 2; the
   result banner appears when it finishes (2027, week 6).
5. Open an event from the overview: follow the winner, their coach and caddie, the course, the tournament,
   then Back to where you were.
6. *To end of season*, then press *Stop after this week* after a few weeks: the banner says how many weeks
   were kept; the date matches.
7. *To end of season* again and let it finish: Seasons shows 2027 with its majors; Records & frivolities lists
   are filled (youngest/oldest major champion, youngest/oldest Premier debut, most starts without a win —
   pick a tour); an event from week 10 reads the same as before the season ended.
8. Quit with the Quit button; start the .bat again; Open the world: same date, same history.
9. Start a 4-week advance and close the console window while it runs; start again and Open: a banner says
   the advance did not finish; the date is the last saved week.
10. Copy the world, open the copy, advance it; open the original: unchanged.
11. Report a problem on the copy: a zip appears in `worlds/_diagnostics/` with your note in `ISSUE.md`.

Write down anything surprising, with the world's name and date, and send the diagnostic zip.

## Measuring speed on your computer

Double-click **`RUN_BENCHMARK_WINDOWS.bat`** (laptop plugged in, other programs closed; about 5 minutes). It
creates a temporary world, times "To end of season" for season 1 with all your logical CPUs as workers and
then with half of them, measures memory, and writes `benchmark_result.txt` in the Golf Legacy folder: send
that file. To measure a bigger world, drag its folder (for example the 50-season `world_2027`) onto the .bat:
it works on a temporary copy and never changes the world.

## Known limits of the alpha

- Performance: on your laptop a season-1 skip took 47.9 s (16 workers) and 49.9 s (8). Older worlds take
  longer (season 51 took about 190 s on our slower 4-CPU test machine, not yet measured on yours; see
  `docs/BACKLOG.md`). The first open of a world saved by older code
  can take a minute or two (its history index is upgraded once).
- Records and frivolities use archived seasons only; the current season counts once it ends (Stats include
  the current season so far).
- Rating changes need recorded snapshots: worlds simulated before this version (and every world's first
  season) show "unavailable" until a season has been archived by this version. Ages are
  season year minus birth year (birth dates are not recorded). Careers that began before the world are
  marked partial and left out of debut lists.
- Dated coach and caddie partnerships come from the archive (through the last season end); during a season
  the profile shows the current coach and caddie, and every result shows the team that week.
- Not yet: as-of-year views, the university directory, nation development over time, charts, portraits.
- Windows: the launcher, file locking and replacing files while they are read were designed for Windows
  but have not been run on Windows by us yet — please tell us if anything fails there.
