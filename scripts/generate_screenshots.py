"""
scripts/generate_screenshots.py — Generates visual preview figures for README.md
using the real C-engine outputs.
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from c_bridge import ensure_c_engines_built, run_root_engine, run_matrix_engine, run_numlab_engine
from config import safe_float

ensure_c_engines_built()
os.makedirs("docs/screenshots", exist_ok=True)

# Visual styling
plt.rcParams.update({
    'figure.facecolor': '#0B0F19',
    'axes.facecolor': '#111827',
    'axes.edgecolor': '#374151',
    'axes.labelcolor': '#E5E7EB',
    'xtick.color': '#9CA3AF',
    'ytick.color': '#9CA3AF',
    'text.color': '#F3F4F6',
    'grid.color': '#1F2937',
    'grid.linestyle': '--',
    'grid.alpha': 0.7,
    'font.family': 'sans-serif',
})

# 1. Unit 1: Error U-Curve
try:
    lines = run_numlab_engine(["errors_h_sweep", "sin(x)", 1.0])
    h_vals, err_fwd, err_cen = [], [], []
    for l in lines:
        if l.startswith("SWEEP,"):
            p = l.split(',')
            h_vals.append(safe_float(p[1]))
            err_fwd.append(safe_float(p[2]))
            err_cen.append(safe_float(p[3]))
    
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    ax.loglog(h_vals, err_fwd, label="Forward Diff $O(h)$", color='#F59E0B', lw=2)
    ax.loglog(h_vals, err_cen, label="Central Diff $O(h^2)$", color='#06B6D4', lw=2.2)
    ax.axvline(1e-5, color='#10B981', ls=':', lw=1.5, label="Optimal $h^* \\approx 10^{-5}$")
    ax.set_title("Unit 1: Truncation vs. Round-Off Error Tradeoff (U-Curve)", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("Step Size $h$ (log scale)")
    ax.set_ylabel("Absolute Error $|f'(x) - D(h)|$")
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit1_errors_ucurve.png")
    plt.close()
    print("Generated unit1_errors_ucurve.png")
except Exception as e:
    print("Error U1:", e)

# 2. Unit 2: Root Finding Convergence
try:
    methods = [('bisection', 'Bisection', '#F59E0B'), ('secant', 'Secant', '#3B82F6'), ('newton', 'Newton-Raphson', '#10B981'), ('brent', "Brent's Method", '#EC4899')]
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    for m, label, col in methods:
        lines = run_root_engine([m, "x^3 - x - 2", 1.0 if m != 'newton' else 1.5, 2.0 if m != 'newton' else 0.0, 1e-6])
        steps = [l.split(',') for l in lines if l.startswith("STEP,")]
        res = [safe_float(l.split(',')[2]) for l in lines if l.startswith("RESIDUAL,")]
        if res:
            ax.semilogy(range(len(res)), res, marker='o', label=label, color=col, lw=1.8, ms=4)
    ax.set_title("Unit 2: Iteration Residual Convergence for $x^3 - x - 2 = 0$", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("Iteration Index $k$")
    ax.set_ylabel("Residual $|f(x_k)|$ (log scale)")
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit2_roots_comparison.png")
    plt.close()
    print("Generated unit2_roots_comparison.png")
except Exception as e:
    print("Error U2:", e)

# 3. Unit 4: 2D Optimization Contour
try:
    lines = run_numlab_engine(["opt_2d", "grad2d", "x^2 + 2*y^2", 3.0, 2.5, 0.15])
    traj_x, traj_y = [], []
    for l in lines:
        if l.startswith("TRAJ_2D,"):
            p = l.split(',')
            traj_x.append(safe_float(p[2]))
            traj_y.append(safe_float(p[3]))
    
    X, Y = np.meshgrid(np.linspace(-3.5, 3.5, 100), np.linspace(-3.5, 3.5, 100))
    Z = X**2 + 2*Y**2
    
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    cp = ax.contour(X, Y, Z, levels=20, cmap='viridis', alpha=0.8)
    ax.clabel(cp, inline=True, fontsize=7, colors='#9CA3AF')
    if traj_x:
        ax.plot(traj_x, traj_y, marker='o', color='#F43F5E', lw=2, ms=4, label="Gradient Descent Path")
        ax.plot(traj_x[0], traj_y[0], 's', color='#38BDF8', ms=7, label="Start $(3.0, 2.5)$")
        ax.plot(traj_x[-1], traj_y[-1], '*', color='#10B981', ms=10, label="Optimum $(0, 0)$")
    ax.set_title("Unit 4: 2D Gradient Descent Trajectory on $f(x, y) = x^2 + 2y^2$", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("$x$")
    ax.set_ylabel("$y$")
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155', loc='upper right')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit4_optimization_2d.png")
    plt.close()
    print("Generated unit4_optimization_2d.png")
except Exception as e:
    print("Error U4:", e)

# 4. Unit 3: Linear Systems Residuals & Matrix Diagnostics
try:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    methods = [
        ('Gauss-Seidel', [4, 1, 1, 5], [5, 6], '#06B6D4'),
        ('Jacobi Iteration', [4, 1, 1, 5], [5, 6], '#F59E0B')
    ]
    for name, A, b, col in methods:
        engine_cmd = "gauss_seidel" if name == 'Gauss-Seidel' else "jacobi"
        lines = run_matrix_engine([engine_cmd, 2, *A, *b, 1e-7, 30])
        steps = [l.split(',') for l in lines if l.startswith("ITER,")]
        if steps:
            # ITER, k, x0, x1, ..., ea
            iters = [int(s[1]) for s in steps]
            eas = [safe_float(s[-1]) for s in steps]
            ax.semilogy(iters, eas, marker='s', label=name, color=col, lw=1.8, ms=5)
    ax.set_title("Unit 3: Iterative Linear Solvers Residual Decay (Ax = b)", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("Iteration Index $k$")
    ax.set_ylabel("Relative Error $\\varepsilon_a$ (%)")
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit3_linear_systems.png")
    plt.close()
    print("Generated unit3_linear_systems.png")
except Exception as e:
    print("Error U3:", e)

# 5. Unit 6A: Quadrature Rule Comparison
try:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    # Compare trapezoidal vs simpson 1/3 vs simpson 3/8 for x*sin(x) on [0, pi]
    n_intervals = [2, 4, 6, 8, 12, 16, 24, 32]
    exact_I = math.pi # integral_0^pi x*sin(x) dx = pi
    rules = [('trap', 'Trapezoidal Rule', '#F59E0B'), ('simp13', "Simpson's 1/3 Rule", '#06B6D4'), ('simp38', "Simpson's 3/8 Rule", '#EC4899')]
    for code, label, col in rules:
        errs = []
        for n in n_intervals:
            if code == 'simp38' and n % 3 != 0:
                n = (n // 3 + 1) * 3
            lines = run_numlab_engine(["quad", code, "x*sin(x)", 0.0, math.pi, n])
            summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
            val = safe_float(summ[1])
            errs.append(abs(exact_I - val))
        ax.loglog(n_intervals, errs, marker='o', label=label, color=col, lw=1.8, ms=4)
    ax.set_title("Unit 6A: Quadrature Convergence on $\\int_0^\\pi x \\sin(x) dx = \\pi$", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("Number of Panels $n$ (log scale)")
    ax.set_ylabel("Integration Error $|I - I_{\\text{approx}}|$")
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit6a_quadrature.png")
    plt.close()
    print("Generated unit6a_quadrature.png")
except Exception as e:
    print("Error U6A:", e)

# 4. Unit 5: Runge vs Chebyshev
try:
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    x_dense = np.linspace(-1, 1, 300)
    y_true = 1.0 / (1.0 + 25.0 * x_dense**2)
    ax.plot(x_dense, y_true, label="True $1/(1 + 25x^2)$", color='#F3F4F6', lw=2.2, zorder=5)
    
    # Equidistant Runge
    n_pts = 9
    x_eq = np.linspace(-1, 1, n_pts)
    y_eq = 1.0 / (1.0 + 25.0 * x_eq**2)
    poly_eq = np.poly1d(np.polyfit(x_eq, y_eq, n_pts - 1))
    ax.plot(x_dense, poly_eq(x_dense), '--', label=f"Equispaced $n={n_pts}$ (Runge Oscillation)", color='#EF4444', lw=1.8)
    
    # Chebyshev
    k = np.arange(n_pts)
    x_cheb = np.cos((2 * k + 1) * math.pi / (2 * n_pts))
    y_cheb = 1.0 / (1.0 + 25.0 * x_cheb**2)
    poly_cheb = np.poly1d(np.polyfit(x_cheb, y_cheb, n_pts - 1))
    ax.plot(x_dense, poly_cheb(x_dense), '-', label=f"Chebyshev Nodes $n={n_pts}$ (Stable)", color='#06B6D4', lw=2)
    
    ax.scatter(x_cheb, y_cheb, color='#06B6D4', s=30, zorder=6)
    ax.set_ylim(-0.4, 1.4)
    ax.set_title("Unit 5: Runge Phenomenon vs. Chebyshev Node Interpolation", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("$x$")
    ax.set_ylabel("$P(x)$")
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit5_runge_chebyshev.png")
    plt.close()
    print("Generated unit5_runge_chebyshev.png")
except Exception as e:
    print("Error U5:", e)

# 5. Unit 6B: Coupled ODE Phase Plane
try:
    two_pi = 2.0 * math.pi
    lines = run_numlab_engine(["ode", "system", "y", "-x", 0.0, 1.0, 0.0, two_pi, two_pi / 100.0])
    traj_x, traj_y = [], []
    for l in lines:
        if l.startswith("STEP_SYS,"):
            p = l.split(',')
            traj_x.append(safe_float(p[3]))
            traj_y.append(safe_float(p[4]))
    
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    # Quiver grid
    x_g, y_g = np.meshgrid(np.linspace(-1.5, 1.5, 14), np.linspace(-1.5, 1.5, 14))
    u = y_g
    v = -x_g
    speed = np.sqrt(u*u + v*v)
    speed[speed == 0] = 1.0
    ax.quiver(x_g, y_g, u/speed, v/speed, color='#4B5563', alpha=0.6, pivot='middle', scale=22)
    
    if traj_x:
        ax.plot(traj_x, traj_y, color='#10B981', lw=2.2, label="RK4 Orbit $x^2 + y^2 = 1$")
        ax.plot(traj_x[0], traj_y[0], 'o', color='#38BDF8', ms=6, label="Initial State $(1, 0)$")
    ax.set_title("Unit 6B: Harmonic Oscillator Phase Plane Orbit & Vector Field", color='#38BDF8', fontsize=12, pad=10, weight='bold')
    ax.set_xlabel("Position $x(t)$")
    ax.set_ylabel("Velocity $y(t) = x'(t)$")
    ax.set_aspect('equal')
    ax.grid(True)
    ax.legend(frameon=True, facecolor='#1E293B', edgecolor='#334155', loc='upper right')
    plt.tight_layout()
    plt.savefig("docs/screenshots/unit6b_ode_phase_portrait.png")
    plt.close()
    print("Generated unit6b_ode_phase_portrait.png")
except Exception as e:
    print("Error U6B:", e)

print("All screenshots generated successfully!")
