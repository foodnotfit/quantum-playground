#!/usr/bin/env python3
"""
Unit tests for password_cracker.py
Run: python3 tests.py

Tier labels (NIST SP 800-63B-4 aligned):
  VERY WEAK | WEAK | FAIR | STRONG | VERY STRONG | EXCEPTIONAL
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from password_cracker import (
    estimate_crack_time, format_time, get_strength_tier,
    HASH_ALGORITHMS, COMMON_PASSWORDS, COMMON_WORDS,
    _contains_profanity, _compute_hash,
)

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ {name}")
        PASS += 1
    else:
        print(f"  ❌ {name}{' — ' + detail if detail else ''}")
        FAIL += 1

# ─────────────────────────────────────────────────────────────────
print("\n=== 1. Wordlist loading ===")
check("COMMON_PASSWORDS loaded (>10k)",  len(COMMON_PASSWORDS) > 10_000, f"got {len(COMMON_PASSWORDS):,}")
check("COMMON_WORDS loaded (>1k)",       len(COMMON_WORDS) > 1_000,      f"got {len(COMMON_WORDS):,}")
check("HASH_ALGORITHMS has 5 entries",   len(HASH_ALGORITHMS) == 5)
check("MD5 fastest",    HASH_ALGORITHMS["MD5"]["speed"] > HASH_ALGORITHMS["SHA-1"]["speed"])
check("Argon2 slowest", HASH_ALGORITHMS["Argon2"]["speed"] < HASH_ALGORITHMS["bcrypt"]["speed"])

# ─────────────────────────────────────────────────────────────────
print("\n=== 2. Common / known-bad passwords (should crack instantly) ===")
instant = ["123456", "password", "qwerty", "abc123", "iloveyou", "1234",
           "admin", "letmein", "welcome", "monkey"]
for pw in instant:
    quality, display, cs, m = estimate_crack_time(pw)
    check(f"'{pw}' → instant (<1s)", quality < 1, f"{format_time(quality)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 3. Patterns (repeat / walk / sequential) ===")
patterns = [("aaaaaa","pattern"), ("qwerty","keyboard_walk"), ("abcdef","sequential"),
            ("111111","common"), ("zxcvbn","keyboard_walk")]
for pw, hint in patterns:
    quality, display, cs, m = estimate_crack_time(pw)
    check(f"'{pw}' → fast (<1s)", quality < 1, f"{format_time(quality)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 4. Dictionary + rule mutations ===")
dict_tests = [
    ("Summer2024!",  3600,  "word+suffix should crack < 1hr"),
    ("Football99!",  3600,  "word+suffix should crack < 1hr"),
    ("P@ssw0rd",     1,     "leet of common should crack < 1s"),
    ("Dragon2024!",  3600,  "word+suffix should crack < 1hr"),
    ("Welcome1!",    3600,  "word+suffix should crack < 1hr"),
]
for pw, max_secs, desc in dict_tests:
    quality, display, cs, m = estimate_crack_time(pw)
    check(f"'{pw}' ({desc})", quality <= max_secs, f"{format_time(quality)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 5. Name+name combos (must be VERY WEAK) ===")
name_combos = [
    "JasonMoore", "CarlosEmbury", "JohnSmith", "MaryJones",
    "MichaelDavis", "jasonmoore", "carlosembury",
]
for pw in name_combos:
    quality, display, cs, m = estimate_crack_time(pw)
    label, _, _, _ = get_strength_tier(quality)
    check(f"'{pw}' → VERY WEAK", label == "VERY WEAK",
          f"got {label} ({format_time(quality)} via {m})")

# ─────────────────────────────────────────────────────────────────
print("\n=== 6. Strong / high-entropy passwords ===")
strong_tests = [
    ("correcthorsebatterystaple", 86400*365*10,    "strong multi-word passphrase"),
    ("X9$mK2!vQ8nL",             86400*365*100,   "high-entropy random"),
    ("R4nd0m!xK9#Lp2qZ",        86400*365*1000,  "long high-entropy random"),
]
for pw, min_secs, desc in strong_tests:
    quality, display, cs, m = estimate_crack_time(pw)
    check(f"'{pw}' strong (>{format_time(min_secs)})", quality >= min_secs,
          f"got {format_time(quality)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 7. Hash speed scaling (display time scales with algo) ===")
pw = "Summer2024!"
times = {}
for algo, info in HASH_ALGORITHMS.items():
    quality, display, cs, m = estimate_crack_time(pw, hash_speed=info["speed"])
    times[algo] = display  # display time scales with hash speed

check("MD5 display faster than bcrypt display",    times["MD5"]    < times["bcrypt"])
check("SHA-256 display faster than bcrypt display",times["SHA-256"] < times["bcrypt"])
check("bcrypt display faster than Argon2 display", times["bcrypt"]  < times["Argon2"])
check("bcrypt vs MD5 display difference significant (>10x)",
      times["bcrypt"] / times["MD5"] > 10,
      f"ratio={times['bcrypt']/times['MD5']:.0f}x")

# Strength LABEL must be same regardless of hash (quality score is always MD5 baseline)
labels = {}
for algo, info in HASH_ALGORITHMS.items():
    quality, display, cs, m = estimate_crack_time(pw, hash_speed=info["speed"])
    labels[algo], _, _, _ = get_strength_tier(quality)
check("Strength label identical across all hash algorithms",
      len(set(labels.values())) == 1,
      f"got: {labels}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 8. Strength tiers (NIST SP 800-63B-4 aligned) ===")
tier_tests = [
    (0.0001,               "VERY WEAK"),
    (30,                   "WEAK"),
    (1800,                 "WEAK"),
    (86400 * 5,            "FAIR"),
    (86400 * 365 * 2,      "STRONG"),
    (86400 * 365 * 500,    "VERY STRONG"),
    (86400 * 365 * 2_000_000, "EXCEPTIONAL"),
]
for secs, exp_label in tier_tests:
    label, _, _, _ = get_strength_tier(secs)
    check(f"{format_time(secs)} → {exp_label}", label == exp_label,
          f"got '{label}'")

# ─────────────────────────────────────────────────────────────────
print("\n=== 9. format_time ===")
check("milliseconds",    "milliseconds" in format_time(0.05))
check("seconds",         "seconds"      in format_time(30))
check("minutes",         "minutes"      in format_time(300))
check("hours",           "hours"        in format_time(7200))
check("days",            "days"         in format_time(86400*3))
check("years",           "years"        in format_time(86400*365*5))
check("INSTANTLY",       format_time(0.0005) == "INSTANTLY")

# ─────────────────────────────────────────────────────────────────
print("\n=== 10. Profanity filter ===")
clean = ["Summer2024!", "password", "Dragon99", "Sunshine7", "hello123",
         "correcthorse", "Dallas2023"]
dirty = ["sh1t!", "a55hole", "F4CK"]

for pw in clean:
    check(f"'{pw}' passes filter", not _contains_profanity(pw))
for pw in dirty:
    check(f"'{pw}' caught by filter", _contains_profanity(pw))

# ─────────────────────────────────────────────────────────────────
print("\n=== 11. Hash computation ===")
h = _compute_hash("password", "MD5")
check("MD5 hash is 32 hex chars", len(h) == 32 and all(c in "0123456789abcdef" for c in h))
h2 = _compute_hash("password", "SHA-256")
check("SHA-256 hash is 64 hex chars", len(h2) == 64)
check("Different passwords → different hashes",
      _compute_hash("abc", "MD5") != _compute_hash("xyz", "MD5"))
check("Same password → same hash (deterministic)",
      _compute_hash("test123", "SHA-1") == _compute_hash("test123", "SHA-1"))

# ─────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
total = PASS + FAIL
print(f"Results: {PASS}/{total} passed  |  {FAIL} failed")
if FAIL == 0:
    print("🎉 All tests passed!")
else:
    print("⚠️  Some tests failed — review above.")
sys.exit(0 if FAIL == 0 else 1)
