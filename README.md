# Pomodoro Timer

A beautiful terminal-based Pomodoro Timer with animations and a modern aesthetic.

## Features

- **Animated timer display** - Clean numbers with animated decorations
- **Fun progress bar** - Train during work sessions, unicorn during breaks
- **Ambient animations** - Optional rain or twinkling stars
- **Break activities** - Stretch exercises for short breaks, fun facts for long breaks
- **Multiple alert sounds** - Bell, chime, gong, arcade, or gentle tones
- **Custom quotes** - Load your own motivational quotes
- **Session statistics** - Track pomodoros completed and focus time

## Installation

```bash
pip install rich
```

## Usage

```bash
# Default settings (25/5/15 minutes)
python pomodoro.py

# Custom work duration
python pomodoro.py --work 30

# Enable ambient animations
python pomodoro.py --ambient stars
python pomodoro.py --ambient rain

# Change alert sound
python pomodoro.py --sound chime

# Load custom quotes
python pomodoro.py --quotes my_quotes.txt

# Combine options
python pomodoro.py -w 50 -s 10 --ambient stars --sound arcade
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-w, --work` | Work session duration (minutes) | 25 |
| `-s, --short-break` | Short break duration (minutes) | 5 |
| `-l, --long-break` | Long break duration (minutes) | 15 |
| `-p, --pomodoros` | Pomodoros before long break | 4 |
| `-a, --ambient` | Animation mode: none, rain, stars | none |
| `--sound` | Alert sound: bell, chime, gong, arcade, gentle | bell |
| `-q, --quotes` | Path to custom quotes file | - |

## Controls

| Key | Action |
|-----|--------|
| `P` | Pause timer |
| `R` | Resume timer |
| `S` | Skip to next session |
| `Q` | Quit |

## Custom Quotes File Format

Create a text file with one quote per line. Use `---` to separate work quotes from break quotes:

```
Focus on the process, not the outcome.
One thing at a time.
Stay curious, stay focused.
---
Take a moment to breathe.
You deserve this rest.
Stretch and smile!
```

## Screenshots

```
╭─────────────────── 🍅 POMODORO ───────────────────╮
│                                                    │
│                        ▼                           │
│               ✧   25:00   ✧                        │
│                  ─────────                         │
│                                                    │
│       ═══════════════🚂🚃─────────────  45.2%     │
│                                                    │
│                 🎯  FOCUS TIME                     │
│                                                    │
│                   ● ● ○ ○                          │
│                                                    │
│          "Focus is the new superpower."            │
│                                                    │
│          Today: 2 🍅  •  50m focused               │
│                                                    │
│           P pause   S skip   Q quit                │
╰────────────────────────────────────────────────────╯
```

## License

MIT
