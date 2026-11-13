#!/usr/bin/env python3
"""ESCAPE ROOM: PROJECT OBSCURA  -  realistic edition (pygame-ce).

Install:  py -3.14 -m pip install pygame-ce
Run:      py -3.14 escape_pygame.py

Self-contained: every texture, light and sound is generated in code.
Walk (WASD / arrows), E to interact, I inventory, Esc menu.
Solve 5 riddles of rising difficulty to reveal the 5-digit exit code.
"""

import array
import math
import random
import time

import pygame

# ------------------------------------------------------------------ config
W, H = 960, 640
HUD_H = 64
FLOOR = pygame.Rect(40, 150, 880, 450)     # walkable area
FPS = 60
NLEVELS = 5
ALARM_LIMIT = 14
MAX_HINTS = 4
SPEED = 215

LEVEL_INFO = {1: ("EASY", 1), 2: ("MEDIUM", 2), 3: ("HARD", 3),
              4: ("EXPERT", 4), 5: ("MASTER", 5)}

C_BG = (10, 13, 20)
C_PANEL = (22, 30, 44)
C_EDGE = (70, 110, 150)
C_TEXT = (220, 232, 245)
C_DIM = (120, 140, 160)
C_ACCENT = (80, 220, 200)
C_WARN = (255, 90, 80)
C_GOOD = (110, 230, 130)
C_GOLD = (255, 205, 90)


def R(x, y, w, h):
    return pygame.Rect(x, y, w, h)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum() or c in " .").strip()


# ================================================================== riddles
def easy_riddles():
    return [
        ("I have keys but open no locks. I have space but no room.\n"
         "You can enter, but you can never go outside. What am I?",
         {"keyboard", "a keyboard", "computer keyboard"},
         "You are probably typing on one right now."),
        ("The more of me you take, the more you leave behind.\nWhat am I?",
         {"footsteps", "steps", "footstep", "step"}, "Think about walking."),
        ("I have hands but cannot clap. I have a face but no eyes.\n"
         "What am I?", {"clock", "a clock", "watch", "a watch"},
         "Scientists check me all day long."),
        ("What gets wetter the more it dries?", {"towel", "a towel"},
         "You use me after a shower."),
        ("I have a neck but no head, and a body but no legs.\n"
         "Scientists keep liquids in me. What am I?",
         {"bottle", "a bottle", "flask", "a flask"},
         "Think of a container for liquids."),
    ]


def medium_riddles():
    out = []
    n = random.randint(2, 4)
    seq = [k * (k + 1) for k in range(n, n + 5)]
    out.append(("The screen shows a sequence: " + ", ".join(map(str, seq)) +
                ", ?\nWhat number comes next?", {str((n + 5) * (n + 6))},
                "Each number is k times (k+1). Look at how the gaps grow."))
    word = random.choice(["laboratory", "chemistry", "formula", "quantum",
                          "reactor", "specimen", "centrifuge"])
    shift = random.randint(2, 5)
    coded = "".join(chr((ord(c) - 97 + shift) % 26 + 97) for c in word)
    out.append((f"A coded word blinks on the terminal: {coded.upper()}\n"
                f"The log says: 'each letter was pushed {shift} places "
                "FORWARD in the alphabet'.\nType the original word. "
                "(A torn page in the storage room explains ciphers.)",
                {word}, f"Move every letter {shift} places BACK "
                        "(with shift 1, C becomes B)."))
    out.append(("A three-digit lock reads: 'My tens digit is 5 more than my "
                "ones digit.\nMy hundreds digit is 3 less than my ones "
                "digit.'\nWhat number am I?", {"194"},
                "Try the ones digit = 4. Remember 9 is the biggest digit."))
    w2 = random.choice(["molecule", "scalpel", "vaccine", "beaker",
                        "pipette", "serum"])
    letters = list(w2)
    for _ in range(20):
        random.shuffle(letters)
        if "".join(letters) != w2:
            break
    out.append((f"Unscramble this laboratory word: {''.join(letters).upper()}",
                {w2}, f"It starts with {w2[0].upper()} and has {len(w2)} "
                      "letters."))
    out.append(("In a factory, 3 machines make 3 widgets in 3 minutes.\n"
                "How many minutes would 100 machines need to make 100 "
                "widgets?", {"3", "three"},
                "Each machine makes one widget every 3 minutes."))
    return out


def hard_riddles():
    out = []
    out.append(("Three boxes hide the master key. Each carries a label:\n"
                "  Box 1: 'The key is in this box.'\n"
                "  Box 2: 'The key is NOT in this box.'\n"
                "  Box 3: 'The key is NOT in box 1.'\n"
                "Exactly ONE label is true. Which box (1, 2 or 3) holds the "
                "key?", {"2", "box 2", "two"},
                "Test each position and count how many labels would be true."))
    out.append(("A 3-digit lock, with these hints scratched on the wall:\n"
                "  6 8 2 : one digit is correct and well placed\n"
                "  6 1 4 : one digit is correct but wrongly placed\n"
                "  2 0 6 : two digits are correct but wrongly placed\n"
                "  7 3 8 : nothing is correct\n"
                "  7 8 0 : one digit is correct but wrongly placed\n"
                "Enter the code.", {"042"},
                "Digits 7, 3, 8 and 1 are out. Only 0, 2 and 4 remain."))
    v = random.randint(20, 60)
    out.append((f"The panel shows a binary number: {v:b}\nConvert it to "
                "decimal, then DOUBLE it. Enter the result.", {str(v * 2)},
                "Powers of two from the right: 1, 2, 4, 8, 16, 32."))
    out.append(("I speak without a mouth and hear without ears.\n"
                "I have no body, but I come alive with the wind. What am I?",
                {"echo", "an echo", "the echo"},
                "You hear me in caves and canyons."))
    out.append(("Look-and-say sequence: 1, 11, 21, 1211, 111221, ?\n"
                "What comes next?", {"312211"},
                "Read the previous term aloud: 'one 1, one 2, two 1s'..."))
    out.append({"kind": "simon", "length": 5})
    return out


def expert_riddles():
    out = []
    out.append(("Two doors: one leads to freedom, the other to a trap. Two "
                "guards:\none ALWAYS lies, the other ALWAYS tells the truth "
                "(you don't know\nwhich is which). You ask either guard: "
                "'Which door would the OTHER\nguard say is the safe one?' He "
                "points to door A.\nWhich door (A or B) is really safe?",
                {"b", "door b"},
                "Whoever you ask, the answer is a lie about the real safe "
                "door."))
    a, b = random.randint(1, 5), random.randint(2, 6)
    seq = [a, b]
    for _ in range(6):
        seq.append(seq[-1] + seq[-2])
    out.append(("The reactor panel shows: " + ", ".join(map(str, seq[:6])) +
                ", ?, ?\nEnter the 8th number of the sequence.",
                {str(seq[7])},
                "Each number is the sum of the two numbers before it."))
    word = random.choice(["isotope", "neutron", "catalyst", "pressure",
                          "plutonium", "radiation"])
    shift = random.randint(6, 12)
    coded = "".join(chr((ord(c) - 97 + shift) % 26 + 97)
                    for c in reversed(word))
    out.append((f"A double-coded word glows on the console: {coded.upper()}\n"
                f"Step 1: each letter was pushed {shift} places FORWARD.\n"
                "Step 2: the whole word was then written BACKWARDS.\n"
                "Type the original word.", {word},
                f"First shift each letter {shift} places back, then reverse "
                "the word."))
    out.append(("A snail climbs 3 m up a 10 m wall each day, then slips back "
                "2 m\neach night. On which day does it first reach the top?",
                {"8", "day 8", "eight"},
                "On the last day it climbs out without slipping back."))
    return out


def master_riddles():
    return [
        ("Ana, Ben and Cyd are a Chemist, a Biologist and a Physicist\n"
         "(not necessarily in that order).\n"
         "  - Ana is not the Chemist.\n"
         "  - Ben is neither the Biologist nor the Chemist.\n"
         "Type the first letter of the job of Ana, then Ben, then Cyd\n"
         "(C, B or P), as three letters with no spaces.", {"bpc"},
         "Ben can only be one job. Then Ana, then Cyd."),
        ("The director's safe asks for the smallest positive number that:\n"
         "  - leaves remainder 1 when divided by 2, 3, 4, 5 AND 6,\n"
         "  - and is exactly divisible by 7.\nEnter the number.", {"301"},
         "The number is a multiple of 60, plus 1. Try 61, 121, 181..."),
        ("The director's clock reads exactly 3:15.\nWhat is the angle "
         "between the hour hand and the minute hand,\nin degrees? (use a "
         "dot for decimals)", {"7.5", "7,5"},
         "The hour hand has moved a quarter of the way from 3 to 4 "
         "(30 degrees)."),
        ("In 12 hours, how many times do the hour hand and the minute hand\n"
         "of a clock overlap?", {"11", "eleven"},
         "It is not 12! The 11:xx and 12:xx overlaps merge."),
    ]


POOLS = {1: easy_riddles, 2: medium_riddles, 3: hard_riddles,
         4: expert_riddles, 5: master_riddles}


def pick_riddle(level):
    item = random.choice(POOLS[level]())
    if isinstance(item, dict):
        return item
    q, answers, hint = item
    return {"kind": "text", "q": q, "answers": answers, "hint": hint}


# ================================================================== audio
class Audio:
    """All sounds are synthesised at start-up (no asset files)."""
    RATE = 22050

    def __init__(self):
        self.ok = False
        self.s = {}
        try:
            pygame.mixer.init(frequency=self.RATE, size=-16, channels=1,
                              buffer=512, allowedchanges=0)
            self.ok = True
        except pygame.error:
            return
        self._build()

    # --- synthesis helpers
    def _n(self, d):
        return int(self.RATE * d)

    def _tone(self, f, d, decay=5.0, vol=1.0):
        return [vol * math.sin(2 * math.pi * f * i / self.RATE) *
                math.exp(-decay * i / self.RATE) for i in range(self._n(d))]

    def _noise(self, d, decay=20.0, vol=1.0):
        return [vol * random.uniform(-1, 1) *
                math.exp(-decay * i / self.RATE) for i in range(self._n(d))]

    @staticmethod
    def _lp(data, k):
        out, y = [], 0.0
        for x in data:
            y += k * (x - y)
            out.append(y)
        return out

    def _snd(self, data, vol=1.0):
        a = array.array("h", [max(-32767, min(32767, int(x * 32767)))
                              for x in data])
        snd = pygame.mixer.Sound(buffer=a.tobytes())
        snd.set_volume(vol)
        return snd

    def _build(self):
        s = self.s
        s["step"] = self._snd(self._lp(self._noise(0.1, 28), 0.25), 0.9)
        s["step2"] = self._snd(self._lp(self._noise(0.1, 30), 0.18), 0.9)
        s["click"] = self._snd(self._noise(0.02, 160) + [0] * 700 +
                               self._noise(0.02, 160), 0.5)
        s["tick"] = self._snd(self._noise(0.015, 250), 0.25)
        s["pickup"] = self._snd(self._tone(880, 0.07, 18) +
                                self._tone(1320, 0.14, 12), 0.35)
        s["unlock"] = self._snd(self._noise(0.02, 160) + [0] * 900 +
                                self._tone(523, 0.14, 7) +
                                self._tone(784, 0.14, 7) +
                                self._tone(1046, 0.5, 5), 0.4)
        sq = [0.5 * (1 if math.sin(2 * math.pi * 110 * i / self.RATE) > 0
                     else -1) * math.exp(-3.5 * i / self.RATE)
              for i in range(self._n(0.4))]
        s["wrong"] = self._snd(sq, 0.35)
        ph, siren = 0.0, []
        for i in range(self._n(0.7)):
            f = 650 + 250 * math.sin(2 * math.pi * 1.4 * i / self.RATE)
            ph += 2 * math.pi * f / self.RATE
            siren.append(0.55 * math.sin(ph))
        s["alarm"] = self._snd(siren, 0.22)
        door = self._lp(self._noise(0.45, 5), 0.07)
        door = [d * 5 + 0.5 * math.sin(2 * math.pi * 55 * i / self.RATE) *
                math.exp(-9 * i / self.RATE) for i, d in enumerate(door)]
        s["door"] = self._snd(door, 0.7)
        hum = [0.22 * math.sin(2 * math.pi * 60 * i / self.RATE) +
               0.10 * math.sin(2 * math.pi * 120 * i / self.RATE) +
               0.05 * math.sin(2 * math.pi * 180 * i / self.RATE)
               for i in range(self.RATE * 2)]
        s["hum"] = self._snd(hum, 0.35)
        for i, f in enumerate((262, 330, 392, 523)):
            s[f"simon{i}"] = self._snd(self._tone(f, 0.4, 4), 0.4)
        win = []
        for f in (523, 659, 784, 1046, 1318):
            win += self._tone(f, 0.18, 4)
        s["win"] = self._snd(win + self._tone(1568, 0.8, 3), 0.4)
        lose = []
        for f in (440, 392, 349, 262):
            lose += self._tone(f, 0.3, 3)
        s["lose"] = self._snd(lose, 0.4)

    def play(self, name):
        if self.ok and name in self.s:
            self.s[name].play()

    def start_hum(self):
        if self.ok:
            self.s["hum"].play(loops=-1)


# ================================================================== gfx
def vgrad(rect, top, bottom, radius=0):
    """Vertical gradient surface (optionally with rounded corners)."""
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    h = max(1, rect.h)
    for y in range(rect.h):
        t = y / h
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (rect.w, y))
    if radius:
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                         border_radius=radius)
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surf


def bevel(screen, rect, base, radius=5, outline=(8, 8, 10)):
    screen.blit(vgrad(rect, shade(base, 1.25), shade(base, 0.75), radius),
                rect.topleft)
    pygame.draw.rect(screen, outline, rect, 2, border_radius=radius)
    pygame.draw.line(screen, shade(base, 1.5), (rect.x + radius, rect.y + 2),
                     (rect.right - radius, rect.y + 2))


def radial(radius, color):
    s = pygame.Surface((radius * 2, radius * 2))
    steps = max(8, radius // 2)
    for i in range(steps):
        t = i / steps
        f = t ** 1.7
        pygame.draw.circle(s, (int(color[0] * f), int(color[1] * f),
                               int(color[2] * f)), (radius, radius),
                           int(radius * (1 - t)) + 1)
    return s


def make_cone(radius=270, half_deg=30):
    s = radial(radius, (255, 244, 215))
    mask = pygame.Surface((radius * 2, radius * 2))
    c = (radius, radius)
    for deg, br in ((half_deg + 14, 50), (half_deg + 7, 120),
                    (half_deg, 255)):
        pts = [c]
        for k in range(-12, 13):
            a = math.radians(deg * k / 12)
            pts.append((radius + radius * math.cos(a),
                        radius + radius * math.sin(a)))
        pygame.draw.polygon(mask, (br, br, br), pts)
    s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return s


def speckle(surf, rect, base, count, spread, seed):
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.randint(rect.left, rect.right - 2)
        y = rnd.randint(rect.top, rect.bottom - 2)
        d = rnd.randint(-spread, spread)
        c = tuple(max(0, min(255, v + d)) for v in base)
        surf.fill(c, (x, y, rnd.randint(1, 3), rnd.randint(1, 3)))


# ================================================================== world
def make_rooms():
    rooms = {}
    names = {"storage": "STORAGE", "lab": "CHEMISTRY LAB",
             "control": "CONTROL ROOM", "server": "SERVER ROOM",
             "reactor": "REACTOR", "office": "DIRECTOR", "cell": "CELL",
             "exit": "EXIT", "corridor": "CORRIDOR"}

    def back_door():
        return [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                     label="Corridor")]

    rooms["cell"] = {
        "name": "Holding Cell", "floor": "concrete", "wall": (74, 80, 90),
        "ambient": (70, 76, 92),
        "lights": [dict(x=480, y=300, r=330, c=(150, 150, 130), fl=0.25)],
        "objects": [
            dict(id="bed", rect=R(80, 170, 200, 96), kind="bed",
                 label="Search the bed",
                 text="You search under the thin mattress...",
                 item="paperclip", item_text="a bent PAPERCLIP"),
            dict(id="desk", rect=R(640, 170, 200, 80), kind="desk",
                 label="Search the desk",
                 text="You open the drawer of the desk...",
                 item="flashlight", item_text="a small FLASHLIGHT"),
            dict(id="wall", rect=R(380, 88, 200, 56), kind="note",
                 label="Read the scratches", solid=False,
                 text="Scratched into the wall: 'FIVE RIDDLES. FIVE DIGITS. "
                      "ONE DOOR. Solve the lab's riddles; each gives a digit "
                      "of the exit code.'"),
        ],
        "doors": [dict(id="to_corridor", rect=R(420, 584, 120, 36),
                       dest="corridor", label="Cell door")],
    }
    top = [("storage", 80), ("lab", 290), ("control", 500), ("server", 710)]
    bottom = [("reactor", 120), ("office", 380), ("cell", 640)]
    doors = []
    for dest, x in top:
        doors.append(dict(id="d_" + dest, rect=R(x, 90, 140, 60), dest=dest,
                          label=names[dest], top=True))
    for dest, x in bottom:
        doors.append(dict(id="d_" + dest, rect=R(x, 584, 140, 36), dest=dest,
                          label=names[dest]))
    doors.append(dict(id="d_exit", rect=R(904, 260, 36, 140), dest="exit",
                      label="EXIT", vertical=True))
    rooms["corridor"] = {
        "name": "Central Corridor", "floor": "metal", "wall": (84, 94, 108),
        "ambient": (52, 58, 74),
        "lights": [dict(x=x, y=330, r=250, c=(170, 180, 190), fl=0.12)
                   for x in (170, 400, 640, 830)],
        "objects": [
            dict(id="map", rect=R(400, 330, 160, 70), kind="map",
                 label="Read the facility plan",
                 text="A faded plan: Storage (dark), Chemistry Lab (Level 1), "
                      "Control Room (barred, Level 2), Server Room (keycard, "
                      "Level 3), Reactor Room (access log, Level 4), "
                      "Director's Office (master key, Level 5), Exit."),
        ],
        "doors": doors,
    }
    rooms["storage"] = {
        "name": "Storage Room", "floor": "concrete", "wall": (58, 56, 52),
        "ambient": (7, 7, 11), "dark": True, "lights": [],
        "objects": [
            dict(id="shelves", rect=R(70, 168, 300, 76), kind="shelf",
                 label="Feel the shelves",
                 text="You feel around the metal shelves...",
                 item="crowbar", item_text="a heavy CROWBAR"),
            dict(id="crates", rect=R(620, 330, 220, 120), kind="crate",
                 label="Open a crate", text="You open a dusty crate...",
                 item="torn page",
                 item_text="a TORN PAGE: 'Cipher logs: every letter is "
                           "shifted by the number in the log. Undo it by "
                           "going BACKWARDS in the alphabet.'"),
            dict(id="coat", rect=R(440, 168, 90, 130), kind="coat",
                 label="Check the lab coat",
                 text="In the pocket: a sticky note - 'The hardest locks hide "
                      "deeper in the building. Use logic, not luck.'"),
        ],
        "doors": back_door(),
    }
    rooms["lab"] = {
        "name": "Chemistry Lab", "floor": "tile", "wall": (150, 170, 170),
        "ambient": (100, 112, 116),
        "lights": [dict(x=x, y=330, r=300, c=(190, 220, 215), fl=0.08)
                   for x in (260, 700)],
        "objects": [
            dict(id="flasks", rect=R(80, 170, 260, 76), kind="flask",
                 label="Examine the flasks",
                 text="Green liquid bubbles quietly. Nothing useful, but it "
                      "smells awful."),
            dict(id="cabinet", rect=R(600, 166, 240, 110), kind="cabinet",
                 label="Open the riddle cabinet", riddle=1),
        ],
        "doors": back_door(),
    }
    rooms["control"] = {
        "name": "Control Room", "floor": "carpet", "wall": (46, 52, 84),
        "ambient": (36, 42, 70),
        "lights": [dict(x=250, y=230, r=260, c=(60, 110, 200), fl=0.3),
                   dict(x=720, y=330, r=240, c=(40, 150, 140), fl=0.2),
                   dict(x=480, y=420, r=240, c=(70, 80, 110), fl=0.1)],
        "objects": [
            dict(id="monitors", rect=R(80, 168, 340, 76), kind="monitor",
                 label="Watch the monitors",
                 text="The cameras show empty corridors. A guard walks "
                      "past... You'd better not set off the alarm."),
            dict(id="terminal", rect=R(620, 280, 200, 110), kind="terminal",
                 label="Use the terminal", riddle=2),
        ],
        "doors": back_door(),
    }
    rooms["server"] = {
        "name": "Server Room", "floor": "grate", "wall": (36, 46, 48),
        "ambient": (26, 38, 40),
        "lights": [dict(x=230, y=230, r=230, c=(40, 180, 120), fl=0.4),
                   dict(x=730, y=330, r=220, c=(40, 120, 190), fl=0.3)],
        "objects": [
            dict(id="servers", rect=R(80, 168, 300, 60), kind="server",
                 label="Inspect the servers",
                 text="Thousands of blinking lights. You feel watched."),
            dict(id="servers2", rect=R(80, 300, 300, 60), kind="server",
                 label="Inspect the servers",
                 text="A fan whirs. The hum is almost hypnotic."),
            dict(id="vault", rect=R(620, 240, 200, 150), kind="vault",
                 label="Open the vault console", riddle=3),
        ],
        "doors": back_door(),
    }
    rooms["reactor"] = {
        "name": "Reactor Room", "floor": "grate", "wall": (74, 50, 46),
        "ambient": (42, 28, 28),
        "lights": [dict(x=480, y=300, r=380, c=(60, 130, 255), fl=0.0,
                        pulse=True),
                   dict(x=130, y=200, r=200, c=(255, 50, 30), fl=0.0,
                        blink=True)],
        "objects": [
            dict(id="core", rect=R(380, 200, 200, 200), kind="core",
                 label="Look at the reactor core",
                 text="The reactor glows blue. You keep your distance."),
            dict(id="console", rect=R(700, 168, 200, 90), kind="console",
                 label="Use the reactor console", riddle=4),
        ],
        "doors": back_door(),
    }
    rooms["office"] = {
        "name": "Director's Office", "floor": "wood", "wall": (92, 68, 50),
        "ambient": (66, 52, 40),
        "lights": [dict(x=240, y=320, r=260, c=(255, 190, 110), fl=0.1),
                   dict(x=730, y=260, r=200, c=(255, 200, 130), fl=0.05)],
        "objects": [
            dict(id="desk2", rect=R(120, 300, 260, 90), kind="desk",
                 label="Search the desk",
                 text="Photos of the director shaking hands with strange "
                      "visitors. Nothing useful."),
            dict(id="safe", rect=R(640, 168, 190, 150), kind="safe",
                 label="Open the director's safe", riddle=5),
        ],
        "doors": back_door(),
    }
    rooms["exit"] = {
        "name": "Exit Door", "floor": "metal", "wall": (90, 96, 104),
        "ambient": (54, 60, 70),
        "lights": [dict(x=480, y=250, r=300, c=(160, 190, 210), fl=0.1)],
        "objects": [
            dict(id="keypad", rect=R(400, 90, 160, 64), kind="keypad",
                 label="Use the keypad", keypad=True, solid=False),
        ],
        "doors": back_door(),
    }
    for k, r in rooms.items():
        r["key"] = k
        r.setdefault("dark", False)
    return rooms


ROOMS = make_rooms()


class State:
    def __init__(self):
        self.room = "cell"
        self.items = []
        self.found = set()
        self.solved = {n: False for n in range(1, NLEVELS + 1)}
        self.code = [random.randint(0, 9) for _ in range(NLEVELS)]
        self.alarm = 0
        self.hints = MAX_HINTS
        self.moves = 0
        self.cell_open = False
        self.start = time.time()
        self.riddles = {n: pick_riddle(n) for n in range(1, NLEVELS + 1)}
        self.pos = pygame.Vector2(FLOOR.centerx, FLOOR.centery + 120)


# ================================================================== game
class Game:
    SIMON_COLORS = [(230, 70, 70), (70, 190, 90), (70, 120, 235),
                    (240, 210, 70)]

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Escape Room - Project Obscura")
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.audio.start_hum()
        self.f_title = self.font(64, True)
        self.f_big = self.font(34, True)
        self.f_med = self.font(22)
        self.f_small = self.font(17)
        self.f_tiny = self.font(14)
        self.scene = "title"
        self.menu_idx = 0
        self.st = None
        self.dialog = []
        self.toast = ("", 0.0)
        self.t = 0.0
        self.shake = 0.0
        self.show_inv = False
        self.paused = False
        self.pause_idx = 0
        self.riddle_ui = None
        self.keypad_text = ""
        self.end_info = ""
        self.running = True
        self.trans = None
        self.facing = "down"
        self.angle = 90.0
        self.walk_t = 0.0
        self.step_t = 0.0
        self.moving = False
        self.alarm_t = 0.0
        self.bg_cache = {}
        self.grad_cache = {}
        self.cone = make_cone()
        self.light = pygame.Surface((W, H))
        self.vignette = self.make_vignette()
        self.glow_list = []
        rnd = random.Random(7)
        self.motes = [[rnd.uniform(FLOOR.left, FLOOR.right),
                       rnd.uniform(FLOOR.top, FLOOR.bottom),
                       rnd.uniform(-6, 6), rnd.uniform(-5, 2),
                       rnd.uniform(0, 6.28)] for _ in range(60)]

    # -------------------------------------------------- utilities
    @staticmethod
    def font(size, bold=False):
        return pygame.font.SysFont(
            "consolas,couriernew,dejavusansmono,monospace", size, bold=bold)

    def text(self, s, font, color, x, y, anchor="topleft", surf=None):
        surf = surf or self.screen
        img = font.render(s, True, color)
        r = img.get_rect(**{anchor: (x, y)})
        surf.blit(img, r)
        return r

    def wrap(self, s, font, width):
        lines = []
        for para in s.split("\n"):
            cur = ""
            for w in para.split(" "):
                test = (cur + " " + w).strip()
                if font.size(test)[0] <= width:
                    cur = test
                else:
                    lines.append(cur)
                    cur = w
            lines.append(cur)
        return lines

    def say(self, *msgs):
        self.dialog.extend(msgs)

    def flash(self, s, secs=2.2):
        self.toast = (s, self.t + secs)

    def panel(self, rect, border=C_EDGE, fill=C_PANEL, alpha=235):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill((*fill, alpha))
        self.screen.blit(s, rect.topleft)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=8)

    def make_vignette(self):
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(26):
            a = int(150 * (1 - i / 26) ** 2.2)
            pygame.draw.rect(v, (0, 0, 0, a), (i * 6, i * 5, W - i * 12,
                                               H - i * 10), 7,
                             border_radius=60)
        return v

    def light_blob(self, radius, color):
        key = (radius, color)
        if key not in self.grad_cache:
            self.grad_cache[key] = radial(radius, color)
        return self.grad_cache[key]

    # -------------------------------------------------- game rules
    def can_enter(self, dest):
        g = self.st
        if dest == "storage" and "flashlight" not in g.items:
            return False, "It is pitch black in there. You need a light source."
        if dest == "control" and "crowbar" not in g.items:
            return False, "The door is barred shut. You need something to pry it."
        if dest == "server" and "keycard" not in g.items:
            return False, "A card reader blocks the door. You need a keycard."
        if dest == "reactor" and "access log" not in g.items:
            return False, ("The reactor door wants an authorisation. Maybe "
                           "the Control Room has one.")
        if dest == "office" and "master key" not in g.items:
            return False, "The office door needs a special MASTER KEY."
        return True, ""

    def raise_alarm(self, pts, why):
        self.st.alarm += pts
        self.shake = 0.4
        self.audio.play("wrong")
        self.flash(f"ALARM +{pts}!  {why}", 2.6)
        if self.st.alarm >= ALARM_LIMIT:
            self.end_game(False)
            return True
        return False

    def end_game(self, won):
        g = self.st
        self.scene = "win" if won else "lose"
        self.audio.play("win" if won else "lose")
        self.riddle_ui = None
        self.dialog.clear()
        elapsed = int(time.time() - g.start)
        rank = ("Silent shadow" if g.alarm <= 3 else
                "Sharp escapist" if g.alarm <= 8 else "Lucky survivor")
        self.end_info = (f"Time {elapsed // 60}m {elapsed % 60:02d}s   |   "
                         f"Alarm {g.alarm}/{ALARM_LIMIT}   |   "
                         f"Hints used {MAX_HINTS - g.hints}   |   "
                         f"Rank: {rank if won else '-'}")

    def give(self, item, text):
        if item not in self.st.items:
            self.st.items.append(item)
        self.audio.play("pickup")
        self.say(f"You found {text}.")

    def start_transition(self, dest):
        self.trans = {"dest": dest, "origin": self.st.room, "t": 0.0,
                      "done": False}
        self.audio.play("door")

    def goto(self, dest, origin):
        g = self.st
        g.room = dest
        g.moves += 1
        center = pygame.Vector2(FLOOR.center)
        spawn = center
        for d in ROOMS[dest]["doors"]:
            if d["dest"] == origin:
                c = pygame.Vector2(d["rect"].center)
                v = center - c
                if v.length() > 0:
                    v.scale_to_length(80)
                spawn = c + v
                break
        g.pos = pygame.Vector2(
            max(FLOOR.left + 16, min(FLOOR.right - 16, spawn.x)),
            max(FLOOR.top + 16, min(FLOOR.bottom - 16, spawn.y)))

    def update_trans(self, dt):
        tr = self.trans
        if not tr:
            return
        tr["t"] += dt
        if tr["t"] >= 0.25 and not tr["done"]:
            tr["done"] = True
            self.goto(tr["dest"], tr["origin"])
        if tr["t"] >= 0.5:
            self.trans = None

    # -------------------------------------------------- interactions
    def interactables(self):
        room = ROOMS[self.st.room]
        return ([("obj", o, o["rect"]) for o in room["objects"]] +
                [("door", d, d["rect"]) for d in room["doors"]])

    def nearest(self):
        g = self.st
        p = R(0, 0, 30, 30)
        p.center = (int(g.pos.x), int(g.pos.y))
        best, best_d = None, 1e9
        for kind, data, rect in self.interactables():
            if rect.inflate(46, 46).colliderect(p):
                d = pygame.Vector2(rect.center).distance_to(g.pos)
                if d < best_d:
                    best, best_d = (kind, data, rect), d
        return best

    def interact(self):
        if self.trans:
            return
        hit = self.nearest()
        if not hit:
            return
        kind, data, _ = hit
        g = self.st
        self.audio.play("click")
        if kind == "door":
            dest = data["dest"]
            if g.room == "cell" and not g.cell_open:
                if "paperclip" in g.items:
                    g.cell_open = True
                    self.audio.play("unlock")
                    self.say("You pick the rusty lock with the paperclip... "
                             "CLICK! The door opens.")
                else:
                    self.say("The cell door is locked. Maybe something in "
                             "here can pick it...")
                return
            ok, msg = self.can_enter(dest)
            if not ok:
                self.say(msg)
                return
            self.start_transition(dest)
            return
        o = data
        if o.get("keypad"):
            if not all(g.solved.values()):
                self.say("The keypad is dead silent. You haven't learned the "
                         "full code yet. Solve all five riddles first!")
            else:
                self.scene = "keypad"
                self.keypad_text = ""
            return
        if "riddle" in o:
            lv = o["riddle"]
            if g.solved[lv]:
                self.say(f"Already solved. Digit {lv} of the code is "
                         f"{g.code[lv - 1]}.")
            else:
                self.open_riddle(lv)
            return
        self.say(o["text"])
        if o.get("item"):
            key = (g.room, o["id"])
            if key in g.found or o["item"] in g.items:
                self.say("(You already took what was here.)")
            else:
                g.found.add(key)
                self.give(o["item"], o["item_text"])

    # -------------------------------------------------- riddles
    def open_riddle(self, lv):
        r = self.st.riddles[lv]
        ui = {"level": lv, "r": r, "input": "", "msg": "", "msg_t": 0.0}
        if r["kind"] == "simon":
            ui.update(seq=[random.randint(0, 3) for _ in range(r["length"])],
                      phase="show", phase_t=self.t + 0.8, step=0, progress=0,
                      lit=-1, sub="off")
        self.riddle_ui = ui
        self.scene = "riddle"

    def solve(self, lv):
        g = self.st
        g.solved[lv] = True
        self.scene = "play"
        self.riddle_ui = None
        reward = {
            1: ("keycard", "a white KEYCARD (opens the Server Room)"),
            2: ("access log", "an ACCESS LOG printout (opens the Reactor "
                              "Room)"),
            3: ("master key", "the MASTER KEY (opens the Director's Office)"),
            4: ("reactor badge", "a glowing REACTOR BADGE"),
            5: ("director's seal", "the DIRECTOR'S SEAL"),
        }[lv]
        self.audio.play("unlock")
        self.say("*** CLICK! The lock opens! ***")
        self.give(*reward)
        self.say(f"A display flashes: DIGIT {lv} OF THE EXIT CODE = "
                 f"[ {g.code[lv - 1]} ]")

    def riddle_hint(self):
        g, ui = self.st, self.riddle_ui
        if g.hints <= 0:
            ui["msg"], ui["msg_t"] = "No hints left!", self.t + 2.5
            return
        g.hints -= 1
        r = ui["r"]
        if r["kind"] == "simon":
            ui.update(phase="show", step=0, sub="off", lit=-1, progress=0,
                      phase_t=self.t + 0.6)
            ui["msg"] = "Sequence replayed"
        else:
            ui["msg"] = "HINT: " + r["hint"]
        ui["msg_t"] = self.t + 6
        self.raise_alarm(1, "Using the intercom was noisy.")

    def submit_answer(self):
        ui = self.riddle_ui
        ans = norm(ui["input"])
        r, lv = ui["r"], ui["level"]
        if not ans:
            return
        if ans in {norm(a) for a in r["answers"]}:
            self.solve(lv)
        else:
            ui["input"] = ""
            ui["msg"], ui["msg_t"] = "Wrong answer!", self.t + 2.5
            self.raise_alarm(LEVEL_INFO[lv][1], "Wrong answer!")

    def simon_press(self, pad):
        ui = self.riddle_ui
        if ui["phase"] != "input":
            return
        ui["lit"], ui["lit_t"] = pad, self.t + 0.25
        self.audio.play(f"simon{pad}")
        if pad == ui["seq"][ui["progress"]]:
            ui["progress"] += 1
            if ui["progress"] == len(ui["seq"]):
                self.solve(ui["level"])
        else:
            ui.update(progress=0, phase="show", step=0, sub="off",
                      phase_t=self.t + 1.0)
            ui["msg"], ui["msg_t"] = "Wrong pad! Watch again...", self.t + 2.5
            self.raise_alarm(LEVEL_INFO[ui["level"]][1], "Wrong pad!")

    def simon_update(self):
        ui = self.riddle_ui
        if not ui or ui["r"]["kind"] != "simon":
            return
        if ui["phase"] == "input":
            if ui["lit"] >= 0 and ui.get("lit_t", 0) < self.t:
                ui["lit"] = -1
        elif self.t >= ui["phase_t"]:
            if ui["sub"] == "on":
                ui["lit"], ui["sub"] = -1, "off"
                ui["phase_t"] = self.t + 0.25
            elif ui["step"] < len(ui["seq"]):
                ui["lit"] = ui["seq"][ui["step"]]
                self.audio.play(f"simon{ui['lit']}")
                ui["step"] += 1
                ui["sub"] = "on"
                ui["phase_t"] = self.t + 0.55
            else:
                ui["phase"], ui["lit"] = "input", -1

    def simon_pads(self):
        cx, cy, s = W // 2, 340, 100
        return [R(cx - s - 8, cy - s - 8, s, s), R(cx + 8, cy - s - 8, s, s),
                R(cx - s - 8, cy + 8, s, s), R(cx + 8, cy + 8, s, s)]

    # -------------------------------------------------- update
    def update_play(self, dt):
        g = self.st
        keys = pygame.key.get_pressed()
        v = pygame.Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) -
            (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) -
            (keys[pygame.K_w] or keys[pygame.K_UP]))
        self.moving = v.length() > 0
        if self.moving:
            target = math.degrees(math.atan2(v.y, v.x))
            diff = (target - self.angle + 180) % 360 - 180
            self.angle += diff * min(1, dt * 14)
            if abs(v.x) > abs(v.y):
                self.facing = "right" if v.x > 0 else "left"
            else:
                self.facing = "down" if v.y > 0 else "up"
            v.scale_to_length(SPEED * dt)
            self.walk_t += dt * 9
            self.step_t -= dt
            if self.step_t <= 0:
                self.audio.play("step" if int(self.walk_t) % 2 else "step2")
                self.step_t = 0.36
        solids = [o["rect"].inflate(-4, -10) for o in
                  ROOMS[g.room]["objects"] if o.get("solid", True)]
        for axis in (0, 1):
            old = g.pos[axis]
            g.pos[axis] += v[axis]
            lo = (FLOOR.left if axis == 0 else FLOOR.top) + 14
            hi = (FLOOR.right if axis == 0 else FLOOR.bottom) - 14
            g.pos[axis] = max(lo, min(hi, g.pos[axis]))
            body = R(int(g.pos.x) - 12, int(g.pos.y) - 6, 24, 20)
            if any(body.colliderect(s) for s in solids):
                g.pos[axis] = old
        # alarm siren when high
        if g.alarm / ALARM_LIMIT > 0.7:
            self.alarm_t -= dt
            if self.alarm_t <= 0:
                self.audio.play("alarm")
                self.alarm_t = 4.0

    # -------------------------------------------------- static background
    def build_bg(self, key):
        room = ROOMS[key]
        bg = pygame.Surface((W, H))
        bg.fill((14, 16, 22))
        wall = room["wall"]
        # --- wall face (back wall)
        wall_r = R(0, HUD_H, W, FLOOR.top - HUD_H)
        bg.blit(vgrad(wall_r, shade(wall, 1.15), shade(wall, 0.7)),
                wall_r.topleft)
        speckle(bg, wall_r, wall, 900, 10, key)
        for x in range(0, W, 120):                     # wall panels
            pygame.draw.line(bg, shade(wall, 0.55), (x, HUD_H),
                             (x, FLOOR.top), 2)
            pygame.draw.line(bg, shade(wall, 1.3), (x + 2, HUD_H),
                             (x + 2, FLOOR.top))
        pygame.draw.rect(bg, shade(wall, 0.45),
                         (0, FLOOR.top - 14, W, 14))   # skirting
        pygame.draw.line(bg, shade(wall, 1.4), (0, FLOOR.top - 14),
                         (W, FLOOR.top - 14), 2)
        pygame.draw.line(bg, shade(wall, 0.4), (0, HUD_H + 6), (W, HUD_H + 6),
                         6)
        # pipes
        if key in ("corridor", "lab", "reactor", "server", "control"):
            for i, y in enumerate((HUD_H + 14, HUD_H + 24)):
                col = (110, 118, 128) if i == 0 else (150, 90, 60)
                pygame.draw.rect(bg, col, (0, y, W, 6))
                pygame.draw.rect(bg, shade(col, 1.5), (0, y, W, 2))
                pygame.draw.rect(bg, shade(col, 0.5), (0, y + 4, W, 2))
                for x in range(60, W, 200):
                    pygame.draw.rect(bg, shade(col, 0.6), (x, y - 2, 8, 10))
        # vents
        for x in (60, 880):
            vent = R(x, HUD_H + 44, 44, 30)
            pygame.draw.rect(bg, (28, 30, 34), vent)
            for i in range(5):
                pygame.draw.line(bg, (80, 84, 92), (vent.x + 3, vent.y + 5 + i * 5),
                                 (vent.right - 3, vent.y + 5 + i * 5), 2)
            pygame.draw.rect(bg, (120, 126, 134), vent, 2)
        if key == "corridor":
            for x in (200, 770):                      # hazard signs
                pygame.draw.polygon(bg, (240, 200, 40),
                                    [(x, 104), (x + 22, 140), (x - 22, 140)])
                pygame.draw.polygon(bg, (20, 20, 20),
                                    [(x, 104), (x + 22, 140), (x - 22, 140)], 3)
                pygame.draw.rect(bg, (20, 20, 20), (x - 2, 114, 4, 14))
                pygame.draw.circle(bg, (20, 20, 20), (x, 133), 3)
        # --- floor
        self.paint_floor(bg, room["floor"], key)
        # floor shading near back wall
        sh = pygame.Surface((FLOOR.w, 36), pygame.SRCALPHA)
        for y in range(36):
            pygame.draw.line(sh, (0, 0, 0, int(110 * (1 - y / 36) ** 1.5)),
                             (0, y), (FLOOR.w, y))
        bg.blit(sh, FLOOR.topleft)
        # side walls + bottom wall
        side = shade(wall, 0.5)
        for rect in (R(0, FLOOR.top, FLOOR.left, FLOOR.h + 40),
                     R(FLOOR.right, FLOOR.top, W - FLOOR.right, FLOOR.h + 40),
                     R(0, FLOOR.bottom, W, H - FLOOR.bottom)):
            bg.fill(side, rect)
            speckle(bg, rect, side, 250, 8, key + "s")
        pygame.draw.line(bg, shade(wall, 1.1), (FLOOR.left, FLOOR.top),
                         (FLOOR.left, FLOOR.bottom), 3)
        pygame.draw.line(bg, shade(wall, 1.1), (FLOOR.right, FLOOR.top),
                         (FLOOR.right, FLOOR.bottom), 3)
        pygame.draw.line(bg, shade(wall, 1.1), (FLOOR.left, FLOOR.bottom),
                         (FLOOR.right, FLOOR.bottom), 3)
        # extra floor details
        self.paint_floor_details(bg, key)
        return bg

    def paint_floor(self, bg, kind, key):
        f = FLOOR
        base = {"concrete": (88, 90, 94), "metal": (92, 98, 108),
                "tile": (170, 190, 192), "carpet": (52, 56, 92),
                "grate": (52, 56, 60), "wood": (118, 80, 50)}[kind]
        bg.fill(base, f)
        speckle(bg, f, base, 5000, 12, key + "f")
        if kind in ("metal", "grate"):
            step = 80 if kind == "metal" else 40
            for x in range(f.left, f.right, step):
                for y in range(f.top, f.bottom, step):
                    pygame.draw.rect(bg, shade(base, 0.82),
                                     (x, y, step, step), 2)
                    pygame.draw.line(bg, shade(base, 1.2), (x + 2, y + 2),
                                     (x + step - 3, y + 2))
                    if kind == "metal":
                        for dx, dy in ((8, 8), (step - 9, 8), (8, step - 9),
                                       (step - 9, step - 9)):
                            pygame.draw.circle(bg, shade(base, 0.6),
                                               (x + dx, y + dy), 2)
                    else:
                        pygame.draw.rect(bg, (18, 20, 22),
                                         (x + 8, y + 8, step - 16, step - 16))
                        for k in range(x + 10, x + step - 8, 6):
                            pygame.draw.line(bg, shade(base, 1.1), (k, y + 8),
                                             (k, y + step - 9))
        elif kind == "concrete":
            for x in range(f.left, f.right, 110):
                pygame.draw.line(bg, shade(base, 0.7), (x, f.top),
                                 (x, f.bottom), 2)
            for y in range(f.top, f.bottom, 110):
                pygame.draw.line(bg, shade(base, 0.7), (f.left, y),
                                 (f.right, y), 2)
            rnd = random.Random(key)
            for _ in range(8):                           # cracks
                x, y = rnd.randint(f.left, f.right), rnd.randint(f.top, f.bottom)
                for _ in range(8):
                    nx, ny = x + rnd.randint(-18, 18), y + rnd.randint(-8, 22)
                    pygame.draw.line(bg, shade(base, 0.55), (x, y), (nx, ny))
                    x, y = nx, ny
            for _ in range(10):                          # stains
                s = pygame.Surface((90, 60), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (30, 26, 20, 40), s.get_rect())
                bg.blit(s, (rnd.randint(f.left, f.right - 90),
                            rnd.randint(f.top, f.bottom - 60)))
        elif kind == "tile":
            for x in range(f.left, f.right, 55):
                for y in range(f.top, f.bottom, 55):
                    c = shade(base, 1.0 if (x // 55 + y // 55) % 2 else 0.92)
                    pygame.draw.rect(bg, c, (x, y, 55, 55))
                    pygame.draw.rect(bg, shade(base, 0.6), (x, y, 55, 55), 1)
        elif kind == "wood":
            for i, y in enumerate(range(f.top, f.bottom, 28)):
                c = shade(base, 0.9 + 0.2 * ((i * 37) % 10) / 10)
                pygame.draw.rect(bg, c, (f.left, y, f.w, 28))
                pygame.draw.line(bg, shade(base, 0.45), (f.left, y),
                                 (f.right, y), 2)
                rnd = random.Random(i)
                off = rnd.randint(0, 140)
                for x in range(f.left + off, f.right, 170):
                    pygame.draw.line(bg, shade(base, 0.45), (x, y), (x, y + 28))
        elif kind == "carpet":
            for y in range(f.top, f.bottom, 4):
                pygame.draw.line(bg, shade(base, 0.92 + 0.1 * (y % 8 == 0)),
                                 (f.left, y), (f.right, y))

    def paint_floor_details(self, bg, key):
        f = FLOOR
        if key == "corridor":
            for x in range(f.left + 40, f.right - 40, 70):   # centre line
                pygame.draw.rect(bg, (210, 180, 50), (x, 300, 38, 5))
            for x in (300, 600):                              # arrows
                pygame.draw.polygon(bg, (210, 180, 50),
                                    [(x, 440), (x + 22, 470), (x - 22, 470)])
        elif key == "office":
            rug = R(160, 280, 560, 240)
            pygame.draw.rect(bg, (96, 28, 36), rug, border_radius=6)
            pygame.draw.rect(bg, (200, 160, 90), rug.inflate(-26, -26), 3)
            pygame.draw.rect(bg, (150, 100, 60), rug.inflate(-50, -50), 2)
        elif key == "reactor":
            c = (480, 300)
            for r in (170, 140):
                pygame.draw.circle(bg, (200, 170, 30), c, r, 8)
            for a in range(0, 360, 24):
                p1 = (c[0] + 142 * math.cos(math.radians(a)),
                      c[1] + 142 * math.sin(math.radians(a)))
                pygame.draw.circle(bg, (20, 20, 20), p1, 5)
        elif key == "lab":
            pygame.draw.circle(bg, (40, 44, 48), (480, 470), 20)
            pygame.draw.circle(bg, (110, 116, 120), (480, 470), 20, 3)
            for i in range(-2, 3):
                pygame.draw.line(bg, (110, 116, 120), (466, 470 + i * 6),
                                 (494, 470 + i * 6), 2)
        elif key == "server":
            rnd = random.Random(3)
            for _ in range(6):                                # cables
                x, y = rnd.randint(f.left, 500), rnd.randint(400, f.bottom - 20)
                pts = [(x, y)]
                for _ in range(6):
                    x += rnd.randint(20, 60)
                    y += rnd.randint(-20, 20)
                    pts.append((x, y))
                pygame.draw.lines(bg, (20, 22, 26), False, pts, 5)
                pygame.draw.lines(bg, (60, 70, 90), False, pts, 2)
        elif key == "exit":
            for i in range(0, 120, 24):
                pygame.draw.polygon(bg, (210, 180, 50),
                                    [(f.right - 24 - i, f.top + 120),
                                     (f.right - 4 - i, f.top + 120),
                                     (f.right - 4 - i + 20, f.top + 180),
                                     (f.right - 24 - i + 20, f.top + 180)])
        elif key == "cell":
            pygame.draw.rect(bg, (60, 64, 70), (420, 560, 120, 28))

    def bg_for(self, key):
        if key not in self.bg_cache:
            self.bg_cache[key] = self.build_bg(key)
        return self.bg_cache[key]

    # -------------------------------------------------- object sprites
    def draw_shadow(self, rect, alpha=90):
        w, h = rect.w + 30, 26
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alpha), s.get_rect())
        self.screen.blit(s, (rect.x - 15, rect.bottom - 12))

    def draw_object(self, o):
        r, k = o["rect"], o["kind"]
        scr = self.screen
        rnd = random.Random(o["id"])
        if k == "bed":
            bevel(scr, r, (70, 74, 82), 4)
            m = r.inflate(-14, -14)
            bevel(scr, m, (150, 160, 175), 6)
            bevel(scr, R(m.x + 6, m.y + 6, 44, m.h - 12), (225, 228, 235), 8)
            blanket = R(m.x + 56, m.y, m.w - 56, m.h)
            bevel(scr, blanket, (82, 96, 70), 4)
            for i in range(1, 4):
                pygame.draw.line(scr, (60, 72, 52),
                                 (blanket.x + 8, blanket.y + i * 20),
                                 (blanket.right - 8, blanket.y + i * 20), 2)
        elif k == "desk":
            bevel(scr, r, (130, 92, 58), 4)
            for i in range(1, 6):
                y = r.y + i * r.h // 6
                pygame.draw.line(scr, (96, 66, 40), (r.x + 4, y),
                                 (r.right - 4, y))
            pygame.draw.rect(scr, (230, 230, 220), (r.x + 14, r.y + 14, 46, 32))
            pygame.draw.rect(scr, (210, 210, 200), (r.x + 20, r.y + 18, 46, 32))
            for i in range(3):
                pygame.draw.line(scr, (110, 110, 120),
                                 (r.x + 26, r.y + 24 + i * 8),
                                 (r.x + 60, r.y + 24 + i * 8))
            pygame.draw.circle(scr, (40, 44, 50), (r.right - 30, r.y + 26), 14)
            pygame.draw.circle(scr, (90, 96, 104), (r.right - 30, r.y + 26), 14, 3)
            pygame.draw.line(scr, (40, 44, 50), (r.right - 30, r.y + 26),
                             (r.right - 50, r.y + 44), 4)
        elif k == "note":
            for _ in range(46):
                x = rnd.randint(r.x + 6, r.right - 20)
                y = rnd.randint(r.y + 6, r.bottom - 14)
                pygame.draw.line(scr, (190, 194, 200), (x, y),
                                 (x + rnd.randint(-10, 14), y + rnd.randint(8, 22)))
            for i in range(4):
                pygame.draw.line(scr, (190, 194, 200), (r.x + 20 + i * 6, r.y + 8),
                                 (r.x + 20 + i * 6, r.y + 34), 2)
            pygame.draw.line(scr, (190, 194, 200), (r.x + 16, r.y + 30),
                             (r.x + 48, r.y + 36), 2)
        elif k == "map":
            self.draw_shadow(r, 70)
            bevel(scr, r, (110, 80, 50), 3)
            inner = r.inflate(-12, -12)
            scr.fill((210, 200, 160), inner)
            for i in range(0, inner.w, 16):
                pygame.draw.line(scr, (180, 170, 130), (inner.x + i, inner.y),
                                 (inner.x + i, inner.bottom))
            for i in range(0, inner.h, 16):
                pygame.draw.line(scr, (180, 170, 130), (inner.x, inner.y + i),
                                 (inner.right, inner.y + i))
            for (a, b, w, h) in ((8, 8, 30, 20), (50, 8, 30, 20), (92, 8, 30, 20),
                                 (8, 34, 114, 10)):
                pygame.draw.rect(scr, (90, 70, 50), (inner.x + a, inner.y + b, w, h), 2)
            pygame.draw.circle(scr, (200, 40, 40), (inner.x + 100, inner.y + 20), 4)
        elif k == "shelf":
            self.draw_shadow(r)
            bevel(scr, r, (84, 90, 98), 3)
            for i in range(1, 3):
                y = r.y + i * r.h // 3
                pygame.draw.rect(scr, (128, 134, 142), (r.x, y - 2, r.w, 5))
            for sy in (r.y, r.y + r.h // 3, r.y + 2 * r.h // 3):
                x = r.x + 8
                while x < r.right - 24:
                    w, h = rnd.randint(16, 34), rnd.randint(14, 22)
                    col = rnd.choice([(150, 110, 60), (90, 110, 130),
                                      (120, 60, 60), (70, 100, 70)])
                    bevel(scr, R(x, sy + r.h // 3 - h - 4, w, h), col, 2)
                    x += w + rnd.randint(4, 14)
        elif k == "crate":
            self.draw_shadow(r)
            bevel(scr, r, (150, 108, 62), 3)
            for i in range(1, 5):
                pygame.draw.line(scr, (88, 60, 34), (r.x + i * r.w // 5, r.y),
                                 (r.x + i * r.w // 5, r.bottom), 2)
            pygame.draw.line(scr, (88, 60, 34), r.topleft, r.bottomright, 5)
            pygame.draw.line(scr, (88, 60, 34), r.topright, r.bottomleft, 5)
            for p in (r.topleft, r.topright, r.bottomleft, r.bottomright):
                pygame.draw.circle(scr, (60, 60, 64),
                                   (p[0] + (6 if p[0] == r.x else -6),
                                    p[1] + (6 if p[1] == r.y else -6)), 2)
        elif k == "coat":
            pygame.draw.circle(scr, (60, 60, 64), (r.centerx, r.y + 6), 5)
            coat = [(r.centerx - 8, r.y + 12), (r.centerx + 8, r.y + 12),
                    (r.right - 4, r.y + 40), (r.right - 10, r.bottom - 4),
                    (r.x + 10, r.bottom - 4), (r.x + 4, r.y + 40)]
            pygame.draw.polygon(scr, (205, 208, 214), coat)
            pygame.draw.polygon(scr, (70, 70, 80), coat, 2)
            pygame.draw.line(scr, (150, 154, 162), (r.centerx, r.y + 14),
                             (r.centerx, r.bottom - 6), 2)
            pygame.draw.rect(scr, (170, 174, 182), (r.x + 18, r.y + 64, 22, 18), 2)
        elif k == "flask":
            self.draw_shadow(r)
            bevel(scr, r, (160, 170, 172), 3)
            pygame.draw.rect(scr, (60, 70, 74), (r.x, r.y + 10, r.w, 6))
            for i in range(4):
                x = r.x + 26 + i * 58
                pygame.draw.polygon(scr, (220, 235, 240),
                                    [(x + 8, r.y - 4), (x + 22, r.y - 4),
                                     (x + 30, r.y + 40), (x, r.y + 40)], 2)
        elif k == "cabinet":
            self.draw_shadow(r)
            bevel(scr, r, (120, 128, 138), 3)
            pygame.draw.line(scr, (30, 32, 36), (r.centerx, r.y + 4),
                             (r.centerx, r.bottom - 4), 3)
            for hx in (r.centerx - 12, r.centerx + 8):
                pygame.draw.rect(scr, (200, 204, 210), (hx, r.y + 36, 5, 36), border_radius=2)
            pygame.draw.rect(scr, (30, 34, 40), (r.right - 52, r.y + 16, 34, 28), border_radius=3)
        elif k in ("monitor", "terminal", "console"):
            self.draw_shadow(r)
            bevel(scr, r, (52, 56, 66), 4)
            n = 3 if k == "monitor" else 1
            for i in range(n):
                sw = (r.w - 24) // n
                bez = R(r.x + 10 + i * (sw + 2), r.y + 8, sw - 4, r.h - 36)
                bevel(scr, bez, (20, 22, 26), 3)
            kb = R(r.x + 14, r.bottom - 24, r.w - 28, 14)
            pygame.draw.rect(scr, (30, 32, 36), kb, border_radius=3)
            for x in range(kb.x + 4, kb.right - 4, 8):
                pygame.draw.rect(scr, (110, 114, 120), (x, kb.y + 3, 5, 3))
                pygame.draw.rect(scr, (110, 114, 120), (x, kb.y + 8, 5, 3))
        elif k == "server":
            self.draw_shadow(r)
            bevel(scr, r, (34, 38, 44), 3)
            for x in range(r.x + 4, r.right - 6, r.w // 4):
                pygame.draw.line(scr, (80, 86, 94), (x, r.y + 4), (x, r.bottom - 6))
            for y in range(r.y + 10, r.bottom - 8, 12):
                pygame.draw.line(scr, (14, 16, 18), (r.x + 4, y), (r.right - 4, y), 2)
        elif k == "vault":
            self.draw_shadow(r)
            bevel(scr, r, (118, 122, 132), 6)
            inner = r.inflate(-24, -24)
            bevel(scr, inner, (96, 100, 110), 6)
            pygame.draw.circle(scr, (60, 64, 70), inner.center, 40)
            pygame.draw.circle(scr, (180, 184, 192), inner.center, 40, 5)
            for a in range(0, 360, 60):
                ex = inner.centerx + 56 * math.cos(math.radians(a + 30))
                ey = inner.centery + 56 * math.sin(math.radians(a + 30))
                pygame.draw.line(scr, (180, 184, 192), inner.center, (ex, ey), 4)
                pygame.draw.circle(scr, (210, 214, 220), (int(ex), int(ey)), 5)
            for p in (r.topleft, r.topright, r.bottomleft, r.bottomright):
                pygame.draw.circle(scr, (60, 62, 66),
                                   (p[0] + (10 if p[0] == r.x else -10),
                                    p[1] + (10 if p[1] == r.y else -10)), 4)
        elif k == "core":
            c = r.center
            self.draw_shadow(R(r.x + 20, r.y + 20, r.w - 40, r.h - 40), 120)
            pygame.draw.circle(scr, (30, 32, 36), c, 100)
            pygame.draw.circle(scr, (110, 114, 124), c, 100, 6)
            pygame.draw.circle(scr, (16, 24, 40), c, 78)
            pygame.draw.circle(scr, (180, 200, 230), c, 80, 3)
            for a in range(0, 360, 45):
                x = c[0] + 90 * math.cos(math.radians(a))
                y = c[1] + 90 * math.sin(math.radians(a))
                pygame.draw.circle(scr, (60, 64, 70), (int(x), int(y)), 6)
        elif k == "safe":
            self.draw_shadow(r)
            bevel(scr, r, (92, 96, 106), 5)
            inner = r.inflate(-20, -20)
            bevel(scr, inner, (112, 116, 126), 4)
            pygame.draw.circle(scr, (30, 32, 36), (inner.centerx, inner.centery - 8), 30)
            pygame.draw.circle(scr, (200, 170, 70), (inner.centerx, inner.centery - 8), 30, 4)
            for a in range(0, 360, 30):
                pygame.draw.line(scr, (200, 170, 70),
                                 (inner.centerx + 22 * math.cos(math.radians(a)),
                                  inner.centery - 8 + 22 * math.sin(math.radians(a))),
                                 (inner.centerx + 28 * math.cos(math.radians(a)),
                                  inner.centery - 8 + 28 * math.sin(math.radians(a))), 2)
            pygame.draw.rect(scr, (200, 170, 70), (inner.right - 14, inner.centery - 6, 6, 36),
                             border_radius=3)
        elif k == "keypad":
            bevel(scr, r, (40, 44, 52), 5)
            for i in range(12):
                b = R(r.x + 76 + (i % 3) * 22, r.y + 8 + (i // 3) * 13, 18, 10)
                pygame.draw.rect(scr, (150, 156, 166), b, border_radius=2)
            pygame.draw.rect(scr, (8, 22, 14), (r.x + 10, r.y + 10, 56, 40))

    def draw_glow(self, o):
        """Emissive parts, drawn after lighting so they stay bright."""
        r, k = o["rect"], o["kind"]
        scr, t = self.screen, self.t
        rnd = random.Random(o["id"])
        if k in ("monitor", "terminal", "console"):
            n = 3 if k == "monitor" else 1
            for i in range(n):
                sw = (r.w - 24) // n
                bez = R(r.x + 10 + i * (sw + 2), r.y + 8, sw - 4, r.h - 36)
                inner = bez.inflate(-6, -6)
                col = [(60, 200, 130), (70, 150, 230), (230, 160, 60)][i % 3]
                scr.fill(shade(col, 0.25), inner)
                if k == "monitor":                        # camera noise
                    for _ in range(14):
                        x = inner.x + rnd.randint(0, inner.w - 6)
                        y = inner.y + (rnd.randint(0, inner.h) + int(t * 20)) % inner.h
                        scr.fill(shade(col, 0.6), (x, y, rnd.randint(3, 14), 2))
                else:
                    for j in range(0, inner.h - 6, 8):
                        wd = 10 + (hash((j, int(t * 2 + j))) % (inner.w - 24))
                        scr.fill(col, (inner.x + 4, inner.y + 3 + j, wd, 2))
                scan = inner.y + int((t * 40 + i * 20) % inner.h)
                scr.fill(shade(col, 0.5), (inner.x, scan, inner.w, 2))
                pygame.draw.rect(scr, shade(col, 0.7), inner, 1)
        elif k == "server":
            for yy in range(r.y + 10, r.bottom - 8, 12):
                for xx in range(r.x + 10, r.right - 12, 14):
                    ph = (int(t * 3) + xx // 7 + yy // 3) % 7
                    c = ((60, 255, 110) if ph else (255, 70, 60)) if ph != 3 else (30, 40, 30)
                    scr.fill(c, (xx, yy - 3, 4, 3))
        elif k == "cabinet":
            solved = self.st.solved[o["riddle"]]
            c = C_GOOD if solved else (255, 70, 60)
            pygame.draw.circle(scr, c, (r.right - 36, r.y + 22), 4)
            scr.fill((30, 120, 70), (r.right - 50, r.y + 30, 28, 8))
        elif k == "flask":
            for i in range(4):
                x = r.x + 26 + i * 58
                pygame.draw.polygon(scr, (60, 230, 150),
                                    [(x + 4, r.y + 20), (x + 26, r.y + 20),
                                     (x + 30 - 2, r.y + 38), (x + 2, r.y + 38)])
                for b in range(3):
                    by = r.y + 26 - ((t * 20 + b * 9 + i * 5) % 28)
                    pygame.draw.circle(scr, (190, 255, 220),
                                       (int(x + 10 + b * 5), int(by + 14)), 2)
        elif k == "core":
            c = r.center
            p = (math.sin(t * 2.2) + 1) / 2
            for rad, col in ((74, (30, 90, 200)), (56, (60, 150, 255)),
                             (36, (150, 210, 255)), (18, (240, 250, 255))):
                pygame.draw.circle(scr, shade(col, 0.8 + 0.3 * p), c, int(rad + 3 * p))
            for i in range(3):
                a = t * (1.2 + i * .5) + i * 2.1
                pygame.draw.circle(scr, (200, 235, 255),
                                   (int(c[0] + 62 * math.cos(a)),
                                    int(c[1] + 62 * math.sin(a))), 4)
        elif k == "vault":
            solved = self.st.solved[o["riddle"]]
            pygame.draw.circle(scr, C_GOOD if solved else (255, 70, 60),
                               (r.right - 22, r.y + 22), 5)
        elif k == "safe":
            solved = self.st.solved[o["riddle"]]
            pygame.draw.circle(scr, C_GOOD if solved else (255, 70, 60),
                               (r.x + 24, r.y + 22), 5)
        elif k == "keypad":
            ok = all(self.st.solved.values())
            scr.fill((50, 255, 130) if ok else (255, 60, 50),
                     (r.x + 14, r.y + 18, 48, 8))
        if o.get("riddle") and not self.st.solved[o["riddle"]]:
            p = (math.sin(t * 4) + 1) / 2
            pygame.draw.circle(scr, C_GOLD, (r.centerx, r.y - 14), int(5 + 3 * p))

    # -------------------------------------------------- doors
    def draw_door(self, d):
        g, scr = self.st, self.screen
        r = d["rect"]
        ok, _ = self.can_enter(d["dest"])
        if g.room == "cell" and not g.cell_open:
            ok = False
        exit_door = d["dest"] == "exit"
        if exit_door:
            ok = all(g.solved.values())
        if d.get("top"):
            frame = r.inflate(10, 4)
            bevel(scr, frame, (60, 66, 78), 3)
            leaf = r.inflate(-10, -4)
            bevel(scr, leaf, (100, 112, 120) if ok else (96, 84, 86), 3)
            pygame.draw.rect(scr, (24, 30, 36), (leaf.x + 14, leaf.y + 8, leaf.w - 28, 16))
            pygame.draw.line(scr, (90, 110, 130), (leaf.x + 20, leaf.y + 10),
                             (leaf.x + 60, leaf.y + 22), 2)
            pygame.draw.rect(scr, (200, 204, 210), (leaf.right - 22, leaf.y + 30, 6, 20),
                             border_radius=3)
            pygame.draw.line(scr, (60, 66, 74), (leaf.centerx, leaf.y + 26),
                             (leaf.centerx, leaf.bottom - 2), 2)
            plate = R(r.centerx - 56, HUD_H + 8, 112, 18) if False else None
        elif d.get("vertical"):
            bevel(scr, r.inflate(8, 8), (60, 66, 78), 3)
            bevel(scr, r, (130, 120, 70) if ok else (110, 98, 60), 3)
            for i in range(0, r.h, 24):
                pygame.draw.polygon(scr, (210, 180, 50),
                                    [(r.x, r.y + i), (r.right, r.y + i + 10),
                                     (r.right, r.y + i + 22), (r.x, r.y + i + 12)])
            pygame.draw.circle(scr, (60, 62, 66), r.center, 10)
            pygame.draw.circle(scr, (200, 204, 210), r.center, 10, 3)
        else:
            frame = r.inflate(8, 0)
            bevel(scr, frame, (60, 66, 78), 3)
            pygame.draw.rect(scr, (18, 20, 26), r.inflate(-12, -10))
            for x in range(r.x + 8, r.right - 8, 16):
                pygame.draw.polygon(scr, (200, 170, 40),
                                    [(x, r.bottom - 12), (x + 8, r.bottom - 12),
                                     (x + 4, r.bottom - 4), (x - 4, r.bottom - 4)])
        # label plate
        lab = d["label"]
        font = self.f_tiny
        if d.get("top"):
            pos = (r.centerx, HUD_H + 18)
        elif d.get("vertical"):
            pos = (r.left - 34, r.centery)
        else:
            pos = (r.centerx, r.y - 14)
        tw = font.size(lab)[0] + 14
        pl = R(0, 0, tw, 18)
        pl.center = pos
        bevel(scr, pl, (48, 54, 64), 3)
        self.text(lab, font, (200, 215, 230), pl.centerx, pl.centery, "center")
        self.glow_list.append(("door", d, ok))

    # -------------------------------------------------- player
    def draw_player(self):
        p = self.st.pos
        x, y = int(p.x), int(p.y)
        scr = self.screen
        sh = pygame.Surface((36, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 110), sh.get_rect())
        scr.blit(sh, (x - 18, y + 14))
        swing = math.sin(self.walk_t) * 6 if self.moving else 0
        bob = abs(math.sin(self.walk_t)) * 2 if self.moving else 0
        side = self.facing in ("left", "right")
        # legs
        if side:
            for s in (-1, 1):
                dx = swing * s
                pygame.draw.rect(scr, (44, 48, 64), (x - 4 + dx, y + 4, 8, 16),
                                 border_radius=3)
                pygame.draw.rect(scr, (20, 20, 24), (x - 5 + dx, y + 17, 10, 5),
                                 border_radius=2)
        else:
            for s in (-1, 1):
                dy = swing * s * 0.7
                pygame.draw.rect(scr, (44, 48, 64), (x - 9 + (s + 1) * 5, y + 4 + dy, 8, 15),
                                 border_radius=3)
                pygame.draw.rect(scr, (20, 20, 24), (x - 10 + (s + 1) * 5, y + 17 + dy, 10, 5),
                                 border_radius=2)
        by = y - 12 - bob
        # arms (behind torso for side view)
        if side:
            pygame.draw.rect(scr, (220, 120, 40), (x - 4 - swing, by + 6, 8, 16),
                             border_radius=4)
        torso = R(x - 13, by + 2, 26, 22)
        bevel(scr, torso, (240, 140, 50), 7, (60, 30, 10))
        pygame.draw.line(scr, (180, 90, 30), (x, by + 4), (x, by + 22), 2)
        if not side:
            for s in (-1, 1):
                pygame.draw.rect(scr, (230, 130, 45),
                                 (x + s * 17 - 4, by + 6 + swing * s * -0.5, 8, 16),
                                 border_radius=4)
                pygame.draw.circle(scr, (230, 190, 160),
                                   (x + s * 17, int(by + 22 + swing * s * -0.5)), 4)
        # head
        hy = by - 4
        pygame.draw.circle(scr, (232, 190, 158), (x, hy), 10)
        hair = (40, 28, 22)
        if self.facing == "up":
            pygame.draw.circle(scr, hair, (x, hy), 10)
        elif self.facing == "down":
            pygame.draw.arc(scr, hair, (x - 10, hy - 10, 20, 20), 0.2, 2.95, 6)
            pygame.draw.circle(scr, (30, 30, 36), (x - 4, hy + 1), 1)
            pygame.draw.circle(scr, (30, 30, 36), (x + 4, hy + 1), 1)
        else:
            sx = 1 if self.facing == "right" else -1
            pygame.draw.circle(scr, hair, (x - sx * 3, hy - 1), 9)
            pygame.draw.circle(scr, (232, 190, 158), (x + sx * 3, hy + 1), 7)
            pygame.draw.circle(scr, (30, 30, 36), (x + sx * 5, hy), 1)

    # -------------------------------------------------- lighting
    def room_lights(self):
        g = self.st
        room = ROOMS[g.room]
        out = []
        for L in room["lights"]:
            m = 1.0
            if L.get("fl"):
                m -= L["fl"] * (0.5 + 0.5 * math.sin(self.t * 23 + L["x"])) * \
                     (1 if math.sin(self.t * 3.1 + L["x"]) > 0.6 else 0.2)
            if L.get("pulse"):
                m = 0.75 + 0.25 * math.sin(self.t * 2.2)
            if L.get("blink"):
                m = 1.0 if int(self.t * 2) % 2 == 0 else 0.15
            out.append((L["x"], L["y"], L["r"], shade(L["c"], max(0.05, m))))
        return out

    def apply_lighting(self):
        g = self.st
        room = ROOMS[g.room]
        light = self.light
        amb = room["ambient"]
        # tension: slight red tint as alarm rises
        k = g.alarm / ALARM_LIMIT
        amb = (min(255, int(amb[0] * (1 + 0.5 * k))), int(amb[1] * (1 - 0.25 * k)),
               int(amb[2] * (1 - 0.25 * k)))
        light.fill(amb)
        for x, y, rad, col in self.room_lights():
            col = tuple(int(c) // 12 * 12 for c in col)
            blob = self.light_blob(rad, col)
            light.blit(blob, (x - rad, y - rad), special_flags=pygame.BLEND_RGB_ADD)
        p = g.pos
        small = self.light_blob(86, (70, 66, 60))
        light.blit(small, (p.x - 86, p.y - 86), special_flags=pygame.BLEND_RGB_ADD)
        if "flashlight" in g.items:
            cone = pygame.transform.rotate(self.cone, -self.angle)
            cr = cone.get_rect(center=(int(p.x), int(p.y)))
            light.blit(cone, cr, special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(light, (0, HUD_H), area=R(0, HUD_H, W, H - HUD_H),
                         special_flags=pygame.BLEND_RGB_MULT)

    def draw_glows(self):
        scr = self.screen
        room = ROOMS[self.st.room]
        for o in room["objects"]:
            if room["dark"] and not self.lit_by_flash(o["rect"]):
                continue
            self.draw_glow(o)
        for kind, d, ok in self.glow_list:
            r = d["rect"]
            if room["dark"] and not self.lit_by_flash(r):
                continue
            c = (60, 255, 120) if ok else (255, 60, 50)
            if d["dest"] == "exit":
                c = (60, 255, 120) if ok else (255, 150, 40)
            pos = (r.right + 10, r.centery) if kind == "door" and d.get("top") \
                else (r.x - 8, r.centery) if d.get("vertical") else (r.right + 12, r.centery)
            pygame.draw.circle(scr, shade(c, 0.35), pos, 8)
            pygame.draw.circle(scr, c, pos, 4)
        # dust motes drifting in the light
        for m in self.motes:
            m[0] += m[2] * 0.016
            m[1] += m[3] * 0.016
            m[4] += 0.02
            if not FLOOR.collidepoint(m[0], m[1]):
                m[0] = random.uniform(FLOOR.left, FLOOR.right)
                m[1] = random.uniform(FLOOR.top, FLOOR.bottom)
            a = int(40 + 30 * math.sin(m[4]))
            s = pygame.Surface((3, 3), pygame.SRCALPHA)
            s.fill((255, 245, 220, a))
            scr.blit(s, (int(m[0]), int(m[1])))

    def lit_by_flash(self, rect):
        if "flashlight" not in self.st.items:
            return False
        return pygame.Vector2(rect.center).distance_to(self.st.pos) < 230

    # -------------------------------------------------- world render
    def draw_world(self):
        g = self.st
        room = ROOMS[g.room]
        self.screen.blit(self.bg_for(g.room), (0, 0))
        self.glow_list = []
        for d in room["doors"]:
            self.draw_door(d)
        items = [(o["rect"].bottom, "obj", o) for o in room["objects"]]
        items.append((g.pos.y + 20, "player", None))
        for _, kind, o in sorted(items, key=lambda i: i[0]):
            if kind == "obj":
                self.draw_object(o)
            else:
                self.draw_player()
        self.apply_lighting()
        self.draw_glows()
        self.screen.blit(self.vignette, (0, 0))
        near = self.nearest()
        if near and not self.dialog and not self.trans:
            kind, data, rect = near
            label = (f"Go to {data['label']}" if kind == "door"
                     else data["label"])
            tw = self.f_small.size(label + "   [E]")[0] + 24
            box = R(0, 0, tw, 32)
            box.midbottom = (rect.centerx, rect.top - (34 if kind == "door" else 8))
            if box.top < HUD_H + 4 or rect.top < FLOOR.top:
                box.midtop = (rect.centerx, rect.bottom + 8)
            box.x = max(10, min(W - box.w - 10, box.x))
            self.panel(box, C_ACCENT)
            self.text(label + "   [E]", self.f_small, C_TEXT, box.centerx,
                      box.centery, "center")
        self.draw_hud()
        frac = g.alarm / ALARM_LIMIT
        if frac > 0.6:
            a = int(70 * (frac - .6) / .4 * (0.6 + 0.4 * math.sin(self.t * 8)))
            v = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.rect(v, (255, 0, 0, max(0, a)), (0, 0, W, H), 28)
            self.screen.blit(v, (0, 0))
        if g.room == "cell" and not self.dialog and g.moves == 0:
            self.text("WASD / arrows: move   E: interact   I: inventory   "
                      "Esc: menu", self.f_small, C_DIM, W // 2, H - 10,
                      "midbottom")

    def draw_hud(self):
        g = self.st
        pygame.draw.rect(self.screen, (8, 12, 18), (0, 0, W, HUD_H))
        pygame.draw.line(self.screen, C_EDGE, (0, HUD_H), (W, HUD_H), 2)
        self.text(ROOMS[g.room]["name"].upper(), self.f_med, C_ACCENT, 16, 10)
        bar = R(16, 38, 260, 14)
        pygame.draw.rect(self.screen, (40, 20, 24), bar, border_radius=6)
        frac = min(1, g.alarm / ALARM_LIMIT)
        col = C_GOOD if frac < .4 else C_GOLD if frac < .7 else C_WARN
        if frac > 0:
            pygame.draw.rect(self.screen, col,
                             R(bar.x, bar.y, int(bar.w * frac), bar.h),
                             border_radius=6)
        pygame.draw.rect(self.screen, C_EDGE, bar, 1, border_radius=6)
        self.text(f"ALARM {g.alarm}/{ALARM_LIMIT}", self.f_tiny, C_TEXT,
                  bar.right + 10, 38)
        self.text("CODE", self.f_tiny, C_DIM, 470, 8)
        for i in range(NLEVELS):
            r = R(470 + i * 44, 26, 38, 30)
            pygame.draw.rect(self.screen, (10, 24, 30), r, border_radius=5)
            pygame.draw.rect(self.screen, C_ACCENT if g.solved[i + 1]
                             else C_EDGE, r, 2, border_radius=5)
            self.text(str(g.code[i]) if g.solved[i + 1] else "?",
                      self.f_med, C_GOLD if g.solved[i + 1] else C_DIM,
                      r.centerx, r.centery, "center")
        self.text(f"Hints: {g.hints}", self.f_small, C_TEXT, 720, 10)
        self.text(f"Items: {len(g.items)}  [I]", self.f_small, C_TEXT, 720, 36)
        self.text("[Esc] menu", self.f_tiny, C_DIM, 860, 40)

    def draw_dialog(self):
        if not self.dialog:
            return
        box = R(60, H - 170, W - 120, 130)
        self.panel(box, C_ACCENT)
        for i, ln in enumerate(self.wrap(self.dialog[0], self.f_med,
                                         box.w - 40)[:4]):
            self.text(ln, self.f_med, C_TEXT, box.x + 20, box.y + 16 + i * 26)
        more = f"  (+{len(self.dialog) - 1} more)" if len(self.dialog) > 1 else ""
        self.text("[E / Enter] continue" + more, self.f_tiny, C_DIM,
                  box.right - 16, box.bottom - 10, "bottomright")

    def draw_toast(self):
        s, until = self.toast
        if s and self.t < until:
            r = R(0, 0, self.f_med.size(s)[0] + 30, 38)
            r.midtop = (W // 2, HUD_H + 10)
            self.panel(r, C_WARN, (50, 16, 20))
            self.text(s, self.f_med, C_TEXT, r.centerx, r.centery, "center")

    def draw_inventory(self):
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.screen.blit(veil, (0, 0))
        box = R(180, 120, 600, 400)
        self.panel(box, C_ACCENT)
        self.text("INVENTORY", self.f_big, C_ACCENT, box.centerx, box.y + 20,
                  "midtop")
        if not self.st.items:
            self.text("Your pockets are empty.", self.f_med, C_DIM,
                      box.centerx, box.centery, "center")
        for i, it in enumerate(self.st.items):
            y = box.y + 80 + i * 36
            pygame.draw.rect(self.screen, C_GOLD, R(box.x + 30, y + 4, 18, 18),
                             border_radius=4)
            self.text(it.upper(), self.f_med, C_TEXT, box.x + 62, y)
        self.text("[I / Esc] close", self.f_tiny, C_DIM, box.centerx,
                  box.bottom - 12, "midbottom")

    # -------------------------------------------------- menus & scenes
    def menu(self, items, idx, y0, step=56):
        mouse = pygame.mouse.get_pos()
        rects = []
        for i, label in enumerate(items):
            r = R(0, 0, 380, 46)
            r.center = (W // 2, y0 + i * step)
            rects.append(r)
            if r.collidepoint(mouse) and pygame.mouse.get_focused() \
                    and mouse != getattr(self, "_last_mouse", None):
                idx = i
            sel = (i == idx)
            self.panel(r, C_ACCENT if sel else C_EDGE,
                       (30, 70, 80) if sel else C_PANEL)
            self.text(("> " if sel else "") + label, self.f_med,
                      C_TEXT if sel else C_DIM, r.centerx, r.centery, "center")
        self._last_mouse = mouse
        return idx, rects

    def draw_title(self):
        self.screen.blit(self.bg_for("corridor"), (0, 0))
        tint = pygame.Surface((W, H), pygame.SRCALPHA)
        tint.fill((6, 10, 18, 205))
        self.screen.blit(tint, (0, 0))
        # sweeping searchlight
        a = math.sin(self.t * 0.6) * 0.9
        beam = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(beam, (255, 240, 200, 26),
                            [(W // 2, 0), (W // 2 + 520 * math.tan(a - .15), H),
                             (W // 2 + 520 * math.tan(a + .15), H)])
        self.screen.blit(beam, (0, 0))
        glow = 150 + int(100 * (0.5 + 0.5 * math.sin(self.t * 2.5)))
        flick = 1 if math.sin(self.t * 31) > -0.9 else 0.5
        self.text("ESCAPE ROOM", self.f_title, shade((glow, 255, 230), flick),
                  W // 2, 120, "center")
        self.text("P R O J E C T   O B S C U R A", self.f_big, C_WARN,
                  W // 2, 190, "center")
        self.text("You wake up in a secret laboratory. The door is locked.",
                  self.f_small, C_DIM, W // 2, 240, "center")
        self.text("Five riddles stand between you and freedom...",
                  self.f_small, C_DIM, W // 2, 264, "center")
        self.menu_idx, self.menu_rects = self.menu(
            ["Start a new game", "How to play", "Quit"], self.menu_idx, 350)
        self.screen.blit(self.vignette, (0, 0))

    def draw_how(self):
        self.screen.fill(C_BG)
        self.text("HOW TO PLAY", self.f_big, C_ACCENT, W // 2, 50, "midtop")
        lines = [
            "MOVE: WASD or arrow keys.   INTERACT: E (or Space).",
            "INVENTORY: I.   MENU: Esc.",
            "",
            "Explore the laboratory, search objects and collect items.",
            "Your flashlight reveals dark rooms, a crowbar opens barred",
            "doors, keycards and keys open the deeper rooms.",
            "",
            "Five riddles (EASY, MEDIUM, HARD, EXPERT, MASTER) each reveal",
            "one digit of the exit code. Enter the code at the Exit door.",
            "",
            "Wrong answers raise the ALARM (+1 to +5 depending on level).",
            f"At {ALARM_LIMIT} the guards catch you. You have {MAX_HINTS} hints; "
            "each costs 1 alarm.",
            "In a riddle: type the answer + Enter, Tab for a hint, Esc to leave.",
        ]
        for i, ln in enumerate(lines):
            self.text(ln, self.f_small, C_TEXT, W // 2, 130 + i * 30, "midtop")
        self.text("[Enter / Esc] back", self.f_small, C_DIM, W // 2, H - 40,
                  "midbottom")

    def draw_pause(self):
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        self.screen.blit(veil, (0, 0))
        self.text("PAUSED", self.f_big, C_ACCENT, W // 2, 150, "center")
        self.pause_idx, self.pause_rects = self.menu(
            ["Resume", "Main menu", "Quit game"], self.pause_idx, 260)

    def draw_riddle(self):
        ui = self.riddle_ui
        lv = ui["level"]
        name, pen = LEVEL_INFO[lv]
        self.screen.blit(self.bg_for(self.st.room), (0, 0))
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((4, 8, 14, 215))
        self.screen.blit(veil, (0, 0))
        self.draw_hud()
        box = R(70, 90, W - 140, H - 130)
        self.panel(box, C_ACCENT)
        self.text(f"RIDDLE {lv}/{NLEVELS}  -  {name}", self.f_big, C_GOLD,
                  box.x + 24, box.y + 16)
        self.text(f"wrong answer = +{pen} alarm", self.f_small, C_WARN,
                  box.right - 24, box.y + 26, "topright")
        r = ui["r"]
        if r["kind"] == "simon":
            self.draw_simon(box)
            return
        y = box.y + 80
        for ln in self.wrap(r["q"], self.f_med, box.w - 60):
            self.text(ln, self.f_med, C_TEXT, box.x + 30, y)
            y += 30
        ibox = R(box.x + 30, box.bottom - 150, box.w - 60, 50)
        self.panel(ibox, C_ACCENT, (10, 18, 28))
        cursor = "_" if int(self.t * 2) % 2 == 0 else " "
        self.text("> " + ui["input"] + cursor, self.f_med, C_TEXT,
                  ibox.x + 14, ibox.centery, "midleft")
        self.text("[Enter] answer     [Tab] hint (" + str(self.st.hints) +
                  " left)     [Esc] walk away", self.f_small, C_DIM,
                  box.centerx, box.bottom - 80, "center")
        if ui["msg"] and self.t < ui["msg_t"]:
            for i, ln in enumerate(self.wrap(ui["msg"], self.f_small,
                                             box.w - 60)):
                self.text(ln, self.f_small,
                          C_WARN if "Wrong" in ui["msg"] else C_GOOD,
                          box.centerx, box.bottom - 50 + i * 20, "center")

    def draw_simon(self, box):
        ui = self.riddle_ui
        self.text("The vault console lights up. Memorise the light sequence,",
                  self.f_med, C_TEXT, box.centerx, box.y + 90, "center")
        self.text("then repeat it: click the pads or press 1 2 3 4.",
                  self.f_med, C_TEXT, box.centerx, box.y + 120, "center")
        for i, pad in enumerate(self.simon_pads()):
            col = self.SIMON_COLORS[i]
            lit = ui["lit"] == i
            if lit:
                g = pygame.Surface((pad.w + 60, pad.h + 60), pygame.SRCALPHA)
                pygame.draw.rect(g, (*col, 70), g.get_rect(), border_radius=30)
                self.screen.blit(g, (pad.x - 30, pad.y - 30))
            fill = col if lit else tuple(c // 4 for c in col)
            pygame.draw.rect(self.screen, fill, pad, border_radius=14)
            pygame.draw.rect(self.screen, C_TEXT if lit else C_EDGE, pad, 3,
                             border_radius=14)
            self.text(str(i + 1), self.f_big, C_TEXT, pad.centerx, pad.centery,
                      "center")
        status = ("Watch..." if ui["phase"] == "show" else
                  f"Your turn: {ui['progress']}/{len(ui['seq'])}")
        self.text(status, self.f_med, C_GOLD, box.centerx, box.bottom - 110,
                  "center")
        self.text(f"[Tab] replay sequence (costs a hint, {self.st.hints} left)"
                  "     [Esc] walk away", self.f_small, C_DIM, box.centerx,
                  box.bottom - 70, "center")
        if ui["msg"] and self.t < ui["msg_t"]:
            self.text(ui["msg"], self.f_small, C_WARN, box.centerx,
                      box.bottom - 40, "center")

    def draw_keypad(self):
        self.screen.blit(self.bg_for("exit"), (0, 0))
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((4, 8, 14, 215))
        self.screen.blit(veil, (0, 0))
        self.draw_hud()
        box = R(250, 110, 460, 460)
        self.panel(box, C_GOLD)
        self.text("EXIT KEYPAD", self.f_big, C_GOLD, box.centerx, box.y + 20,
                  "midtop")
        disp = R(box.x + 40, box.y + 80, box.w - 80, 60)
        self.panel(disp, C_ACCENT, (6, 20, 14))
        shown = self.keypad_text.ljust(NLEVELS, "_")
        self.text(" ".join(shown), self.f_big, C_GOOD, disp.centerx,
                  disp.centery, "center")
        self.keypad_rects = []
        labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "DEL", "0", "OK"]
        for i, lab in enumerate(labels):
            r = R(box.x + 60 + (i % 3) * 120, box.y + 170 + (i // 3) * 64,
                  100, 52)
            self.keypad_rects.append((lab, r))
            hover = r.collidepoint(pygame.mouse.get_pos())
            self.panel(r, C_ACCENT if hover else C_EDGE,
                       (30, 70, 80) if hover else C_PANEL)
            self.text(lab, self.f_med, C_TEXT, r.centerx, r.centery, "center")
        self.text("Type digits or click. [Enter] confirm  [Esc] leave",
                  self.f_tiny, C_DIM, box.centerx, box.bottom - 10, "midbottom")

    def draw_end(self):
        won = self.scene == "win"
        self.screen.fill((10, 28, 20) if won else (34, 10, 12))
        for i in range(40):
            x = (i * 97 + int(self.t * (30 + i))) % W
            y = (i * 53 + int(self.t * (20 + i * 2))) % H
            pygame.draw.circle(self.screen, C_GOLD if won else C_WARN,
                               (x, y), 3)
        self.text("YOU ESCAPED!" if won else "GAME OVER", self.f_title,
                  C_GOOD if won else C_WARN, W // 2, 200, "center")
        msg = ("The steel door grinds open. Fresh air! Daylight! You sprint "
               "outside as the alarms wail far behind you..." if won else
               "The alarm blares through the building. Guards burst in and "
               "drag you back to your cell.")
        for i, ln in enumerate(self.wrap(msg, self.f_med, 700)):
            self.text(ln, self.f_med, C_TEXT, W // 2, 290 + i * 30, "center")
        self.text(self.end_info, self.f_small, C_GOLD, W // 2, 400, "center")
        self.text("[Enter] main menu", self.f_med, C_DIM, W // 2, 520, "center")

    # -------------------------------------------------- events
    def start_new(self):
        self.st = State()
        self.dialog = []
        self.scene = "play"
        self.show_inv = False
        self.paused = False
        self.trans = None
        self.angle, self.facing = 90.0, "down"
        self.say("It is dark. Your head aches. A metal door slams somewhere.",
                 "You are locked in a SECRET LABORATORY. Solve five riddles "
                 "to find the exit code and ESCAPE!")

    def on_keydown(self, ev):
        k = ev.key
        confirm = (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE)
        if self.scene == "title":
            if k in (pygame.K_UP, pygame.K_w):
                self.menu_idx = (self.menu_idx - 1) % 3
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.menu_idx = (self.menu_idx + 1) % 3
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                self.title_choose(self.menu_idx)
        elif self.scene == "how":
            if k in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self.scene = "title"
        elif self.scene in ("win", "lose"):
            if k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.scene = "title"
        elif self.scene == "play":
            if self.paused:
                if k in (pygame.K_UP, pygame.K_w):
                    self.pause_idx = (self.pause_idx - 1) % 3
                elif k in (pygame.K_DOWN, pygame.K_s):
                    self.pause_idx = (self.pause_idx + 1) % 3
                elif k in (pygame.K_RETURN, pygame.K_SPACE):
                    self.pause_choose(self.pause_idx)
                elif k == pygame.K_ESCAPE:
                    self.paused = False
            elif self.dialog:
                if k in confirm:
                    self.dialog.pop(0)
            elif self.show_inv:
                if k in (pygame.K_i, pygame.K_ESCAPE):
                    self.show_inv = False
            else:
                if k in confirm:
                    self.interact()
                elif k == pygame.K_i:
                    self.show_inv = True
                elif k == pygame.K_ESCAPE:
                    self.paused = True
        elif self.scene == "riddle":
            self.riddle_key(ev)
        elif self.scene == "keypad":
            self.keypad_key(ev)

    def riddle_key(self, ev):
        ui = self.riddle_ui
        k = ev.key
        if self.dialog:
            if k in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                self.dialog.pop(0)
            return
        if k == pygame.K_ESCAPE:
            self.scene, self.riddle_ui = "play", None
        elif k == pygame.K_TAB:
            self.riddle_hint()
        elif ui["r"]["kind"] == "simon":
            if pygame.K_1 <= k <= pygame.K_4:
                self.simon_press(k - pygame.K_1)
        else:
            if k == pygame.K_RETURN:
                self.submit_answer()
            elif k == pygame.K_BACKSPACE:
                ui["input"] = ui["input"][:-1]
            elif ev.unicode and ev.unicode.isprintable() and len(ui["input"]) < 40:
                ui["input"] += ev.unicode
                self.audio.play("tick")

    def keypad_press(self, lab):
        self.audio.play("tick")
        if lab == "DEL":
            self.keypad_text = self.keypad_text[:-1]
        elif lab == "OK":
            self.keypad_submit()
        elif lab.isdigit() and len(self.keypad_text) < NLEVELS:
            self.keypad_text += lab

    def keypad_key(self, ev):
        k = ev.key
        if self.dialog:
            if k in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                self.dialog.pop(0)
            return
        if k == pygame.K_ESCAPE:
            self.scene = "play"
        elif k == pygame.K_RETURN:
            self.keypad_submit()
        elif k == pygame.K_BACKSPACE:
            self.keypad_press("DEL")
        elif ev.unicode and ev.unicode.isdigit():
            self.keypad_press(ev.unicode)

    def keypad_submit(self):
        if self.keypad_text == "".join(map(str, self.st.code)):
            self.end_game(True)
        else:
            self.keypad_text = ""
            self.raise_alarm(2, "ACCESS DENIED!")

    def on_click(self, pos):
        if self.scene == "title":
            for i, r in enumerate(getattr(self, "menu_rects", [])):
                if r.collidepoint(pos):
                    self.title_choose(i)
        elif self.scene == "play" and self.paused:
            for i, r in enumerate(getattr(self, "pause_rects", [])):
                if r.collidepoint(pos):
                    self.pause_choose(i)
        elif self.scene == "play" and self.dialog:
            self.dialog.pop(0)
        elif self.scene == "riddle" and self.riddle_ui["r"]["kind"] == "simon":
            for i, r in enumerate(self.simon_pads()):
                if r.collidepoint(pos):
                    self.simon_press(i)
        elif self.scene == "keypad":
            for lab, r in getattr(self, "keypad_rects", []):
                if r.collidepoint(pos):
                    self.keypad_press(lab)

    def title_choose(self, i):
        if i == 0:
            self.start_new()
        elif i == 1:
            self.scene = "how"
        else:
            self.running = False

    def pause_choose(self, i):
        if i == 0:
            self.paused = False
        elif i == 1:
            self.paused = False
            self.scene = "title"
        else:
            self.running = False

    # -------------------------------------------------- main loop
    def run(self):
        while self.running:
            dt = min(0.05, self.clock.tick(FPS) / 1000)
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.KEYDOWN:
                    if not self.trans:
                        self.on_keydown(ev)
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.on_click(ev.pos)
            self.update_trans(dt)
            if (self.scene == "play" and not self.dialog and not self.paused
                    and not self.show_inv and not self.trans):
                self.update_play(dt)
            else:
                self.moving = False
            self.simon_update()
            self.render()
        pygame.quit()

    def render(self):
        s = self.scene
        if s == "title":
            self.draw_title()
        elif s == "how":
            self.draw_how()
        elif s == "play":
            self.draw_world()
            if self.show_inv:
                self.draw_inventory()
            self.draw_dialog()
            self.draw_toast()
            if self.paused:
                self.draw_pause()
        elif s == "riddle":
            self.draw_riddle()
            self.draw_toast()
            self.draw_dialog()
        elif s == "keypad":
            self.draw_keypad()
            self.draw_toast()
            self.draw_dialog()
        else:
            self.draw_end()
        if self.trans:
            t = self.trans["t"]
            a = int(255 * (t / 0.25 if t < 0.25 else max(0, (0.5 - t) / 0.25)))
            veil = pygame.Surface((W, H))
            veil.set_alpha(max(0, min(255, a)))
            self.screen.blit(veil, (0, 0))
        if self.shake > 0:
            self.shake -= 1 / FPS
            off = (random.randint(-5, 5), random.randint(-5, 5))
            frame = self.screen.copy()
            self.screen.fill((0, 0, 0))
            self.screen.blit(frame, off)
        pygame.display.flip()


def main():
    Game().run()


if __name__ == "__main__":
    main()
