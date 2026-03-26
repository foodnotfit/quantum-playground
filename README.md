# 🔐 Password Cracker

A fun, family-friendly offline password strength visualizer built with Python and Tkinter.  
Enter a password and watch it get cracked in real time — with a full visual pipeline showing exactly how a hacker would break it.

---

## ✨ Features

### 🎨 UI & Visual
- Dark terminal aesthetic with color-coded strength tiers
- **Rainbow Table Crawl** — animated scrolling panel simulates a real table lookup, highlights a match if found (or escalates to dictionary attack if not)
- **Matrix-style crack animation** — characters scramble and resolve as each position is "cracked"
- Live strength indicator as you type (updates on every keystroke)
- Animated progress bar with attack phase labels
- Segmented strength meter (Weak → Fort Knox)
- Show/Hide password toggle

### 🧠 Realistic Crack Time Engine
Uses a **layered attack model** — always picks the fastest (worst-case for the defender):

| Layer | Attack Type | Example Caught |
|-------|------------|----------------|
| 1 | Credential stuffing (known list) | `password`, `123456` → instant |
| 2 | Repeat / sequential patterns | `aaaaaa`, `qwerty`, `abcde` → instant |
| 3 | Leet-speak reversal | `P@ssw0rd` → instant |
| 4 | Dictionary word + appended digits/symbols | `Summer2024!`, `Football99!` → milliseconds |
| 5 | Dictionary + rule-based mutations | `Tr0ub4dor&3` → ~200ms |
| 6 | Multi-word combination attack | `correcthorsebatterystaple` → 507 years ✅ |
| 7 | Pure brute-force | `X9$mK2!vQ8nL` → 2 million years ✅ |

**Speed model:** 10 billion guesses/sec (GPU cluster) for brute-force, 100 billion/sec for dictionary/rule attacks — based on realistic 2024 benchmarks.

### 📊 Strength Tiers (8 levels)
| Rating | Time to Crack |
|--------|--------------|
| CRACKED! | < 1 second |
| TERRIBLE | < 1 minute |
| WEAK | < 1 hour |
| FAIR | < 1 day |
| MEDIUM | < 30 days |
| STRONG | < 10 years |
| VERY STRONG | < 1 million years |
| UNBREAKABLE | 1 million+ years |

### 🔑 Hash Algorithm Layer

Real-world password cracking depends entirely on *how* the password was stored. The app now includes a full hash education layer:

**Algorithm Selector** — choose how the password is "stored" and watch crack time change dramatically:

| Algorithm | GPU Speed | Notes |
|-----------|-----------|-------|
| MD5 | ~100 billion/sec | Ancient — effectively broken |
| SHA-1 | ~10 billion/sec | Old standard — fast to crack |
| SHA-256 | ~3 billion/sec | Common but still too fast |
| bcrypt | ~100,000/sec | Designed to be slow — game changer |
| Argon2 | ~1,000/sec | Modern gold standard |

**Same password, radically different outcomes** — `Summer2024!` as an example:
| Algorithm | Time to Crack |
|-----------|--------------|
| MD5 | 8 seconds |
| SHA-1 | 1.3 minutes |
| SHA-256 | 4.5 minutes |
| bcrypt | 93 days |
| Argon2 | 25 years |

**Live Hash Display** — as you type, the app computes and shows the real hex hash of your password using `hashlib`. This demonstrates that databases never store your actual password — only this unreadable fingerprint. bcrypt/Argon2 show a SHA-256 stand-in since those require external libraries, clearly labeled.

**Hash Phase Animation** — Phase 2 of the crack pipeline: password characters feed into an animated "HASH FN" box, and the hash output builds up character by character on the right. Final frame shows the full hash with the label *"↑ This is what a hacker sees after a data breach."*

### 📚 Offline Wordlist Augmentation (80k+ entries)
Three sources merged at startup — no internet required:

| Source | Entries | File |
|--------|---------|------|
| SecLists top-10k common passwords | 10,000 | `wordlists/common-10k.txt` |
| RockyYou top-75k breach passwords | 59,186 | `wordlists/rockyou-75k.txt` |
| Google 10k common English words | 9,894 | `wordlists/english-words-10k.txt` |
| Rainbow table passwords | 18,069 | `rainbow_passwords.txt` |
| Rainbow table dictionary words | 15,321 | `rainbow_words.txt` |
| **Combined unique total** | **~80,000+** | `wordlists/combined.pkl.gz` |

The `.pkl.gz` is a pre-compiled compressed binary (~309KB) for fast startup loading.

### 🚫 Profanity Filter
- Blocks inappropriate passwords — shows `⚠ INAPPROPRIATE` live as you type
- Full message on submit: *"Inappropriate language is not allowed."*
- Catches leet-speak variants and word+digit combinations
- Uses [`better-profanity`](https://pypi.org/project/better-profanity/) library with hardcoded fallback if not installed

---

## 🚀 Getting Started

### Requirements
- Python 3.x
- Tkinter (included with most Python installs)
- `better-profanity` (optional but recommended)

### Install & Run

```bash
# Clone the repo
git clone https://github.com/foodnotfit/password-cracker.git
cd password-cracker

# Install profanity filter (optional)
pip3 install better-profanity

# Run
python3 password_cracker.py
```

---

## 📁 File Structure

```
password-cracker/
├── password_cracker.py          # Main application
├── rainbow_passwords.txt        # 18k common passwords (rainbow table)
├── rainbow_words.txt            # 15k dictionary words (rainbow table)
├── wordlists/
│   ├── combined.pkl.gz          # Pre-compiled 65k merged wordlist (fast load)
│   ├── common-10k.txt           # SecLists top-10k passwords
│   ├── rockyou-75k.txt          # RockyYou top-75k breach passwords
│   └── english-words-10k.txt   # Google 10k common English words
└── README.md
```

---

## 🔬 How It Works

### Rainbow Table Phase
When you hit **CRACK IT!**, the app first simulates a rainbow table lookup:
- Scrolls through known password entries at high speed
- If the password is in the table → entries freeze, row highlights red, match displayed
- If not found → escalates to dictionary + brute-force phase

### Crack Animation Phase
- Weak passwords: characters resolve one by one (like a real brute-force)
- Strong passwords: cracker "gives up" — unresolved chars show as `?`
- Progress bar and status label show the active attack method throughout

### Attack Method Detection
The result always shows which attack vector cracked it:
- *"Cracked via credential stuffing (known password list) in: instantly"*
- *"Cracked via dictionary + appended digits/symbols in: 8 seconds"*
- *"Estimated time to crack (full brute-force): 2 million years"*

---

## 💡 Password Tips

- **Longer = stronger** — every character exponentially increases crack time
- **Mix character types** — UPPER + lower + 123 + !@#
- **Avoid real words** — even with numbers added, dictionary attacks find them fast
- **Passphrases work** — `correcthorsebatterystaple` beats `P@ssw0rd` by 500 years
- **Never reuse passwords** — use a password manager

---

## 📜 License

MIT — free to use, modify, and share.

---

*Built for family learning and security education. All cracking is simulated — no actual hashing or network calls.*
