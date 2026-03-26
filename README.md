# 🔐 Password Cracker

A fun, family-friendly password strength visualizer built with Python and Tkinter.

## What It Does

Enter any password and watch the animated "cracker" try to break it. It shows you:

- A **matrix-style animation** of characters being cracked in real time
- A **live strength rating** as you type (CRACKED → WEAK → MEDIUM → STRONG → UNBREAKABLE)
- The **estimated time** to brute-force your password (milliseconds to trillion years)
- **Actionable tips** on how to make your password stronger

## Features

- 🎨 Dark terminal aesthetic with color-coded strength tiers
- ⚡ Real-time stats: length, character types, live strength rating
- 💥 Animated cracking display with matrix rain effect
- 🔑 Show/Hide password toggle
- 🧠 Entropy-based crack time estimation (10 billion guesses/sec GPU model)
- ⚠️ Instant detection of 40+ common weak passwords
- 📊 Visual strength meter (Weak → Fort Knox)

## Requirements

- Python 3.x
- Tkinter (included with most Python installs)

## Run It

```bash
python3 password_cracker.py
```

## How Crack Time Is Estimated

The app estimates brute-force time based on:
- **Character set size** (lowercase, uppercase, digits, symbols)
- **Password length** (combinations = charset^length)
- **10 billion guesses/second** — a realistic modern GPU cluster attack rate
- **Common password list** — instant detection for known weak passwords

This is for **educational purposes** — teaching password hygiene through interactive feedback.

## Strength Tiers

| Rating | Time to Crack |
|--------|--------------|
| CRACKED! | < 1 second |
| WEAK | < 1 hour |
| MEDIUM | < 30 days |
| STRONG | < 100 years |
| UNBREAKABLE | 100+ years |

## License

MIT
