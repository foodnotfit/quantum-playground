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
import os
import re
import gzip
import pickle
import hashlib

# ─── Profanity Filter ────────────────────────────────────────────────────────
_LEET_NORMALIZE = str.maketrans({
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
    '6': 'g', '7': 't', '8': 'b', '9': 'g', '@': 'a',
    '$': 's', '!': 'i', '+': 't', '|': 'i',
})

def _normalize_for_profanity(text):
    """Lowercase + decode leet-speak so filters catch variants like f4ck, sh1t."""
    return text.lower().translate(_LEET_NORMALIZE)

def _profanity_candidates(text):
    """
    Generate multiple forms of the password to maximize detection:
    - raw text
    - leet-normalized
    - only-alpha chars extracted (strips digits/symbols surrounding words)
    - space-separated alpha tokens from leet-normalized
    """
    raw = text.lower()
    normalized = _normalize_for_profanity(text)
    # Extract only alpha sequences (catches "fuck123" → "fuck")
    alpha_only = " ".join(re.findall(r'[a-z]+', raw))
    alpha_norm  = " ".join(re.findall(r'[a-z]+', normalized))
    return {raw, normalized, alpha_only, alpha_norm}

try:
    from better_profanity import profanity as _profanity_checker
    _profanity_checker.load_censor_words()
    def _contains_profanity(text):
        return any(_profanity_checker.contains_profanity(v)
                   for v in _profanity_candidates(text))
except ImportError:
    _PROFANITY_FALLBACK = {
        "fuck", "shit", "ass", "bitch", "cunt", "dick", "cock", "pussy",
        "bastard", "damn", "crap", "piss", "slut", "whore", "nigger",
        "faggot", "retard", "twat", "wank", "bollocks",
    }
    def _contains_profanity(text):
        for variant in _profanity_candidates(text):
            words = re.findall(r'[a-z]+', variant)
            if any(w in _PROFANITY_FALLBACK for w in words):
                return True
        return False

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

# ─── Attack Speed Constants ──────────────────────────────────────────────
# Modeled on realistic 2024 benchmarks
GUESSES_PER_SEC_BRUTE = 10_000_000_000   # 10B/sec - GPU cluster on fast hashes
GUESSES_PER_SEC_DICT  = 100_000_000_000  # 100B/sec - dictionary/rule-based (smaller keyspace)
DICTIONARY_SIZE       = 200_000          # ~200k common English words
RULE_MULTIPLIER       = 1_000           # leet speak + appends + case variants

# ─── Hash Algorithm Table ────────────────────────────────────────────────
HASH_ALGORITHMS = {
    "MD5":     {"speed": 100_000_000_000, "color": "#f85149", "desc": "Ancient — ~100B/sec"},
    "SHA-1":   {"speed":  10_000_000_000, "color": "#f0883e", "desc": "Old — ~10B/sec"},
    "SHA-256": {"speed":   3_000_000_000, "color": "#e3b341", "desc": "Common — ~3B/sec"},
    "bcrypt":  {"speed":         100_000, "color": "#39d353", "desc": "Slow by design — ~100K/sec"},
    "Argon2":  {"speed":           1_000, "color": "#bc8cff", "desc": "Modern standard — ~1K/sec"},
}

def _compute_hash(password, algo):
    """Compute hash of password for the given algorithm name."""
    algo_map = {"MD5": "md5", "SHA-1": "sha1", "SHA-256": "sha256",
                "bcrypt": "sha256", "Argon2": "sha256"}
    h = hashlib.new(algo_map[algo])
    h.update(password.encode("utf-8"))
    return h.hexdigest()

# ─── Common weak passwords (top ~200 from breach databases) ──────────────

COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "master",
    "dragon", "111111", "baseball", "iloveyou", "trustno1", "sunshine",
    "letmein", "football", "shadow", "michael", "ninja", "mustang",
    "password1", "123456789", "1234", "12345", "princess", "admin",
    "welcome", "hello", "charlie", "donald", "login", "starwars",
    "soccer", "batman", "test", "pass", "killer", "cookie", "robert",
    "flower", "summer", "winter", "spring", "ashley", "bailey", "cheese",
    "chicken", "computer", "diamond", "freedom", "forever", "friends",
    "ginger", "hannah", "hockey", "hunter", "jessica", "jordan",
    "joshua", "love", "maggie", "matrix", "merlin", "michelle",
    "monday", "orange", "peanut", "pepper", "purple", "ranger",
    "samantha", "secret", "silver", "soccer", "sparky", "spider",
    "success", "superman", "thomas", "thunder", "tiger", "trustno1",
    "whatever", "william", "yankees", "zeppelin", "access", "albert",
    "andrea", "angel", "apple", "austin", "banana", "biteme",
    "buster", "calvin", "camaro", "carolina", "cheese", "chester",
    "cocacola", "coffee", "dallas", "dolphin", "dolphins", "digital",
    "eagles", "edward", "falcon", "fender", "ferrari", "fishing",
    "gateway", "george", "gators", "golden", "guitar", "hammer",
    "harley", "harvest", "heather", "helpme", "iceman", "internet",
    "jackson", "jasmine", "jennifer", "johnson", "killer", "knight",
    "lakers", "legend", "london", "lucky", "marina", "marlboro",
    "martin", "maverick", "mercedes", "michigan", "miller", "mistress",
    "mountain", "murphy", "nascar", "nicole", "oliver", "password",
    "patrick", "phoenix", "player", "please", "rabbit", "rachel",
    "rocket", "rosebud", "runner", "samson", "saturn", "scooter",
    "shannon", "sierra", "smokey", "snake", "songbird", "spartan",
    "stanley", "steelers", "testing", "thunder", "topgun", "toyota",
    "travis", "trustme", "tucker", "twitter", "united", "victory",
    "viking", "viper", "warrior", "wizard", "xavier", "yamaha",
    "yankee", "yellow", "123321", "654321", "666666", "696969",
    "777777", "888888", "999999", "000000", "112233", "121212",
    "131313", "abcabc", "abcdef", "qazwsx", "qwerty123", "password123",
    "iloveu", "fuckyou", "asshole", "pussy", "money",
}

# ─── Keyboard walk patterns ─────────────────────────────────────────────

KEYBOARD_WALKS = {
    "qwerty", "qwertz", "qwert", "asdf", "asdfgh", "asdfghjkl",
    "zxcvbn", "zxcvbnm", "qazwsx", "wsxedc", "rfvtgb",
    "123456", "234567", "345678", "456789", "567890",
    "1qaz2wsx", "qweasd", "qweasdzxc",
}

# ─── Leet speak mapping ─────────────────────────────────────────────────

LEET_MAP = {
    "@": "a", "4": "a", "^": "a",
    "8": "b",
    "(": "c", "{": "c", "<": "c",
    "3": "e",
    "6": "g", "9": "g",
    "#": "h",
    "1": "i", "!": "i", "|": "i",
    "0": "o",
    "$": "s", "5": "s",
    "7": "t", "+": "t",
    "2": "z",
}

# ─── Small dictionary of common English words (for compound detection) ──

COMMON_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know",
    "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how",
    "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "love", "life", "hand",
    "high", "keep", "last", "long", "great", "old", "big", "small", "here",
    "man", "world", "head", "still", "name", "food", "home", "night",
    "house", "water", "fire", "game", "car", "city", "tree", "sun", "moon",
    "star", "fish", "bird", "dog", "cat", "book", "door", "girl", "boy",
    "king", "baby", "open", "play", "run", "walk", "talk", "read", "move",
    "live", "real", "dark", "light", "word", "line", "turn", "end", "show",
    "ever", "best", "help", "start", "hard", "left", "right", "hand",
    "red", "blue", "green", "black", "white", "gold", "silver", "rock",
    "music", "band", "song", "cool", "super", "fast", "slow", "hot", "cold",
    "dead", "free", "true", "half", "much", "many", "each", "team", "eye",
    "face", "room", "body", "part", "next", "sure", "full", "kind", "sort",
    "young", "power", "money", "point", "place", "state", "number", "group",
    "table", "class", "north", "south", "east", "west", "story", "child",
    "school", "family", "student", "country", "problem", "mother", "father",
    "brother", "sister", "friend", "system", "program", "question", "change",
    "order", "level", "reason", "office", "leader", "person", "heart",
    "party", "market", "company", "ground", "center", "period", "member",
    "horse", "monkey", "dragon", "tiger", "eagle", "bear", "wolf", "lion",
    "snake", "shark", "hawk", "fox", "rabbit", "mouse", "spider", "queen",
    "prince", "knight", "castle", "tower", "bridge", "river", "ocean",
    "storm", "cloud", "rain", "snow", "wind", "flame", "earth", "stone",
    "sword", "shield", "magic", "spirit", "ghost", "angel", "devil",
    "shadow", "ninja", "pirate", "robot", "alien", "zombie", "vampire",
    "wizard", "warrior", "hunter", "ranger", "master", "legend", "hero",
    "secret", "hidden", "mystic", "crystal", "cosmic", "cyber", "pixel",
    "turbo", "ultra", "mega", "alpha", "omega", "delta", "sigma", "theta",
    "gamma", "beta", "phantom", "titan", "atlas", "phoenix", "falcon",
    "viper", "cobra", "panther", "leopard", "cheetah", "jaguar", "raptor",
    "maverick", "trooper", "captain", "general", "admiral", "pilot",
    "rocket", "comet", "nebula", "galaxy", "cosmos", "orbit", "solar",
    "lunar", "stellar", "quantum", "proton", "neutron", "photon", "laser",
    "plasma", "fusion", "matrix", "cipher", "enigma", "puzzle", "riddle",
    "summer", "winter", "spring", "autumn", "morning", "evening",
    "sunday", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "football", "baseball", "basketball", "soccer", "tennis", "hockey",
    "golf", "boxing", "surfing", "skiing", "racing", "fishing", "hiking",
    "dancing", "singing", "guitar", "piano", "drums", "violin", "flute",
    "banana", "apple", "orange", "cherry", "grape", "lemon", "mango",
    "peach", "melon", "berry", "coconut", "cookie", "chocolate", "candy",
    "sugar", "butter", "pepper", "cheese", "coffee", "pizza", "burger",
    "chicken", "turkey", "bacon", "pasta", "salad", "cream", "sauce",
    "bread", "toast", "juice", "water", "soda", "milk", "cake",
    "diamond", "ruby", "emerald", "pearl", "sapphire", "topaz", "jade",
    "bronze", "copper", "iron", "steel", "chrome", "titanium", "platinum",
    "purple", "yellow", "orange", "pink", "brown", "grey", "gray",
    "violet", "indigo", "scarlet", "crimson", "ivory", "amber", "coral",
    "password", "computer", "internet", "network", "server", "system",
    "hacker", "coder", "gaming", "player", "winner", "loser", "champion",
    "correct", "horse", "battery", "staple", "troubador", "electric",
}


# ─── Rainbow Table Loader ────────────────────────────────────────────────
# Loads external wordlists from files next to this script.
# Falls back to the hardcoded sets above if files aren't found.

def _load_rainbow_table(filename, fallback_set):
    """Load a wordlist file into a set. Returns fallback_set if file not found."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    if not os.path.exists(filepath):
        return fallback_set
    loaded = set()
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            word = line.strip().lower()
            if word:
                loaded.add(word)
    # Merge with the hardcoded fallback so we never lose built-in entries
    loaded.update(fallback_set)
    return loaded


# Load expanded tables (files are optional — game works without them)
COMMON_PASSWORDS = _load_rainbow_table("rainbow_passwords.txt", COMMON_PASSWORDS)
COMMON_WORDS     = _load_rainbow_table("rainbow_words.txt", COMMON_WORDS)

# Update the dictionary size constant to match actual loaded size
DICTIONARY_SIZE = max(DICTIONARY_SIZE, len(COMMON_WORDS))

# Print stats at startup (visible in terminal)
_pw_count = len(COMMON_PASSWORDS)
_wd_count = len(COMMON_WORDS)
print(f"[Rainbow Tables] Loaded {_pw_count:,} passwords + {_wd_count:,} dictionary words")
if _pw_count > 5000:
    print(f"[Rainbow Tables] Enhanced mode: rainbow_passwords.txt loaded!")
if _wd_count > 5000:
    print(f"[Rainbow Tables] Enhanced mode: rainbow_words.txt loaded!")

# ─── Compressed Wordlist Loader (pkl.gz) ────────────────────────────────────
# Loads combined.pkl.gz (SecLists + RockyYou + Google-10k = 65k entries)
# and merges into the existing sets for richer dictionary detection.

def _load_pkl_wordlists():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_path = os.path.join(script_dir, "wordlists", "combined.pkl.gz")
    if not os.path.exists(pkl_path):
        return set(), set()
    try:
        with gzip.open(pkl_path, "rb") as f:
            all_words = pickle.load(f)
        pws  = {w for w in all_words if 2 < len(w) <= 20}
        words = all_words
        print(f"[Wordlist] Loaded {len(pws):,} passwords + {len(words):,} words from combined.pkl.gz")
        return pws, words
    except Exception as e:
        print(f"[Wordlist] Failed to load combined.pkl.gz: {e}")
        return set(), set()

_pkl_passwords, _pkl_words = _load_pkl_wordlists()
COMMON_PASSWORDS |= _pkl_passwords
COMMON_WORDS     |= _pkl_words
DICTIONARY_SIZE   = max(DICTIONARY_SIZE, len(COMMON_WORDS))
_pw_count  = len(COMMON_PASSWORDS)
_wd_count  = len(COMMON_WORDS)
print(f"[Wordlist] Final: {_pw_count:,} passwords, {_wd_count:,} dictionary words")


def _deleet(password):
    """Convert leet-speak password back to plain lowercase."""
    result = []
    for ch in password:
        lower = ch.lower()
        if lower in LEET_MAP:
            result.append(LEET_MAP[lower])
        elif ch in LEET_MAP:
            result.append(LEET_MAP[ch])
        else:
            result.append(lower)
    return "".join(result)


def _strip_trailing_digits_symbols(password):
    """Strip trailing digits and symbols, return (base, suffix)."""
    i = len(password)
    while i > 0 and (password[i-1].isdigit() or password[i-1] in string.punctuation):
        i -= 1
    if i == 0:
        return password, ""
    return password[:i], password[i:]


def _is_keyboard_walk(password):
    """Check if password is a known keyboard walk pattern."""
    return password.lower() in KEYBOARD_WALKS


def _is_sequential(password):
    """Check if password is a simple ascending/descending sequence."""
    if len(password) < 3:
        return False
    chars = [ord(c) for c in password]
    diffs = [chars[i+1] - chars[i] for i in range(len(chars) - 1)]
    # All same diff (ascending or descending by 1)
    if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
        return True
    # All same diff (e.g. "acegi" step of 2)
    if len(set(diffs)) == 1 and abs(diffs[0]) <= 2:
        return True
    return False


def _find_dictionary_words(text):
    """Find dictionary words within text (greedy, longest first)."""
    lower = text.lower()
    found = []
    i = 0
    while i < len(lower):
        best = None
        for length in range(min(12, len(lower) - i), 2, -1):
            candidate = lower[i:i+length]
            if candidate in COMMON_WORDS:
                best = candidate
                break
        if best:
            found.append(best)
            i += len(best)
        else:
            i += 1
    return found


def _compute_charset_size(password):
    """Compute the character space size based on character types present."""
    charset_size = 0
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)
    has_space = " " in password

    if has_lower:   charset_size += 26
    if has_upper:   charset_size += 26
    if has_digit:   charset_size += 10
    if has_special: charset_size += 32
    if has_space:   charset_size += 1  # space is predictable but adds a bit

    if charset_size == 0:
        charset_size = 26  # fallback for weird chars (unicode etc)
    return charset_size


def estimate_crack_time(password, hash_speed=None):
    """
    Estimate realistic password crack time using multiple attack models.
    Returns (seconds, charset_size, method_description).

    Models three attack phases that a real cracker would use:
      1. Dictionary lookup (common passwords, keyboard walks, patterns)
      2. Rule-based attack (leet speak, word + digits, word combos)
      3. Brute-force (raw character-by-character guessing)

    Returns the FASTEST time across all models (worst case for defender).

    If hash_speed is provided (guesses/sec), it overrides the default speed
    constants for ALL attack phases.
    """
    pw_len = len(password)
    pw_lower = password.lower()
    charset_size = _compute_charset_size(password)

    # Determine effective speeds
    eff_brute = hash_speed if hash_speed is not None else GUESSES_PER_SEC_BRUTE
    eff_dict  = hash_speed if hash_speed is not None else GUESSES_PER_SEC_DICT

    # ── Phase 1: Instant / near-instant catches ──────────────────────────

    # (a) Common passwords list (breach databases)
    if pw_lower in COMMON_PASSWORDS:
        return (0.001, charset_size, "common")

    # (b) All identical characters
    if len(set(password)) == 1:
        return (0.001, charset_size, "pattern")

    # (c) Keyboard walks
    if _is_keyboard_walk(password):
        return (0.001, charset_size, "keyboard_walk")

    # (d) Simple sequences (abc, 123, etc.)
    if _is_sequential(password):
        return (0.001, charset_size, "sequential")

    # ── Phase 2: Rule-based / dictionary attacks ─────────────────────────

    best_time = float("inf")
    best_method = "brute_force"

    # (a) De-leet the password and check common list
    deleeted = _deleet(password)
    if deleeted in COMMON_PASSWORDS:
        best_time = 0.01  # leet variant of common password
        best_method = "leet_common"

    # (b) Strip trailing digits/symbols and check base word
    base, suffix = _strip_trailing_digits_symbols(password)
    base_lower = base.lower()
    base_deleeted = _deleet(base)

    if base_lower in COMMON_PASSWORDS or base_deleeted in COMMON_PASSWORDS:
        # Common word + appended digits/symbols
        # Keyspace = common_list × suffix_combos
        suffix_combos = max(1, 10 ** max(len(suffix), 1)) if suffix else 1
        combos = len(COMMON_PASSWORDS) * suffix_combos * 100  # case variants
        t = combos / eff_dict
        if t < best_time:
            best_time = t
            best_method = "common_variant"

    # (c) Check if base is a dictionary word (with or without leet)
    if len(base_lower) >= 3:
        if base_lower in COMMON_WORDS or base_deleeted in COMMON_WORDS:
            suffix_combos = max(1, 10 ** max(len(suffix), 1)) if suffix else 1
            # Dictionary + rules attack
            combos = DICTIONARY_SIZE * RULE_MULTIPLIER * suffix_combos
            t = combos / eff_dict
            if t < best_time:
                best_time = t
                best_method = "dictionary_variant"

    # (d) Check if the de-leeted password is a dictionary word
    if len(deleeted) >= 3 and deleeted in COMMON_WORDS:
        combos = DICTIONARY_SIZE * RULE_MULTIPLIER
        t = combos / eff_dict
        if t < best_time:
            best_time = t
            best_method = "leet_dictionary"

    # (e) Multi-word compound (e.g. "monkeybanana", "soccerball")
    words_found = _find_dictionary_words(deleeted)
    total_word_chars = sum(len(w) for w in words_found)
    leftover = pw_len - total_word_chars
    if len(words_found) >= 2 and leftover <= 4:
        # Combination attack: dictionary^N × small brute-force for leftovers
        combos = (DICTIONARY_SIZE ** len(words_found)) * (94 ** leftover if leftover > 0 else 1)
        t = combos / eff_dict
        if t < best_time:
            best_time = t
            best_method = "multi_word"

    # (f) Pure numeric (PIN-style)
    if password.isdigit():
        combos = 10 ** pw_len
        t = combos / eff_brute
        if t < best_time:
            best_time = t
            best_method = "pin"

    # ── Phase 3: Brute-force ─────────────────────────────────────────────

    combos = charset_size ** pw_len
    brute_time = combos / eff_brute

    if brute_time < best_time:
        best_time = brute_time
        best_method = "brute_force"

    return (best_time, charset_size, best_method)


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
    """Returns (label, color, message, tip)."""
    if seconds < 1:
        return ("CRACKED!", C["red"],
                "Oh no! A hacker would break this instantly!",
                "Try a longer password with UPPER, lower, numbers & symbols — and avoid real words!")
    if seconds < 60:
        return ("TERRIBLE", C["red"],
                "This falls in seconds. Any hacker tool would get in immediately.",
                "Avoid dictionary words, names, and common patterns like Summer2024!")
    if seconds < 3600:
        return ("WEAK", C["orange"],
                "A hacker could crack this in minutes. Still way too easy!",
                "Avoid real words and predictable patterns — even with numbers and symbols added.")
    if seconds < 86400:
        return ("FAIR", C["orange"],
                "Better, but a dedicated attacker could crack this in hours.",
                "Try a passphrase of 4+ random words, or add more random characters.")
    if seconds < 86400 * 30:
        return ("MEDIUM", C["yellow"],
                "A hacker would need days to weeks. Getting there!",
                "Longer and more random is always better — avoid real words if possible.")
    if seconds < 86400 * 365 * 10:
        return ("STRONG", C["green"],
                "Nice! This would take months to years to crack.",
                "Great job! Consider using a password manager to store it safely.")
    if seconds < 86400 * 365 * 1_000_000:
        return ("VERY STRONG", C["green"],
                "Excellent! Even a powerful GPU cluster would take centuries.",
                "You're doing great. A password manager helps you use unique passwords everywhere.")
    return ("UNBREAKABLE", C["purple"],
            "WOW! Even a supercomputer would give up before the universe ends!",
            "You're a password master! 🏆")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═════════════════════════════════════════════════════════════════════════════

class PasswordCrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PASSWORD CRACKER")
        self.root.configure(bg=C["bg"])
        self.root.geometry("960x1020")
        self.root.minsize(800, 860)

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

        # Rainbow table status indicator
        if _pw_count > 5000:
            rt_text = f"RAINBOW TABLE LOADED: {_pw_count:,} passwords + {_wd_count:,} words"
            rt_color = C["green"]
        else:
            rt_text = f"Basic mode: {_pw_count:,} passwords (add rainbow_passwords.txt for more!)"
            rt_color = C["yellow"]
        tk.Label(header, text=rt_text, font=("Courier", 10),
                 fg=rt_color, bg=C["bg2"]).pack()

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

        # ── HASH ALGORITHM SELECTOR ──
        hash_row = tk.Frame(input_section, bg=C["bg"], pady=4)
        hash_row.pack(fill="x")

        tk.Label(hash_row, text="HASH ALGORITHM (how your password is stored):",
                 font=("Courier", 11, "bold"), fg=C["cyan"], bg=C["bg"]).pack(side="left", padx=(0, 8))

        self.hash_algo_var = tk.StringVar(value="MD5")
        algo_menu = tk.OptionMenu(hash_row, self.hash_algo_var, *HASH_ALGORITHMS.keys())
        algo_menu.config(font=("Courier", 11), bg=C["bg3"], fg=C["white"],
                         activebackground=C["bg2"], activeforeground=C["cyan"],
                         highlightthickness=1, highlightbackground=C["border"],
                         relief="flat", bd=0)
        algo_menu["menu"].config(bg=C["bg3"], fg=C["white"], font=("Courier", 11),
                                  activebackground=C["blue"], activeforeground=C["white"])
        algo_menu.pack(side="left", padx=(0, 10))

        self.hash_desc_label = tk.Label(hash_row,
                                         text=HASH_ALGORITHMS["MD5"]["desc"],
                                         font=("Courier", 10), fg=C["dim"], bg=C["bg"])
        self.hash_desc_label.pack(side="left")

        self.hash_algo_var.trace_add("write", self.on_hash_algo_change)

        # ── ALGORITHM COMPARISON BARS ──
        cmp_frame = tk.Frame(input_section, bg=C["bg"], pady=4)
        cmp_frame.pack(fill="x")

        tk.Label(cmp_frame, text="HOW YOUR PASSWORD HOLDS UP BY STORAGE METHOD:",
                 font=("Courier", 10, "bold"), fg=C["dim"], bg=C["bg"]).pack(anchor="w", pady=(0, 4))

        self.algo_cmp_canvas = tk.Canvas(cmp_frame, bg=C["bg"],
                                          highlightthickness=1,
                                          highlightbackground=C["border"],
                                          height=len(HASH_ALGORITHMS) * 22 + 6)
        self.algo_cmp_canvas.pack(fill="x")

        # ── CRACKING ANIMATION AREA ──
        self.anim_frame = tk.Frame(self.root, bg=C["bg"])
        self.anim_frame.pack(fill="both", expand=True, padx=40, pady=(0, 5))

        # ── LIVE HASH DISPLAY PANEL ──
        live_hash_frame = tk.Frame(self.anim_frame, bg=C["bg2"],
                                    highlightthickness=1,
                                    highlightbackground=C["border"])
        live_hash_frame.pack(fill="x", pady=(0, 6))

        lh_top = tk.Frame(live_hash_frame, bg=C["bg2"])
        lh_top.pack(fill="x", padx=8, pady=(4, 0))

        tk.Label(lh_top, text="LIVE HASH", font=("Courier", 10, "bold"),
                 fg=C["dim"], bg=C["bg2"]).pack(side="left")
        self.live_hash_algo_label = tk.Label(lh_top, text="MD5",
                                              font=("Courier", 10, "bold"),
                                              fg=C["cyan"], bg=C["bg2"])
        self.live_hash_algo_label.pack(side="left", padx=(6, 0))

        self.live_hash_value = tk.Label(live_hash_frame,
                                         text="—" * 24,
                                         font=("Courier", 11),
                                         fg=C["cyan"], bg=C["bg2"])
        self.live_hash_value.pack(anchor="w", padx=8, pady=(2, 0))

        tk.Label(live_hash_frame,
                 text="This is what gets stored in a database — not your actual password",
                 font=("Helvetica", 9, "italic"), fg=C["dim"], bg=C["bg2"]).pack(
                     anchor="w", padx=8, pady=(0, 4))

        # ── HASH ANIMATION CANVAS ──
        self.hash_anim_canvas = tk.Canvas(self.anim_frame, bg=C["bg"],
                                           highlightthickness=1,
                                           highlightbackground=C["border"],
                                           height=70)
        self.hash_anim_canvas.pack(fill="x", pady=(0, 6))

        # ── RAINBOW TABLE CRAWL SECTION ──
        rt_header = tk.Frame(self.anim_frame, bg=C["bg"])
        rt_header.pack(fill="x")
        tk.Label(rt_header, text="RAINBOW TABLE LOOKUP",
                 font=("Courier", 10, "bold"), fg=C["purple"], bg=C["bg"]).pack(side="left")
        self.rt_status_label = tk.Label(rt_header, text="",
                 font=("Courier", 10), fg=C["dim"], bg=C["bg"])
        self.rt_status_label.pack(side="left", padx=(10, 0))

        self.rt_canvas = tk.Canvas(self.anim_frame, bg=C["bg"],
                                    highlightthickness=1,
                                    highlightbackground=C["border"],
                                    height=55)
        self.rt_canvas.pack(fill="x", pady=(2, 6))

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

    # ─── Hash algorithm change handler ──────────────────────────────────

    def on_hash_algo_change(self, *args):
        algo = self.hash_algo_var.get()
        info = HASH_ALGORITHMS[algo]
        self.hash_desc_label.config(text=info["desc"], fg=info["color"])
        self.live_hash_algo_label.config(text=algo, fg=info["color"])
        # Refresh live hash display and strength label
        self.on_password_change()

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

        # Update live hash display
        algo = self.hash_algo_var.get()
        algo_info = HASH_ALGORITHMS[algo]
        if length == 0:
            self.live_hash_value.config(text="—" * 24)
        else:
            is_standin = algo in ("bcrypt", "Argon2")
            h = _compute_hash(pw, algo)
            truncated = h[:48] + "..."
            label_prefix = f"[SHA-256 stand-in] " if is_standin else ""
            self.live_hash_value.config(text=f"{label_prefix}{truncated}")
        self.live_hash_algo_label.config(text=algo, fg=algo_info["color"])

        if length == 0:
            self.live_strength.config(text="", fg=C["dim"])
            self.update_algo_comparison("")
        elif _contains_profanity(pw):
            self.live_strength.config(text="⚠ INAPPROPRIATE", fg=C["red"])
            self.update_algo_comparison("")
        else:
            hash_speed = HASH_ALGORITHMS[algo]["speed"]
            secs, _, _ = estimate_crack_time(pw, hash_speed=hash_speed)
            label, color, _, _ = get_strength_tier(secs)
            self.live_strength.config(text=label, fg=color)
            self.update_algo_comparison(pw)

    def update_algo_comparison(self, pw):
        """Draw side-by-side algorithm comparison bars — updates on every keystroke."""
        c = self.algo_cmp_canvas
        c.delete("all")
        cw = c.winfo_width()
        if cw < 10:
            cw = 860

        selected_algo = self.hash_algo_var.get()
        row_h = 22
        label_w = 80    # algorithm name column
        time_w  = 150   # crack time text column
        bar_x   = label_w + 8
        bar_max = cw - bar_x - time_w - 12

        # Log scale: map seconds to 0.0–1.0
        # Range: 0.001s (INSTANTLY) → 3.15e19s (trillion years)
        LOG_MIN = math.log10(0.001)
        LOG_MAX = math.log10(3.15e19)

        def secs_to_fill(secs):
            if secs <= 0: return 0.0
            return max(0.02, min(1.0, (math.log10(max(secs, 0.001)) - LOG_MIN) / (LOG_MAX - LOG_MIN)))

        algos = list(HASH_ALGORITHMS.items())

        for i, (algo, info) in enumerate(algos):
            y = 3 + i * row_h
            is_selected = (algo == selected_algo)

            if pw:
                secs, _, _ = estimate_crack_time(pw, hash_speed=info["speed"])
                fill = secs_to_fill(secs)
                time_str = format_time(secs)
                tier_label, tier_color, _, _ = get_strength_tier(secs)
            else:
                fill = 0.0
                time_str = "—"
                tier_label = ""
                tier_color = C["dim"]

            bar_color = info["color"]

            # Highlight selected row
            if is_selected:
                c.create_rectangle(0, y - 1, cw, y + row_h - 3,
                                   fill=C["bg3"], outline="", stipple="")

            # Algorithm name
            font_weight = "bold" if is_selected else "normal"
            c.create_text(4, y + 8, text=algo, fill=bar_color,
                          font=("Courier", 10, font_weight), anchor="w")

            # Bar background
            c.create_rectangle(bar_x, y + 2, bar_x + bar_max, y + row_h - 4,
                               fill=C["bg3"], outline=C["border"])

            # Bar fill
            if fill > 0:
                fill_w = max(4, int(fill * bar_max))
                c.create_rectangle(bar_x, y + 2, bar_x + fill_w, y + row_h - 4,
                                   fill=bar_color, outline="")

            # Crack time text
            txt_x = bar_x + bar_max + 8
            c.create_text(txt_x, y + 8, text=time_str, fill=bar_color,
                          font=("Courier", 10, font_weight), anchor="w")

            # Selected marker
            if is_selected:
                c.create_text(cw - 4, y + 8, text="◀ selected",
                              fill=C["dim"], font=("Courier", 8), anchor="e")

    # ─── Start the cracking process ──────────────────────────────────────

    def start_crack(self):
        pw = self.password_var.get()
        if not pw:
            self.status_label.config(text="Enter a password first!", fg=C["orange"])
            return
        if _contains_profanity(pw):
            self.status_label.config(
                text="⚠  Inappropriate language is not allowed. Please choose a different password.",
                fg=C["red"])
            self.verdict_label.config(text="NOT ALLOWED", fg=C["red"])
            self.time_label.config(text="", fg=C["dim"])
            self.message_label.config(
                text="This app is for everyone — please keep it clean! 😊",
                fg=C["white"])
            self.tip_label.config(
                text="Tip: A strong password doesn't need bad words. Try mixing words, numbers, and symbols!",
                fg=C["yellow"])
            self.clear_meter()
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

        # Calculate crack time using selected hash algorithm speed
        algo = self.hash_algo_var.get()
        hash_speed = HASH_ALGORITHMS[algo]["speed"]
        crack_seconds, charset_size, method = estimate_crack_time(pw, hash_speed=hash_speed)
        strength_label, strength_color, message, tip = get_strength_tier(crack_seconds)

        # Map method to human-readable attack label
        method_labels = {
            "common":             "credential stuffing (known password list)",
            "pattern":            "pattern attack (repeated chars)",
            "keyboard_walk":      "keyboard pattern attack",
            "sequential":         "sequential pattern attack",
            "leet_common":        "leet-speak variant of known password",
            "common_variant":     "dictionary + appended digits/symbols",
            "dictionary_variant": "dictionary + rule-based mutations",
            "leet_dictionary":    "leet-speak dictionary attack",
            "multi_word":         "multi-word combination attack",
            "pin":                "numeric brute-force",
            "brute_force":        "full brute-force",
        }
        attack_label = method_labels.get(method, "brute-force")

        # Decide animation duration (real-time visual, capped for fun)
        if crack_seconds < 1:
            anim_duration = max(0.5, crack_seconds * 2)
        elif crack_seconds < 3600:
            anim_duration = min(4.0, 1.5 + math.log10(max(crack_seconds, 1)))
        else:
            anim_duration = 5.0  # strong passwords get a timeout animation

        is_timeout = crack_seconds > 3600  # Will "give up" for strong passwords

        # Kick off rainbow table phase first, then crack animation
        thread = threading.Thread(
            target=self.run_rainbow_then_crack,
            args=(pw, anim_duration, crack_seconds, charset_size,
                  is_timeout, strength_label, strength_color, message, tip,
                  attack_label, method),
            daemon=True)
        thread.start()

    def run_rainbow_then_crack(self, password, anim_duration, crack_seconds,
                               charset_size, is_timeout, strength_label,
                               strength_color, message, tip, attack_label, method):
        """Phase 1: Rainbow table crawl animation. Phase 2: crack animation."""
        # ── Rainbow Table Phase (1.2s fixed) ──
        rt_duration = 1.2
        rt_start = time.time()
        pw_lower = password.lower()
        found_in_rt = method in ("common", "leet_common", "pattern",
                                  "keyboard_walk", "sequential")

        # Build a pool of fake "table entries" scrolling past
        rt_pool = list(COMMON_PASSWORDS)
        random.shuffle(rt_pool)
        rt_pool = rt_pool[:300] if len(rt_pool) > 300 else rt_pool
        rt_idx = [0]

        while time.time() - rt_start < rt_duration and not self.cancel_crack:
            elapsed = time.time() - rt_start
            progress = elapsed / rt_duration

            # Grab a window of entries to display
            visible = 8
            start_i = rt_idx[0] % max(1, len(rt_pool))
            window = [rt_pool[(start_i + i) % len(rt_pool)] for i in range(visible)]
            rt_idx[0] += 3

            # At 85%+ of time, if found, freeze on the password
            highlight_idx = -1
            if found_in_rt and progress > 0.82:
                window[visible // 2] = pw_lower
                highlight_idx = visible // 2

            status = (f"Scanning {_pw_count:,} entries... "
                      f"{int(progress * _pw_count):,} checked")
            self.root.after(0, self.update_rt_display,
                            window, highlight_idx, progress, status, found_in_rt)
            time.sleep(0.06)

        # Final RT frame
        if found_in_rt:
            final_window = [rt_pool[i % len(rt_pool)] for i in range(3)]
            final_window += [f">>> {pw_lower} <<<"]
            final_window += [rt_pool[(3 + i) % len(rt_pool)] for i in range(4)]
            self.root.after(0, self.update_rt_display,
                            final_window, 3, 1.0, f"MATCH FOUND: '{pw_lower}'", True)
        else:
            self.root.after(0, self.update_rt_display,
                            [], -1, 1.0, f"No match — escalating to dictionary attack...", False)

        time.sleep(0.3)

        # ── Phase 2: Hash animation (~1.2s) ──
        algo = self.hash_algo_var.get()
        hash_done = threading.Event()
        self.root.after(0, lambda: self.run_hash_phase(
            password, algo, hash_done.set))
        hash_done.wait(timeout=3.0)
        time.sleep(0.15)

        # ── Phase 3: Standard crack animation ──
        self.run_crack_animation(password, anim_duration, crack_seconds,
                                  charset_size, is_timeout, strength_label,
                                  strength_color, message, tip, attack_label)

    def run_hash_phase(self, password, algo, on_complete_callback):
        """Phase 2: Hash animation — runs ~2.4s, then holds result, then calls on_complete_callback."""
        anim_duration = 2.4
        start_time = time.time()
        hash_hex = _compute_hash(password, algo)
        scramble_chars = string.ascii_letters + string.digits + "!@#$%^&*"

        def _tick():
            elapsed = time.time() - start_time
            progress = min(elapsed / anim_duration, 1.0)
            cw = self.hash_anim_canvas.winfo_width()
            if cw < 10:
                cw = 880

            self.hash_anim_canvas.delete("all")

            # Layout zones
            left_w = int(cw * 0.30)
            mid_w  = int(cw * 0.22)
            right_x = left_w + mid_w + 10

            # ── Left: password chars appearing one by one ──
            pw_reveal = max(1, int(len(password) * min(progress * 2.5, 1.0)))
            pw_display = password[:pw_reveal]
            self.hash_anim_canvas.create_text(
                8, 22, text="INPUT:", fill=C["dim"],
                font=("Courier", 9), anchor="w")
            self.hash_anim_canvas.create_text(
                8, 42, text=pw_display[:28],
                fill=C["green"], font=("Courier", 13, "bold"), anchor="w")

            # ── Middle: animated HASH FN box ──
            box_x1 = left_w + 4
            box_x2 = left_w + mid_w - 4
            self.hash_anim_canvas.create_rectangle(
                box_x1, 10, box_x2, 60,
                outline=C["yellow"], fill=C["bg3"], width=2)
            scramble = "".join(random.choice(scramble_chars) for _ in range(6))
            self.hash_anim_canvas.create_text(
                (box_x1 + box_x2) // 2, 28,
                text="HASH FN", fill=C["yellow"],
                font=("Courier", 10, "bold"))
            self.hash_anim_canvas.create_text(
                (box_x1 + box_x2) // 2, 46,
                text=scramble, fill=C["yellow"],
                font=("Courier", 10))

            # Arrow
            arrow_x = box_x2 + 4
            self.hash_anim_canvas.create_text(
                arrow_x, 35, text="→", fill=C["dim"],
                font=("Courier", 12))

            # ── Right: hash output building up ──
            hash_reveal = max(4, int(len(hash_hex) * min(progress * 3, 1.0)))
            hash_display = hash_hex[:hash_reveal]
            self.hash_anim_canvas.create_text(
                right_x, 22, text=f"{algo} OUTPUT:", fill=C["dim"],
                font=("Courier", 9), anchor="w")
            self.hash_anim_canvas.create_text(
                right_x, 44, text=(hash_display[:36] + "...")[:40],
                fill=C["cyan"], font=("Courier", 11, "bold"), anchor="w")

            if progress < 1.0:
                delay = int((anim_duration - elapsed) * 1000 / 20)
                delay = max(30, min(delay, 80))
                self.root.after(delay, _tick)
            else:
                # Final frame with label
                self.hash_anim_canvas.delete("all")
                truncated = hash_hex[:48] + "..."
                self.hash_anim_canvas.create_text(
                    8, 20, text=f"{algo}: {truncated}",
                    fill=C["cyan"], font=("Courier", 10, "bold"), anchor="w")
                self.hash_anim_canvas.create_text(
                    8, 50, text="↑ This hash is what a hacker sees after a data breach",
                    fill=C["yellow"], font=("Courier", 9, "italic"), anchor="w")
                # Hold the final frame for 1.5s so it's readable before proceeding
                self.root.after(1500, on_complete_callback)

        _tick()

    def update_rt_display(self, entries, highlight_idx, progress, status, found):
        """Animate the rainbow table scrolling lookup panel."""
        self.rt_canvas.delete("all")
        cw = self.rt_canvas.winfo_width()
        if cw < 10: cw = 880

        # Background grid lines (table rows)
        row_h = 13
        cols = 4
        col_w = cw // cols

        for ci in range(cols):
            for ri, entry in enumerate(entries[ci*2:(ci+1)*2] if len(entries) > ci*2 else []):
                x = ci * col_w + 4
                y = 4 + ri * row_h
                idx = ci * 2 + ri
                if idx == highlight_idx:
                    self.rt_canvas.create_rectangle(
                        x - 2, y - 1, x + col_w - 6, y + row_h - 2,
                        fill=C["red"], outline="")
                    self.rt_canvas.create_text(
                        x + 2, y + 5, text=entry[:18], fill=C["white"],
                        font=("Courier", 9, "bold"), anchor="w")
                else:
                    col = C["purple"] if random.random() > 0.6 else C["dim"]
                    self.rt_canvas.create_text(
                        x + 2, y + 5, text=entry[:18], fill=col,
                        font=("Courier", 9), anchor="w")

        # Progress bar at bottom of RT canvas
        bar_y = 42
        bar_h = 10
        fill_w = max(2, progress * cw)
        bar_col = C["red"] if found and progress > 0.8 else C["purple"]
        self.rt_canvas.create_rectangle(0, bar_y, cw, bar_y + bar_h,
                                         fill=C["bg3"], outline="")
        self.rt_canvas.create_rectangle(0, bar_y, fill_w, bar_y + bar_h,
                                         fill=bar_col, outline="")
        self.rt_canvas.create_text(cw // 2, bar_y + 5, text=status,
                                    fill=C["white"], font=("Courier", 8, "bold"))

        self.rt_status_label.config(
            text="✓ FOUND" if (found and progress >= 1.0) else
                 "✗ NOT FOUND" if (not found and progress >= 1.0) else "scanning...",
            fg=C["red"] if (found and progress >= 1.0) else
               C["green"] if (not found and progress >= 1.0) else C["dim"])

    def run_crack_animation(self, password, anim_duration, crack_seconds,
                            charset_size, is_timeout, strength_label,
                            strength_color, message, tip, attack_label="brute-force"):
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
                status = (f"[{attack_label}] {attempts:,} combinations... "
                          f"({progress*100:.0f}% of time)")
            else:
                status = f"[{attack_label}] {attempts:,} attempts..."

            self.root.after(0, self.update_crack_display,
                            display_copy, cracked_copy, pw_len, progress,
                            status, is_timeout)

            time.sleep(0.05)  # ~20fps

        # ── FINAL RESULT ──
        if is_timeout:
            final_display = []
            for i in range(pw_len):
                if cracked[i]:
                    final_display.append(password[i])
                else:
                    final_display.append("?")
            self.root.after(0, self.show_timeout_result,
                            final_display, cracked, pw_len, crack_seconds,
                            strength_label, strength_color, message, tip,
                            attack_label)
        else:
            self.root.after(0, self.show_cracked_result,
                            list(password), pw_len, crack_seconds,
                            strength_label, strength_color, message, tip,
                            attack_label)

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
                             label, color, message, tip, attack_label="brute-force"):
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
            text=f"Cracked via {attack_label} in: {time_str}",
            fg=color)
        self.message_label.config(text=message, fg=C["white"])
        self.tip_label.config(text=f"Tip: {tip}", fg=C["yellow"])

        self.draw_strength_meter(crack_seconds, color)

    def show_timeout_result(self, display, cracked, pw_len, crack_seconds,
                             label, color, message, tip, attack_label="brute-force"):
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
            text=f"Estimated time to crack ({attack_label}): {time_str}",
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
