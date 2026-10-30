from __future__ import annotations

import random
import time
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from typing import Callable, Generator, List, Tuple, Dict, Any

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch


BG = "#0B1020"
PANEL = "#111A2E"
PANEL2 = "#17233B"
TEXT = "#EAF0FF"
MUTED = "#9BAAC7"
CYAN = "#53D8FB"
PURPLE = "#A78BFA"
GREEN = "#50E3A4"
ORANGE = "#FFB86B"
RED = "#FF6B83"
BAR = "#4D83F7"
COMPARE = "#FFB86B"
ACTIVE = "#53D8FB"
SORTED = "#50E3A4"

@dataclass
class Stats:
    comparisons: int = 0
    writes: int = 0
    swaps: int = 0

@dataclass
class Step:
    values: List[int]
    highlights: Tuple[int, ...] = ()
    sorted_indices: Tuple[int, ...] = ()
    note: str = ""

def snapshot(a, highlights=(), sorted_indices=(), note=""):
    return Step(a.copy(), tuple(highlights), tuple(sorted_indices), note)

def quick_sort_steps(values: List[int]) -> Generator[Step, None, Stats]:
    a = values.copy()
    stats = Stats()
    yield snapshot(a, note="Quick Sort: partition the array around a pivot.")
    def partition(lo, hi):
        pivot = a[hi]
        i = lo - 1
        for j in range(lo, hi):
            stats.comparisons += 1
            yield snapshot(a, (j, hi), note=f"Compare {a[j]} with pivot {pivot}.")
            if a[j] <= pivot:
                i += 1 
                if i != j:
                    a[i], a[j] = a[j], a[i]
                    stats.swaps += 1
                    stats.writes += 2
                    yield snapshot(a, (i, j, hi), note="Swap into the left partition.")
        if i + 1 != hi:
            a[i + 1], a[hi] = a[hi], a[i + 1]
            stats.swaps += 1
            stats.writes += 2
            yield snapshot(a, (i + 1, hi), note="Place pivot in its final position.")
        return i + 1
    def qs(lo, hi):
        if lo < hi:
            gen = partition(lo, hi)
            pivot_index = None
            while True:
                try:
                    step = next(gen)
                    yield step
                except StopIteration as e:
                    pivot_index = e.value
                    break
            yield snapshot(a, (pivot_index,), (pivot_index,), note=f"Pivot {a[pivot_index]} is now in its final position.")
            yield from qs(lo, pivot_index - 1)
            yield from qs(pivot_index + 1, hi)
    yield from qs(0, len(a) - 1)
    yield snapshot(a, sorted_indices=tuple(range(len(a))), note="Quick Sort complete.")
    return stats


def merge_sort_steps(values: List[int]) -> Generator[Step, None, Stats]:
    a = values.copy()
    stats = Stats()
    yield snapshot(a, note="Merge Sort: divide the array, then merge sorted halves.")
    def merge(lo, mid, hi):
        left, right = a[lo:mid+1], a[mid+1:hi+1]
        i = j = 0
        out = []
        while i < len(left) and j < len(right):
            stats.comparisons += 1
            yield snapshot(a, (lo+i, mid+1+j), note=f"Compare {left[i]} and {right[j]} while merging.")
            if left[i] <= right[j]:
                out.append(left[i]); i += 1
            else:
                out.append(right[j]); j += 1
        out.extend(left[i:]); out.extend(right[j:])
        for k, v in enumerate(out, lo):
            a[k] = v
            stats.writes += 1
            yield snapshot(a, (k,), note=f"Write {v} into position {k}.")
    def ms(lo, hi):
        if lo >= hi: return
        mid = (lo + hi) // 2
        yield snapshot(a, (lo, mid, hi), note=f"Divide range {lo}–{hi} into two halves.")
        yield from ms(lo, mid)
        yield from ms(mid+1, hi)
        yield from merge(lo, mid, hi)
    yield from ms(0, len(a)-1)
    yield snapshot(a, sorted_indices=tuple(range(len(a))), note="Merge Sort complete.")
    return stats

def heap_sort_steps(values: List[int]) -> Generator[Step, None, Stats]:
    a = values.copy()
    stats = Stats()
    n = len(a)
    yield snapshot(a, note="Heap Sort: build a max heap, then extract its maximum.")
    def sift_down(root, end):
        while True:
            child = 2 * root + 1
            if child > end: break
            swap_child = child
            if child + 1 <= end:
                stats.comparisons += 1
                yield snapshot(a, (child, child+1, root), note="Compare the two children.")
                if a[child+1] > a[child]:
                    swap_child = child + 1
            stats.comparisons += 1
            yield snapshot(a, (root, swap_child), note="Compare parent with its larger child.")
            if a[root] < a[swap_child]:
                a[root], a[swap_child] = a[swap_child], a[root]
                stats.swaps += 1; stats.writes += 2
                yield snapshot(a, (root, swap_child), note="Restore the max-heap property.")
                root = swap_child
            else: break
    for start in range(n//2 - 1, -1, -1):
        yield from sift_down(start, n-1)
    for end in range(n-1, 0, -1):
        a[0], a[end] = a[end], a[0]
        stats.swaps += 1; stats.writes += 2
        yield snapshot(a, (0, end), tuple(range(end, n)), note=f"Move heap maximum to final position {end}.")
        yield from sift_down(0, end-1)
    yield snapshot(a, sorted_indices=tuple(range(n)), note="Heap Sort complete.")
    return stats

def counting_sort_steps(values: List[int]) -> Generator[Step, None, Stats]:
    a = values.copy()
    stats = Stats()
    yield snapshot(a, note="Counting Sort: count each integer, then rebuild in order.")
    if not a:
        return stats
    lo, hi = min(a), max(a)
    # Guard against pathological ranges; the UI also keeps generated values small.
    if hi - lo > 5000:
        raise ValueError("Counting Sort needs a manageable value range (max-min ≤ 5000).")
    counts = [0] * (hi - lo + 1)
    for i, v in enumerate(a):
        counts[v-lo] += 1
        stats.writes += 1
        yield snapshot(a, (i,), note=f"Count value {v}: frequency is now {counts[v-lo]}.")
    pos = 0
    for offset, count in enumerate(counts):
        for _ in range(count):
            a[pos] = offset + lo
            stats.writes += 1
            yield snapshot(a, (pos,), note=f"Write {offset+lo} from the frequency table.")
            pos += 1
    yield snapshot(a, sorted_indices=tuple(range(len(a))), note="Counting Sort complete.")
    return stats


ALGORITHMS: Dict[str, Callable] = {
    "Quick Sort": quick_sort_steps,
    "Merge Sort": merge_sort_steps,
    "Heap Sort": heap_sort_steps,
    "Counting Sort": counting_sort_steps,
}
COMPLEXITY = {
    "Quick Sort": ("O(n log n)", "O(n²)", "O(log n) avg"),
    "Merge Sort": ("O(n log n)", "O(n log n)", "O(n)"),
    "Heap Sort": ("O(n log n)", "O(n log n)", "O(1)"),
    "Counting Sort": ("O(n + k)", "O(n + k)", "O(k)"),
    "Radix Sort": ("O(d(n + b))", "O(d(n + b))", "O(n + b)"),
}

class SortQuestApp:
    def __init__(self, root):
        self.root = root
        root.title("SortQuest | Interactive Sorting Studio")
        root.geometry("1320x850")
        root.minsize(1080, 720)
        root.configure(bg=BG)
        self.values = [random.randint(8, 96) for _ in range(36)]
        self.steps: List[Step] = []
        self.step_index = 0
        self.stats = Stats()
        self.current_algorithm = tk.StringVar(value="Quick Sort")
        self.speed = tk.IntVar(value=70)
        self.array_size = tk.IntVar(value=36)
        self.data_type = tk.StringVar(value="Random")
        self.is_playing = False
        self.after_id = None
        self.current_generator = None
        self.last_elapsed = 0.0
        self.challenge_score = 0
        self.challenge_answer = tk.StringVar(value="Quick Sort")
        self._style()
        self._build_ui()
        self._new_array()
        self._show_complexity()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL2)], foreground=[("readonly", TEXT)])
        style.configure("Horizontal.TScale", background=PANEL, troughcolor=PANEL2)
        style.configure("TProgressbar", troughcolor=PANEL2, background=CYAN)

    def _label(self, parent, text, size=10, color=TEXT, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    def _button(self, parent, text, command, color=PANEL2, fg=TEXT, width=None):
        b = tk.Button(parent, text=text, command=command, bg=color, fg=fg,
                      activebackground=color, activeforeground=fg, relief="flat",
                      bd=0, padx=12, pady=8, cursor="hand2",
                      font=("Segoe UI", 9, "bold"))
        if width: b.configure(width=width)
        return b

    def _panel(self, parent, bg=PANEL, **kwargs):
        return tk.Frame(parent, bg=bg, **kwargs)

    def _build_ui(self):
        header = self._panel(self.root, BG)
        header.pack(fill="x", padx=24, pady=(18, 12))
        left = self._panel(header, BG); left.pack(side="left")
        tk.Label(left, text="◈  SORTQUEST", bg=BG, fg=CYAN, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(left, text="INTERACTIVE SORTING ALGORITHM STUDIO", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(2,0))
        self._label(header, "EXPLORE  •  RACE  •  DISCOVER", 10, PURPLE, True).pack(side="right", pady=12)

        controls = self._panel(self.root, PANEL)
        controls.pack(fill="x", padx=24, pady=(0, 12))
        row = self._panel(controls, PANEL); row.pack(fill="x", padx=14, pady=12)
        self._label(row, "ALGORITHM", 9, MUTED, True).pack(side="left", padx=(0,8))
        self.alg_combo = ttk.Combobox(row, textvariable=self.current_algorithm, values=list(ALGORITHMS), state="readonly", width=15)
        self.alg_combo.pack(side="left", padx=(0,16), ipady=4)
        self.alg_combo.bind("<<ComboboxSelected>>", lambda e: self._show_complexity())
        self._label(row, "DATA PATTERN", 9, MUTED, True).pack(side="left", padx=(0,8))
        self.data_combo = ttk.Combobox(row, textvariable=self.data_type, values=["Random","Nearly sorted","Reversed","Few unique"], state="readonly", width=14)
        self.data_combo.pack(side="left", padx=(0,8), ipady=4)
        self._button(row, "↻ Generate", self._new_array, PANEL2, CYAN).pack(side="left", padx=4)
        self._button(row, "▶  Run", self._run, "#1E8066", "#FFFFFF").pack(side="left", padx=4)
        self._button(row, "Ⅱ  Pause", self._pause, PANEL2, TEXT).pack(side="left", padx=4)
        self._button(row, "↤ Step", self._previous, PANEL2, TEXT).pack(side="left", padx=4)
        self._button(row, "Step ↦", self._next, PANEL2, TEXT).pack(side="left", padx=4)
        self._button(row, "↺ Reset", self._reset, PANEL2, TEXT).pack(side="left", padx=4)

        row2 = self._panel(controls, PANEL); row2.pack(fill="x", padx=14, pady=(0,12))
        self._label(row2, "ARRAY SIZE", 9, MUTED, True).pack(side="left", padx=(0,8))
        tk.Scale(row2, from_=1, to=100, variable=self.array_size, orient="horizontal", bg=PANEL, fg=TEXT,
                 troughcolor=PANEL2, highlightthickness=0, bd=0, length=190, showvalue=True,
                 command=lambda _=None: None).pack(side="left", padx=(0,20))
        self._label(row2, "ANIMATION SPEED", 9, MUTED, True).pack(side="left", padx=(0,8))
        tk.Scale(row2, from_=1, to=100, variable=self.speed, orient="horizontal", bg=PANEL, fg=TEXT,
                 troughcolor=PANEL2, highlightthickness=0, bd=0, length=180, showvalue=False).pack(side="left")
        self._label(row2, "SLOW", 8, MUTED).pack(side="left", padx=(0,5))
        self._label(row2, "FAST", 8, MUTED).pack(side="left")

        body = self._panel(self.root, BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0,12))
        chart_panel = self._panel(body, PANEL)
        chart_panel.pack(side="left", fill="both", expand=True, padx=(0,12))
        chart_head = self._panel(chart_panel, PANEL); chart_head.pack(fill="x", padx=16, pady=(13,0))
        self._label(chart_head, "LIVE ARRAY VISUALIZATION", 11, TEXT, True).pack(side="left")
        self.status_label = self._label(chart_head, "READY", 9, GREEN, True); self.status_label.pack(side="right")
        self.fig = Figure(figsize=(8, 4.8), dpi=100, facecolor=PANEL)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=.045, right=.99, top=.94, bottom=.12)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=4)
        self.note_label = tk.Label(chart_panel, text="Generate an array, then run or step through the algorithm.",
                                   bg=PANEL2, fg=TEXT, anchor="w", padx=12, pady=10,
                                   font=("Segoe UI", 10))
        self.note_label.pack(fill="x", padx=12, pady=(0,12))

        side = self._panel(body, BG, width=290)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        self._metric_card(side, "COMPARISONS", "comparisons", CYAN)
        self._metric_card(side, "WRITES", "writes", PURPLE)
        self._metric_card(side, "SWAPS", "swaps", ORANGE)
        self._metric_card(side, "ELAPSED", "elapsed", GREEN)
        comp = self._panel(side, PANEL)
        comp.pack(fill="x", pady=(0,10))
        self._label(comp, "COMPLEXITY CHEAT SHEET", 10, CYAN, True).pack(anchor="w", padx=12, pady=(12,8))
        self.complexity_labels = {}
        for label in ["Best","Average","Worst","Extra space"]:
            line = self._panel(comp, PANEL); line.pack(fill="x", padx=12, pady=3)
            self._label(line, label, 9, MUTED).pack(side="left")
            val = self._label(line, "—", 9, TEXT, True); val.pack(side="right")
            self.complexity_labels[label] = val
        self._label(comp, "k = value range • d = digit count • b = base", 8, MUTED).pack(anchor="w", padx=12, pady=(8,12))

        challenge = self._panel(side, PANEL)
        challenge.pack(fill="both", expand=True)
        self._label(challenge, "SMART CHALLENGE", 10, PURPLE, True).pack(anchor="w", padx=12, pady=(12,5))
        self.challenge_prompt = tk.Label(challenge, text="Which algorithm is often a strong choice for a large, general-purpose array?",
                                         wraplength=245, justify="left", bg=PANEL, fg=TEXT, font=("Segoe UI", 9))
        self.challenge_prompt.pack(anchor="w", padx=12, pady=(0,8))
        self.challenge_combo = ttk.Combobox(challenge, textvariable=self.challenge_answer, values=list(ALGORITHMS), state="readonly")
        self.challenge_combo.pack(fill="x", padx=12, pady=4)
        self._button(challenge, "Check my answer", self._check_challenge, PANEL2, CYAN).pack(fill="x", padx=12, pady=5)
        self.challenge_result = self._label(challenge, f"Score: {self.challenge_score}  •  Learn by experimenting", 8, MUTED)
        self.challenge_result.pack(anchor="w", padx=12, pady=(2,12))

        footer = self._panel(self.root, BG)
        footer.pack(fill="x", padx=24, pady=(0,14))
        self._label(footer, "SORTQUEST  /  Python • Tkinter • Matplotlib", 8, MUTED).pack(side="left")
        self._label(footer, "Educational demo • benchmark results depend on input and machine", 8, MUTED).pack(side="right")

    def _metric_card(self, parent, title, key, accent):
        card = self._panel(parent, PANEL)
        card.pack(fill="x", pady=(0,9))
        tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y")
        inner = self._panel(card, PANEL); inner.pack(side="left", fill="x", expand=True, padx=12, pady=9)
        self._label(inner, title, 8, MUTED, True).pack(anchor="w")
        val = self._label(inner, "0" if key != "elapsed" else "0.000 s", 18, TEXT, True)
        val.pack(anchor="w", pady=(2,0))
        setattr(self, f"metric_{key}", val)

    def _new_array(self):
        self._pause()
        n = int(self.array_size.get())
        mode = self.data_type.get()
        if mode == "Random":
            self.values = [random.randint(5, 100) for _ in range(n)]
        elif mode == "Nearly sorted":
            self.values = sorted(random.randint(5, 100) for _ in range(n))
            for _ in range(max(1, n//10)):
                i, j = random.sample(range(n), 2)
                self.values[i], self.values[j] = self.values[j], self.values[i]
        elif mode == "Reversed":
            self.values = sorted((random.randint(5, 100) for _ in range(n)), reverse=True)
        else:
            self.values = [random.choice([10,20,30,40,50,60,70]) for _ in range(n)]
        self._reset()

    def _reset(self):
        self._pause()
        self.steps = []
        self.step_index = 0
        self.stats = Stats()
        self.last_elapsed = 0
        self._update_metrics()
        self.status_label.configure(text="READY", fg=GREEN)
        self.note_label.configure(text="Ready. Press Run or use Step to explore the algorithm.")
        self._draw(snapshot(self.values))

    def _draw(self, step: Step):
        self.ax.clear()
        self.ax.set_facecolor(PANEL)
        self.ax.tick_params(axis="x", colors=MUTED, bottom=False, labelbottom=False)
        self.ax.tick_params(axis="y", colors=MUTED, labelsize=8)
        for spine in self.ax.spines.values(): spine.set_visible(False)
        self.ax.grid(axis="y", color="#26334D", linewidth=.6, alpha=.7)
        hi = set(step.highlights)
        sorted_set = set(step.sorted_indices)
        colors = [ACTIVE if i in hi else SORTED if i in sorted_set else BAR for i in range(len(step.values))]
        bars = self.ax.bar(range(len(step.values)), step.values, color=colors, width=.82, edgecolor="none")
        self.ax.set_xlim(-.6, max(len(step.values)-.4, .6))
        maxv = max(step.values, default=1)
        self.ax.set_ylim(0, maxv * 1.18 + 1)
        self.ax.set_ylabel("VALUE", color=MUTED, fontsize=8, labelpad=8)
        self.ax.set_title("Each bar is one value • cyan = active • green = finalized",
                          color=MUTED, fontsize=9, loc="left", pad=12)
        if len(step.values) <= 24:
            for bar, val in zip(bars, step.values):
                self.ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+maxv*.018,
                             str(val), ha="center", va="bottom", color=TEXT, fontsize=7)
        self.canvas.draw_idle()

    def _run(self):
        if self.is_playing: return
        if self.step_index >= len(self.steps):
            self._prepare_steps()
        if not self.steps: return
        self.is_playing = True
        self.status_label.configure(text="RUNNING", fg=CYAN)
        self._play_tick()

    def _prepare_steps(self):
        algorithm = self.current_algorithm.get()
        start = time.perf_counter()
        try:
            gen = ALGORITHMS[algorithm](self.values)
            self.steps = []
            while True:
                try:
                    self.steps.append(next(gen))
                except StopIteration as e:
                    self.stats = e.value or Stats()
                    break
            self.last_elapsed = time.perf_counter() - start
        except ValueError as e:
            messagebox.showwarning("Input not supported", str(e))
            self.steps = []
            return
        self.step_index = 0
        self._update_metrics()

    def _play_tick(self):
        if not self.is_playing: return
        if self.step_index >= len(self.steps):
            self.is_playing = False
            self.status_label.configure(text="COMPLETE", fg=GREEN)
            self._draw(self.steps[-1])
            self.note_label.configure(text=self.steps[-1].note)
            self._update_metrics()
            return
        step = self.steps[self.step_index]
        self._draw(step)
        self.note_label.configure(text=f"STEP {self.step_index+1:,} / {len(self.steps):,}   •   {step.note}")
        self.step_index += 1
        self._update_metrics()
        delay = max(10, int(500 - self.speed.get()*4.7))
        self.after_id = self.root.after(delay, self._play_tick)

    def _pause(self):
        self.is_playing = False
        if self.after_id is not None:
            try: self.root.after_cancel(self.after_id)
            except tk.TclError: pass
            self.after_id = None
        if hasattr(self, "status_label"):
            self.status_label.configure(text="PAUSED", fg=ORANGE)

    def _next(self):
        self._pause()
        if not self.steps: self._prepare_steps()
        if not self.steps: return
        self.step_index = min(self.step_index + 1, len(self.steps))
        idx = max(0, self.step_index - 1)
        self._draw(self.steps[idx])
        self.note_label.configure(text=f"STEP {idx+1:,} / {len(self.steps):,}   •   {self.steps[idx].note}")
        if self.step_index >= len(self.steps): self.status_label.configure(text="COMPLETE", fg=GREEN)
        self._update_metrics()

    def _previous(self):
        self._pause()
        if not self.steps: self._prepare_steps()
        if not self.steps: return
        self.step_index = max(1, self.step_index - 1)
        step = self.steps[self.step_index - 1]
        self._draw(step)
        self.note_label.configure(text=f"STEP {self.step_index:,} / {len(self.steps):,}   •   {step.note}")
        self._update_metrics()

    def _update_metrics(self):
        self.metric_comparisons.configure(text=f"{self.stats.comparisons:,}")
        self.metric_writes.configure(text=f"{self.stats.writes:,}")
        self.metric_swaps.configure(text=f"{self.stats.swaps:,}")
        self.metric_elapsed.configure(text=f"{self.last_elapsed:.4f} s")

    def _show_complexity(self):
        name = self.current_algorithm.get()
        best, worst, space = COMPLEXITY[name]
        avg = {
            "Quick Sort": "O(n log n)",
            "Merge Sort": "O(n log n)",
            "Heap Sort": "O(n log n)",
            "Counting Sort": "O(n + k)",
            "Radix Sort": "O(d(n + b))",
        }[name]
        self.complexity_labels["Best"].configure(text=best)
        self.complexity_labels["Average"].configure(text=avg)
        self.complexity_labels["Worst"].configure(text=worst)
        self.complexity_labels["Extra space"].configure(text=space)

    def _check_challenge(self):
        answer = self.challenge_answer.get()
        if answer == "Quick Sort":
            self.challenge_score += 1
            msg = "Correct! Quick Sort is often fast in practice on general arrays, though its worst case is O(n²)."
            color = GREEN
        else:
            msg = "Good try! Quick Sort is often a strong practical choice here. Try another algorithm and compare."
            color = ORANGE
        self.challenge_prompt.configure(text=msg, fg=color)
        self.challenge_result.configure(text=f"Score: {self.challenge_score}  •  Choose an algorithm and test it", fg=color)

def main():
    root = tk.Tk()
    app = SortQuestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
