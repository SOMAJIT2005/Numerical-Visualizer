# Numerical Analysis Suite — Complete 6-Unit Learning Lab
### C-Powered Numerical Computation & Visual Learning Platform for Windows

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-informational?style=for-the-badge&logo=windows" />
  <img src="https://img.shields.io/badge/backend-100%25%20C%20Engines-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" />
</p>

> A comprehensive, step-by-step **6-Unit Numerical Methods Learning Lab** powered 100% by compiled C engines (`build/engine.exe`, `build/matrix_engine.exe`, `build/numlab_engine.exe`) with an interactive Python/Tkinter + Matplotlib desktop UI. Built for students and engineers with **full open access** (no trial timers or activation locks).

---

## ✨ Complete 6-Unit Syllabus Coverage (All Math Computed in C)

### 🔬 Unit 1 (CLO 1): Numerical Approximations & Round-Off Errors
- **Step-Size ($h$) Truncation vs. Round-Off U-Curve**: Sweeps $h \in [10^{-16}, 10^0]$ in C (`errors_h_sweep`) comparing forward, backward, central, and 2nd-order finite differences.
- **Taylor Polynomial Approximation**: Builds degree-$n$ Taylor polynomials in C (`errors_taylor`) with term-by-term truncation remainder tracking.
- **Catastrophic Cancellation Lab**: Contrasts naive $\sqrt{x^2+1}-x$ against rationalized $\frac{1}{\sqrt{x^2+1}+x}$ across $x = 10^0 \dots 10^8$ (`errors_cancellation`).
- **IEEE-754 64-Bit Float Inspector**: Extracts exact 64-bit sign, 11-bit biased exponent, 52-bit mantissa, machine epsilon $\varepsilon_{\text{mach}}$, ULP gap, and Scarborough tolerances in C (`errors_ieee754`).

### 📈 Unit 2 (CLO 2, 3, 4, 5): Roots of Equations & Polynomials (`build/engine.exe`)
- **Bracketing Methods**: Bisection, False Position (Regula Falsi), and Brent's Method with central bracket, continuity/pole, and domain validation.
- **Open Methods**: Newton-Raphson, Modified Newton (for multiple roots), Secant, Modified Secant, and Fixed-Point Iteration ($x = g(x)$ cobweb plot).
- **Horner's Method & Polynomial Root Deflation**: Nested synthetic division for $P(x_0)$, $P'(x_0)$, deflated quotient $Q(x)$, and all real/complex polynomial roots in C (`horner`).

### 🧮 Unit 3 (CLO 2, 3, 4, 5): Linear Systems, Matrix Inversion & Special Matrices (`build/matrix_engine.exe`)
- **Direct Solvers**: Gaussian Elimination with partial pivoting, Gauss-Jordan RREF, and $PA = LU$ Factorization with forward/back substitution.
- **Iterative Solver**: Gauss-Seidel relaxation with diagonal dominance diagnostics and $\lVert Ax - b\rVert_\infty$ residual verification.
- **Matrix Inversion Lab**: Animated $[A \mid I] \to [I \mid A^{-1}]$ reduction with $\lVert AA^{-1} - I\rVert_\infty$ verification.
- **Special Matrices & Diagnostics**: $\det(A)$, $\kappa_\infty(A)$, Symmetry, Diagonal Dominance, and Sylvester's criterion for **Symmetric Positive Definite (SPD)** matrices, plus presets for Textbook, Diagonally Dominant, SPD, Upper Triangular, Hilbert Ill-Conditioned, and Identity matrices.

### 🎯 Unit 4 (CLO 1, 2): 1D & 2D Unconstrained Optimization (`build/numlab_engine.exe`)
- **1D Optimization**: Golden-Section Search, Successive Parabolic Interpolation, and 1D Newton Optimization with $f''(x^*)$ classification.
- **2D Multivariable Optimization**: Steepest Gradient Descent and 2D Newton Optimization on a 40×40 C-evaluated contour grid with Hessian eigenvalue ($\lambda_1, \lambda_2, \det H$) classification of Local Minima, Maxima, and Saddle Points.

### 📐 Unit 5 & Unit 3: Polynomial Interpolation & Least-Squares Regression (`build/numlab_engine.exe`)
- **Newton's Divided-Difference Table** & nested polynomial evaluation.
- **Lagrange Interpolation** basis polynomials $L_i(x)$ and weighted sum.
- **Interpolating Polynomial Coefficients** in standard power basis $c_0 + c_1 x + \dots + c_n x^n$ with Vandermonde conditioning $\kappa_\infty(V)$.
- **Inverse Interpolation** $x = P^{-1}(y^*)$ with strict monotonicity validation.
- **Ordinary Least-Squares (OLS) Linear & Polynomial Regression** with $S_r$ (SSE), $s_{y/x}$, and $R^2$.

### ∫ Unit 6A (CLO 2, 3, 4, 5): Numerical Integration / Quadrature (`build/numlab_engine.exe`)
- **Newton-Cotes Rules**: Composite Trapezoidal, Simpson's 1/3 Rule, Simpson's 3/8 Rule, and Boole's Rule ($n$ auto-adjusted to valid multiples).
- **Romberg Integration**: Richardson extrapolation tableau $R(k, j)$ up to $O(h^8)$.
- **Gauss-Legendre Quadrature**: 2-, 3-, 4-, and 5-point optimal interior nodes mapped from $[-1, 1]$ to $[a, b]$.

### ⚡ Unit 6B (CLO 2, 3, 4, 5): Ordinary Differential Equations (`build/numlab_engine.exe`)
- **Scalar IVP Solvers**: Euler's Method, Heun's Predictor-Corrector, Midpoint RK2, and Classical 4th-Order Runge-Kutta (RK4) with full stage slopes ($k_1, k_2, k_3, k_4$) and C-computed quiver slope fields.
- **Coupled 2D ODE Systems**: Vector RK4 solver for $\frac{dx}{dt} = f(t,x,y), \frac{dy}{dt} = g(t,x,y)$ with time-series and $(x, y)$ phase-plane portraits.

### ⚖ Method Comparison Lab & 🎯 Practice Quiz
- **Method Comparison Lab**: Benchmarks Root Solvers, Quadrature Rules, or ODE Solvers side-by-side on the same problem using the C engines.
- **Exam Practice & Self-Test Quiz**: Interactive numerical problems across all 6 units verified live by the C engines with formula hints.

---

## 🛠️ Building & Testing from Source

### 1. Compile the 3 C Engines
```powershell
make
# Or auto-compile via Python bridge:
python -c "from c_bridge import ensure_c_engines_built; print(ensure_c_engines_built(force=True))"
```

### 2. Run the Automated Test Suite
```powershell
python -m unittest discover -s tests -p "test_suite.py" -v
```

### 3. Launch the Desktop Application
```powershell
python main.py
```

---

## 👨‍💻 Developer

**Somajit Deb**  
B.Sc. in Computer Science & Engineering — Khulna University

---

## 📄 License

Licensed under the [MIT License](LICENSE). Free for students, educators, and academic use.
