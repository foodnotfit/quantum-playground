#!/usr/bin/env python3
"""
PASSWORD CRACKER - Family Day Edition!
Kids enter a password and watch the cracker try to break it.
Teaches password strength through fun visual feedback.
"""

import tkinter as tk
from tkinter import font as tkfont
import random
import string
import math
import time
import threading

# ─── Palette ─────────────────────────────────────────────────────────────────

C = {
    "bg":          "#0d1117",
    "bg2":         "#161b22",
    "bg3":         "#21262d",
    "border":      "#30363d",
    "green":       "#39d353",
    "green_dim":   "#1a7f37",
    "yellow":      "#e3b341",
    "orange":      "#f0883e",
    "red":         "#f85149",
    "blue":        "#58a6ff",
    "purple":      "#bc8cff",
    "cyan":        "#39c5cf",
    "white":       "#f0f6fc",
    "dim":         "#8b949e",
    "matrix":      "#00ff41",
}

# Characters the cracker cycles through during animation
CRACK_CHARS = string.ascii_uppercase + string.digits + "!@#$%&*"

# Common weak passwords for instant-crack detection
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "master",
    "dragon", "111111", "baseball", "iloveyou", "trustno1", "sunshine",
    "letmein", "football", "shadow", "michael", "ninja", "mustang",
    "password1", "123456789", "1234", "12345", "princess", "admin",
    "welcome", "hello", "charlie", "donald", "login", "starwars",
    "soccer", "batman", "test", "pass", "killer", "cookie", "robert",
}


def estimate_crack_time(password):
    """
    Estimate realistic brute-force crack time.
    Returns (seconds, charset_size, description).
    """
    charset_size = 0
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)

    if has_lower:   charset_size += 26
    if has_upper:   charset_size += 26
    if has_digit:   charset_size += 10
    if has_special: charset_size += 32

    if charset_size == 0:
        charset_size = 26  # fallback

    # Check common passwords first
    if password.lower() in COMMON_PASSWORDS:
        return (0.001, charset_size, "common")

    # Simple patterns (all same char, sequential)
    if len(set(password)) == 1:
        return (0.01, charset_size, "pattern")
    if password.isdigit() and len(password) <= 6:
        # PIN-style: small keyspace
        combinations = 10 ** len(password)
        seconds = combinations / 10_000_000_000  # 10 billion guesses/sec
        return (max(seconds, 0.01), charset_size, "pin")

    # Entropy-based estimate
    # Assume 10 billion guesses per second (modern GPU cluster)
    combinations = charset_size ** len(password)
    seconds = combinations / 10_000_000_000

    return (seconds, charset_size, "brute_force")


def format_time(seconds):
    """Format seconds into a human-friendly string."""
    if seconds < 0.001:
        return "INSTANTLY"
    if seconds < 1:
        return f"{seconds*1000:.0f} milliseconds"
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    if seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    if seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    if seconds < 86400 * 365:
        return f"{seconds/86400:.0f} days"
    if seconds < 86400 * 365 * 1000:
        return f"{seconds/(86400*365):.0f} years"
    if seconds < 86400 * 365 * 1_000_000:
        return f"{seconds/(86400*365*1000):.0f} thousand years"
    if seconds < 86400 * 365 * 1_000_000_000:
        return f"{seconds/(86400*365*1_000_000):.0f} million years"
    if seconds < 86400 * 365 * 1e12:
        return f"{seconds/(86400*365*1e9):.0f} billion years"
    return f"{seconds/(86400*365*1e12):.0f} trillion years"


def get_strength_tier(seconds):
    """Returns (label, color, emoji-text, tip)."""
    if seconds < 1:
        return ("CRACKED!", C["red"],
                "Oh no! That was way too easy!",
                "Try making it longer and mixing UPPER, lower, numbers & symbols!")
    if seconds < 3600:
        return ("WEAK", C["orange"],
                "Hmm, not bad but a hacker could still get in!",
                "Add more characters or throw in some symbols like !@#$")
    if seconds < 86400 * 30:
        return ("MEDIUM", C["yellow"],
                "Getting stronger! A hacker would need some time.",
                "Try making it even longer — every character makes it WAY harder!")
    if seconds < 86400 * 365 * 100:
        return ("STRONG", C["green"],
                "Nice work! That's a tough password!",
                "Great job mixing different types of characters!")
    return ("UNBREAKABLE", C["purple"],
            "WOW! Even a supercomputer would give up!",
            "You're a password master! The universe might end before this gets cracked!")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═════════════════════════════════════════════════════════════════════════════

class PasswordCrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PASSWORD CRACKER")
        self.root.configure(bg=C["bg"])
        self.root.geometry("960x780")
        self.root.minsize(800, 650)

        # State
        self.cracking = False
        self.cancel_crack = False
        self.show_password = False

        self.build_ui()

    # ─── Build the full UI ───────────────────────────────────────────────

    def build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        # ── HEADER ──
        header = tk.Frame(self.root, bg=C["bg2"], pady=12)
        header.pack(fill="x")

        title_canvas = tk.Canvas(header, width=700, height=50, bg=C["bg2"],
                                  highlightthickness=0)
        title_canvas.pack()
        title = "PASSWORD  CRACKER"
        colors = [C["green"], C["cyan"], C["blue"], C["purple"],
                  C["yellow"], C["orange"], C["red"]]
        for i, ch in enumerate(title):
            col = colors[i % len(colors)] if ch != " " else C["bg2"]
            title_canvas.create_text(
                90 + i * 33, 28, text=ch, fill=col,
                font=("Courier", 30, "bold"))

        tk.Label(header, text="Enter a password and watch me try to crack it!",
                 font=("Helvetica", 13), fg=C["dim"], bg=C["bg2"]).pack()

        # ── INPUT SECTION ──
        input_section = tk.Frame(self.root, bg=C["bg"], pady=20)
        input_section.pack(fill="x", padx=40)

        tk.Label(input_section, text="TYPE YOUR SECRET PASSWORD:",
                 font=("Courier", 14, "bold"), fg=C["cyan"],
                 bg=C["bg"]).pack(anchor="w", pady=(0, 8))

        entry_row = tk.Frame(input_section, bg=C["bg"])
        entry_row.pack(fill="x")

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            entry_row, textvariable=self.password_var,
            font=("Courier", 22), show="*",
            bg=C["bg3"], fg=C["green"], insertbackground=C["green"],
            relief="flat", borderwidth=0, highlightthickness=2,
            highlightcolor=C["blue"], highlightbackground=C["border"])
        self.password_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.password_entry.bind("<Return>", lambda e: self.start_crack())
        self.password_entry.focus_set()

        # Show/hide toggle
        self.eye_btn = tk.Label(
            entry_row, text="SHOW", font=("Courier", 11, "bold"),
            fg=C["dim"], bg=C["bg3"], cursor="hand2",
            padx=10, pady=8, relief="flat",
            highlightthickness=2, highlightbackground=C["border"])
        self.eye_btn.pack(side="left", padx=(0, 8))
        self.eye_btn.bind("<Button-1>", lambda e: self.toggle_show())

        # CRACK IT button
        self.crack_btn = tk.Button(
            entry_row, text="CRACK IT!", font=("Courier", 16, "bold"),
            fg=C["bg"], bg=C["green"], activebackground=C["cyan"],
            relief="flat", padx=20, pady=6, cursor="hand2",
            command=self.start_crack)
        self.crack_btn.pack(side="left")

        # ── LIVE STATS BAR ──
        stats_frame = tk.Frame(input_section, bg=C["bg"], pady=10)
        stats_frame.pack(fill="x")

        self.len_label = tk.Label(stats_frame, text="Length: 0",
                                   font=("Courier", 11), fg=C["dim"], bg=C["bg"])
        self.len_label.pack(side="left", padx=(0, 20))

        self.charset_label = tk.Label(stats_frame, text="Types: —",
                                       font=("Courier", 11), fg=C["dim"], bg=C["bg"])
        self.charset_label.pack(side="left", padx=(0, 20))

        self.live_strength = tk.Label(stats_frame, text="",
                                       font=("Courier", 11, "bold"), fg=C["dim"], bg=C["bg"])
        self.live_strength.pack(side="left")

        self.password_var.trace_add("write", self.on_password_change)

        # ── CRACKING ANIMATION AREA ──
        self.anim_frame = tk.Frame(self.root, bg=C["bg"])
        self.anim_frame.pack(fill="both", expand=True, padx=40, pady=(0, 5))

        # Matrix-style cracking display
        self.crack_canvas = tk.Canvas(self.anim_frame, bg=C["bg"],
                                       highlightthickness=2,
                                       highlightbackground=C["border"],
                                       height=120)
        self.crack_canvas.pack(fill="x", pady=(0, 10))

        # Progress bar
        prog_outer = tk.Frame(self.anim_frame, bg=C["border"], height=30)
        prog_outer.pack(fill="x", pady=(0, 10))
        prog_outer.pack_propagate(False)

        self.progress_canvas = tk.Canvas(prog_outer, bg=C["bg3"],
                                          highlightthickness=0, height=26)
        self.progress_canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.progress_bar = None
        self.progress_text = None

        # Status text
        self.status_label = tk.Label(self.anim_frame, text="Waiting for a password...",
                                      font=("Courier", 13), fg=C["dim"], bg=C["bg"])
        self.status_label.pack(pady=(0, 5))

        # ── RESULTS AREA ──
        self.results_frame = tk.Frame(self.root, bg=C["bg"])
        self.results_frame.pack(fill="x", padx=40, pady=(0, 10))

        # Result verdict (hidden initially)
        self.verdict_label = tk.Label(self.results_frame, text="",
                                       font=("Courier", 28, "bold"),
                                       fg=C["dim"], bg=C["bg"])
        self.verdict_label.pack(pady=(0, 2))

        self.time_label = tk.Label(self.results_frame, text="",
                                    font=("Courier", 15), fg=C["dim"], bg=C["bg"])
        self.time_label.pack(pady=(0, 2))

        self.message_label = tk.Label(self.results_frame, text="",
                                       font=("Helvetica", 14), fg=C["dim"],
                                       bg=C["bg"], wraplength=700)
        self.message_label.pack(pady=(0, 2))

        self.tip_label = tk.Label(self.results_frame, text="",
                                   font=("Helvetica", 12, "italic"), fg=C["dim"],
                                   bg=C["bg"], wraplength=700)
        self.tip_label.pack(pady=(0, 5))

        # ── STRENGTH METER ──
        meter_outer = tk.Frame(self.results_frame, bg=C["border"], height=20)
        meter_outer.pack(fill="x", pady=(5, 5))
        meter_outer.pack_propagate(False)

        self.meter_canvas = tk.Canvas(meter_outer, bg=C["bg3"],
                                       highlightthickness=0, height=16)
        self.meter_canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.meter_fill = None
        self.meter_text_id = None

        # ── BOTTOM TIPS ──
        tips_frame = tk.Frame(self.root, bg=C["bg2"], pady=10)
        tips_frame.pack(fill="x", side="bottom")

        tk.Label(tips_frame, text="PASSWORD TIPS:",
                 font=("Courier", 11, "bold"), fg=C["cyan"],
                 bg=C["bg2"]).pack()
        tk.Label(tips_frame,
                 text="Longer = Stronger  |  Mix UPPER + lower + 123 + !@#  |  "
                      "Avoid common words  |  Never use 'password' or '123456'",
                 font=("Helvetica", 11), fg=C["dim"],
                 bg=C["bg2"]).pack()

    # ─── Toggle password visibility ──────────────────────────────────────

    def toggle_show(self):
        self.show_password = not self.show_password
        if self.show_password:
            self.password_entry.config(show="")
            self.eye_btn.config(text="HIDE", fg=C["green"])
        else:
            self.password_entry.config(show="*")
            self.eye_btn.config(text="SHOW", fg=C["dim"])

    # ─── Live stats as user types ────────────────────────────────────────

    def on_password_change(self, *args):
        pw = self.password_var.get()
        length = len(pw)
        self.len_label.config(text=f"Length: {length}")

        types = []
        if any(c.islower() for c in pw): types.append("a-z")
        if any(c.isupper() for c in pw): types.append("A-Z")
        if any(c.isdigit() for c in pw): types.append("0-9")
        if any(c in string.punctuation for c in pw): types.append("!@#")
        self.charset_label.config(text=f"Types: {', '.join(types) if types else '—'}")

        if length == 0:
            self.live_strength.config(text="", fg=C["dim"])
        else:
            secs, _, _ = estimate_crack_time(pw)
            label, color, _, _ = get_strength_tier(secs)
            self.live_strength.config(text=label, fg=color)

    # ─── Start the cracking process ──────────────────────────────────────

    def start_crack(self):
        pw = self.password_var.get()
        if not pw:
            self.status_label.config(text="Enter a password first!", fg=C["orange"])
            return
        if self.cracking:
            return

        self.cracking = True
        self.cancel_crack = False
        self.crack_btn.config(state="disabled", bg=C["dim"])
        self.password_entry.config(state="disabled")

        # Clear previous results
        self.verdict_label.config(text="")
        self.time_label.config(text="")
        self.message_label.config(text="")
        self.tip_label.config(text="")
        self.clear_meter()

        # Calculate crack time
        crack_seconds, charset_size, method = estimate_crack_time(pw)
        strength_label, strength_color, message, tip = get_strength_tier(crack_seconds)

        # Decide animation duration (real-time visual, capped for fun)
        if crack_seconds < 1:
            anim_duration = max(0.5, crack_seconds * 2)  # very fast
        elif crack_seconds < 3600:
            anim_duration = min(4.0, 1.5 + math.log10(max(crack_seconds, 1)))
        else:
            anim_duration = 5.0  # strong passwords get a timeout animation

        is_timeout = crack_seconds > 3600  # Will "give up" for strong passwords

        # Run animation in a thread to keep UI responsive
        thread = threading.Thread(
            target=self.run_crack_animation,
            args=(pw, anim_duration, crack_seconds, charset_size,
                  is_timeout, strength_label, strength_color, message, tip),
            daemon=True)
        thread.start()

    def run_crack_animation(self, password, anim_duration, crack_seconds,
                            charset_size, is_timeout, strength_label,
                            strength_color, message, tip):
        """Runs the cracking animation, then shows results."""
        pw_len = len(password)
        cracked = [False] * pw_len
        display = [random.choice(CRACK_CHARS) for _ in range(pw_len)]
        start_time = time.time()

        # For weak passwords, reveal characters progressively
        # For strong passwords, never fully reveal (timeout)
        if not is_timeout:
            # Schedule when each character gets "cracked"
            reveal_times = sorted([random.uniform(0.15, anim_duration * 0.85)
                                   for _ in range(pw_len)])
        else:
            # Strong: reveal at most a couple early chars to tease, then stall
            partial = min(2, pw_len)
            reveal_times = sorted([random.uniform(0.3, anim_duration * 0.3)
                                   for _ in range(partial)])
            reveal_times += [anim_duration + 99] * (pw_len - partial)  # never

        attempts = 0
        frame = 0

        while time.time() - start_time < anim_duration and not self.cancel_crack:
            elapsed = time.time() - start_time
            frame += 1
            attempts += random.randint(50000, 200000)

            # Check if any chars should be revealed
            for i in range(pw_len):
                if not cracked[i] and elapsed >= reveal_times[i]:
                    cracked[i] = True
                    display[i] = password[i]

            # Scramble unrevealed characters
            for i in range(pw_len):
                if not cracked[i]:
                    display[i] = random.choice(CRACK_CHARS)

            # Update UI from main thread
            display_copy = list(display)
            cracked_copy = list(cracked)
            progress = min(elapsed / anim_duration, 1.0)

            if is_timeout:
                status = (f"Trying {attempts:,} combinations... "
                          f"({progress*100:.0f}% of available time)")
            else:
                status = f"Cracking... {attempts:,} attempts"

            self.root.after(0, self.update_crack_display,
                            display_copy, cracked_copy, pw_len, progress,
                            status, is_timeout)

            time.sleep(0.05)  # ~20fps

        # ── FINAL RESULT ──
        if is_timeout:
            # Show "GAVE UP" state — fill remaining with ?
            final_display = []
            for i in range(pw_len):
                if cracked[i]:
                    final_display.append(password[i])
                else:
                    final_display.append("?")
            self.root.after(0, self.show_timeout_result,
                            final_display, cracked, pw_len, crack_seconds,
                            strength_label, strength_color, message, tip)
        else:
            # Cracked — reveal all
            self.root.after(0, self.show_cracked_result,
                            list(password), pw_len, crack_seconds,
                            strength_label, strength_color, message, tip)

        self.cracking = False
        self.root.after(0, lambda: self.crack_btn.config(state="normal", bg=C["green"]))
        self.root.after(0, lambda: self.password_entry.config(state="normal"))

    # ─── UI update helpers (called from main thread) ─────────────────────

    def update_crack_display(self, display, cracked, pw_len, progress,
                              status, is_timeout):
        self.crack_canvas.delete("all")
        canvas_w = self.crack_canvas.winfo_width()
        if canvas_w < 10:
            canvas_w = 800

        # Character sizing
        char_w = min(45, max(25, (canvas_w - 40) // pw_len))
        total_w = char_w * pw_len
        start_x = (canvas_w - total_w) / 2 + char_w / 2

        for i in range(pw_len):
            x = start_x + i * char_w
            y = 60

            if cracked[i]:
                # Cracked char — green box
                self.crack_canvas.create_rectangle(
                    x - char_w/2 + 2, y - 22, x + char_w/2 - 2, y + 22,
                    fill=C["green_dim"], outline=C["green"], width=2)
                self.crack_canvas.create_text(
                    x, y, text=display[i], fill=C["green"],
                    font=("Courier", 20, "bold"))
            else:
                # Scrambling char — dim box with cycling text
                self.crack_canvas.create_rectangle(
                    x - char_w/2 + 2, y - 22, x + char_w/2 - 2, y + 22,
                    fill=C["bg3"], outline=C["border"], width=1)
                col = C["matrix"] if random.random() > 0.3 else C["dim"]
                self.crack_canvas.create_text(
                    x, y, text=display[i], fill=col,
                    font=("Courier", 20, "bold"))

        # Raining characters effect at top
        for _ in range(8):
            rx = random.randint(10, max(canvas_w - 10, 20))
            ry = random.randint(2, 25)
            rc = random.choice(CRACK_CHARS)
            self.crack_canvas.create_text(
                rx, ry, text=rc, fill=C["matrix"],
                font=("Courier", 9), stipple="gray25")

        # Progress bar
        self.progress_canvas.delete("all")
        bar_w = self.progress_canvas.winfo_width()
        if bar_w < 10:
            bar_w = 700
        fill_w = max(1, progress * bar_w)

        bar_color = C["green"] if not is_timeout else (
            C["yellow"] if progress < 0.7 else C["orange"])

        self.progress_canvas.create_rectangle(
            0, 0, fill_w, 30, fill=bar_color, outline="")
        self.progress_canvas.create_text(
            bar_w / 2, 13, text=f"{progress*100:.0f}%",
            fill=C["white"], font=("Courier", 11, "bold"))

        self.status_label.config(text=status, fg=C["cyan"])

    def show_cracked_result(self, display, pw_len, crack_seconds,
                             label, color, message, tip):
        """Password was cracked."""
        # Final display — all green
        self.crack_canvas.delete("all")
        canvas_w = self.crack_canvas.winfo_width()
        if canvas_w < 10: canvas_w = 800

        char_w = min(45, max(25, (canvas_w - 40) // pw_len))
        total_w = char_w * pw_len
        start_x = (canvas_w - total_w) / 2 + char_w / 2

        for i in range(pw_len):
            x = start_x + i * char_w
            y = 60
            self.crack_canvas.create_rectangle(
                x - char_w/2 + 2, y - 22, x + char_w/2 - 2, y + 22,
                fill=C["green_dim"], outline=C["green"], width=2)
            self.crack_canvas.create_text(
                x, y, text=display[i], fill=C["green"],
                font=("Courier", 20, "bold"))

        # Full progress bar in red/orange
        self.progress_canvas.delete("all")
        bar_w = self.progress_canvas.winfo_width()
        self.progress_canvas.create_rectangle(0, 0, bar_w, 30, fill=color, outline="")
        self.progress_canvas.create_text(
            bar_w/2, 13, text="CRACKED!", fill=C["bg"],
            font=("Courier", 12, "bold"))

        self.status_label.config(text="Password decoded!", fg=color)

        time_str = format_time(crack_seconds)
        self.verdict_label.config(text=label, fg=color)
        self.time_label.config(
            text=f"A hacker could crack this in: {time_str}",
            fg=color)
        self.message_label.config(text=message, fg=C["white"])
        self.tip_label.config(text=f"Tip: {tip}", fg=C["yellow"])

        self.draw_strength_meter(crack_seconds, color)

    def show_timeout_result(self, display, cracked, pw_len, crack_seconds,
                             label, color, message, tip):
        """Password was too strong — cracker gave up!"""
        self.crack_canvas.delete("all")
        canvas_w = self.crack_canvas.winfo_width()
        if canvas_w < 10: canvas_w = 800

        char_w = min(45, max(25, (canvas_w - 40) // pw_len))
        total_w = char_w * pw_len
        start_x = (canvas_w - total_w) / 2 + char_w / 2

        for i in range(pw_len):
            x = start_x + i * char_w
            y = 60
            if cracked[i]:
                self.crack_canvas.create_rectangle(
                    x - char_w/2 + 2, y - 22, x + char_w/2 - 2, y + 22,
                    fill=C["green_dim"], outline=C["yellow"], width=2)
                self.crack_canvas.create_text(
                    x, y, text=display[i], fill=C["yellow"],
                    font=("Courier", 20, "bold"))
            else:
                # Failed — red question mark
                self.crack_canvas.create_rectangle(
                    x - char_w/2 + 2, y - 22, x + char_w/2 - 2, y + 22,
                    fill="#2d1015", outline=C["red"], width=2)
                self.crack_canvas.create_text(
                    x, y, text="?", fill=C["red"],
                    font=("Courier", 22, "bold"))

        # Progress bar — stalled
        self.progress_canvas.delete("all")
        bar_w = self.progress_canvas.winfo_width()
        self.progress_canvas.create_rectangle(0, 0, bar_w, 30, fill=C["purple"], outline="")
        self.progress_canvas.create_text(
            bar_w/2, 13, text="GAVE UP!", fill=C["white"],
            font=("Courier", 12, "bold"))

        self.status_label.config(
            text="The cracker couldn't break your password!", fg=C["purple"])

        time_str = format_time(crack_seconds)
        self.verdict_label.config(text=label, fg=color)
        self.time_label.config(
            text=f"Estimated time to crack: {time_str}",
            fg=color)
        self.message_label.config(text=message, fg=C["white"])
        self.tip_label.config(text=f"Tip: {tip}", fg=C["yellow"])

        self.draw_strength_meter(crack_seconds, color)

    # ─── Strength meter ──────────────────────────────────────────────────

    def draw_strength_meter(self, crack_seconds, color):
        self.meter_canvas.delete("all")
        w = self.meter_canvas.winfo_width()
        if w < 10: w = 700

        # Map seconds to 0-1 (log scale)
        if crack_seconds < 0.001:
            fill = 0.02
        else:
            fill = min(1.0, (math.log10(max(crack_seconds, 0.001)) + 3) / 18)
            # -3 (milliseconds) to 15 (trillion years) mapped to 0-1

        fill_w = max(4, fill * w)

        # Draw segmented meter
        segments = [
            (0.15, C["red"]),
            (0.30, C["orange"]),
            (0.50, C["yellow"]),
            (0.75, C["green"]),
            (1.0,  C["purple"]),
        ]

        drawn = 0
        for threshold, seg_color in segments:
            seg_end = threshold * w
            if drawn < fill_w:
                draw_to = min(seg_end, fill_w)
                if draw_to > drawn:
                    self.meter_canvas.create_rectangle(
                        drawn, 0, draw_to, 20,
                        fill=seg_color, outline="")
                drawn = draw_to

        # Labels
        labels = [
            (0.08, "Weak"), (0.25, "Fair"),
            (0.42, "Medium"), (0.65, "Strong"), (0.88, "Fort Knox")
        ]
        for pos, text in labels:
            self.meter_canvas.create_text(
                pos * w, 9, text=text, fill=C["bg"],
                font=("Helvetica", 8, "bold"))

    def clear_meter(self):
        self.meter_canvas.delete("all")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordCrackerApp(root)
    root.mainloop()
