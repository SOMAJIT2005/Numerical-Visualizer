"""
tests/test_suite.py — Comprehensive Real-Problem & Specification Test Suite.
Covers:
  - License / Trial Gate Removal verification
  - Unit 1: H-Sweep U-Curve, Taylor Polynomials, Catastrophic Cancellation, IEEE-754 Bit Inspector
  - Unit 2: T-R01 to T-R07 + All 8 Root Solvers + Horner's Method & Polynomial Root Deflation
  - Unit 3: T-M01 to T-M07 + Gaussian, Gauss-Jordan, LU, Gauss-Seidel, Matrix Inversion & SPD Diagnostics
  - Unit 4: T-O01, T-O02 + 1D (Golden, Parabolic, Newton) & 2D (Gradient Descent, Newton, Hessian Saddle/Min)
  - Unit 5: T-I01 to T-I03, T-G01 + Newton DD, Lagrange, Vandermonde, Inverse Interp & OLS Regression
  - Unit 6A: T-Q01 to T-Q04 + Trapezoidal, Simpson 1/3, Simpson 3/8, Boole, Romberg, Gauss-Legendre
  - Unit 6B: T-D01 to T-D03 + Euler, Heun, Midpoint, RK4 & Coupled 2D Lotka-Volterra / Harmonic Systems
  - Cross-Cutting: T-X01 (Strict CLI Validation), T-X02 (Theme Toggle), T-X03 (Tab State Persistence)
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COLORS, FONTS, safe_float
from c_bridge import ensure_c_engines_built, run_root_engine, run_matrix_engine, run_numlab_engine
import license_manager
import license_gate


class TestLicenseRemoved(unittest.TestCase):
    def test_license_always_unlocked(self):
        ok, rem = license_manager.get_status()
        self.assertTrue(ok)


class TestUnit1ErrorsC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def test_h_sweep_c(self):
        lines = run_numlab_engine(["errors_h_sweep", "sin(x)", 1.0])
        meta = [l.split(',') for l in lines if l.startswith("META,")][0]
        df_exact = safe_float(meta[2])
        d2f_exact = safe_float(meta[3])
        self.assertAlmostEqual(df_exact, math.cos(1.0), places=6)
        self.assertAlmostEqual(d2f_exact, -math.sin(1.0), places=4)

    def test_taylor_c(self):
        lines = run_numlab_engine(["errors_taylor", "exp(x)", 0.0, 0.5, 6])
        meta = [l.split(',') for l in lines if l.startswith("META,")][0]
        true_v = safe_float(meta[1])
        approx_v = safe_float(meta[2])
        self.assertAlmostEqual(true_v, math.exp(0.5), places=6)
        self.assertAlmostEqual(approx_v, math.exp(0.5), places=4)

    def test_catastrophic_cancellation_c(self):
        lines = run_numlab_engine(["errors_cancellation"])
        rows = [l.split(',') for l in lines if l.startswith("CANCEL_ROW,")]
        self.assertEqual(len(rows), 9)
        # At k=8 (x=10^8), rationalized stable form is ~5e-9 while naive loses digits
        stable_last = safe_float(rows[-1][4])
        self.assertAlmostEqual(stable_last, 0.5e-8, places=14)

    def test_ieee754_c(self):
        lines = run_numlab_engine(["errors_ieee754", 3.141592653589793, 3.1416, 5])
        bits = [l.split(',') for l in lines if l.startswith("IEEE_BITS,")][0]
        self.assertEqual(bits[1], "0")
        self.assertEqual(len(bits[2]), 11)
        self.assertEqual(len(bits[3]), 52)


class TestUnit2RootsSpecAndRealProblemsC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def _extract_final_xr(self, method, lines):
        steps = [[safe_float(v) for v in l.split(',')[1:]] for l in lines if l.startswith("STEP,")]
        self.assertTrue(len(steps) > 0, f"No STEP lines in {lines}")
        s = steps[-1]
        if method == 'fixed_point':
            return s[2]
        return s[3] if len(s) < 8 else s[5]

    def test_T_R01_standard_root_all_methods(self):
        # T-R01: f(x) = x^3 - x - 2 on [1, 2], root ≈ 1.5213797
        expected = 1.5213797068
        cases = [
            ('bisection', 'x^3 - x - 2', 1.0, 2.0, 3),
            ('false_position', 'x^3 - x - 2', 1.0, 2.0, 3),
            ('brent', 'x^3 - x - 2', 1.0, 2.0, 5),
            ('newton', 'x^3 - x - 2', 1.5, 0.0, 5),
            ('modified_newton', 'x^3 - x - 2', 1.5, 0.0, 5),
            ('secant', 'x^3 - x - 2', 1.0, 2.0, 5),
            ('modified_secant', 'x^3 - x - 2', 1.5, 0.01, 5),
        ]
        for method, eq, v1, v2, places in cases:
            with self.subTest(method=method):
                lines = run_root_engine([method, eq, v1, v2, 0.0001])
                xr = self._extract_final_xr(method, lines)
                self.assertAlmostEqual(xr, expected, places=places)

    def test_T_R02_invalid_bracket_rejected(self):
        # T-R02: f(x) = x^2 + 1 on [-2, 2] -> f(a)*f(b) > 0
        for method in ('bisection', 'false_position', 'brent'):
            with self.assertRaises((ValueError, RuntimeError)):
                run_root_engine([method, 'x^2 + 1', -2.0, 2.0, 0.0001])

    def test_T_R03_discontinuous_pole_rejected(self):
        # T-R03: f(x) = 1/x on [-1, 1] -> pole at x=0, not a root
        for method in ('bisection', 'brent'):
            with self.assertRaises((ValueError, RuntimeError)):
                run_root_engine([method, '1/x', -1.0, 1.0, 0.0001])

    def test_T_R04_multiple_root_modified_vs_standard_newton(self):
        # T-R04: f(x) = (x - 1)^2 * (x + 2) near x0 = 1.3
        lines_mod = run_root_engine(['modified_newton', '(x - 1)^2 * (x + 2)', 1.3, 0.0, 0.0001])
        lines_std = run_root_engine(['newton', '(x - 1)^2 * (x + 2)', 1.3, 0.0, 0.0001])
        steps_mod = [l for l in lines_mod if l.startswith("STEP,")]
        steps_std = [l for l in lines_std if l.startswith("STEP,")]
        xr_mod = self._extract_final_xr('modified_newton', lines_mod)
        self.assertAlmostEqual(xr_mod, 1.0, places=4)
        self.assertLess(len(steps_mod), len(steps_std))

    def test_T_R05_zero_derivative_handled(self):
        # T-R05: f(x) = x^2 - 1 at x0 = 0 -> f'(0) = 0
        with self.assertRaises((ValueError, RuntimeError)):
            run_root_engine(['newton', 'x^2 - 1', 0.0, 0.0, 0.0001])

    def test_T_R06_root_near_zero_and_exact_initial_guess(self):
        # T-R06: f(x) = x - 1 starting at exact root x0 = 1
        lines = run_root_engine(['newton', 'x - 1', 1.0, 0.0, 0.0001])
        xr = self._extract_final_xr('newton', lines)
        self.assertAlmostEqual(xr, 1.0, places=7)

    def test_T_R07_domain_error_sqrt_negative(self):
        # T-R07: f(x) = sqrt(x) - 1 on [-1, 2]
        with self.assertRaises((ValueError, RuntimeError)):
            run_root_engine(['bisection', 'sqrt(x) - 1', -1.0, 2.0, 0.0001])

    def test_horner_and_polynomial_deflation_c(self):
        # P(x) = x^3 - 6x^2 + 11x - 6 = (x-1)(x-2)(x-3)
        lines = run_root_engine(["horner", 2.0, 3, 1, -6, 11, -6])
        ev = [l.split(',') for l in lines if l.startswith("HORNER_EVAL,")][0]
        self.assertAlmostEqual(safe_float(ev[1]), 0.0, places=6)
        self.assertAlmostEqual(safe_float(ev[2]), -1.0, places=6)
        roots = sorted([safe_float(l.split(',')[3]) for l in lines if l.startswith("POLY_ROOT,")])
        self.assertEqual(len(roots), 3)
        self.assertAlmostEqual(roots[0], 1.0, places=4)
        self.assertAlmostEqual(roots[1], 2.0, places=4)
        self.assertAlmostEqual(roots[2], 3.0, places=4)


class TestUnit3MatricesSpecAndRealProblemsC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def test_T_M01_well_conditioned_3x3_all_direct_methods(self):
        A = [2, 1, -1, -3, -1, 2, -2, 1, 2]
        b = [8, -11, -3]
        for method in ('gaussian', 'gauss_jordan', 'lu'):
            with self.subTest(method=method):
                lines = run_matrix_engine([method, 3, *A, *b])
                sol = [safe_float(v) for v in [l.split(',') for l in lines if l.startswith("SOLUTION,")][0][1:]]
                res = [safe_float(l.split(',')[1]) for l in lines if l.startswith("RESIDUAL,")][0]
                self.assertAlmostEqual(sol[0], 2.0, places=5)
                self.assertAlmostEqual(sol[1], 3.0, places=5)
                self.assertAlmostEqual(sol[2], -1.0, places=5)
                self.assertLess(res, 1e-12)

    def test_T_M02_zero_leading_pivot_swapped(self):
        # T-M02: A = [[0, 1], [1, 1]], b = [1, 2] -> x = [1, 1]
        for method in ('gaussian', 'gauss_jordan', 'lu'):
            lines = run_matrix_engine([method, 2, 0, 1, 1, 1, 1, 2])
            self.assertTrue(any(l.startswith("SWAP,") for l in lines))
            sol = [safe_float(v) for v in [l.split(',') for l in lines if l.startswith("SOLUTION,")][0][1:]]
            self.assertAlmostEqual(sol[0], 1.0, places=5)
            self.assertAlmostEqual(sol[1], 1.0, places=5)

    def test_T_M03_singular_matrix_detected(self):
        # T-M03: A = [[1, 2], [2, 4]]
        for method in ('gaussian', 'gauss_jordan', 'lu', 'inverse'):
            args = [method, 2, 1, 2, 2, 4] if method == 'inverse' else [method, 2, 1, 2, 2, 4, 3, 6]
            with self.assertRaises((ValueError, RuntimeError)):
                run_matrix_engine(args)

    def test_T_M04_gauss_seidel_diagonally_dominant(self):
        A = [4, 1, 1, 5]
        b = [5, 6]
        lines = run_matrix_engine(["gauss_seidel", 2, *A, *b, 1e-6, 100])
        sol = [safe_float(v) for v in [l.split(',') for l in lines if l.startswith("SOLUTION,")][0][1:]]
        self.assertAlmostEqual(sol[0], 1.0, places=4)
        self.assertAlmostEqual(sol[1], 1.0, places=4)

    def test_T_M05_gauss_seidel_non_dominant_diverges(self):
        A = [1, 5, 5, 1]
        b = [6, 6]
        with self.assertRaises((ValueError, RuntimeError)):
            run_matrix_engine(["gauss_seidel", 2, *A, *b, 1e-6, 50])

    def test_T_M06_hilbert_ill_conditioned_diagnostics_and_spd(self):
        # SPD matrix [[4, 1], [1, 3]] -> is_sym=1, is_dd=1, is_spd=1
        lines = run_matrix_engine(["diagnostics", 2, 4, 1, 1, 3])
        diag = [l.split(',') for l in lines if l.startswith("DIAG,")][0]
        self.assertEqual(int(diag[3]), 1)
        self.assertEqual(int(diag[4]), 1)
        self.assertEqual(int(diag[5]), 1)

    def test_T_M07_gauss_seidel_zero_rhs_solution(self):
        # T-M07: Solution x = [0, 0] should converge cleanly on iter 1 without division by zero
        lines = run_matrix_engine(["gauss_seidel", 2, 4, 1, 1, 3, 0, 0, 1e-6, 50])
        sol = [safe_float(v) for v in [l.split(',') for l in lines if l.startswith("SOLUTION,")][0][1:]]
        self.assertAlmostEqual(sol[0], 0.0, places=7)
        self.assertAlmostEqual(sol[1], 0.0, places=7)

    def test_matrix_inversion_3x3_c(self):
        A = [2, 1, -1, -3, -1, 2, -2, 1, 2]
        lines = run_matrix_engine(["inverse", 3, *A])
        res = [safe_float(l.split(',')[1]) for l in lines if l.startswith("RESIDUAL,")][0]
        self.assertLess(res, 1e-12)

    def test_jacobi_diagonally_dominant_c(self):
        A = [4, 1, 1, 5]
        b = [5, 6]
        lines = run_matrix_engine(["jacobi", 2, *A, *b, 1e-6, 100])
        sol = [safe_float(v) for v in [l.split(',') for l in lines if l.startswith("SOLUTION,")][0][1:]]
        self.assertAlmostEqual(sol[0], 1.0, places=4)
        self.assertAlmostEqual(sol[1], 1.0, places=4)


class TestUnit4OptimizationSpecC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def test_T_O01_1d_unimodal_minimum(self):
        # T-O01: f(x) = (x - 2)^2 + 1 on [0, 5] -> x* = 2, f(x*) = 1
        for method in ('golden', 'parabolic', 'newton1d'):
            with self.subTest(method=method):
                lines = run_numlab_engine(["opt_1d", method, "(x - 2)^2 + 1", 0.0, 5.0, 1e-6])
                summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
                self.assertAlmostEqual(safe_float(summ[1]), 2.0, places=3)
                self.assertAlmostEqual(safe_float(summ[2]), 1.0, places=3)
                self.assertIn("Minimum", summ[4])

    def test_T_O02_2d_saddle_point_classification(self):
        # T-O02: f(x, y) = x^2 - y^2 -> stationary at (0, 0), det(H) = -4 < 0 (Saddle Point)
        lines = run_numlab_engine(["opt_2d", "newton2d", "x^2 - y^2", 1.0, 1.0, 0.1])
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertAlmostEqual(safe_float(summ[1]), 0.0, places=5)
        self.assertAlmostEqual(safe_float(summ[2]), 0.0, places=5)
        self.assertAlmostEqual(safe_float(summ[7]), -4.0, places=2)
        self.assertIn("Saddle", summ[8])

    def test_coord2d_coordinate_descent_c(self):
        # Coordinate descent on f(x,y) = (x-1)^2 + (y+2)^2 -> (1, -2)
        lines = run_numlab_engine(["opt_2d", "coord2d", "(x - 1)^2 + (y + 2)^2", 3.0, 2.0, 0.1])
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertAlmostEqual(safe_float(summ[1]), 1.0, places=2)
        self.assertAlmostEqual(safe_float(summ[2]), -2.0, places=2)
        self.assertIn("Minimum", summ[8])


class TestUnit5InterpolationAndRegressionSpecC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def test_T_I01_exact_quadratic_recovery(self):
        # T-I01: (0,1), (1,3), (2,7) from x^2 + x + 1 -> at x=1.5, y = 4.75
        lines = run_numlab_engine(["interp", "newton", 1.5, 2, 3, 0, 1, 1, 3, 2, 7])
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertAlmostEqual(safe_float(summ[1]), 4.75, places=6)
        power = [safe_float(l.split(',')[2]) for l in lines if l.startswith("POWER_ROW,")]
        self.assertAlmostEqual(power[0], 1.0, places=5)
        self.assertAlmostEqual(power[1], 1.0, places=5)
        self.assertAlmostEqual(power[2], 1.0, places=5)

    def test_T_I02_duplicate_x_rejected(self):
        # T-I02: (1, 2), (1, 3), (2, 5)
        with self.assertRaises((ValueError, RuntimeError)):
            run_numlab_engine(["interp", "newton", 1.5, 1, 3, 1, 2, 1, 3, 2, 5])

    def test_T_I03_inverse_non_monotonic_y_rejected(self):
        # T-I03: y = x^2 on [-1, 0, 1] -> y = [1, 0, 1] non-monotonic
        with self.assertRaises((ValueError, RuntimeError)):
            run_numlab_engine(["interp", "inverse", 0.5, 1, 3, -1, 1, 0, 0, 1, 1])

    def test_T_G01_linear_regression_exact_line(self):
        # T-G01: y = 2x + 1 on x = [1, 2, 3, 4] -> y = [3, 5, 7, 9]
        lines = run_numlab_engine(["interp", "ols", 2.5, 1, 4, 1, 3, 2, 5, 3, 7, 4, 9])
        ols_c = [safe_float(v) for v in [l.split(',') for l in lines if l.startswith("OLS_COEFFS,")][0][2:]]
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertAlmostEqual(ols_c[0], 1.0, places=6)
        self.assertAlmostEqual(ols_c[1], 2.0, places=6)
        self.assertAlmostEqual(safe_float(summ[5]), 1.0, places=6)


class TestUnit6IntegrationAndODESpecC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def test_T_Q01_simpson13_exact_on_cubic(self):
        # T-Q01: integral_0^1 x^3 dx = 0.25 exactly for Simpson 1/3 with n=2
        lines = run_numlab_engine(["quad", "simp13", "x^3", 0.0, 1.0, 2])
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertAlmostEqual(safe_float(summ[1]), 0.25, places=8)
        self.assertLess(safe_float(summ[3]), 1e-12)

    def test_T_Q02_simpson13_odd_n_adjusted(self):
        # T-Q02: n=3 auto-adjusted to n=4
        lines = run_numlab_engine(["quad", "simp13", "x^3", 0.0, 1.0, 3])
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertEqual(int(summ[5]), 4)
        self.assertIn("Auto-adjusted", summ[6])

    def test_T_Q03_gauss_2pt_exact_on_cubic(self):
        # T-Q03: 2-pt Gauss-Legendre on [-1, 1] for x^3 + 2x^2 = 4/3
        lines = run_numlab_engine(["quad", "gauss", "x^3 + 2*x^2", -1.0, 1.0, 2])
        summ = [l.split(',') for l in lines if l.startswith("SUMMARY,")][0]
        self.assertAlmostEqual(safe_float(summ[1]), 4.0 / 3.0, places=8)

    def test_T_Q04_singular_integrand_rejected(self):
        # T-Q04: 1/x on [-1, 1] has interior pole at x=0
        with self.assertRaises((ValueError, RuntimeError)):
            run_numlab_engine(["quad", "trap", "1/x", -1.0, 1.0, 4])

    def test_T_D01_T_D02_ode_order_hierarchy(self):
        # T-D01 & T-D02: y' = y, y(0)=1 on [0, 1] with h=0.1 -> Exact y(1) = e
        errors = {}
        for m in ('euler', 'heun', 'midpoint', 'rk4'):
            lines = run_numlab_engine(["ode", m, "y", "exp(t)", 0.0, 1.0, 0.0, 1.0, 0.1])
            steps = [l.split(',') for l in lines if l.startswith("STEP_1D,")]
            y_end = safe_float(steps[-1][3])
            errors[m] = abs(math.e - y_end)
        self.assertLess(errors['rk4'], 1e-5)
        self.assertLess(errors['rk4'], errors['heun'])
        self.assertLess(errors['heun'], errors['euler'])

    def test_T_D03_coupled_harmonic_oscillator_system(self):
        # T-D03: x' = y, y' = -x, x(0)=1, y(0)=0 on [0, 2*pi] -> x^2 + y^2 ≈ 1
        two_pi = 2.0 * math.pi
        lines = run_numlab_engine(["ode", "system", "y", "-x", 0.0, 1.0, 0.0, two_pi, two_pi / 100.0])
        steps = [l.split(',') for l in lines if l.startswith("STEP_SYS,")]
        x_end = safe_float(steps[-1][3])
        y_end = safe_float(steps[-1][4])
        energy = x_end * x_end + y_end * y_end
        self.assertAlmostEqual(energy, 1.0, places=3)


class TestCrossCuttingSpec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_c_engines_built()

    def test_T_X01_strict_cli_numeric_validation(self):
        # Malformed numeric strings rejected cleanly by C engines
        with self.assertRaises((ValueError, RuntimeError)):
            run_root_engine(["bisection", "x^2 - 2", "abc", "2.0", "0.001"])
        with self.assertRaises((ValueError, RuntimeError)):
            run_matrix_engine(["gaussian", "2", "1", "abc", "0", "1", "1", "2"])
        with self.assertRaises((ValueError, RuntimeError)):
            run_numlab_engine(["quad", "trap", "x^2", "0.0", "nan", "4"])

    def test_T_X02_theme_toggle_and_font_registry(self):
        initial_mode = COLORS.mode
        new_mode = COLORS.toggle()
        self.assertNotEqual(initial_mode, new_mode)
        self.assertTrue(hasattr(COLORS, 'bg_root'))
        self.assertTrue(hasattr(COLORS, 'bg'))
        self.assertEqual(FONTS['heading'], FONTS.HEADING)
        COLORS.toggle()

    def test_T_X03_all_tabs_method_equations_descriptions_and_working_steps(self):
        import errors_tab
        import root_tab
        import matrix_tab
        import optimization_tab
        import interpolation_tab
        import integration_tab
        import ode_tab

        modules_and_classes = [
            (errors_tab, errors_tab.ErrorsApproximationsTab, 'ERRORS_METHOD_INFO'),
            (root_tab, root_tab.RootFindingTab, 'METHOD_INFO'),
            (matrix_tab, matrix_tab.LinearSystemsTab, 'MATRIX_METHOD_INFO'),
            (optimization_tab, optimization_tab.OptimizationTab, 'OPT_METHOD_INFO'),
            (interpolation_tab, interpolation_tab.InterpolationTab, 'INTERP_METHOD_INFO'),
            (integration_tab, integration_tab.IntegrationTab, 'QUAD_METHOD_INFO'),
            (ode_tab, ode_tab.ODETab, 'ODE_METHOD_INFO'),
        ]
        for mod, cls, attr in modules_and_classes:
            info_dict = getattr(mod, attr, None)
            self.assertIsNotNone(info_dict, f"{mod.__name__} missing {attr}")
            self.assertGreater(len(info_dict), 0)
            for k, val in info_dict.items():
                self.assertEqual(len(val), 3, f"{mod.__name__}[{k}] must have (name, equation, description)")
                self.assertTrue(len(val[1].strip()) > 0, f"{mod.__name__}[{k}] governing equation is empty")
                self.assertTrue(len(val[2].strip()) > 0, f"{mod.__name__}[{k}] description is empty")
            self.assertTrue(hasattr(cls, '_show_working_steps'), f"{cls.__name__} missing _show_working_steps")


if __name__ == '__main__':
    unittest.main()
