# SortQuest — Interactive Sorting Algorithm Studio

A desktop sorting visualizer made with Python, Tkinter, and Matplotlib.

## Features
- Quick Sort, Merge Sort, Heap Sort, Counting Sort, and Radix Sort
- Animated bar visualization with active and finalized elements highlighted
- Run, pause, step forward, step backward, reset, and speed control
- Random, nearly sorted, reversed, and few-unique-value datasets
- Comparison, write, swap counters and an elapsed-time indicator
- Complexity cheat sheet and a simple interactive challenge

## Run it
Python 3.10+ recommended.

```bash
python -m pip install -r requirements.txt
python sortquest.py
```

Tkinter is included with most standard Python installations. On some Linux distributions, install the system Tk package (for example, `python3-tk`) if Tkinter is missing.

## Notes
- Counting Sort is designed for integer arrays with a manageable value range.
- Radix Sort in this demo accepts non-negative integers.
- Operation counters are algorithm-specific educational metrics, not a universal speed score.
- The elapsed time shown measures generation of the visualization steps, not a rigorous benchmark of the sorting implementation.
