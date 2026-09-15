"""
MindScroll — MVP
A TikTok-style vertical scrolling feed of short-form content, with a puzzle
break inserted every few "videos" to give the user's brain a workout before
they go back to scrolling.

This MVP uses placeholder "video" cards (colored panels with text + a fake
progress bar) instead of real video playback, so the whole feed/puzzle loop
can be tested and tuned before wiring up real media.

Run: python mindscroll.py
Controls:
  - Down Arrow / "Next" button -> advance to next video or puzzle
  - Up Arrow / "Back" button   -> go to previous video (disabled during puzzles)
  - Like button                -> toggle like on current video
  - During a puzzle: click an answer option, or type + press Enter for free-response puzzles
"""

import random
import tkinter as tk
from tkinter import font as tkfont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VIDEOS_PER_PUZZLE = 3           # show a puzzle after this many videos
AUTOPLAY_MS = 4000              # simulated video "duration" in ms
PROGRESS_TICK_MS = 50           # how often the progress bar updates
WINDOW_SIZE = "420x760"         # phone-ish aspect ratio

CARD_COLORS = [
    "#1f2937", "#7c2d12", "#312e81", "#134e4a",
    "#4a044e", "#052e16", "#7f1d1d", "#0c4a6e",
]

# ---------------------------------------------------------------------------
# Placeholder content
# ---------------------------------------------------------------------------

VIDEO_BANK = [
    {"creator": "@nebula.facts", "title": "Octopuses have 3 hearts",
     "desc": "Two pump blood to the gills, one to the rest of the body."},
    {"creator": "@quickcooks", "title": "60-second garlic butter pasta",
     "desc": "Butter, garlic, parm, pasta water. That's it."},
    {"creator": "@urban.sketch", "title": "Drawing a coffee shop in 45s",
     "desc": "Timelapse sketch using just a fineliner and one gray marker."},
    {"creator": "@history.bits", "title": "Why Rome had no police force",
     "desc": "Vigiles handled fires more than crime — wild, right?"},
    {"creator": "@lofi.loops", "title": "Rainy window + lofi beat",
     "desc": "Loop #482. Good for studying or zoning out."},
    {"creator": "@space.daily", "title": "A day on Venus is longer than its year",
     "desc": "Venus rotates so slowly a 'day' outlasts its trip around the sun."},
    {"creator": "@deskplants", "title": "Repotting a stressed pothos",
     "desc": "Yellow leaves? Probably overwatering, not underwatering."},
    {"creator": "@mini.builds", "title": "Tiny cardboard arcade machine",
     "desc": "Rubber bands + a marble + way too much hot glue."},
    {"creator": "@wordnerd", "title": "Where 'salary' comes from",
     "desc": "Roman soldiers were partly paid in salt — 'sal' -> salary."},
    {"creator": "@night.walks", "title": "Empty city streets at 2am",
     "desc": "No music, just footsteps and distant traffic. Weirdly calming."},
]

# Puzzle types: "mc" (multiple choice), "riddle" (free text), "pattern" (free text)
PUZZLE_BANK = [
    {"type": "mc", "q": "Which planet has the most moons (as currently confirmed)?",
     "options": ["Jupiter", "Saturn", "Uranus", "Neptune"], "answer": "Saturn",
     "explain": "Saturn has surpassed Jupiter in confirmed moon count in recent surveys."},
    {"type": "riddle", "q": "The more you take, the more you leave behind. What am I?",
     "answer": "footsteps", "accept": ["footsteps", "footprints"],
     "explain": "Each step taken leaves a footprint behind."},
    {"type": "pattern", "q": "What comes next? 2, 6, 12, 20, 30, __",
     "answer": "42", "accept": ["42"],
     "explain": "Differences increase by 2 each time (4,6,8,10,12) -> 30+12=42."},
    {"type": "mc", "q": "Which of these is NOT a prime number?",
     "options": ["31", "51", "61", "71"], "answer": "51",
     "explain": "51 = 3 x 17, so it's not prime."},
    {"type": "riddle", "q": "I have keys but no locks, space but no rooms. What am I?",
     "answer": "keyboard", "accept": ["keyboard", "a keyboard"],
     "explain": "A keyboard has keys and a space bar, but no literal locks or rooms."},
    {"type": "pattern", "q": "What comes next? A, D, G, J, __",
     "answer": "m", "accept": ["m"],
     "explain": "Each letter skips 2 ahead: +3 in the alphabet each time -> M."},
    {"type": "mc", "q": "In chess, which piece can only move diagonally?",
     "options": ["Rook", "Knight", "Bishop", "Queen"], "answer": "Bishop",
     "explain": "The bishop is restricted to diagonal moves."},
    {"type": "riddle", "q": "What has a face and two hands but no arms or legs?",
     "answer": "clock", "accept": ["clock", "a clock"],
     "explain": "A clock face with an hour and minute hand."},
]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class MindScrollApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MindScroll (MVP)")
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg="#0b0b0f")
        self.root.resizable(False, False)

        self.title_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.body_font = tkfont.Font(family="Helvetica", size=12)
        self.small_font = tkfont.Font(family="Helvetica", size=10)

        # Build a shuffled, endless-ish feed with puzzles interleaved
        self.feed = self._build_feed()
        self.position = 0            # index into self.feed
        self.likes = {}              # video index -> bool
        self.score = {"correct": 0, "attempted": 0}
        self._progress_job = None

        self._build_chrome()
        self._show_current()

        self.root.bind("<Down>", lambda e: self.go_next())
        self.root.bind("<Up>", lambda e: self.go_prev())

    # -- feed construction ---------------------------------------------

    def _build_feed(self):
        """Interleave videos with puzzle breaks: N videos, 1 puzzle, repeat."""
        videos = random.sample(VIDEO_BANK, len(VIDEO_BANK))
        puzzles = random.sample(PUZZLE_BANK, len(PUZZLE_BANK))
        feed = []
        vi, pi = 0, 0
        while vi < len(videos):
            chunk = videos[vi: vi + VIDEOS_PER_PUZZLE]
            for v in chunk:
                feed.append({"kind": "video", "data": v})
            vi += VIDEOS_PER_PUZZLE
            if vi < len(videos):  # don't tack a puzzle onto the very end
                puzzle = puzzles[pi % len(puzzles)]
                feed.append({"kind": "puzzle", "data": puzzle})
                pi += 1
        return feed

    # -- chrome (persistent widgets) -------------------------------------

    def _build_chrome(self):
        self.card = tk.Frame(self.root, bg="#111827", width=420, height=680)
        self.card.place(x=0, y=0)

        self.status_bar = tk.Frame(self.root, bg="#0b0b0f", height=80)
        self.status_bar.place(x=0, y=680, width=420, height=80)

        self.back_btn = tk.Button(self.status_bar, text="\u2191 Back", command=self.go_prev,
                                   bg="#1f2937", fg="white", relief="flat",
                                   activebackground="#374151")
        self.back_btn.place(x=10, y=20, width=90, height=40)

        self.like_btn = tk.Button(self.status_bar, text="\u2661 Like", command=self.toggle_like,
                                   bg="#1f2937", fg="white", relief="flat",
                                   activebackground="#374151")
        self.like_btn.place(x=165, y=20, width=90, height=40)

        self.next_btn = tk.Button(self.status_bar, text="Next \u2193", command=self.go_next,
                                   bg="#2563eb", fg="white", relief="flat",
                                   activebackground="#1d4ed8")
        self.next_btn.place(x=320, y=20, width=90, height=40)

        self.progress_canvas = tk.Canvas(self.root, width=420, height=4, bg="#0b0b0f",
                                          highlightthickness=0)
        self.progress_canvas.place(x=0, y=0)

    # -- navigation --------------------------------------------------------

    def go_next(self):
        if self._progress_job:
            self.root.after_cancel(self._progress_job)
            self._progress_job = None
        if self.position < len(self.feed) - 1:
            self.position += 1
            self._show_current()
        else:
            # loop back around when the feed runs out, like an endless scroll
            self.feed = self._build_feed()
            self.position = 0
            self._show_current()

    def go_prev(self):
        item = self.feed[self.position]
        if item["kind"] == "puzzle":
            return  # don't let users skip backwards out of a puzzle mid-think
        if self._progress_job:
            self.root.after_cancel(self._progress_job)
            self._progress_job = None
        if self.position > 0 and self.feed[self.position - 1]["kind"] == "video":
            self.position -= 1
            self._show_current()

    def toggle_like(self):
        item = self.feed[self.position]
        if item["kind"] != "video":
            return
        self.likes[self.position] = not self.likes.get(self.position, False)
        self.like_btn.configure(
            text="\u2665 Liked" if self.likes[self.position] else "\u2661 Like",
            fg="#f43f5e" if self.likes[self.position] else "white",
        )

    # -- rendering -----------------------------------------------------

    def _clear_card(self):
        for w in self.card.winfo_children():
            w.destroy()
        self.progress_canvas.delete("all")

    def _show_current(self):
        self._clear_card()
        item = self.feed[self.position]
        if item["kind"] == "video":
            self.back_btn.configure(state="normal")
            self.like_btn.configure(state="normal")
            self._render_video(item["data"])
        else:
            self.back_btn.configure(state="disabled")
            self.like_btn.configure(state="disabled")
            self._render_puzzle(item["data"])

    def _render_video(self, video):
        color = random.choice(CARD_COLORS)
        self.card.configure(bg=color)

        tk.Label(self.card, text=video["creator"], font=self.small_font,
                 bg=color, fg="#e5e7eb").place(x=16, y=24)
        tk.Label(self.card, text=video["title"], font=self.title_font,
                 bg=color, fg="white", wraplength=380, justify="left").place(x=16, y=54)
        tk.Label(self.card, text=video["desc"], font=self.body_font,
                 bg=color, fg="#d1d5db", wraplength=380, justify="left").place(x=16, y=110)

        liked = self.likes.get(self.position, False)
        self.like_btn.configure(text="\u2665 Liked" if liked else "\u2661 Like",
                                 fg="#f43f5e" if liked else "white")

        tk.Label(self.card, text="\u25b6 playing (simulated)", font=self.small_font,
                 bg=color, fg="#9ca3af").place(x=16, y=630)

        self._animate_progress(AUTOPLAY_MS)

    def _animate_progress(self, duration_ms):
        self.progress_canvas.delete("all")
        steps = max(duration_ms // PROGRESS_TICK_MS, 1)
        self._progress_step = 0

        def tick():
            self._progress_step += 1
            frac = min(self._progress_step / steps, 1.0)
            self.progress_canvas.delete("all")
            self.progress_canvas.create_rectangle(0, 0, 420 * frac, 4,
                                                    fill="#2563eb", width=0)
            if frac < 1.0:
                self._progress_job = self.root.after(PROGRESS_TICK_MS, tick)
            else:
                self._progress_job = None
                self.go_next()  # autoplay advance, like TikTok

        tick()

    def _render_puzzle(self, puzzle):
        self.card.configure(bg="#0f172a")
        tk.Label(self.card, text="\U0001F9E9 Brain break", font=self.small_font,
                 bg="#0f172a", fg="#93c5fd").place(x=16, y=24)
        tk.Label(self.card, text=puzzle["q"], font=self.title_font,
                 bg="#0f172a", fg="white", wraplength=380, justify="left").place(x=16, y=56)

        self.feedback_label = tk.Label(self.card, text="", font=self.body_font,
                                        bg="#0f172a", fg="#facc15", wraplength=380,
                                        justify="left")
        self.feedback_label.place(x=16, y=560)

        if puzzle["type"] == "mc":
            self._render_mc_options(puzzle)
        else:
            self._render_free_response(puzzle)

    def _render_mc_options(self, puzzle):
        y = 170
        for opt in puzzle["options"]:
            btn = tk.Button(self.card, text=opt, font=self.body_font,
                             bg="#1e293b", fg="white", relief="flat",
                             activebackground="#334155", anchor="w", padx=12,
                             command=lambda o=opt: self._check_answer(puzzle, o))
            btn.place(x=16, y=y, width=388, height=44)
            y += 56

    def _render_free_response(self, puzzle):
        entry = tk.Entry(self.card, font=self.body_font)
        entry.place(x=16, y=180, width=300, height=36)
        entry.focus_set()

        def submit(event=None):
            self._check_answer(puzzle, entry.get())

        entry.bind("<Return>", submit)
        tk.Button(self.card, text="Submit", command=submit, bg="#2563eb", fg="white",
                  relief="flat", activebackground="#1d4ed8").place(x=324, y=180, width=80, height=36)

    def _check_answer(self, puzzle, user_answer):
        self.score["attempted"] += 1
        accepted = puzzle.get("accept", [puzzle["answer"]])
        correct = user_answer.strip().lower() in [a.lower() for a in accepted]
        if correct:
            self.score["correct"] += 1
            self.feedback_label.configure(
                text=f"\u2705 Correct! {puzzle['explain']}  (Score: {self.score['correct']}/{self.score['attempted']})",
                fg="#4ade80")
        else:
            self.feedback_label.configure(
                text=f"\u274c Not quite — answer: {puzzle['answer']}. {puzzle['explain']}  (Score: {self.score['correct']}/{self.score['attempted']})",
                fg="#f87171")

        # disable further input on this puzzle screen
        for w in self.card.winfo_children():
            if isinstance(w, (tk.Button, tk.Entry)):
                try:
                    w.configure(state="disabled")
                except tk.TclError:
                    pass

        continue_btn = tk.Button(self.card, text="Continue scrolling \u2193",
                                  command=self.go_next, bg="#2563eb", fg="white",
                                  relief="flat", activebackground="#1d4ed8")
        continue_btn.place(x=16, y=610, width=388, height=44)


if __name__ == "__main__":
    root = tk.Tk()
    app = MindScrollApp(root)
    root.mainloop()
