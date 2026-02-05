#!/usr/bin/env python3
"""
Pomodoro Timer - A beautiful terminal-based pomodoro timer
with ASCII art, smooth animations, and a modern aesthetic.
"""

import argparse
import sys
import time
import random
import os
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    import msvcrt  # Windows
    WINDOWS = True
except ImportError:
    import select
    import tty
    import termios
    WINDOWS = False

# Windows sound support
if WINDOWS:
    try:
        import winsound
        HAS_WINSOUND = True
    except ImportError:
        HAS_WINSOUND = False
else:
    HAS_WINSOUND = False

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
import pyfiglet


# Motivational quotes for work sessions
WORK_QUOTES = [
    "Focus is the new superpower.",
    "Small steps lead to big results.",
    "Deep work, deep rewards.",
    "You're building something great.",
    "Stay in the zone.",
    "Progress over perfection.",
    "One task at a time.",
    "Your future self will thank you.",
    "Distractions can wait.",
    "You're in the flow.",
    "Quality time, quality work.",
    "Make this session count.",
]

# Relaxing messages for breaks
BREAK_QUOTES = [
    "Stretch those muscles!",
    "Hydrate yourself.",
    "Rest your eyes, look away.",
    "Take a deep breath.",
    "You've earned this break.",
    "Movement is medicine.",
    "Clear your mind.",
    "Relax and recharge.",
]

# Stretch exercises for breaks
STRETCH_EXERCISES = [
    "🙆 Neck rolls: Slowly roll your head in circles, 5 times each direction.",
    "💪 Shoulder shrugs: Raise shoulders to ears, hold 5 sec, release. Repeat 5x.",
    "🖐️ Wrist circles: Rotate your wrists slowly, 10 times each direction.",
    "👀 Eye exercise: Look at something 20 feet away for 20 seconds.",
    "🧘 Seated twist: Twist your torso left, hold 15 sec. Repeat on right.",
    "🦵 Leg stretch: Extend one leg, reach for your toes. Hold 15 sec each.",
    "🤲 Finger stretches: Spread fingers wide, hold 5 sec. Make fists. Repeat 5x.",
    "🏃 Stand up! Walk around for a minute to get blood flowing.",
    "😤 Deep breathing: Inhale 4 sec, hold 4 sec, exhale 4 sec. Repeat 5x.",
    "🙂 Face relaxation: Scrunch your face tight, then relax. Repeat 3x.",
]

# Fun facts for long breaks
FUN_FACTS = [
    "🍅 The Pomodoro Technique was invented by Francesco Cirillo in the late 1980s.",
    "🧠 Your brain can only focus intensely for about 90-120 minutes before needing rest.",
    "☕ Coffee takes about 20 minutes to kick in - time it with your break!",
    "🌊 The human brain is about 75% water. Stay hydrated!",
    "😴 A 20-minute power nap can boost alertness and performance.",
    "🎵 Listening to music without lyrics can improve focus for many people.",
    "🌿 Having plants nearby can increase productivity by up to 15%.",
    "💡 Thomas Edison took regular naps to boost his creativity.",
    "🚶 Walking increases creative thinking by up to 60%.",
    "🌅 Most people are most productive in the late morning (9-11 AM).",
]

# Ambient animation characters
RAIN_CHARS = ["│", "┃", "╽", "╿", "┆", "┇", "┊", "┋"]
STAR_CHARS = ["✦", "✧", "⋆", "∗", ".", "·", "✶", "✷", "✸", "★", "☆"]

# Sound types
SOUND_TYPES = ["bell", "chime", "gong", "arcade", "gentle"]


class SessionType(Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass
class TimerConfig:
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    pomodoros_until_long_break: int = 4
    ambient_mode: str = "none"  # none, rain, stars
    sound_type: str = "bell"    # bell, chime, gong, arcade, gentle
    quotes_file: str = ""       # path to custom quotes file


@dataclass
class SessionStats:
    """Track session statistics."""
    total_pomodoros_completed: int = 0
    total_focus_minutes: int = 0
    session_start_time: datetime = field(default_factory=datetime.now)
    current_quote: str = ""
    current_activity: str = ""  # stretch or fun fact for breaks


def load_custom_quotes(filepath: str) -> tuple[list[str], list[str]]:
    """Load custom quotes from a file. Format: one quote per line, '---' separates work/break quotes."""
    work_quotes = []
    break_quotes = []

    try:
        path = Path(filepath)
        if not path.exists():
            return [], []

        content = path.read_text(encoding='utf-8')
        sections = content.split('---')

        if len(sections) >= 1:
            work_quotes = [q.strip() for q in sections[0].strip().split('\n') if q.strip()]
        if len(sections) >= 2:
            break_quotes = [q.strip() for q in sections[1].strip().split('\n') if q.strip()]

        return work_quotes, break_quotes
    except Exception:
        return [], []


class PomodoroTimer:
    def __init__(self, config: TimerConfig):
        self.config = config
        self.console = Console()
        self.current_session = SessionType.WORK
        self.pomodoro_count = 0
        self.is_running = False
        self.is_paused = False
        self.should_quit = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.key_pressed = None
        self.stats = SessionStats()
        self.animation_frame = 0

        # Load custom quotes if provided
        self.work_quotes = WORK_QUOTES.copy()
        self.break_quotes = BREAK_QUOTES.copy()
        if config.quotes_file:
            custom_work, custom_break = load_custom_quotes(config.quotes_file)
            if custom_work:
                self.work_quotes = custom_work
            if custom_break:
                self.break_quotes = custom_break

        self.stats.current_quote = random.choice(self.work_quotes)

        # Generate ambient animation field (for rain/stars)
        self.ambient_field = self._generate_ambient_field()

    def _generate_ambient_field(self) -> list[list[str]]:
        """Generate a field of ambient characters for animation."""
        width, height = 60, 8
        field = []
        for _ in range(height):
            row = []
            for _ in range(width):
                if random.random() < 0.15:  # 15% chance of a character
                    if self.config.ambient_mode == "rain":
                        row.append(random.choice(RAIN_CHARS))
                    elif self.config.ambient_mode == "stars":
                        row.append(random.choice(STAR_CHARS))
                    else:
                        row.append(" ")
                else:
                    row.append(" ")
            field.append(row)
        return field

    def _animate_ambient_field(self):
        """Animate the ambient field."""
        if self.config.ambient_mode == "none":
            return

        if self.config.ambient_mode == "rain":
            # Rain falls down
            for col in range(len(self.ambient_field[0])):
                # Move everything down
                for row in range(len(self.ambient_field) - 1, 0, -1):
                    self.ambient_field[row][col] = self.ambient_field[row - 1][col]
                # New drop at top
                if random.random() < 0.1:
                    self.ambient_field[0][col] = random.choice(RAIN_CHARS)
                else:
                    self.ambient_field[0][col] = " "

        elif self.config.ambient_mode == "stars":
            # Stars twinkle
            for row in range(len(self.ambient_field)):
                for col in range(len(self.ambient_field[0])):
                    if self.ambient_field[row][col] != " ":
                        if random.random() < 0.3:  # 30% chance to change
                            self.ambient_field[row][col] = random.choice(STAR_CHARS)
                    elif random.random() < 0.02:  # Small chance for new star
                        self.ambient_field[row][col] = random.choice(STAR_CHARS)
                    elif random.random() < 0.05:  # Small chance to disappear
                        if self.ambient_field[row][col] != " ":
                            self.ambient_field[row][col] = " "

    def _render_ambient_line(self, row_idx: int) -> str:
        """Render a single line of the ambient field."""
        if self.config.ambient_mode == "none" or row_idx >= len(self.ambient_field):
            return ""

        row = self.ambient_field[row_idx]
        if self.config.ambient_mode == "rain":
            color = "#4dabf7"  # Light blue for rain
        else:
            color = "#ffd43b"  # Yellow for stars

        return f"[dim {color}]{''.join(row)}[/dim {color}]"

    def get_session_duration(self) -> int:
        """Get duration in seconds for current session type."""
        if self.current_session == SessionType.WORK:
            return self.config.work_minutes * 60
        elif self.current_session == SessionType.SHORT_BREAK:
            return self.config.short_break_minutes * 60
        else:
            return self.config.long_break_minutes * 60

    def get_session_color(self) -> str:
        """Get color for current session type."""
        if self.current_session == SessionType.WORK:
            return "#ff6b6b"  # Coral red
        elif self.current_session == SessionType.SHORT_BREAK:
            return "#51cf66"  # Fresh green
        else:
            return "#339af0"  # Sky blue

    def get_session_accent(self) -> str:
        """Get accent color for current session type."""
        if self.current_session == SessionType.WORK:
            return "#fa5252"
        elif self.current_session == SessionType.SHORT_BREAK:
            return "#40c057"
        else:
            return "#228be6"

    def get_session_emoji(self) -> str:
        """Get emoji for current session type."""
        if self.current_session == SessionType.WORK:
            return "🎯"
        elif self.current_session == SessionType.SHORT_BREAK:
            return "☕"
        else:
            return "🌴"

    def get_session_name(self) -> str:
        """Get display name for current session type."""
        if self.current_session == SessionType.WORK:
            return "FOCUS TIME"
        elif self.current_session == SessionType.SHORT_BREAK:
            return "SHORT BREAK"
        else:
            return "LONG BREAK"

    def get_pomodoro_indicators(self) -> str:
        """Create visual pomodoro count indicators."""
        total = self.config.pomodoros_until_long_break
        filled = self.pomodoro_count
        indicators = ""
        for i in range(total):
            if i < filled:
                indicators += "[#ff6b6b]●[/#ff6b6b] "
            else:
                indicators += "[dim]○[/dim] "
        return indicators.strip()

    def format_duration(self, minutes: int) -> str:
        """Format duration nicely."""
        if minutes >= 60:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m" if mins else f"{hours}h"
        return f"{minutes}m"

    def format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def render_ascii_time(self, time_str: str) -> str:
        """Render time as ASCII art."""
        try:
            fig = pyfiglet.Figlet(font='colossal', width=200)
            return fig.renderText(time_str)
        except Exception:
            # Fallback to a simpler font
            fig = pyfiglet.Figlet(font='big', width=200)
            return fig.renderText(time_str)

    def create_display(self) -> Panel:
        """Create the timer display panel."""
        time_str = self.format_time(self.remaining_seconds)
        ascii_time = self.render_ascii_time(time_str)

        # Calculate progress
        progress_pct = ((self.total_seconds - self.remaining_seconds) / self.total_seconds) * 100 if self.total_seconds > 0 else 0

        color = self.get_session_color()
        accent = self.get_session_accent()

        # Fun progress bar with train (work) or unicorn (breaks)
        bar_width = 40
        filled = int(bar_width * progress_pct / 100)
        empty = bar_width - filled

        # Choose the moving character based on session type
        if self.current_session == SessionType.WORK:
            # Train with steam animation
            steam = ["🚃", "🚃"][self.animation_frame % 2]
            mover = f"🚂{steam}"
            track_char = "═"
            empty_char = "─"
        else:
            # Unicorn with sparkle animation
            sparkle = ["✨", "🌟"][self.animation_frame % 2]
            mover = f"🦄{sparkle}"
            track_char = "~"
            empty_char = "·"

        # Build the progress bar with the moving character
        if filled == 0:
            # At the start
            progress_bar = f"{mover}[dim #555555]{empty_char * empty}[/dim #555555]"
        elif filled >= bar_width:
            # Complete
            progress_bar = f"[{color}]{track_char * (bar_width - 1)}[/{color}]{mover}"
        else:
            # In progress - train/unicorn at the front of progress
            progress_bar = f"[{color}]{track_char * (filled - 1)}[/{color}]{mover}[dim #555555]{empty_char * empty}[/dim #555555]"

        progress_line = f"  {progress_bar}  [bold {color}]{progress_pct:5.1f}%[/bold {color}]"

        # Session info
        emoji = self.get_session_emoji()
        session_name = self.get_session_name()

        # Build the display content
        content = Text()

        # Add ASCII time with color
        lines = ascii_time.split('\n')
        for line in lines:
            if line.strip():
                content.append(f"  {line}\n", style=f"bold {color}")

        # Status section
        if self.is_paused:
            # Pulsing pause indicator
            pulse_chars = ["⏸ ", " ⏸"]
            pulse = pulse_chars[self.animation_frame % 2]
            status_line = f"\n[bold #ffd43b]{pulse} PAUSED[/bold #ffd43b]"
        else:
            status_line = f"\n[bold {color}]{emoji}  {session_name}[/bold {color}]"

        # Pomodoro progress indicators
        pomodoro_indicators = self.get_pomodoro_indicators()

        # Stats line
        focus_time = self.format_duration(self.stats.total_focus_minutes)
        stats_line = f"[dim]Today: {self.stats.total_pomodoros_completed} 🍅  •  {focus_time} focused[/dim]"

        # Quote/tip
        quote_line = f"[italic dim]{self.stats.current_quote}[/italic dim]"

        # Activity line (stretch/fun fact during breaks)
        activity_line = ""
        if self.current_session != SessionType.WORK and self.stats.current_activity:
            activity_line = f"[italic #51cf66]{self.stats.current_activity}[/italic #51cf66]"

        # Controls - more minimal and elegant
        if self.is_paused:
            controls = "[dim]R[/dim] resume   [dim]S[/dim] skip   [dim]Q[/dim] quit"
        else:
            controls = "[dim]P[/dim] pause   [dim]S[/dim] skip   [dim]Q[/dim] quit"

        # Build ambient animation lines
        ambient_top = ""
        ambient_bottom = ""
        if self.config.ambient_mode != "none":
            ambient_top = self._render_ambient_line(0) + "\n" + self._render_ambient_line(1)
            ambient_bottom = self._render_ambient_line(2) + "\n" + self._render_ambient_line(3)

        # Build the layout with proper spacing
        layout_elements = []

        # Add ambient top if enabled
        if ambient_top:
            layout_elements.append(Align.center(Text.from_markup(ambient_top)))

        layout_elements.extend([
            Align.center(content),
            Text(""),
            Align.center(Text.from_markup(progress_line)),
            Text(""),
            Align.center(Text.from_markup(status_line)),
            Text(""),
            Align.center(Text.from_markup(pomodoro_indicators)),
            Text(""),
            Align.center(Text.from_markup(quote_line)),
        ])

        # Add activity line for breaks
        if activity_line:
            layout_elements.extend([
                Text(""),
                Align.center(Text.from_markup(activity_line)),
            ])

        layout_elements.extend([
            Text(""),
            Align.center(Text.from_markup(stats_line)),
        ])

        # Add ambient bottom if enabled
        if ambient_bottom:
            layout_elements.append(Align.center(Text.from_markup(ambient_bottom)))

        final_content = Group(*layout_elements)

        # Determine border style based on state
        if self.is_paused:
            border_color = "#ffd43b"
        else:
            border_color = accent

        panel = Panel(
            final_content,
            title=f"[bold #e599f7]  🍅 POMODORO  [/bold #e599f7]",
            subtitle=Text.from_markup(controls),
            subtitle_align="center",
            border_style=border_color,
            box=box.ROUNDED,
            padding=(1, 4),
        )

        return panel

    def check_key(self) -> str | None:
        """Check for keyboard input (non-blocking)."""
        if WINDOWS:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                try:
                    return key.decode('utf-8').lower()
                except:
                    return None
        else:
            # Unix-like systems
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                return sys.stdin.read(1).lower()
        return None

    def play_alert(self):
        """Play an alert sound based on configured sound type."""
        sound_type = self.config.sound_type

        if WINDOWS and HAS_WINSOUND:
            # Use Windows sounds for better audio
            try:
                if sound_type == "bell":
                    for _ in range(3):
                        winsound.Beep(800, 200)
                        time.sleep(0.1)
                elif sound_type == "chime":
                    # Ascending chime
                    for freq in [523, 659, 784]:  # C5, E5, G5
                        winsound.Beep(freq, 200)
                        time.sleep(0.05)
                elif sound_type == "gong":
                    # Low resonant gong
                    winsound.Beep(150, 500)
                    time.sleep(0.2)
                    winsound.Beep(100, 700)
                elif sound_type == "arcade":
                    # Fun arcade sound
                    for freq in [440, 550, 660, 880]:
                        winsound.Beep(freq, 100)
                    winsound.Beep(880, 300)
                elif sound_type == "gentle":
                    # Soft gentle tone
                    winsound.Beep(440, 300)
                    time.sleep(0.3)
                    winsound.Beep(440, 300)
                return
            except Exception:
                pass  # Fall through to terminal bell

        # Fallback to terminal bell with different patterns
        if sound_type == "bell":
            for _ in range(3):
                print('\a', end='', flush=True)
                time.sleep(0.3)
        elif sound_type == "chime":
            for _ in range(4):
                print('\a', end='', flush=True)
                time.sleep(0.15)
        elif sound_type == "gong":
            print('\a', end='', flush=True)
            time.sleep(0.8)
            print('\a', end='', flush=True)
        elif sound_type == "arcade":
            for _ in range(5):
                print('\a', end='', flush=True)
                time.sleep(0.1)
        elif sound_type == "gentle":
            print('\a', end='', flush=True)
            time.sleep(0.5)
            print('\a', end='', flush=True)

    def next_session(self):
        """Move to the next session."""
        if self.current_session == SessionType.WORK:
            # Track completed pomodoro
            self.stats.total_pomodoros_completed += 1
            self.stats.total_focus_minutes += self.config.work_minutes
            self.pomodoro_count += 1

            if self.pomodoro_count >= self.config.pomodoros_until_long_break:
                self.current_session = SessionType.LONG_BREAK
                self.pomodoro_count = 0
                # Fun fact for long breaks
                self.stats.current_activity = random.choice(FUN_FACTS)
            else:
                self.current_session = SessionType.SHORT_BREAK
                # Stretch exercise for short breaks
                self.stats.current_activity = random.choice(STRETCH_EXERCISES)

            # Switch to break quote
            self.stats.current_quote = random.choice(self.break_quotes)
        else:
            self.current_session = SessionType.WORK
            # Switch to work quote
            self.stats.current_quote = random.choice(self.work_quotes)
            # Clear activity for work sessions
            self.stats.current_activity = ""

        self.total_seconds = self.get_session_duration()
        self.remaining_seconds = self.total_seconds

    def run_session(self, live: Live):
        """Run a single timer session."""
        self.total_seconds = self.get_session_duration()
        self.remaining_seconds = self.total_seconds
        last_tick = time.time()
        animation_tick = 0

        while self.remaining_seconds > 0 and not self.should_quit:
            # Check for key presses
            key = self.check_key()
            if key:
                if key == 'q':
                    self.should_quit = True
                    break
                elif key == 'p' and not self.is_paused:
                    self.is_paused = True
                elif key == 'r' and self.is_paused:
                    self.is_paused = False
                elif key == 's':
                    # Skip to next session
                    break

            # Update animation frame for pause pulsing and ambient effects
            animation_tick += 1
            if animation_tick >= 5:  # Update animation every 0.5 seconds
                self.animation_frame += 1
                self._animate_ambient_field()
                animation_tick = 0

            # Update display
            live.update(self.create_display())

            current_time = time.time()
            if not self.is_paused:
                if current_time - last_tick >= 1.0:
                    self.remaining_seconds -= 1
                    last_tick = current_time
                time.sleep(0.1)
            else:
                time.sleep(0.1)

        if not self.should_quit and self.remaining_seconds == 0:
            self.play_alert()

    def run(self):
        """Main timer loop."""
        self.is_running = True

        # Setup terminal for Unix
        old_settings = None
        if not WINDOWS:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

        try:
            with Live(self.create_display(), console=self.console, refresh_per_second=10, screen=True) as live:
                while not self.should_quit:
                    self.run_session(live)

                    if not self.should_quit:
                        self.next_session()
        finally:
            # Restore terminal settings for Unix
            if not WINDOWS and old_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        # Show session summary
        self.console.print()
        summary_panel = Panel(
            Align.center(Text.from_markup(
                f"[bold #e599f7]Session Complete![/bold #e599f7]\n\n"
                f"🍅 Pomodoros completed: [bold]{self.stats.total_pomodoros_completed}[/bold]\n"
                f"⏱️  Total focus time: [bold]{self.format_duration(self.stats.total_focus_minutes)}[/bold]\n\n"
                f"[dim]Great work! See you next time.[/dim]"
            )),
            border_style="#e599f7",
            box=box.ROUNDED,
            padding=(1, 4),
        )
        self.console.print(summary_panel)
        self.console.print()


def main():
    parser = argparse.ArgumentParser(
        description="A beautiful terminal-based Pomodoro Timer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pomodoro.py                        # Default settings
  python pomodoro.py --work 30              # 30 min work sessions
  python pomodoro.py --ambient rain         # Enable rain animation
  python pomodoro.py --ambient stars        # Enable stars animation
  python pomodoro.py --sound chime          # Use chime alert sound
  python pomodoro.py --quotes my_quotes.txt # Load custom quotes

Controls:
  P - Pause      S - Skip session
  R - Resume     Q - Quit

Custom Quotes File Format:
  Line-separated quotes. Use '---' to separate work quotes from break quotes.
        """
    )

    parser.add_argument(
        '-w', '--work',
        type=int,
        default=25,
        metavar='MIN',
        help='Work session duration in minutes (default: 25)'
    )
    parser.add_argument(
        '-s', '--short-break',
        type=int,
        default=5,
        metavar='MIN',
        help='Short break duration in minutes (default: 5)'
    )
    parser.add_argument(
        '-l', '--long-break',
        type=int,
        default=15,
        metavar='MIN',
        help='Long break duration in minutes (default: 15)'
    )
    parser.add_argument(
        '-p', '--pomodoros',
        type=int,
        default=4,
        metavar='NUM',
        help='Number of pomodoros before long break (default: 4)'
    )
    parser.add_argument(
        '-a', '--ambient',
        type=str,
        default='none',
        choices=['none', 'rain', 'stars'],
        metavar='MODE',
        help='Ambient animation mode: none, rain, stars (default: none)'
    )
    parser.add_argument(
        '--sound',
        type=str,
        default='bell',
        choices=['bell', 'chime', 'gong', 'arcade', 'gentle'],
        metavar='TYPE',
        help='Alert sound type: bell, chime, gong, arcade, gentle (default: bell)'
    )
    parser.add_argument(
        '-q', '--quotes',
        type=str,
        default='',
        metavar='FILE',
        help='Path to custom quotes file'
    )

    args = parser.parse_args()

    config = TimerConfig(
        work_minutes=args.work,
        short_break_minutes=args.short_break,
        long_break_minutes=args.long_break,
        pomodoros_until_long_break=args.pomodoros,
        ambient_mode=args.ambient,
        sound_type=args.sound,
        quotes_file=args.quotes,
    )

    console = Console()
    console.print()

    # Build startup info
    ambient_info = ""
    if config.ambient_mode != "none":
        ambient_icon = "🌧️" if config.ambient_mode == "rain" else "✨"
        ambient_info = f"\n{ambient_icon} Ambient: [bold]{config.ambient_mode}[/bold]"

    sound_icons = {"bell": "🔔", "chime": "🎵", "gong": "🎶", "arcade": "🕹️", "gentle": "🔕"}
    sound_icon = sound_icons.get(config.sound_type, "🔔")

    startup_panel = Panel(
        Align.center(Text.from_markup(
            f"[bold #e599f7]🍅 POMODORO TIMER[/bold #e599f7]\n\n"
            f"[#ff6b6b]●[/#ff6b6b] Focus: [bold]{config.work_minutes}[/bold] min\n"
            f"[#51cf66]●[/#51cf66] Short break: [bold]{config.short_break_minutes}[/bold] min\n"
            f"[#339af0]●[/#339af0] Long break: [bold]{config.long_break_minutes}[/bold] min\n"
            f"{sound_icon} Sound: [bold]{config.sound_type}[/bold]"
            f"{ambient_info}\n\n"
            f"[dim]Starting in a moment...[/dim]"
        )),
        border_style="#e599f7",
        box=box.ROUNDED,
        padding=(1, 4),
    )
    console.print(startup_panel)
    time.sleep(1.5)

    timer = PomodoroTimer(config)

    try:
        timer.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Timer interrupted. Goodbye![/dim]\n")


if __name__ == "__main__":
    main()
