"""
MindScroll — MVP
A TikTok-style vertical scrolling feed of short-form content, with a puzzle
break inserted every few "videos" to give the user's brain a workout before
they go back to scrolling.

This MVP uses placeholder "video" cards (colored panels with text + a fake
progress bar) instead of real video playback, so the whole feed/puzzle loop
can be tested and tuned before wiring up real media.

New in this version: a genre-select screen at startup. Pick one or more
puzzle genres (math, science, geography, english, engineering, history,
language) and puzzles are drawn only from those genres for the session.

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

GENRES = ["math", "science", "geography", "english", "engineering", "history", "language"]
GENRE_LABELS = {
    "math": "Math",
    "science": "Science",
    "geography": "Geography",
    "english": "English",
    "engineering": "Engineering",
    "history": "History",
    "language": "Language",
}

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
# Each puzzle now carries a "genre" tag from GENRES.
PUZZLE_BANK = [
    # --- math ---
    {"genre": "math", "type": "pattern", "q": "What comes next? 2, 6, 12, 20, 30, __",
     "answer": "42", "accept": ["42"],
     "explain": "Differences increase by 2 each time (4,6,8,10,12) -> 30+12=42."},
    {"genre": "math", "type": "mc", "q": "Which of these is NOT a prime number?",
     "options": ["31", "51", "61", "71"], "answer": "51",
     "explain": "51 = 3 x 17, so it's not prime."},
    {"genre": "math", "type": "riddle", "q": "What is the next number? 1, 1, 2, 3, 5, 8, __",
     "answer": "13", "accept": ["13"],
     "explain": "Fibonacci sequence: each number is the sum of the two before it."},
    {"genre": "math", "type": "mc", "q": "What is the sum of the interior angles of a triangle?",
     "options": ["90 degrees", "180 degrees", "270 degrees", "360 degrees"], "answer": "180 degrees",
     "explain": "Any triangle's interior angles always sum to 180 degrees."},

    # --- science ---
    {"genre": "science", "type": "mc", "q": "Which planet has the most confirmed moons?",
     "options": ["Jupiter", "Saturn", "Uranus", "Neptune"], "answer": "Saturn",
     "explain": "Saturn has surpassed Jupiter in confirmed moon count in recent surveys."},
    {"genre": "science", "type": "riddle", "q": "What gas do plants absorb from the air to make food?",
     "answer": "carbon dioxide", "accept": ["carbon dioxide", "co2"],
     "explain": "Plants use CO2 plus sunlight and water to photosynthesize."},
    {"genre": "science", "type": "mc", "q": "What is the powerhouse of the cell?",
     "options": ["Nucleus", "Ribosome", "Mitochondria", "Golgi apparatus"], "answer": "Mitochondria",
     "explain": "Mitochondria generate most of the cell's ATP energy supply."},
    {"genre": "science", "type": "riddle", "q": "What is the chemical symbol for gold?",
     "answer": "au", "accept": ["au"],
     "explain": "From the Latin word for gold, 'aurum'."},

    # --- geography ---
    {"genre": "geography", "type": "mc", "q": "Which is the longest river in the world?",
     "options": ["Amazon", "Nile", "Yangtze", "Mississippi"], "answer": "Nile",
     "explain": "The Nile is generally considered the longest river, at ~6,650 km."},
    {"genre": "geography", "type": "riddle", "q": "What is the smallest country in the world by area?",
     "answer": "vatican city", "accept": ["vatican city", "vatican"],
     "explain": "Vatican City covers just about 0.49 square kilometers."},
    {"genre": "geography", "type": "mc", "q": "Which desert is the largest hot desert in the world?",
     "options": ["Gobi", "Kalahari", "Sahara", "Mojave"], "answer": "Sahara",
     "explain": "The Sahara spans much of North Africa, about 9.2 million sq km."},
    {"genre": "geography", "type": "riddle", "q": "Which mountain range separates Europe from Asia?",
     "answer": "ural mountains", "accept": ["ural mountains", "urals", "ural"],
     "explain": "The Ural Mountains form part of the conventional Europe-Asia boundary."},

    # --- english ---
    {"genre": "english", "type": "riddle", "q": "What is the plural of 'goose'?",
     "answer": "geese", "accept": ["geese"],
     "explain": "'Goose' has an irregular plural: 'geese'."},
    {"genre": "english", "type": "mc", "q": "Which word is a synonym for 'benevolent'?",
     "options": ["Cruel", "Kind", "Indifferent", "Timid"], "answer": "Kind",
     "explain": "'Benevolent' means well-meaning and kindly."},
    {"genre": "english", "type": "riddle", "q": "What figure of speech compares two things using 'like' or 'as'?",
     "answer": "simile", "accept": ["simile", "a simile"],
     "explain": "A simile makes an explicit comparison using 'like' or 'as'."},
    {"genre": "english", "type": "mc", "q": "Which sentence uses the correct homophone?",
     "options": ["Their going to the store.", "There going to the store.",
                 "They're going to the store.", "Ther going to the store."],
     "answer": "They're going to the store.",
     "explain": "'They're' is the contraction of 'they are'."},

    # --- engineering ---
    {"genre": "engineering", "type": "mc", "q": "Which material property describes resistance to being stretched?",
     "options": ["Density", "Tensile strength", "Conductivity", "Viscosity"], "answer": "Tensile strength",
     "explain": "Tensile strength measures how much a material resists pulling/stretching forces."},
    {"genre": "engineering", "type": "riddle", "q": "What force pulls a bridge cable taut and keeps it in tension?",
     "answer": "gravity", "accept": ["gravity", "the load", "weight"],
     "explain": "Gravity pulling down on the deck's weight puts the cables into tension."},
    {"genre": "engineering", "type": "mc", "q": "In circuits, what unit measures electrical resistance?",
     "options": ["Volt", "Amp", "Ohm", "Watt"], "answer": "Ohm",
     "explain": "Resistance is measured in ohms, per Ohm's Law: V = IR."},
    {"genre": "engineering", "type": "riddle", "q": "What is the term for the maximum load a structure can safely support?",
     "answer": "load capacity", "accept": ["load capacity", "capacity", "safe load", "load-bearing capacity"],
     "explain": "Engineers design for a safe load (or load) capacity with a margin of safety."},

    # --- history ---
    {"genre": "history", "type": "riddle", "q": "In what year did World War II end?",
     "answer": "1945", "accept": ["1945"],
     "explain": "WWII ended in 1945 with Japan's surrender in September."},
    {"genre": "history", "type": "mc", "q": "Who was the first President of the United States?",
     "options": ["Thomas Jefferson", "John Adams", "George Washington", "Benjamin Franklin"],
     "answer": "George Washington",
     "explain": "George Washington served as the first U.S. President, 1789-1797."},
    {"genre": "history", "type": "riddle", "q": "What ancient wonder was located in Giza, Egypt?",
     "answer": "great pyramid", "accept": ["great pyramid", "great pyramid of giza", "pyramids", "the pyramids"],
     "explain": "The Great Pyramid of Giza is the last surviving Ancient Wonder of the World."},
    {"genre": "history", "type": "mc", "q": "Which empire built the Colosseum?",
     "options": ["Greek", "Roman", "Ottoman", "Persian"], "answer": "Roman",
     "explain": "The Colosseum was completed around 80 AD under the Roman Empire."},

    # --- language ---
    {"genre": "language", "type": "riddle", "q": "In Spanish, what does 'biblioteca' mean?",
     "answer": "library", "accept": ["library", "a library"],
     "explain": "'Biblioteca' is Spanish (and Italian) for 'library'."},
    {"genre": "language", "type": "mc", "q": "Which language has the most native speakers worldwide?",
     "options": ["English", "Hindi", "Mandarin Chinese", "Spanish"], "answer": "Mandarin Chinese",
     "explain": "Mandarin Chinese has the largest number of native speakers globally."},
    {"genre": "language", "type": "riddle", "q": "What does the French word 'merci' mean?",
     "answer": "thank you", "accept": ["thank you", "thanks"],
     "explain": "'Merci' is French for 'thank you'."},
    {"genre": "language", "type": "mc", "q": "Which alphabet is used to write Russian?",
     "options": ["Latin", "Cyrillic", "Greek", "Arabic"], "answer": "Cyrillic",
     "explain": "Russian is written using the Cyrillic alphabet."},
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

        self.selected_genres = set(GENRES)  # default: all selected on the genre screen
        self.feed = []
        self.position = 0
        self.likes = {}
        self.score = {"correct": 0, "attempted": 0}
        self._progress_job = None

        self.card = tk.Frame(self.root, bg="#111827", width=420, height=680)
        self.card.place(x=0, y=0)

        self.status_bar = tk.Frame(self.root, bg="#0b0b0f", height=80)
        self.progress_canvas = tk.Canvas(self.root, width=420, height=4, bg="#0b0b0f",
                                          highlightthickness=0)

        self._show_genre_select()

        self.root.bind("<Down>", lambda e: self.go_next() if self.feed else None)
        self.root.bind("<Up>", lambda e: self.go_prev() if self.feed else None)

    # -- genre selection screen -----------------------------------------

    def _show_genre_select(self):
        self.status_bar.place_forget()
        self.progress_canvas.place_forget()
        for w in self.card.winfo_children():
            w.destroy()
        self.card.configure(bg="#0f172a")
        self.card.place(x=0, y=0, width=420, height=760)

        tk.Label(self.card, text="MindScroll", font=self.title_font,
                 bg="#0f172a", fg="white").place(x=16, y=24)
        tk.Label(self.card, text="Pick the puzzle genres you want mixed into your feed:",
                 font=self.body_font, bg="#0f172a", fg="#cbd5e1",
                 wraplength=388, justify="left").place(x=16, y=60)

        self._genre_vars = {}
        y = 110
        for genre in GENRES:
            var = tk.BooleanVar(value=True)
            self._genre_vars[genre] = var
            cb = tk.Checkbutton(self.card, text=GENRE_LABELS[genre], variable=var,
                                 font=self.body_font, bg="#0f172a", fg="white",
                                 selectcolor="#1e293b", activebackground="#0f172a",
                                 anchor="w")
            cb.place(x=16, y=y, width=388, height=32)
            y += 40

        self.genre_error = tk.Label(self.card, text="", font=self.small_font,
                                     bg="#0f172a", fg="#f87171")
        self.genre_error.place(x=16, y=y + 10)

        start_btn = tk.Button(self.card, text="Start scrolling \u2193", font=self.body_font,
                               bg="#2563eb", fg="white", relief="flat",
                               activebackground="#1d4ed8", command=self._confirm_genres)
        start_btn.place(x=16, y=690, width=388, height=48)

    def _confirm_genres(self):
        chosen = {g for g, v in self._genre_vars.items() if v.get()}
        if not chosen:
            self.genre_error.configure(text="Pick at least one genre to continue.")
            return
        self.selected_genres = chosen
        self.status_bar.place(x=0, y=680, width=420, height=80)
        self.progress_canvas.place(x=0, y=0)
        self._build_chrome()
        self.feed = self._build_feed()
        self.position = 0
        self._show_current()

    # -- feed construction ---------------------------------------------

    def _build_feed(self):
        """Interleave videos with puzzle breaks: N videos, 1 puzzle, repeat.
        Puzzles are drawn only from self.selected_genres."""
        videos = random.sample(VIDEO_BANK, len(VIDEO_BANK))
        pool = [p for p in PUZZLE_BANK if p["genre"] in self.selected_genres]
        if not pool:
            pool = list(PUZZLE_BANK)  # safety net; shouldn't happen
        puzzles = random.sample(pool, len(pool))
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
        for w in self.status_bar.winfo_children():
            w.destroy()

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
        self.card.place(x=0, y=0, width=420, height=680)
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
        tk.Label(self.card, text=f"\U0001F9E9 Brain break \u2014 {GENRE_LABELS[puzzle['genre']]}",
                 font=self.small_font, bg="#0f172a", fg="#93c5fd").place(x=16, y=24)
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
