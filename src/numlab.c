#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <float.h>
#include <math.h>
#include "tinyexpr.h"
#include "numlab.h"

/* =========================================================================
 * C Expression Evaluator Helpers (tinyexpr with x, y, t variables)
 * ========================================================================= */
static double g_x = 0.0, g_y = 0.0, g_t = 0.0;

static te_expr* compile_expr_xyt(const char* eq) {
    te_variable vars[] = {
        {"x", &g_x},
        {"y", &g_y},
        {"t", &g_t}
    };
    int err = 0;
    return te_compile(eq, vars, 3, &err);
}

static double eval_1d(te_expr* ex, double x) {
    g_x = x;
    g_t = x;
    return te_eval(ex);
}

static double eval_2d(te_expr* ex, double x, double y) {
    g_x = x;
    g_y = y;
    return te_eval(ex);
}

static double eval_txy(te_expr* ex, double t, double x, double y) {
    g_t = t;
    g_x = x;
    g_y = y;
    return te_eval(ex);
}

static double deriv1_1d(te_expr* ex, double x) {
    double h = 1e-6 * (1.0 + fabs(x));
    double f_p1 = eval_1d(ex, x + h);
    double f_m1 = eval_1d(ex, x - h);
    double f_p2 = eval_1d(ex, x + 2.0 * h);
    double f_m2 = eval_1d(ex, x - 2.0 * h);
    /* 4th-order Richardson central difference */
    return (-f_p2 + 8.0 * f_p1 - 8.0 * f_m1 + f_m2) / (12.0 * h);
}

static double deriv2_1d(te_expr* ex, double x) {
    double h = 1e-4 * (1.0 + fabs(x));
    double f0 = eval_1d(ex, x);
    double f_p1 = eval_1d(ex, x + h);
    double f_m1 = eval_1d(ex, x - h);
    double f_p2 = eval_1d(ex, x + 2.0 * h);
    double f_m2 = eval_1d(ex, x - 2.0 * h);
    return (-f_p2 + 16.0 * f_p1 - 30.0 * f0 + 16.0 * f_m1 - f_m2) / (12.0 * h * h);
}

static double factorial_d(int k) {
    double r = 1.0;
    for (int i = 2; i <= k; i++) r *= (double)i;
    return r;
}

static double binomial_d(int n, int k) {
    if (k < 0 || k > n) return 0.0;
    return factorial_d(n) / (factorial_d(k) * factorial_d(n - k));
}

static double deriv_k_1d(te_expr* ex, double x0, int k) {
    if (k == 0) return eval_1d(ex, x0);
    if (k == 1) return deriv1_1d(ex, x0);
    if (k == 2) return deriv2_1d(ex, x0);
    double h = 0.04;
    double sum = 0.0;
    for (int j = 0; j <= k; j++) {
        double sgn = ((j % 2) == 0) ? 1.0 : -1.0;
        double pt = x0 + (0.5 * k - j) * h;
        sum += sgn * binomial_d(k, j) * eval_1d(ex, pt);
    }
    return sum / pow(h, k);
}

/* Dense linear solver with partial pivoting in C (for Vandermonde & OLS) */
static int solve_linear_system_c(int n, double* A, double* b, double* x_out) {
    double* aug = (double*)malloc(n * (n + 1) * sizeof(double));
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) aug[i * (n + 1) + j] = A[i * n + j];
        aug[i * (n + 1) + n] = b[i];
    }
    for (int k = 0; k < n; k++) {
        int piv = k;
        double max_v = fabs(aug[k * (n + 1) + k]);
        for (int i = k + 1; i < n; i++) {
            double v = fabs(aug[i * (n + 1) + k]);
            if (v > max_v) { max_v = v; piv = i; }
        }
        if (piv != k) {
            for (int j = k; j <= n; j++) {
                double tmp = aug[k * (n + 1) + j];
                aug[k * (n + 1) + j] = aug[piv * (n + 1) + j];
                aug[piv * (n + 1) + j] = tmp;
            }
        }
        double diag = aug[k * (n + 1) + k];
        if (fabs(diag) < 1e-14) {
            free(aug);
            return 1;
        }
        for (int i = k + 1; i < n; i++) {
            double factor = aug[i * (n + 1) + k] / diag;
            for (int j = k; j <= n; j++) {
                aug[i * (n + 1) + j] -= factor * aug[k * (n + 1) + j];
            }
        }
    }
    for (int i = n - 1; i >= 0; i--) {
        double s = 0.0;
        for (int j = i + 1; j < n; j++) s += aug[i * (n + 1) + j] * x_out[j];
        x_out[i] = (aug[i * (n + 1) + n] - s) / aug[i * (n + 1) + i];
    }
    free(aug);
    return 0;
}

static double matrix_cond_inf_c(int n, const double* A) {
    double norm_a = 0.0;
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++) s += fabs(A[i * n + j]);
        if (s > norm_a) norm_a = s;
    }
    double* W = (double*)calloc(n * 2 * n, sizeof(double));
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) W[i * (2 * n) + j] = A[i * n + j];
        W[i * (2 * n) + n + i] = 1.0;
    }
    for (int k = 0; k < n; k++) {
        int piv = k;
        double max_v = fabs(W[k * (2 * n) + k]);
        for (int i = k + 1; i < n; i++) {
            double v = fabs(W[i * (2 * n) + k]);
            if (v > max_v) { max_v = v; piv = i; }
        }
        if (piv != k) {
            for (int j = 0; j < 2 * n; j++) {
                double tmp = W[k * (2 * n) + j];
                W[k * (2 * n) + j] = W[piv * (2 * n) + j];
                W[piv * (2 * n) + j] = tmp;
            }
        }
        double diag = W[k * (2 * n) + k];
        if (fabs(diag) < 1e-14) {
            free(W);
            return INFINITY;
        }
        for (int j = k; j < 2 * n; j++) W[k * (2 * n) + j] /= diag;
        for (int i = 0; i < n; i++) {
            if (i != k) {
                double f = W[i * (2 * n) + k];
                for (int j = k; j < 2 * n; j++) W[i * (2 * n) + j] -= f * W[k * (2 * n) + j];
            }
        }
    }
    double norm_inv = 0.0;
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++) s += fabs(W[i * (2 * n) + n + j]);
        if (s > norm_inv) norm_inv = s;
    }
    free(W);
    return norm_a * norm_inv;
}

/* =========================================================================
 * UNIT 1: Errors, Taylor Series, Cancellation & IEEE-754
 * ========================================================================= */
int run_errors_h_sweep(const char* eq, double x0) {
    te_expr* ex = compile_expr_xyt(eq);
    if (!ex) {
        printf("ERROR,Invalid mathematical expression.\n");
        return 1;
    }
    double f0 = eval_1d(ex, x0);
    double df_exact = deriv1_1d(ex, x0);
    double d2f_exact = deriv2_1d(ex, x0);

    int n_pts = 65;
    double best_h = 1e-5;
    double min_err = INFINITY;

    for (int i = 0; i < n_pts; i++) {
        double exp_pow = -16.0 + (16.0 * i) / (double)(n_pts - 1);
        double h = pow(10.0, exp_pow);
        double fp = eval_1d(ex, x0 + h);
        double fm = eval_1d(ex, x0 - h);

        double fwd = (fp - f0) / h;
        double bwd = (f0 - fm) / h;
        double cen = (fp - fm) / (2.0 * h);
        double d2 = (fp - 2.0 * f0 + fm) / (h * h);

        double err_fwd = fmax(fabs(fwd - df_exact), 1e-17);
        double err_bwd = fmax(fabs(bwd - df_exact), 1e-17);
        double err_cen = fmax(fabs(cen - df_exact), 1e-17);
        double err_d2 = fmax(fabs(d2 - d2f_exact), 1e-17);

        if (err_cen < min_err) {
            min_err = err_cen;
            best_h = h;
        }
        printf("H_ROW,%.10e,%.10e,%.10e,%.10e,%.10e,%.10e,%.10e,%.10e\n",
               h, fwd, bwd, cen, err_fwd, err_bwd, err_cen, err_d2);
    }
    printf("META,%.10g,%.10g,%.10g,%.10e,%.10e\n", f0, df_exact, d2f_exact, best_h, min_err);
    te_free(ex);
    return 0;
}

int run_errors_taylor(const char* eq, double x0, double x_eval, int order) {
    if (order < 1) order = 1;
    if (order > 8) order = 8;

    te_expr* ex = compile_expr_xyt(eq);
    if (!ex) {
        printf("ERROR,Invalid mathematical expression.\n");
        return 1;
    }

    double true_val = eval_1d(ex, x_eval);
    double coeffs[10];
    double dx = x_eval - x0;
    double partial = 0.0;

    for (int k = 0; k <= order; k++) {
        double dk = deriv_k_1d(ex, x0, k);
        coeffs[k] = dk / factorial_d(k);
        double term = coeffs[k] * pow(dx, k);
        partial += term;
        double rem = fabs(true_val - partial);
        double rel_pct = (fabs(true_val) > 1e-14) ? (rem / fabs(true_val) * 100.0) : 0.0;
        printf("TAYLOR_ROW,%d,%.10g,%.10g,%.10g,%.10g,%.10e,%.10e\n",
               k, dk, coeffs[k], term, partial, rem, rel_pct);
    }

    double rem_final = fabs(true_val - partial);
    double rel_final = (fabs(true_val) > 1e-14) ? (rem_final / fabs(true_val) * 100.0) : 0.0;
    printf("META,%.10g,%.10g,%.10e,%.10e\n", true_val, partial, rem_final, rel_final);

    double span = fmax(2.5, fabs(x_eval - x0) * 1.6);
    double xmin = x0 - span, xmax = x0 + span;
    int n_pts = 200;
    for (int i = 0; i < n_pts; i++) {
        double x = xmin + (xmax - xmin) * i / (double)(n_pts - 1);
        double y_true = eval_1d(ex, x);
        printf("CURVE,%.8f,%.8f", x, y_true);
        double p_sum = 0.0;
        for (int k = 0; k <= order; k++) {
            p_sum += coeffs[k] * pow(x - x0, k);
            printf(",%.8f", p_sum);
        }
        printf("\n");
    }

    te_free(ex);
    return 0;
}

int run_errors_cancellation(void) {
    for (int k = 0; k <= 8; k++) {
        double xv = pow(10.0, k);
        double naive = sqrt(xv * xv + 1.0) - xv;
        double stable = 1.0 / (sqrt(xv * xv + 1.0) + xv);
        double rel_err = fmax(fabs(naive - stable) / fabs(stable), 1e-16);
        double lost = (rel_err <= 1e-16) ? 0.0 : fmin(16.0, fmax(0.0, 16.0 + log10(rel_err)));
        printf("CANCEL_ROW,%d,%.10e,%.10e,%.10e,%.10e,%.4f\n",
               k, xv, naive, stable, rel_err, lost);
    }
    int n_pts = 100;
    for (int i = 0; i < n_pts; i++) {
        double p = (8.0 * i) / (double)(n_pts - 1);
        double xv = pow(10.0, p);
        double naive = sqrt(xv * xv + 1.0) - xv;
        double stable = 1.0 / (sqrt(xv * xv + 1.0) + xv);
        double rel_err = fmax(fabs(naive - stable) / fabs(stable), 1e-16);
        printf("CURVE,%.8e,%.8e\n", xv, rel_err);
    }
    return 0;
}

int run_errors_ieee754(double val, double approx, int sig_figs) {
    union {
        double d;
        uint64_t u;
    } conv;
    conv.d = val;

    int sign_bit = (int)((conv.u >> 63) & 1ULL);
    int biased_exp = (int)((conv.u >> 52) & 0x7FFULL);
    int unbiased_exp = biased_exp - 1023;
    uint64_t mantissa = conv.u & 0xFFFFFFFFFFFFFULL;

    char sign_str[2];
    sign_str[0] = sign_bit ? '1' : '0';
    sign_str[1] = '\0';

    char exp_str[12];
    for (int i = 10; i >= 0; i--) {
        exp_str[10 - i] = ((biased_exp >> i) & 1) ? '1' : '0';
    }
    exp_str[11] = '\0';

    char man_str[53];
    for (int i = 51; i >= 0; i--) {
        man_str[51 - i] = ((mantissa >> i) & 1ULL) ? '1' : '0';
    }
    man_str[52] = '\0';

    double abs_v = fabs(val);
    double ulp = nextafter(abs_v, INFINITY) - abs_v;
    double eps = DBL_EPSILON;
    if (sig_figs < 1) sig_figs = 1;
    if (sig_figs > 16) sig_figs = 16;
    double es_tol = 0.5 * pow(10.0, 2 - sig_figs);
    double abs_err = fabs(val - approx);
    double rel_err_pct = (fabs(val) > 1e-15) ? (abs_err / fabs(val) * 100.0) : 0.0;

    printf("IEEE_BITS,%s,%s,%s,%d,%d\n", sign_str, exp_str, man_str, biased_exp, unbiased_exp);
    printf("IEEE_METRICS,%.10e,%.10e,%.10e,%.10e,%.10e\n", eps, ulp, es_tol, abs_err, rel_err_pct);

    for (int p = 1; p <= 15; p++) {
        printf("SCARBROUGH,%d,%.10e\n", p, 0.5 * pow(10.0, 2 - p));
    }
    return 0;
}

/* =========================================================================
 * UNIT 4: 1D & 2D Optimization
 * ========================================================================= */
int run_opt_1d(const char* method, const char* eq, double v1, double v2, double tol) {
    te_expr* ex = compile_expr_xyt(eq);
    if (!ex) {
        printf("ERROR,Invalid mathematical expression.\n");
        return 1;
    }

    double min_x = fmin(v1, v2), max_x = fmax(v1, v2);
    double x_opt = v1;
    int step_count = 0;

    if (strcmp(method, "golden") == 0) {
        double a = v1, b = v2;
        if (b <= a) { a = v1 - 2.0; b = v1 + 2.0; }
        min_x = a; max_x = b;
        double phi = (sqrt(5.0) - 1.0) / 2.0;
        for (int k = 1; k <= 60; k++) {
            double d = phi * (b - a);
            double x1 = a + d;
            double x2 = b - d;
            double f1 = eval_1d(ex, x1);
            double f2 = eval_1d(ex, x2);
            x_opt = (f1 < f2) ? x1 : x2;
            double fx = fmin(f1, f2);
            double err = fabs(b - a);
            printf("STEP,%d,%.10f,%.10f,%.10e,%.10f,%.10f,%.10f,%.10f\n",
                   k, x_opt, fx, err, a, b, x1, x2);
            step_count++;
            if (err < tol) break;
            if (f1 < f2) a = x2;
            else b = x1;
        }
    }
    else if (strcmp(method, "parabolic") == 0) {
        double x0 = v1, x2 = v2;
        if (x2 <= x0) { x0 = v1 - 2.0; x2 = v1 + 2.0; }
        min_x = x0; max_x = x2;
        double x1 = 0.5 * (x0 + x2);
        for (int k = 1; k <= 50; k++) {
            double f0 = eval_1d(ex, x0);
            double f1 = eval_1d(ex, x1);
            double f2 = eval_1d(ex, x2);
            double num = f0 * (x1 * x1 - x2 * x2) + f1 * (x2 * x2 - x0 * x0) + f2 * (x0 * x0 - x1 * x1);
            double den = 2.0 * f0 * (x1 - x2) + 2.0 * f1 * (x2 - x0) + 2.0 * f2 * (x0 - x1);
            if (fabs(den) < 1e-14) break;
            double x3 = num / den;
            double f3 = eval_1d(ex, x3);
            double err = fabs(x3 - x1);
            x_opt = x3;
            printf("STEP,%d,%.10f,%.10f,%.10e,%.10f,%.10f,%.10f,%.10f\n",
                   k, x3, f3, err, x0, x1, x2, x3);
            step_count++;
            if (err < tol) break;
            if (x3 > x1) {
                if (f3 < f1) { x0 = x1; x1 = x3; }
                else { x2 = x3; }
            } else {
                if (f3 < f1) { x2 = x1; x1 = x3; }
                else { x0 = x3; }
            }
        }
    }
    else if (strcmp(method, "newton1d") == 0) {
        double x = v1;
        min_x = x - 2.5; max_x = x + 2.5;
        for (int k = 1; k <= 50; k++) {
            double fx = eval_1d(ex, x);
            double dfx = deriv1_1d(ex, x);
            double d2fx = deriv2_1d(ex, x);
            if (fabs(d2fx) < 1e-14) break;
            double x_next = x - dfx / d2fx;
            double err = fabs(x_next - x);
            min_x = fmin(min_x, fmin(x, x_next));
            max_x = fmax(max_x, fmax(x, x_next));
            x_opt = x_next;
            printf("STEP,%d,%.10f,%.10f,%.10e,%.10f,%.10e,%.10e,0.0\n",
                   k, x, fx, err, x_next, dfx, d2fx);
            step_count++;
            x = x_next;
            if (err < tol || fabs(dfx) < 1e-12) break;
        }
    }

    double f_opt = eval_1d(ex, x_opt);
    double d2_opt = deriv2_1d(ex, x_opt);
    const char* kind = (d2_opt > 1e-6) ? "Local Minimum (f''>0)" : ((d2_opt < -1e-6) ? "Local Maximum (f''<0)" : "Inflection / Flat");
    printf("SUMMARY,%.10f,%.10f,%.10e,%s,%d\n", x_opt, f_opt, d2_opt, kind, step_count);

    double span = fmax(1.5, (max_x - min_x) * 0.25);
    double xs = min_x - span, xe = max_x + span;
    int n_pts = 220;
    for (int i = 0; i < n_pts; i++) {
        double xv = xs + (xe - xs) * i / (double)(n_pts - 1);
        double yv = eval_1d(ex, xv);
        if (!isnan(yv) && !isinf(yv)) {
            printf("CURVE,%.8f,%.8f\n", xv, yv);
        }
    }

    te_free(ex);
    return 0;
}

static void grad_hess_2d(te_expr* ex, double x, double y, double* gx, double* gy, double* hxx, double* hyy, double* hxy) {
    double h = 1e-5;
    double f0 = eval_2d(ex, x, y);
    double fx_p = eval_2d(ex, x + h, y);
    double fx_m = eval_2d(ex, x - h, y);
    double fy_p = eval_2d(ex, x, y + h);
    double fy_m = eval_2d(ex, x, y - h);

    *gx = (fx_p - fx_m) / (2.0 * h);
    *gy = (fy_p - fy_m) / (2.0 * h);
    *hxx = (fx_p - 2.0 * f0 + fx_m) / (h * h);
    *hyy = (fy_p - 2.0 * f0 + fy_m) / (h * h);
    *hxy = (eval_2d(ex, x + h, y + h) - eval_2d(ex, x + h, y - h)
          - eval_2d(ex, x - h, y + h) + eval_2d(ex, x - h, y - h)) / (4.0 * h * h);
}

int run_opt_2d(const char* method, const char* eq, double x0, double y0, double param) {
    te_expr* ex = compile_expr_xyt(eq);
    if (!ex) {
        printf("ERROR,Invalid 2D mathematical expression.\n");
        return 1;
    }

    double x = x0, y = y0;
    double min_x = x - 2.5, max_x = x + 2.5;
    double min_y = y - 2.5, max_y = y + 2.5;
    int max_it = (strcmp(method, "grad2d") == 0) ? 60 : 30;
    double alpha = (param > 0.0) ? param : 0.12;
    double tol = 1e-6;

    double last_hxx = 0.0, last_hyy = 0.0, last_hxy = 0.0, last_gnorm = 0.0;

    for (int k = 1; k <= max_it; k++) {
        double fx = eval_2d(ex, x, y);
        double gx, gy, hxx, hyy, hxy;
        grad_hess_2d(ex, x, y, &gx, &gy, &hxx, &hyy, &hxy);
        double gnorm = hypot(gx, gy);
        last_hxx = hxx; last_hyy = hyy; last_hxy = hxy; last_gnorm = gnorm;

        double x_next = x, y_next = y;
        if (strcmp(method, "grad2d") == 0) {
            x_next = x - alpha * gx;
            y_next = y - alpha * gy;
        } else if (strcmp(method, "coord2d") == 0) {
            if (k % 2 == 1) {
                double step_x = (fabs(hxx) > 1e-10) ? (-gx / fabs(hxx)) : (-alpha * gx);
                x_next = x + step_x;
                y_next = y;
            } else {
                double step_y = (fabs(hyy) > 1e-10) ? (-gy / fabs(hyy)) : (-alpha * gy);
                x_next = x;
                y_next = y + step_y;
            }
        } else {
            double det = hxx * hyy - hxy * hxy;
            if (fabs(det) < 1e-14) {
                printf("STEP,%d,%.10f,%.10f,%.10f,%.10e,%.10f,%.10f\n", k, x, y, fx, gnorm, x, y);
                break;
            }
            double dx = -(hyy * gx - hxy * gy) / det;
            double dy = -(-hxy * gx + hxx * gy) / det;
            x_next = x + dx;
            y_next = y + dy;
        }

        min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
        min_y = fmin(min_y, fmin(y, y_next)); max_y = fmax(max_y, fmax(y, y_next));

        printf("STEP,%d,%.10f,%.10f,%.10f,%.10e,%.10f,%.10f\n",
               k, x, y, fx, gnorm, x_next, y_next);

        x = x_next; y = y_next;
        if (gnorm < tol) break;
    }

    double f_final = eval_2d(ex, x, y);
    double tr = last_hxx + last_hyy;
    double det_h = last_hxx * last_hyy - last_hxy * last_hxy;
    double disc = fmax(0.0, tr * tr - 4.0 * det_h);
    double l1 = 0.5 * (tr + sqrt(disc));
    double l2 = 0.5 * (tr - sqrt(disc));
    const char* kind = "Indeterminate";
    if (det_h < -1e-7 || (l1 * l2 < -1e-7)) kind = "Saddle Point (det(H)<0)";
    else if (l1 > 0 && l2 > 0) kind = "Local Minimum (H > 0)";
    else if (l1 < 0 && l2 < 0) kind = "Local Maximum (H < 0)";

    printf("SUMMARY,%.10f,%.10f,%.10f,%.10e,%.10g,%.10g,%.10g,%s\n",
           x, y, f_final, last_gnorm, l1, l2, det_h, kind);

    /* Output 40x40 contour grid evaluated in C */
    int ng = 40;
    double pad_x = fmax(1.5, (max_x - min_x) * 0.25);
    double pad_y = fmax(1.5, (max_y - min_y) * 0.25);
    double gx0 = min_x - pad_x, gx1 = max_x + pad_x;
    double gy0 = min_y - pad_y, gy1 = max_y + pad_y;
    printf("GRID_META,%d,%.8f,%.8f,%.8f,%.8f\n", ng, gx0, gx1, gy0, gy1);
    for (int j = 0; j < ng; j++) {
        double yv = gy0 + (gy1 - gy0) * j / (double)(ng - 1);
        printf("GRID_ROW,%d", j);
        for (int i = 0; i < ng; i++) {
            double xv = gx0 + (gx1 - gx0) * i / (double)(ng - 1);
            printf(",%.6f", eval_2d(ex, xv, yv));
        }
        printf("\n");
    }

    te_free(ex);
    return 0;
}

/* =========================================================================
 * UNIT 5: Interpolation & Least-Squares Curve Fitting
 * ========================================================================= */
static double newton_poly_eval_c(int n, const double* xs, const double* dd_top, double xval) {
    double val = dd_top[n - 1];
    for (int k = n - 2; k >= 0; k--) {
        val = val * (xval - xs[k]) + dd_top[k];
    }
    return val;
}

static double poly_power_eval_c(int m, const double* coeffs, double xval) {
    /* coeffs[0] + coeffs[1]*x + ... + coeffs[m]*x^m */
    double val = coeffs[m];
    for (int k = m - 1; k >= 0; k--) {
        val = val * xval + coeffs[k];
    }
    return val;
}

int run_interpolation(const char* mode, double x_q, int deg, int n, const double* xs, const double* ys) {
    if (n < 2) {
        printf("ERROR,Require at least 2 data points.\n");
        return 1;
    }

    /* Check duplicate x */
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (fabs(xs[i] - xs[j]) < 1e-12 && strcmp(mode, "ols") != 0) {
                printf("ERROR,Duplicate x coordinates detected.\n");
                return 1;
            }
        }
    }

    /* 1. Newton Divided-Difference Table in C */
    double* dd = (double*)calloc(n * n, sizeof(double));
    for (int i = 0; i < n; i++) dd[i * n + 0] = ys[i];
    for (int j = 1; j < n; j++) {
        for (int i = 0; i < n - j; i++) {
            dd[i * n + j] = (dd[(i + 1) * n + (j - 1)] - dd[i * n + (j - 1)]) / (xs[i + j] - xs[i]);
        }
    }
    double* dd_top = (double*)malloc(n * sizeof(double));
    for (int j = 0; j < n; j++) dd_top[j] = dd[0 * n + j];

    for (int i = 0; i < n; i++) {
        printf("DD_ROW,%d,%.10g", i, xs[i]);
        for (int j = 0; j < n - i; j++) printf(",%.10g", dd[i * n + j]);
        printf("\n");
    }

    double y_interp_q = newton_poly_eval_c(n, xs, dd_top, x_q);

    /* 2. Lagrange Basis weights at x_q in C */
    for (int i = 0; i < n; i++) {
        double li = 1.0;
        for (int j = 0; j < n; j++) {
            if (i != j) li *= (x_q - xs[j]) / (xs[i] - xs[j]);
        }
        printf("LAGRANGE_ROW,%d,%.10g,%.10g,%.10g,%.10g\n", i, xs[i], ys[i], li, ys[i] * li);
    }

    /* 3. Vandermonde Matrix, Condition Number & Power-Basis Coefficients in C */
    double* V = (double*)malloc(n * n * sizeof(double));
    for (int i = 0; i < n; i++) {
        double p = 1.0;
        for (int j = 0; j < n; j++) {
            V[i * n + j] = p;
            p *= xs[i];
        }
    }
    double cond_v = matrix_cond_inf_c(n, V);
    double* power_c = (double*)calloc(n, sizeof(double));
    solve_linear_system_c(n, V, (double*)ys, power_c);
    for (int i = 0; i < n; i++) {
        printf("POWER_ROW,%d,%.10g\n", i, power_c[i]);
    }

    /* 4. Inverse Interpolation in C */
    double x_inv_q = NAN;
    int can_inv = 1;
    int inc = 1, dec = 1;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (fabs(ys[i] - ys[j]) < 1e-12) can_inv = 0;
        }
        if (i + 1 < n) {
            if (ys[i + 1] <= ys[i] + 1e-12) inc = 0;
            if (ys[i + 1] >= ys[i] - 1e-12) dec = 0;
        }
    }
    if (strcmp(mode, "inverse") == 0 && (!can_inv || (!inc && !dec))) {
        printf("ERROR,Inverse interpolation requires strictly monotonic y values without duplicates.\n");
        free(dd); free(dd_top); free(V); free(power_c);
        return 1;
    }
    if (can_inv) {
        double* inv_dd = (double*)calloc(n * n, sizeof(double));
        for (int i = 0; i < n; i++) inv_dd[i * n + 0] = xs[i];
        for (int j = 1; j < n; j++) {
            for (int i = 0; i < n - j; i++) {
                inv_dd[i * n + j] = (inv_dd[(i + 1) * n + (j - 1)] - inv_dd[i * n + (j - 1)]) / (ys[i + j] - ys[i]);
            }
        }
        double* inv_top = (double*)malloc(n * sizeof(double));
        for (int j = 0; j < n; j++) inv_top[j] = inv_dd[j];
        x_inv_q = newton_poly_eval_c(n, ys, inv_top, x_q);
        for (int i = 0; i < n; i++) {
            printf("INV_ROW,%d,%.10g,%.10g,%.10g\n", i, ys[i], xs[i], inv_top[i]);
        }
        free(inv_dd);
        free(inv_top);
    }

    /* 5. Ordinary Least-Squares (OLS) Polynomial Regression via Normal Equations in C */
    int m = deg;
    if (m < 1) m = 1;
    if (m > n - 1) m = n - 1;
    int k_cols = m + 1;
    double* XtX = (double*)calloc(k_cols * k_cols, sizeof(double));
    double* Xty = (double*)calloc(k_cols, sizeof(double));
    double* ols_c = (double*)calloc(k_cols, sizeof(double));

    for (int r = 0; r < k_cols; r++) {
        for (int c = 0; c < k_cols; c++) {
            double s = 0.0;
            for (int i = 0; i < n; i++) s += pow(xs[i], r + c);
            XtX[r * k_cols + c] = s;
        }
        double sy = 0.0;
        for (int i = 0; i < n; i++) sy += ys[i] * pow(xs[i], r);
        Xty[r] = sy;
    }
    solve_linear_system_c(k_cols, XtX, Xty, ols_c);

    printf("OLS_COEFFS,%d", m);
    for (int j = 0; j < k_cols; j++) printf(",%.10g", ols_c[j]);
    printf("\n");

    double y_mean = 0.0;
    for (int i = 0; i < n; i++) y_mean += ys[i];
    y_mean /= (double)n;

    double sr = 0.0, st = 0.0;
    for (int i = 0; i < n; i++) {
        double y_hat = poly_power_eval_c(m, ols_c, xs[i]);
        double res = ys[i] - y_hat;
        sr += res * res;
        st += (ys[i] - y_mean) * (ys[i] - y_mean);
        printf("OLS_ROW,%d,%.10g,%.10g,%.10g,%.10g,%.10e\n", i, xs[i], ys[i], y_hat, res, res * res);
    }
    double r2 = (st > 1e-15) ? (1.0 - sr / st) : 1.0;
    int dof = (n - k_cols > 0) ? (n - k_cols) : 1;
    double syx = sqrt(sr / (double)dof);
    double y_ols_q = poly_power_eval_c(m, ols_c, x_q);

    printf("SUMMARY,%.10g,%.10g,%.10g,%.10g,%.10g,%.10e,%.10g\n",
           y_interp_q, y_ols_q, x_inv_q, cond_v, r2, sr, syx);

    /* 6. Dense Curves Evaluated in C */
    double min_x = xs[0], max_x = xs[0];
    for (int i = 1; i < n; i++) {
        if (xs[i] < min_x) min_x = xs[i];
        if (xs[i] > max_x) max_x = xs[i];
    }
    if (strcmp(mode, "inverse") != 0) {
        if (x_q < min_x) min_x = x_q;
        if (x_q > max_x) max_x = x_q;
    }
    double pad = fmax(0.5, (max_x - min_x) * 0.15);
    double x0_c = min_x - pad, x1_c = max_x + pad;
    int n_pts = 200;
    for (int k = 0; k < n_pts; k++) {
        double xv = x0_c + (x1_c - x0_c) * k / (double)(n_pts - 1);
        double y_int = newton_poly_eval_c(n, xs, dd_top, xv);
        double y_reg = poly_power_eval_c(m, ols_c, xv);
        printf("CURVE,%.8f,%.8f,%.8f", xv, y_int, y_reg);
        if (strcmp(mode, "lagrange") == 0) {
            for (int i = 0; i < n; i++) {
                double li = 1.0;
                for (int j = 0; j < n; j++) {
                    if (i != j) li *= (xv - xs[j]) / (xs[i] - xs[j]);
                }
                printf(",%.8f", li);
            }
        }
        printf("\n");
    }

    free(dd); free(dd_top); free(V); free(power_c);
    free(XtX); free(Xty); free(ols_c);
    return 0;
}

/* =========================================================================
 * UNIT 6A: Numerical Integration (Quadrature)
 * ========================================================================= */
static const double GL2_X[2] = {-0.5773502691896257, 0.5773502691896257};
static const double GL2_W[2] = {1.0, 1.0};

static const double GL3_X[3] = {-0.7745966692414834, 0.0, 0.7745966692414834};
static const double GL3_W[3] = {0.5555555555555556, 0.8888888888888888, 0.5555555555555556};

static const double GL4_X[4] = {-0.8611363115940526, -0.3399810435848563, 0.3399810435848563, 0.8611363115940526};
static const double GL4_W[4] = {0.3478548451374538, 0.6521451548625461, 0.6521451548625461, 0.3478548451374538};

static const double GL5_X[5] = {-0.9061798459386640, -0.5384693101056831, 0.0, 0.5384693101056831, 0.9061798459386640};
static const double GL5_W[5] = {0.2369268850561891, 0.4786286704993665, 0.5688888888888889, 0.4786286704993665, 0.2369268850561891};

static double exact_integral_ref_c(te_expr* ex, double a, double b) {
    /* 64-panel 4-point Gauss-Legendre reference integral in C */
    int panels = 64;
    double h = (b - a) / (double)panels;
    double total = 0.0;
    for (int p = 0; p < panels; p++) {
        double pa = a + p * h;
        double pb = pa + h;
        double mid = 0.5 * (pa + pb), half = 0.5 * h;
        double s = 0.0;
        for (int k = 0; k < 4; k++) {
            s += GL4_W[k] * eval_1d(ex, mid + half * GL4_X[k]);
        }
        total += half * s;
    }
    return total;
}

static double trap_rule_c(te_expr* ex, double a, double b, int n) {
    double h = (b - a) / (double)n;
    double s = 0.5 * (eval_1d(ex, a) + eval_1d(ex, b));
    for (int i = 1; i < n; i++) s += eval_1d(ex, a + i * h);
    return h * s;
}

int run_quadrature(const char* method, const char* eq, double a, double b, int n) {
    te_expr* ex = compile_expr_xyt(eq);
    if (!ex) {
        printf("ERROR,Invalid mathematical expression.\n");
        return 1;
    }
    if (fabs(b - a) < 1e-14) {
        printf("SUMMARY,0.0000000000,0.0000000000,0.0000000000e+00,0.0000000000e+00,%d,Zero-width interval\n", n);
        te_free(ex);
        return 0;
    }
    double sign_flip = 1.0;
    if (b < a) {
        double tmp = a; a = b; b = tmp;
        sign_flip = -1.0;
    }

    /* Check for singularities or undefined points on [a, b] */
    for (int k = 0; k <= 32; k++) {
        double xt = a + (b - a) * (k / 32.0);
        double yt = eval_1d(ex, xt);
        if (isnan(yt) || isinf(yt) || fabs(yt) > 1e11) {
            printf("ERROR,Singular or undefined integrand on [a, b] (improper integral).\n");
            te_free(ex);
            return 1;
        }
    }
    double y_mid = eval_1d(ex, 0.5 * (a + b));
    if (isnan(y_mid) || isinf(y_mid) || fabs(y_mid) > 1e11) {
        printf("ERROR,Singular or undefined integrand at midpoint of [a, b].\n");
        te_free(ex);
        return 1;
    }

    double i_exact = sign_flip * exact_integral_ref_c(ex, a, b);
    double i_approx = 0.0;
    int n_used = n;
    const char* note = (sign_flip < 0.0) ? "Reversed limits (b < a): negated integral" : "";

    if (strcmp(method, "trap") == 0) {
        if (n_used < 1) n_used = 1;
        double h = (b - a) / (double)n_used;
        for (int i = 0; i <= n_used; i++) {
            double x = a + i * h;
            double fx = eval_1d(ex, x);
            double w = (i == 0 || i == n_used) ? (0.5 * h) : h;
            i_approx += w * fx;
            printf("NODE,%d,%.10g,%.10g,%.10g,%.10g\n", i, x, fx, w, w * fx);
        }
    }
    else if (strcmp(method, "simp13") == 0) {
        if (n_used < 2) n_used = 2;
        if (n_used % 2 != 0) { n_used++; note = "Auto-adjusted n to even for Simpson 1/3"; }
        double h = (b - a) / (double)n_used;
        for (int i = 0; i <= n_used; i++) {
            double x = a + i * h;
            double fx = eval_1d(ex, x);
            double c = (i == 0 || i == n_used) ? 1.0 : ((i % 2 == 1) ? 4.0 : 2.0);
            double w = (h / 3.0) * c;
            i_approx += w * fx;
            printf("NODE,%d,%.10g,%.10g,%.10g,%.10g\n", i, x, fx, w, w * fx);
        }
    }
    else if (strcmp(method, "simp38") == 0) {
        if (n_used < 3) n_used = 3;
        if (n_used % 3 != 0) { n_used += (3 - n_used % 3); note = "Auto-adjusted n to multiple of 3 for Simpson 3/8"; }
        double h = (b - a) / (double)n_used;
        for (int i = 0; i <= n_used; i++) {
            double x = a + i * h;
            double fx = eval_1d(ex, x);
            double c = (i == 0 || i == n_used) ? 1.0 : ((i % 3 == 0) ? 2.0 : 3.0);
            double w = (3.0 * h / 8.0) * c;
            i_approx += w * fx;
            printf("NODE,%d,%.10g,%.10g,%.10g,%.10g\n", i, x, fx, w, w * fx);
        }
    }
    else if (strcmp(method, "boole") == 0) {
        if (n_used < 4) n_used = 4;
        if (n_used % 4 != 0) { n_used += (4 - n_used % 4); note = "Auto-adjusted n to multiple of 4 for Boole's Rule"; }
        double h = (b - a) / (double)n_used;
        for (int i = 0; i <= n_used; i++) {
            double x = a + i * h;
            double fx = eval_1d(ex, x);
            double c;
            if (i == 0 || i == n_used) c = 7.0;
            else if (i % 2 == 1) c = 32.0;
            else if (i % 4 == 2) c = 12.0;
            else c = 14.0;
            double w = (2.0 * h / 45.0) * c;
            i_approx += w * fx;
            printf("NODE,%d,%.10g,%.10g,%.10g,%.10g\n", i, x, fx, w, w * fx);
        }
    }
    else if (strcmp(method, "romberg") == 0) {
        int levels = 4;
        double R[5][5] = {{0}};
        for (int i = 0; i < levels; i++) {
            int sub_n = 1 << i;
            R[i][0] = trap_rule_c(ex, a, b, sub_n);
            for (int k = 1; k <= i; k++) {
                double p4 = pow(4.0, k);
                R[i][k] = (p4 * R[i][k - 1] - R[i - 1][k - 1]) / (p4 - 1.0);
            }
            printf("ROMBERG_ROW,%d,%d", i, sub_n);
            for (int k = 0; k < levels; k++) {
                if (k <= i) printf(",%.10f", R[i][k]);
                else printf(",NAN");
            }
            printf("\n");
        }
        i_approx = R[levels - 1][levels - 1];
        n_used = 1 << (levels - 1);
        double h = (b - a) / (double)n_used;
        for (int i = 0; i <= n_used; i++) {
            double x = a + i * h;
            double fx = eval_1d(ex, x);
            double w = (i == 0 || i == n_used) ? (0.5 * h) : h;
            printf("NODE,%d,%.10g,%.10g,%.10g,%.10g\n", i, x, fx, w, w * fx);
        }
    }
    else if (strcmp(method, "gauss") == 0) {
        if (n_used < 2) n_used = 2;
        if (n_used > 5) n_used = 5;
        const double* gx = GL3_X;
        const double* gw = GL3_W;
        if (n_used == 2) { gx = GL2_X; gw = GL2_W; }
        else if (n_used == 3) { gx = GL3_X; gw = GL3_W; }
        else if (n_used == 4) { gx = GL4_X; gw = GL4_W; }
        else { gx = GL5_X; gw = GL5_W; }

        double mid = 0.5 * (a + b), half = 0.5 * (b - a);
        for (int i = 0; i < n_used; i++) {
            double x = mid + half * gx[i];
            double w = half * gw[i];
            double fx = eval_1d(ex, x);
            i_approx += w * fx;
            printf("NODE,%d,%.10g,%.10g,%.10g,%.10g\n", i, x, fx, w, w * fx);
        }
    }

    i_approx *= sign_flip;
    double abs_err = fabs(i_exact - i_approx);
    double rel_pct = (fabs(i_exact) > 1e-14) ? (abs_err / fabs(i_exact) * 100.0) : 0.0;
    printf("SUMMARY,%.10f,%.10f,%.10e,%.10e,%d,%s\n",
           i_approx, i_exact, abs_err, rel_pct, n_used, note);

    double span = (b - a) * 0.12;
    double xs = a - span, xe = b + span;
    int n_pts = 240;
    for (int i = 0; i < n_pts; i++) {
        double xv = xs + (xe - xs) * i / (double)(n_pts - 1);
        printf("CURVE,%.8f,%.8f\n", xv, eval_1d(ex, xv));
    }

    te_free(ex);
    return 0;
}

/* =========================================================================
 * UNIT 6B: ODE Initial-Value Problems
 * ========================================================================= */
int run_ode_solver(const char* method, const char* eq1, const char* eq2,
                   double t0, double y0, double z0, double t_end, double h) {
    if (h <= 0.0 || t_end <= t0) {
        printf("ERROR,Require h > 0 and t_end > t0.\n");
        return 1;
    }

    te_expr* ex1 = compile_expr_xyt(eq1);
    if (!ex1) {
        printf("ERROR,Invalid ODE expression f(t, y).\n");
        return 1;
    }
    te_expr* ex2 = (eq2 && strlen(eq2) > 0) ? compile_expr_xyt(eq2) : NULL;

    int n_steps = (int)floor((t_end - t0) / h + 0.5);
    if (n_steps < 1) n_steps = 1;
    if (n_steps > 300) n_steps = 300;

    if (strcmp(method, "system") == 0) {
        if (!ex2) {
            printf("ERROR,Coupled 2D system requires second equation dy/dt = g(t, x, y).\n");
            te_free(ex1);
            return 1;
        }
        double t = t0, x = y0, y = z0;
        for (int idx = 0; idx <= n_steps; idx++) {
            double k1x = eval_txy(ex1, t, x, y);
            double k1y = eval_txy(ex2, t, x, y);
            double k2x = eval_txy(ex1, t + 0.5 * h, x + 0.5 * h * k1x, y + 0.5 * h * k1y);
            double k2y = eval_txy(ex2, t + 0.5 * h, x + 0.5 * h * k1x, y + 0.5 * h * k1y);
            double k3x = eval_txy(ex1, t + 0.5 * h, x + 0.5 * h * k2x, y + 0.5 * h * k2y);
            double k3y = eval_txy(ex2, t + 0.5 * h, x + 0.5 * h * k2x, y + 0.5 * h * k2y);
            double k4x = eval_txy(ex1, t + h, x + h * k3x, y + h * k3y);
            double k4y = eval_txy(ex2, t + h, x + h * k3x, y + h * k3y);

            printf("STEP_SYS,%d,%.8f,%.10f,%.10f,%.6f,%.6f\n", idx, t, x, y, k1x, k1y);

            x += (h / 6.0) * (k1x + 2.0 * k2x + 2.0 * k3x + k4x);
            y += (h / 6.0) * (k1y + 2.0 * k2y + 2.0 * k3y + k4y);
            t += h;
        }
    } else {
        double t = t0, y = y0, y_euler = y0;
        double min_y = y0, max_y = y0;

        for (int idx = 0; idx <= n_steps; idx++) {
            double y_true = ex2 ? eval_txy(ex2, t, t, y) : NAN;
            double err = (!isnan(y_true)) ? fabs(y_true - y) : NAN;

            double k1 = eval_txy(ex1, t, t, y);
            double k2 = 0.0, k3 = 0.0, k4 = 0.0, y_next = y;

            if (strcmp(method, "euler") == 0) {
                y_next = y + h * k1;
            } else if (strcmp(method, "heun") == 0) {
                k2 = eval_txy(ex1, t + h, t + h, y + h * k1);
                y_next = y + 0.5 * h * (k1 + k2);
            } else if (strcmp(method, "midpoint") == 0) {
                k2 = eval_txy(ex1, t + 0.5 * h, t + 0.5 * h, y + 0.5 * h * k1);
                y_next = y + h * k2;
            } else {
                k2 = eval_txy(ex1, t + 0.5 * h, t + 0.5 * h, y + 0.5 * h * k1);
                k3 = eval_txy(ex1, t + 0.5 * h, t + 0.5 * h, y + 0.5 * h * k2);
                k4 = eval_txy(ex1, t + h, t + h, y + h * k3);
                y_next = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4);
            }

            if (y < min_y) min_y = y;
            if (y > max_y) max_y = y;
            if (y_euler < min_y) min_y = y_euler;
            if (y_euler > max_y) max_y = y_euler;

            printf("STEP_1D,%d,%.8f,%.10f,%.10f,%.10f,%.10f,%.10e,%.6f,%.6f,%.6f,%.6f\n",
                   idx, t, y, y_next, y_euler, y_true, err, k1, k2, k3, k4);

            y_euler += h * eval_txy(ex1, t, t, y_euler);
            y = y_next;
            t += h;
        }

        /* Dense Exact Solution Curve in C */
        if (ex2) {
            int n_pts = 200;
            for (int i = 0; i < n_pts; i++) {
                double tv = t0 + (t_end - t0) * i / (double)(n_pts - 1);
                double yv = eval_txy(ex2, tv, tv, 0.0);
                if (!isnan(yv) && !isinf(yv)) {
                    printf("EXACT_CURVE,%.8f,%.8f\n", tv, yv);
                }
            }
        }

        /* Slope Field Vectors Computed in C */
        double span_y = fmax(max_y - min_y, 1.0);
        double y_low = min_y - 0.15 * span_y;
        double y_high = max_y + 0.15 * span_y;
        int nt = 14, ny = 12;
        for (int i = 0; i < nt; i++) {
            double tg = t0 + (t_end - t0) * i / (double)(nt - 1);
            for (int j = 0; j < ny; j++) {
                double yg = y_low + (y_high - y_low) * j / (double)(ny - 1);
                double dy = eval_txy(ex1, tg, tg, yg);
                if (!isnan(dy) && !isinf(dy)) {
                    double norm = hypot(1.0, dy) + 1e-12;
                    printf("QUIVER,%.6f,%.6f,%.6f,%.6f\n", tg, yg, 1.0 / norm, dy / norm);
                }
            }
        }
    }

    te_free(ex1);
    if (ex2) te_free(ex2);
    return 0;
}
