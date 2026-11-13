#!/usr/bin/env python3
"""ESCAPE ROOM: PROJECT OBSCURA  -  graphical edition (pygame-ce).

Install:  py -3.14 -m pip install pygame-ce
Run:      py -3.14 escape_pygame.py

Walk around a secret laboratory (WASD / arrows), press E to interact,
collect items and solve 5 riddles of rising difficulty to reveal the
5-digit exit code.  The riddle pools are shared with the terminal edition
(main.py) and extended here with new riddles and a Simon-style light puzzle.
"""

import math
import random
import sys
import time

import pygame

import main as term     # riddle pools from the terminal version

# ------------------------------------------------------------------ config
W, H = 960, 640
HUD_H = 64
FLOOR = pygame.Rect(40, 100, 880, 500)     # walkable area
FPS = 60
NLEVELS = 5
ALARM_LIMIT = 14
MAX_HINTS = 4
SPEED = 230

LEVEL_INFO = {
    1: ("EASY", 1), 2: ("MEDIUM", 2), 3: ("HARD", 3),
    4: ("EXPERT", 4), 5: ("MASTER", 5),
}

C_BG = (12, 16, 24)
C_PANEL = (22, 30, 44)
C_EDGE = (70, 110, 150)
C_TEXT = (220, 232, 245)
C_DIM = (120, 140, 160)
C_ACCENT = (80, 220, 200)
C_WARN = (255, 90, 80)
C_GOOD = (110, 230, 130)
C_GOLD = (255, 205, 90)


# ------------------------------------------------------------------ riddles
def extra_riddles():
    """New riddles added in the graphical edition, by level."""
    extra = {i: [] for i in range(1, NLEVELS + 1)}
    extra[1] += [
        ("What gets wetter the more it dries?",
         {"towel", "a towel"}, "You use me after a shower."),
        ("I have a neck but no head, and a body but no legs.\n"
         "Scientists keep liquids in me. What am I?",
         {"bottle", "a bottle", "flask", "a flask"},
         "Think of a container for liquids."),
    ]
    word = random.choice(["molecule", "scalpel", "vaccine", "beaker",
                          "pipette", "serum"])
    letters = list(word)
    for _ in range(20):
        random.shuffle(letters)
        if "".join(letters) != word:
            break
    extra[2] += [
        (f"Unscramble this laboratory word: {''.join(letters).upper()}",
         {word}, f"It starts with the letter {word[0].upper()} and has "
                 f"{len(word)} letters."),
        ("In a factory, 3 machines make 3 widgets in 3 minutes.\n"
         "How many minutes would 100 machines need to make 100 widgets?",
         {"3", "three"}, "Each machine makes one widget every 3 minutes."),
    ]
    extra[3] += [
        ("Look-and-say sequence: 1, 11, 21, 1211, 111221, ?\n"
         "What comes next?",
         {"312211"}, "Read the previous term aloud: 'one 1, one 2, two 1s'..."),
        {"kind": "simon", "length": 5},
    ]
    extra[4] += [
        ("A snail climbs 3 m up a 10 m wall each day, then slips back 2 m\n"
         "each night. On which day does it first reach the top?",
         {"8", "day 8", "eight"},
         "On the last day it climbs out without slipping back."),
    ]
    extra[5] += [
        ("In 12 hours, how many times do the hour hand and the minute hand\n"
         "of a clock overlap?",
         {"11", "eleven"}, "It is not 12! The 11:xx and 12:xx overlaps merge."),
    ]
    return extra


def build_pool(level):
    pool = []
    base = {1: term.easy_riddles, 2: term.medium_riddles, 3: term.hard_riddles,
            4: term.expert_riddles, 5: term.master_riddles}[level]()
    for item in base + extra_riddles()[level]:
        if isinstance(item, dict):
            pool.append(item)
        else:
            q, answers, hint = item
            pool.append({"kind": "text", "q": q, "answers": answers,
                         "hint": hint})
    return pool


# ------------------------------------------------------------------ world
def R(x, y, w, h):
    return pygame.Rect(x, y, w, h)


def make_rooms():
    rooms = {}
    rooms["cell"] = {
        "name": "Holding Cell", "floor": (46, 52, 62), "dark": False,
        "objects": [
            dict(id="bed", rect=R(80, 140, 200, 90), kind="bed",
                 label="Search the bed",
                 text="You search under the thin mattress...",
                 item="paperclip", item_text="a bent PAPERCLIP"),
            dict(id="desk", rect=R(640, 130, 200, 80), kind="desk",
                 label="Search the desk",
                 text="You open the drawer of the desk...",
                 item="flashlight", item_text="a small FLASHLIGHT"),
            dict(id="wall", rect=R(380, 104, 200, 40), kind="note",
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
    names = {"storage": "Storage", "lab": "Chemistry Lab",
             "control": "Control Room", "server": "Server Room",
             "reactor": "Reactor Room", "office": "Director's Office",
             "cell": "Holding Cell", "exit": "EXIT"}
    doors = []
    for dest, x in top:
        doors.append(dict(id="d_" + dest, rect=R(x, 84, 140, 36), dest=dest,
                          label=names[dest]))
    for dest, x in bottom:
        doors.append(dict(id="d_" + dest, rect=R(x, 584, 140, 36), dest=dest,
                          label=names[dest]))
    doors.append(dict(id="d_exit", rect=R(904, 260, 36, 140), dest="exit",
                      label="EXIT", vertical=True))
    rooms["corridor"] = {
        "name": "Central Corridor", "floor": (52, 60, 74), "dark": False,
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
        "name": "Storage Room", "floor": (40, 40, 44), "dark": True,
        "objects": [
            dict(id="shelves", rect=R(70, 140, 300, 70), kind="shelf",
                 label="Feel the shelves",
                 text="You feel around the metal shelves...",
                 item="crowbar", item_text="a heavy CROWBAR"),
            dict(id="crates", rect=R(620, 330, 220, 120), kind="crate",
                 label="Open a crate",
                 text="You open a dusty crate...",
                 item="torn page",
                 item_text="a TORN PAGE: 'Cipher logs: every letter is "
                           "shifted by the number in the log. Undo it by "
                           "going BACKWARDS in the alphabet.'"),
            dict(id="coat", rect=R(440, 140, 90, 130), kind="coat",
                 label="Check the lab coat",
                 text="In the pocket: a sticky note - 'The hardest locks hide "
                      "deeper in the building. Use logic, not luck.'"),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    rooms["lab"] = {
        "name": "Chemistry Lab", "floor": (36, 58, 58), "dark": False,
        "objects": [
            dict(id="flasks", rect=R(80, 140, 260, 70), kind="flask",
                 label="Examine the flasks",
                 text="Green liquid bubbles quietly. Nothing useful, but it "
                      "smells awful."),
            dict(id="cabinet", rect=R(600, 130, 240, 110), kind="cabinet",
                 label="Open the riddle cabinet", riddle=1),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    rooms["control"] = {
        "name": "Control Room", "floor": (40, 44, 70), "dark": False,
        "objects": [
            dict(id="monitors", rect=R(80, 130, 340, 70), kind="monitor",
                 label="Watch the monitors",
                 text="The cameras show empty corridors. A guard walks "
                      "past... You'd better not set off the alarm."),
            dict(id="terminal", rect=R(620, 280, 200, 110), kind="terminal",
                 label="Use the terminal", riddle=2),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    rooms["server"] = {
        "name": "Server Room", "floor": (30, 40, 40), "dark": False,
        "objects": [
            dict(id="servers", rect=R(80, 130, 300, 60), kind="server",
                 label="Inspect the servers",
                 text="Thousands of blinking lights. You feel watched."),
            dict(id="servers2", rect=R(80, 290, 300, 60), kind="server",
                 label="Inspect the servers",
                 text="A fan whirs. The hum is almost hypnotic."),
            dict(id="vault", rect=R(620, 240, 200, 150), kind="vault",
                 label="Open the vault console", riddle=3),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    rooms["reactor"] = {
        "name": "Reactor Room", "floor": (58, 40, 40), "dark": False,
        "objects": [
            dict(id="core", rect=R(380, 200, 200, 200), kind="core",
                 label="Look at the reactor core",
                 text="The reactor glows blue. You keep your distance."),
            dict(id="console", rect=R(700, 130, 200, 90), kind="console",
                 label="Use the reactor console", riddle=4),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    rooms["office"] = {
        "name": "Director's Office", "floor": (66, 50, 38), "dark": False,
        "objects": [
            dict(id="desk2", rect=R(120, 300, 260, 90), kind="desk",
                 label="Search the desk",
                 text="Photos of the director shaking hands with strange "
                      "visitors. Nothing useful."),
            dict(id="safe", rect=R(640, 140, 190, 150), kind="safe",
                 label="Open the director's safe", riddle=5),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    rooms["exit"] = {
        "name": "Exit Door", "floor": (50, 54, 60), "dark": False,
        "objects": [
            dict(id="keypad", rect=R(400, 130, 160, 110), kind="keypad",
                 label="Use the keypad", keypad=True),
        ],
        "doors": [dict(id="back", rect=R(420, 584, 120, 36), dest="corridor",
                       label="Corridor")],
    }
    return rooms


ROOMS = make_rooms()


# ------------------------------------------------------------------ state
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
        self.riddles = {n: random.choice(build_pool(n))
                        for n in range(1, NLEVELS + 1)}
        self.pos = pygame.Vector2(FLOOR.centerx, FLOOR.centery + 120)


# ------------------------------------------------------------------ game
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Escape Room - Project Obscura")
        self.clock = pygame.time.Clock()
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

    # -------------------------------------------------- utilities
    @staticmethod
    def font(size, bold=False):
        return pygame.font.SysFont("consolas,couriernew,dejavusansmono,monospace",
                                   size, bold=bold)

    def text(self, s, font, color, x, y, anchor="topleft", surf=None):
        surf = surf or self.screen
        img = font.render(s, True, color)
        r = img.get_rect(**{anchor: (x, y)})
        surf.blit(img, r)
        return r

    def wrap(self, s, font, width):
        lines = []
        for para in s.split("\n"):
            words, cur = para.split(" "), ""
            for w in words:
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
        self.flash(f"ALARM +{pts}!  {why}", 2.6)
        if self.st.alarm >= ALARM_LIMIT:
            self.end_game(False)
            return True
        return False

    def end_game(self, won):
        g = self.st
        self.scene = "win" if won else "lose"
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
        self.say(f"You found {text}.")

    def goto(self, dest, origin):
        g = self.st
        g.room = dest
        g.moves += 1
        room = ROOMS[dest]
        center = pygame.Vector2(FLOOR.center)
        spawn = center
        for d in room["doors"]:
            if d["dest"] == origin:
                c = pygame.Vector2(d["rect"].center)
                v = center - c
                if v.length() > 0:
                    v.scale_to_length(70)
                spawn = c + v
                break
        g.pos = pygame.Vector2(
            max(FLOOR.left + 16, min(FLOOR.right - 16, spawn.x)),
            max(FLOOR.top + 16, min(FLOOR.bottom - 16, spawn.y)))

    # -------------------------------------------------- interactions
    def interactables(self):
        room = ROOMS[self.st.room]
        out = []
        for o in room["objects"]:
            out.append(("obj", o, o["rect"]))
        for d in room["doors"]:
            out.append(("door", d, d["rect"]))
        return out

    def nearest(self):
        g = self.st
        p = pygame.Rect(0, 0, 30, 30)
        p.center = (int(g.pos.x), int(g.pos.y))
        best, best_d = None, 1e9
        for kind, data, rect in self.interactables():
            zone = rect.inflate(46, 46)
            if zone.colliderect(p):
                d = pygame.Vector2(rect.center).distance_to(g.pos)
                if d < best_d:
                    best, best_d = (kind, data, rect), d
        return best

    def interact(self):
        hit = self.nearest()
        if not hit:
            return
        kind, data, _ = hit
        g = self.st
        if kind == "door":
            dest = data["dest"]
            if g.room == "cell" and not g.cell_open:
                if "paperclip" in g.items:
                    g.cell_open = True
                    self.say("You pick the rusty lock with the paperclip... "
                             "CLICK! The door opens.")
                    return
                self.say("The cell door is locked. Maybe something in here "
                         "can pick it...")
                return
            ok, msg = self.can_enter(dest)
            if not ok:
                self.say(msg)
                return
            self.goto(dest, g.room)
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
            ui["seq"] = [random.randint(0, 3) for _ in range(r["length"])]
            ui["phase"] = "show"
            ui["phase_t"] = self.t + 0.8
            ui["step"] = 0
            ui["progress"] = 0
            ui["lit"] = -1
            ui["sub"] = "off"
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
            ui["phase"], ui["step"], ui["sub"], ui["lit"] = "show", 0, "off", -1
            ui["phase_t"] = self.t + 0.6
            ui["progress"] = 0
            ui["msg"] = "Sequence replayed (-1 hint)"
        else:
            ui["msg"] = "HINT: " + r["hint"]
        ui["msg_t"] = self.t + 6
        self.raise_alarm(1, "Using the intercom was noisy.")

    def submit_answer(self):
        ui = self.riddle_ui
        ans = term.norm(ui["input"])
        r, lv = ui["r"], ui["level"]
        if not ans:
            return
        if ans in {term.norm(a) for a in r["answers"]}:
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
        if pad == ui["seq"][ui["progress"]]:
            ui["progress"] += 1
            if ui["progress"] == len(ui["seq"]):
                self.solve(ui["level"])
        else:
            ui["progress"] = 0
            ui["phase"], ui["step"], ui["sub"] = "show", 0, "off"
            ui["phase_t"] = self.t + 1.0
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
                ui["step"] += 1
                ui["sub"] = "on"
                ui["phase_t"] = self.t + 0.55
            else:
                ui["phase"], ui["lit"] = "input", -1

    SIMON_COLORS = [(230, 70, 70), (70, 190, 90), (70, 120, 235),
                    (240, 210, 70)]

    def simon_pads(self):
        cx, cy = W // 2, 340
        s = 100
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
        if v.length() > 0:
            v.scale_to_length(SPEED * dt)
        room = ROOMS[g.room]
        solids = [o["rect"] for o in room["objects"]
                  if o.get("solid", True)]
        for axis in (0, 1):
            old = g.pos[axis]
            g.pos[axis] += v[axis]
            g.pos[axis] = max(FLOOR.left + 14 if axis == 0 else FLOOR.top + 14,
                              min((FLOOR.right if axis == 0 else FLOOR.bottom)
                                  - 14, g.pos[axis]))
            body = R(int(g.pos.x) - 13, int(g.pos.y) - 13, 26, 26)
            if any(body.colliderect(s) for s in solids):
                g.pos[axis] = old

    # -------------------------------------------------- drawing
    def draw_hud(self):
        g = self.st
        pygame.draw.rect(self.screen, (8, 12, 18), (0, 0, W, HUD_H))
        pygame.draw.line(self.screen, C_EDGE, (0, HUD_H), (W, HUD_H), 2)
        self.text(ROOMS[g.room]["name"].upper(), self.f_med, C_ACCENT, 16, 10)
        # alarm bar
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
        # code digits
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

    def draw_object(self, o):
        r, k = o["rect"], o["kind"]
        done = (self.st.room, o["id"]) in self.st.found
        pal = {
            "bed": (90, 110, 140), "desk": (120, 90, 60), "note": (190, 180, 120),
            "map": (170, 160, 110), "shelf": (100, 80, 60), "crate": (150, 110, 60),
            "coat": (200, 200, 210), "flask": (60, 170, 120), "cabinet": (110, 120, 130),
            "monitor": (30, 50, 70), "terminal": (30, 70, 80), "server": (40, 44, 52),
            "vault": (130, 130, 140), "core": (30, 80, 140), "console": (80, 60, 90),
            "safe": (110, 110, 120), "keypad": (60, 64, 70),
        }[k]
        pygame.draw.rect(self.screen, pal, r, border_radius=6)
        pygame.draw.rect(self.screen, (0, 0, 0), r, 2, border_radius=6)
        pulse = (math.sin(self.t * 4) + 1) / 2
        if k == "bed":
            pygame.draw.rect(self.screen, (220, 220, 230),
                             R(r.x + 8, r.y + 8, 50, r.h - 16), border_radius=8)
        elif k in ("monitor", "terminal", "console"):
            scr = r.inflate(-20, -24)
            pygame.draw.rect(self.screen, (10, 30, 20), scr)
            for i in range(3):
                pygame.draw.line(self.screen, (80, 255, 140),
                                 (scr.x + 6, scr.y + 8 + i * 12),
                                 (scr.x + 6 + (30 + 25 * i) % scr.w - 10,
                                  scr.y + 8 + i * 12), 2)
        elif k == "server":
            for i in range(10):
                c = (80, 255, 120) if (int(self.t * 3) + i) % 3 else (255, 90, 80)
                pygame.draw.circle(self.screen, c, (r.x + 16 + i * 28,
                                                    r.centery), 4)
        elif k == "core":
            pygame.draw.circle(self.screen, (80, 180, 255), r.center,
                               int(40 + 12 * pulse))
            pygame.draw.circle(self.screen, (200, 240, 255), r.center, 24)
        elif k in ("vault", "safe"):
            pygame.draw.circle(self.screen, (200, 200, 210), r.center, 34, 4)
            pygame.draw.line(self.screen, (200, 200, 210),
                             r.center, (r.centerx + 20, r.centery - 20), 4)
        elif k == "flask":
            for i in range(4):
                x = r.x + 30 + i * 60
                pygame.draw.rect(self.screen, (120, 255, 190),
                                 R(x, r.y + 28, 24, 30), border_radius=4)
                pygame.draw.rect(self.screen, (220, 230, 240),
                                 R(x + 6, r.y + 10, 12, 20))
        elif k == "keypad":
            for i in range(9):
                pygame.draw.rect(self.screen, (160, 170, 180),
                                 R(r.x + 14 + (i % 3) * 46, r.y + 12 + (i // 3) * 30,
                                   34, 22), border_radius=3)
        elif k == "cabinet":
            pygame.draw.line(self.screen, (0, 0, 0), (r.centerx, r.y),
                             (r.centerx, r.bottom), 2)
        elif k == "crate":
            pygame.draw.line(self.screen, (80, 55, 30), r.topleft, r.bottomright, 3)
            pygame.draw.line(self.screen, (80, 55, 30), r.topright, r.bottomleft, 3)
        elif k == "shelf":
            for i in range(3):
                pygame.draw.line(self.screen, (60, 45, 30),
                                 (r.x, r.y + 20 + i * 20), (r.right, r.y + 20 + i * 20), 3)
        if o.get("riddle") and not self.st.solved[o["riddle"]]:
            pygame.draw.circle(self.screen, C_GOLD, (r.right - 10, r.y + 10),
                               int(6 + 3 * pulse))
        if done or (o.get("riddle") and self.st.solved[o["riddle"]]):
            self.text("done", self.f_tiny, C_GOOD,
                      r.centerx, r.bottom + 10, "center")

    def draw_door(self, d):
        g = self.st
        r = d["rect"]
        ok, _ = self.can_enter(d["dest"])
        if g.room == "cell" and not g.cell_open:
            ok = False
        col = (60, 150, 90) if ok else (150, 60, 60)
        if d["dest"] == "exit":
            col = C_GOLD if all(g.solved.values()) else (150, 110, 40)
        pygame.draw.rect(self.screen, col, r, border_radius=4)
        pygame.draw.rect(self.screen, (0, 0, 0), r, 2, border_radius=4)
        if not ok and d["dest"] != "exit":
            pygame.draw.rect(self.screen, (230, 230, 230),
                             R(r.centerx - 6, r.centery - 4, 12, 10))
            pygame.draw.arc(self.screen, (230, 230, 230),
                            R(r.centerx - 5, r.centery - 12, 10, 14), 0,
                            math.pi, 2)
        if d.get("vertical"):
            self.text(d["label"], self.f_tiny, C_TEXT, r.left - 6, r.centery,
                      "midright")
        elif r.y < 300:
            self.text(d["label"], self.f_tiny, C_TEXT, r.centerx, r.bottom + 10,
                      "center")
        else:
            self.text(d["label"], self.f_tiny, C_TEXT, r.centerx, r.y - 10,
                      "center")

    def draw_player(self):
        p = self.st.pos
        pygame.draw.ellipse(self.screen, (0, 0, 0, 60),
                            R(int(p.x) - 14, int(p.y) + 8, 28, 10))
        pygame.draw.circle(self.screen, (230, 230, 240), (int(p.x), int(p.y) - 8), 8)
        pygame.draw.rect(self.screen, (240, 150, 60),
                         R(int(p.x) - 9, int(p.y) - 1, 18, 20), border_radius=5)

    def draw_world(self):
        g = self.st
        room = ROOMS[g.room]
        self.screen.fill(C_BG)
        pygame.draw.rect(self.screen, room["floor"], FLOOR)
        for x in range(FLOOR.left, FLOOR.right, 40):
            pygame.draw.line(self.screen, tuple(max(0, c - 8) for c in room["floor"]),
                             (x, FLOOR.top), (x, FLOOR.bottom))
        for y in range(FLOOR.top, FLOOR.bottom, 40):
            pygame.draw.line(self.screen, tuple(max(0, c - 8) for c in room["floor"]),
                             (FLOOR.left, y), (FLOOR.right, y))
        pygame.draw.rect(self.screen, (90, 100, 115), FLOOR.inflate(8, 8), 6)
        for d in room["doors"]:
            self.draw_door(d)
        for o in room["objects"]:
            self.draw_object(o)
        self.draw_player()
        if room["dark"]:
            dark = pygame.Surface((W, H), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 235))
            pygame.draw.circle(dark, (0, 0, 0, 0),
                               (int(g.pos.x), int(g.pos.y)), 130)
            pygame.draw.circle(dark, (0, 0, 0, 110),
                               (int(g.pos.x), int(g.pos.y)), 175, 40)
            self.screen.blit(dark, (0, 0))
        near = self.nearest()
        if near and not self.dialog:
            kind, data, rect = near
            label = (f"Go to {data['label']}" if kind == "door"
                     else data["label"])
            tw = self.f_small.size(label + "   [E]")[0] + 24
            box = R(0, 0, tw, 32)
            box.midbottom = (rect.centerx, rect.top - (34 if kind == "door" else 8))
            if box.top < HUD_H + 4:
                box.top = rect.bottom + 8
            box.x = max(10, min(W - box.w - 10, box.x))
            self.panel(box, C_ACCENT)
            self.text(label + "   [E]", self.f_small, C_TEXT, box.centerx,
                      box.centery, "center")
        self.draw_hud()
        # alarm vignette
        frac = g.alarm / ALARM_LIMIT
        if frac > 0.6:
            a = int(60 * (frac - .6) / .4 * (0.6 + 0.4 * math.sin(self.t * 8)))
            v = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.rect(v, (255, 0, 0, max(0, a)), (0, 0, W, H), 24)
            self.screen.blit(v, (0, 0))
        # hint bar
        if g.room == "cell" and not self.dialog and g.moves == 0:
            self.text("WASD / arrows: move   E: interact   I: inventory   Esc: menu",
                      self.f_small, C_DIM, W // 2, H - 14, "midbottom")

    def draw_dialog(self):
        if not self.dialog:
            return
        box = R(60, H - 170, W - 120, 130)
        self.panel(box, C_ACCENT)
        lines = self.wrap(self.dialog[0], self.f_med, box.w - 40)
        for i, ln in enumerate(lines[:4]):
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

    # -------------------------------------------------- scenes
    def menu(self, items, idx, y0, step=56):
        mouse = pygame.mouse.get_pos()
        rects = []
        for i, label in enumerate(items):
            r = R(0, 0, 380, 46)
            r.center = (W // 2, y0 + i * step)
            rects.append(r)
            if r.collidepoint(mouse):
                idx = i
            sel = (i == idx)
            self.panel(r, C_ACCENT if sel else C_EDGE,
                       (30, 70, 80) if sel else C_PANEL)
            self.text(("> " if sel else "") + label, self.f_med,
                      C_TEXT if sel else C_DIM, r.centerx, r.centery, "center")
        return idx, rects

    def draw_title(self):
        self.screen.fill(C_BG)
        for i in range(14):
            x = (i * 137 + int(self.t * 20)) % (W + 80) - 40
            flick = 0.5 + 0.5 * math.sin(self.t * (2 + i % 4) + i)
            c = int(30 + 40 * flick)
            pygame.draw.rect(self.screen, (c, c + 14, c + 24), R(x, 0, 6, H))
        tint = pygame.Surface((W, H), pygame.SRCALPHA)
        tint.fill((8, 12, 20, 170))
        self.screen.blit(tint, (0, 0))
        glow = 150 + int(100 * (0.5 + 0.5 * math.sin(self.t * 2.5)))
        self.text("ESCAPE ROOM", self.f_title, (glow, 255, 230), W // 2, 120,
                  "center")
        self.text("P R O J E C T   O B S C U R A", self.f_big, C_WARN,
                  W // 2, 190, "center")
        self.text("You wake up in a secret laboratory. The door is locked.",
                  self.f_small, C_DIM, W // 2, 240, "center")
        self.text("Five riddles stand between you and freedom...",
                  self.f_small, C_DIM, W // 2, 264, "center")
        self.menu_idx, self.menu_rects = self.menu(
            ["Start a new game", "How to play", "Quit"], self.menu_idx, 350)

    def draw_how(self):
        self.screen.fill(C_BG)
        self.text("HOW TO PLAY", self.f_big, C_ACCENT, W // 2, 50, "midtop")
        lines = [
            "MOVE: WASD or arrow keys.   INTERACT: E (or Space).",
            "INVENTORY: I.   MENU: Esc.",
            "",
            "Explore the laboratory, search objects and collect items.",
            "A flashlight lights dark rooms, a crowbar opens barred doors,",
            "keycards and keys open the deeper rooms.",
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
        self.screen.fill(C_BG)
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
            for i, ln in enumerate(self.wrap(ui["msg"], self.f_small, box.w - 60)):
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
        self.screen.fill(C_BG)
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
            r = R(box.x + 60 + (i % 3) * 120, box.y + 170 + (i // 3) * 64, 100, 52)
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
        for i in range(30):
            x = (i * 97 + int(self.t * (30 + i))) % W
            y = (i * 53 + int(self.t * (20 + i * 2))) % H
            pygame.draw.circle(self.screen, C_GOLD if won else C_WARN, (x, y), 3)
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
        self.say("It is dark. Your head aches. A metal door slams somewhere.",
                 "You are locked in a SECRET LABORATORY. Solve five riddles "
                 "to find the exit code and ESCAPE!")

    def on_keydown(self, ev):
        k = ev.key
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
                if k in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                    self.dialog.pop(0)
            elif self.show_inv:
                if k in (pygame.K_i, pygame.K_ESCAPE):
                    self.show_inv = False
            else:
                if k in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
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

    def keypad_press(self, lab):
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
                    self.on_keydown(ev)
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.on_click(ev.pos)
            if (self.scene == "play" and not self.dialog and not self.paused
                    and not self.show_inv):
                self.update_play(dt)
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
