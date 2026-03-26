#!/usr/bin/env python3
"""
Unit tests for password_cracker.py
Run: python3 tests.py
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
check("COMMON_WORDS loaded (>10k)",      len(COMMON_WORDS) > 10_000,     f"got {len(COMMON_WORDS):,}")
check("HASH_ALGORITHMS has 5 entries",   len(HASH_ALGORITHMS) == 5)
check("MD5 fastest",    HASH_ALGORITHMS["MD5"]["speed"] > HASH_ALGORITHMS["SHA-1"]["speed"])
check("Argon2 slowest", HASH_ALGORITHMS["Argon2"]["speed"] < HASH_ALGORITHMS["bcrypt"]["speed"])

# ─────────────────────────────────────────────────────────────────
print("\n=== 2. Common / known-bad passwords (should crack instantly) ===")
instant = ["123456", "password", "qwerty", "abc123", "iloveyou", "1234",
           "hunter2", "admin", "letmein", "welcome", "monkey"]
for pw in instant:
    secs, _, m = estimate_crack_time(pw)
    check(f"'{pw}' → instant (<1s)", secs < 1, f"{format_time(secs)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 3. Patterns (repeat / walk / sequential) ===")
patterns = [("aaaaaa","pattern"), ("qwerty","keyboard_walk"), ("abcdef","sequential"),
            ("111111","common"), ("zxcvbn","keyboard_walk")]
for pw, hint in patterns:
    secs, _, m = estimate_crack_time(pw)
    check(f"'{pw}' → fast (<1s)", secs < 1, f"{format_time(secs)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 4. Dictionary + rule mutations ===")
dict_tests = [
    ("Summer2024!",  120,   "word+suffix should crack < 2 min"),
    ("Football99!",  120,   "word+suffix should crack < 2 min"),
    ("Dallas2023!",  120,   "word+suffix should crack < 2 min"),
    ("P@ssw0rd",     1,     "leet of common should crack < 1s"),
    ("Tr0ub4dor$3",  1,     "leet dictionary should crack < 1s"),
    ("Dragon2024!",  120,   "word+suffix should crack < 2 min"),
    ("Welcome1!",    60,    "word+suffix should crack < 1 min"),
    ("Fluffy2020!",  120,   "word+suffix should crack < 2 min"),
]
for pw, max_secs, desc in dict_tests:
    secs, _, m = estimate_crack_time(pw)
    check(f"'{pw}' ({desc})", secs <= max_secs, f"{format_time(secs)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 5. Strong / unbreakable passwords ===")
strong_tests = [
    ("correcthorsebatterystaple", 86400*365*100,   86400*365*10,   "VERY STRONG multi-word"),
    ("X9$mK2!vQ8nL",             86400*365*10000,  86400*365*100,  "UNBREAKABLE random"),
    ("R4nd0m!xK9#Lp2",           86400*365*100000, 86400*365*1000, "UNBREAKABLE long random"),
]
for pw, min_secs, sanity_min, desc in strong_tests:
    secs, _, m = estimate_crack_time(pw)
    check(f"'{pw}' strong (>{format_time(sanity_min)})", secs >= sanity_min,
          f"got {format_time(secs)} via {m}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 6. Hash speed scaling ===")
pw = "Summer2024!"
times = {}
for algo, info in HASH_ALGORITHMS.items():
    secs, _, _ = estimate_crack_time(pw, hash_speed=info["speed"])
    times[algo] = secs

check("MD5 faster than SHA-1",    times["MD5"]    < times["SHA-1"])
check("SHA-1 faster than SHA-256", times["SHA-1"]  < times["SHA-256"])
check("SHA-256 faster than bcrypt",times["SHA-256"] < times["bcrypt"])
check("bcrypt faster than Argon2", times["bcrypt"]  < times["Argon2"])
check("bcrypt vs MD5 difference significant (>1000x)",
      times["bcrypt"] / times["MD5"] > 1000,
      f"ratio={times['bcrypt']/times['MD5']:.0f}x")

# ─────────────────────────────────────────────────────────────────
print("\n=== 7. Strength tiers ===")
tier_tests = [
    (0.0001, "CRACKED!"),
    (30,     "TERRIBLE"),
    (1800,   "WEAK"),
    (43200,  "FAIR"),
    (86400*10, "MEDIUM"),
    (86400*365*2, "STRONG"),
    (86400*365*500, "VERY STRONG"),
    (86400*365*1_000_000_000, "UNBREAKABLE"),
]
for secs, exp_label in tier_tests:
    label, _, _, _ = get_strength_tier(secs)
    check(f"{format_time(secs)} → {exp_label}", label == exp_label,
          f"got {label}")

# ─────────────────────────────────────────────────────────────────
print("\n=== 8. format_time ===")
check("milliseconds",    "milliseconds" in format_time(0.05))
check("seconds",         "seconds"      in format_time(30))
check("minutes",         "minutes"      in format_time(300))
check("hours",           "hours"        in format_time(7200))
check("days",            "days"         in format_time(86400*3))
check("years",           "years"        in format_time(86400*365*5))
check("INSTANTLY",       format_time(0.0005) == "INSTANTLY")

# ─────────────────────────────────────────────────────────────────
print("\n=== 9. Profanity filter ===")
clean = ["Summer2024!", "password", "Dragon99", "Sunshine7", "hello123",
         "correcthorse", "Dallas2023"]
dirty = ["sh1t!", "a55hole", "c0ck", "F4CK"]

for pw in clean:
    check(f"'{pw}' passes filter", not _contains_profanity(pw))
for pw in dirty:
    check(f"'{pw}' caught by filter", _contains_profanity(pw))

# ─────────────────────────────────────────────────────────────────
print("\n=== 10. Hash computation ===")
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
