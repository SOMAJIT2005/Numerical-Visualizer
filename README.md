# Numerical Analysis Suite
### C-Powered Numerical Computation — Desktop App for Windows

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-informational?style=for-the-badge&logo=windows" />
  <img src="https://img.shields.io/badge/license-Proprietary-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/type-Portable%20.exe-green?style=for-the-badge" />
</p>

> A visually rich, step-by-step numerical methods visualizer — powered by compiled C engines under the hood, with a modern Python GUI on top. Built for students and engineers who want to *see* the math happen in real time.

---

## ✨ Features at a Glance

- 🔍 **Root Finding Engine** — Solve f(x) = 0 with 8 classical algorithms, visualized step-by-step on an interactive graph
- 🧮 **Linear Systems Engine** — Solve N×N matrix systems with animated, color-coded row operations
- ⚡ **C-Powered Math** — All numerical computation runs in a compiled C engine for native-speed accuracy
- 🎨 **Dark & Light Mode** — Full theme toggle that repaints the entire UI and all graphs instantly
- 📊 **Live Equation Preview** — See your function curve update as you type, before running the solver
- ⌨️ **Keyboard Navigation** — Step through iterations with arrow keys or spacebar
- 🖱️ **Interactive Graphs** — Pan and zoom into any point of the result curve with mouse controls
- 🏆 **Trial + License System** — Ships with a 24-hour free trial; one-time key activation for permanent access

---

## 📥 Download & Run

> **No installation required.** This is a fully portable app — just download and double-click.

### Steps

1. Go to the [**Releases**](../../releases/latest) page of this repository
2. Under **Assets**, download **`NumericalSuite.exe`**
3. Place it anywhere on your PC (Desktop, USB drive, etc.)
4. **Double-click** `NumericalSuite.exe` to launch

That's it. No Python, no compilers, no setup needed.

> **Windows SmartScreen warning?**  
> Since this app is not code-signed, Windows may show a "Windows protected your PC" prompt.  
> Click **"More info"** → **"Run anyway"** to proceed. This is safe.

---

## 🖥️ System Requirements

| | |
|---|---|
| **OS** | Windows 10 or Windows 11 (64-bit) |
| **Disk Space** | ~50 MB |
| **RAM** | 256 MB minimum |
| **Display** | 1440 × 900 or higher recommended |
| **Dependencies** | None — everything is bundled inside the `.exe` |

---

## 🚀 Getting Started

When you first launch the app, a **24-hour free trial** begins automatically. You'll see the time remaining in the title bar.

### Navigation

The app opens on the **Dashboard**. From here, click either card to launch a module:

| Card | Module |
|---|---|
| 📈 **Root Finding Engine** | Find roots of single-variable equations |
| 🧮 **Linear Systems Engine** | Solve systems of linear equations |

Use the **← Back to Dashboard** button at the top-left of any module to return home. Toggle between **Dark Mode** and **Light Mode** using the button in the top-right corner at any time.

---

## 📈 Root Finding Engine — Usage Guide

### Step 1 — Configure the solver

| Field | What to enter |
|---|---|
| **Method** | Pick a bracketing or open method (see full list below) |
| **Tolerance (ε)** | Stopping criterion — e.g. `0.0001` means stop when error < 0.0001% |
| **Equation f(x)** | The equation to solve, written as an expression equal to zero — e.g. `x^3 - 2*x - 5` |
| **Point a / Point b** | *(Bracketing methods)* An interval where the root lies — f(a) and f(b) should have opposite signs |
| **Initial Guess (x0)** | *(Newton, Modified Newton)* A starting point close to the root |

A **live preview graph** on the right updates as you type your equation — use it to visually identify where roots are and pick good bracket values before running.

### Step 2 — Run the solver

Click **▶ CALCULATE**. The solver runs instantly and switches to the result view.

### Step 3 — Explore the results

```
[← BACK]  │ Current xr │ Approx Error │ True Error │ Target Root │
─────────────────────────────────────────────────────────────────
│                              │  Step │  xr    │  εa    │  εt   │
│   Interactive Graph          │   0   │  1.000 │  0%    │  ...  │
│                              │   1   │  1.521 │  34%   │  ...  │
│   (scroll to zoom,           │   2   │  1.503 │  1.2%  │  ...  │
│    drag to pan)              │   3   │  1.521 │  0.06% │  ...  │
│   X: ---  │  Y: ---          │                               │
```

- Click any **row in the table** to jump directly to that iteration
- Use **← → arrow keys** or **Space** to step through iterations one at a time
- **Scroll** on the graph to zoom in/out; **click and drag** to pan

### Supported Methods

**Bracketing** *(require an interval [a, b])*

| Method | Best used when |
|---|---|
| **Bisection** | You need a guaranteed, simple result |
| **False Position** | Faster convergence on smooth functions |
| **Brent's Method** | Best all-around — fast and robust |

**Open Methods** *(require only a starting point)*

| Method | Best used when |
|---|---|
| **Newton-Raphson** | Function is smooth; fastest convergence |
| **Modified Newton** | Equation has repeated (multiple) roots |
| **Secant** | Derivative is hard to compute analytically |
| **Modified Secant** | Similar to Secant but only one starting point needed |
| **Fixed-Point Iteration** | Equation is rearranged as x = g(x) |

---

## 🧮 Linear Systems Engine — Usage Guide

### Step 1 — Configure the system

1. Select a **Solver Method** from the radio buttons
2. Set the **Matrix Size** using the `+` / `−` buttons (supports 2×2 up to 5×5)
3. *(Gauss-Seidel only)* Set the **Tolerance** and **Max Iterations**

### Step 2 — Enter your matrix

The grid on the right represents the augmented matrix **[ A | b ]** for your system Ax = b.

- Click any cell and type a value
- The vertical dashed line separates matrix **A** (coefficients) from vector **b** (constants)
- The grid pre-fills with an identity matrix as a starting example

### Step 3 — Solve and explore

Click **▶ SOLVE SYSTEM**. The result screen shows every row operation performed, step by step.

```
[← BACK]   Step 2: Eliminated Row 2 using Row 1
┌──────────────────────────────┬───────────────────────────┐
│                              │  Step │ Row Operation      │
│   Animated Matrix Display    │   0   │ Initial State      │
│                              │   1   │ R2 → R2 − 2.00 R1  │
│   Color-coded cells          │   2   │ R3 → R3 − 1.50 R1  │
│                              │   3   │ Back-Sub: x₃ = 1.0 │
└──────────────────────────────┴───────────────────────────┘
```

**Cell color guide:**

| Color | Meaning |
|---|---|
| 🔵 Cyan | Standard matrix value |
| 🟡 Amber | Diagonal (pivot) element |
| 🟢 Green | Constant vector b |
| 🔴 Red highlight | Value that changed in this step |

- Click any **row in the table** to view that matrix state
- Use **← → arrow keys** or **Space** to step through operations

### Supported Solvers

| Method | Type | Notes |
|---|---|---|
| **Gaussian Elimination** | Direct | Upper-triangular reduction + back-substitution. Uses partial pivoting. |
| **Gauss-Jordan** | Direct | Full reduction to identity — no back-substitution needed |
| **LU Decomposition** | Direct | Factors A = LU; shows forward and back substitution phases separately |
| **Gauss-Seidel** | Iterative | Best for large, diagonally dominant systems |

---

## ✏️ Equation Syntax Reference

| Operation | Syntax | Example |
|---|---|---|
| Multiply | `*` | `2*x + 1` |
| Power | `^` | `x^3` |
| Square root | `sqrt(...)` | `sqrt(x) - 2` |
| Trig functions | `sin`, `cos`, `tan` | `sin(x) - x/2` |
| Exponential | `e^x` or `exp(x)` | `e^(-x) - x` |
| Natural log | `log(x)` | `log(x) - 1` |
| Constants | `pi`, `e` | `sin(pi*x)` |

**Quick examples to try:**

```
x^3 - 2*x - 5          → A classic cubic
e^(-x) - x             → Exponential equation
sin(x) - x^2 + 1       → Trigonometric
log(x) - cos(x)        → Mixed transcendental
x^4 - 3*x^2 + 2        → Polynomial with multiple roots
```

> ⚠️ Always use `*` for multiplication. `2x` is invalid — write `2*x`.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `→` Right Arrow | Advance to the next iteration step |
| `←` Left Arrow | Go back to the previous step |
| `Space` | Advance to the next iteration step |

---

## 🔑 Trial & Activation

The app ships with a **24-hour free trial**. Remaining time is shown in the window title bar.

Once the trial expires, an **Activation Gate** will appear on next launch. Enter a valid license key to unlock the app permanently — no internet connection required, validation is done locally.

> To request a license key, open an issue or check the pinned post in the [Discussions](../../discussions) tab of this repository.

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| **Windows blocks the app** | Click **"More info"** → **"Run anyway"** on the SmartScreen prompt |
| **Graph is blank after Calculate** | Check your equation syntax — use the live preview to confirm the curve looks correct |
| **"Invalid equation syntax" error** | Use `*` for multiplication (e.g. `2*x` not `2x`) |
| **Gauss-Seidel diverges** | Rearrange equations so the diagonal element in each row is larger than the sum of all other entries in that row |
| **"Zero pivot" error in matrix solver** | Your system may have no unique solution — verify the matrix is not singular |
| **App won't open at all** | Confirm you're on 64-bit Windows 10/11. Try right-clicking → **"Run as administrator"** |

---

## 👨‍💻 Developer

**Somajit Deb**  
B.Sc. in Computer Science & Engineering — Khulna University

---

## 📄 License

This software is proprietary. Redistribution or modification of the executable or source code without explicit written consent from the developer is not permitted. The free trial is provided for personal evaluation only.

---

<p align="center">If this tool helped you, consider leaving a ⭐ on the repository!</p>
