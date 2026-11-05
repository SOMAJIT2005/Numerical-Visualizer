#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "tinyexpr.h"
#include "roots.h"

#define MAX_STEPS 100

static double x_var;
static te_expr *expr = NULL;

int init_math_parser(const char* equation) {
    if (!equation || strlen(equation) == 0) return 1;
    te_variable vars[] = {{"x", &x_var}};
    int err;
    expr = te_compile(equation, vars, 1, &err);
    return (expr == NULL) ? 1 : 0;
}

void cleanup_math_parser(void) {
    if (expr) {
        te_free(expr);
        expr = NULL;
    }
}

double f(double x) {
    x_var = x;
    return te_eval(expr);
}

double df(double x) {
    double h = 1e-8 * (1.0 + fabs(x));
    return (f(x + h) - f(x - h)) / (2.0 * h);
}

double d2f(double x) {
    double h = 1e-5 * (1.0 + fabs(x));
    return (f(x + h) - 2.0 * f(x) + f(x - h)) / (h * h);
}

static double safe_rel_err(double curr, double prev) {
    if (fabs(curr) > 1e-14) {
        return fabs((curr - prev) / curr);
    }
    return fabs(curr - prev);
}

void run_root_solver(const char* method, double val1, double val2, double tol) {
    int max_iterations = 100;

    char step_buffer[MAX_STEPS][256];
    double res_buffer[MAX_STEPS];
    int step_count = 0;

    int is_bracket = (strcmp(method, "bisection") == 0 ||
                      strcmp(method, "false_position") == 0 ||
                      strcmp(method, "brent") == 0);

    if (is_bracket) {
        if (val2 <= val1) {
            printf("ERROR,Invalid bracket: upper bound b must be greater than lower bound a.\n");
            return;
        }
        double fa0 = f(val1);
        double fb0 = f(val2);
        if (isnan(fa0) || isinf(fa0) || isnan(fb0) || isinf(fb0)) {
            printf("ERROR,Domain error: f(x) is undefined (NaN/Inf) at bracket endpoints.\n");
            return;
        }
        /* Check interior domain validity (e.g. sqrt(x) on [-1, 1]) */
        for (int k = 1; k < 16; k++) {
            double x_test = val1 + (val2 - val1) * (k / 16.0);
            double y_test = f(x_test);
            if (isnan(y_test)) {
                printf("ERROR,Domain error: f(x) is undefined (NaN) inside bracket [a, b].\n");
                return;
            }
        }
        if (fabs(fa0) < 1e-14) {
            printf("TRUEROOT,%.12g\n", val1);
            printf("STEP,0,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00\n", val1, val2, val1);
            printf("RESIDUAL,0,%.10e\n", fabs(fa0));
            return;
        }
        if (fabs(fb0) < 1e-14) {
            printf("TRUEROOT,%.12g\n", val2);
            printf("STEP,0,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00\n", val1, val2, val2);
            printf("RESIDUAL,0,%.10e\n", fabs(fb0));
            return;
        }
        if (fa0 * fb0 > 0.0) {
            printf("ERROR,Invalid bracket: f(a) and f(b) have the same sign (f(a)*f(b) > 0).\n");
            return;
        }
    } else {
        double fx0 = f(val1);
        if (isnan(fx0) || isinf(fx0)) {
            printf("ERROR,Domain error: f(x0) is undefined (NaN/Inf) at initial guess.\n");
            return;
        }
    }

    double min_x = val1;
    double max_x = val2;

    if (!is_bracket && strcmp(method, "secant") != 0) {
        min_x = val1 - 2.0;
        max_x = val1 + 2.0;
    }

    double ref_root = val1;
    int found_ref = 0;
    for (int i = 0; i < 2000; i++) {
        double y_val, derivative;

        if (strcmp(method, "fixed_point") == 0) {
            y_val = f(ref_root) - ref_root;
            derivative = df(ref_root) - 1.0;
        } else {
            y_val = f(ref_root);
            derivative = df(ref_root);
        }

        if (isnan(y_val) || isinf(y_val)) break;
        if (fabs(y_val) < 1e-14) { found_ref = 1; break; }

        if (fabs(derivative) < 1e-14) break;
        ref_root = ref_root - y_val / derivative;
    }

    double prev_guess = 0.0;
    double init_endpoint_mag = is_bracket ? fmax(fabs(f(val1)), fabs(f(val2))) : 1.0;

    if (strcmp(method, "bisection") == 0) {
        double a = val1, b = val2;
        for (int i = 0; i < max_iterations; i++) {
            double c = a + (b - a) / 2.0;
            double fc = f(c);
            if (isnan(fc) || isinf(fc) || (fabs(b - a) < 1e-3 && fabs(fc) > 1e5 * fmax(1.0, init_endpoint_mag))) {
                printf("ERROR,Discontinuity or vertical asymptote (pole) detected inside [a, b].\n");
                return;
            }
            min_x = fmin(min_x, fmin(a, b)); max_x = fmax(max_x, fmax(a, b));
            double approx = (i == 0) ? 0.0 : safe_rel_err(c, prev_guess);
            double tr_err = found_ref ? fabs(ref_root - c) : 0.0;

            res_buffer[step_count] = fabs(fc);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%e,%e", i, a, b, c, approx, tr_err);
            if (f(a) * fc < 0) b = c; else a = c;
            prev_guess = c;

            if (fabs(fc) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "false_position") == 0) {
        double a = val1, b = val2;
        for (int i = 0; i < max_iterations; i++) {
            double fa = f(a), fb = f(b);
            if (fabs(fb - fa) < 1e-14) break;

            double c = b - fb * (b - a) / (fb - fa);
            double fc = f(c);
            if (isnan(fc) || isinf(fc) || fabs(fc) > 1e8 * fmax(1.0, init_endpoint_mag)) {
                printf("ERROR,Discontinuity or singularity encountered in False Position.\n");
                return;
            }
            min_x = fmin(min_x, fmin(a, b)); max_x = fmax(max_x, fmax(a, b));
            double approx = (i == 0) ? 0.0 : safe_rel_err(c, prev_guess);
            double tr_err = found_ref ? fabs(ref_root - c) : 0.0;

            res_buffer[step_count] = fabs(fc);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%e,%e", i, a, b, c, approx, tr_err);
            if (fa * fc < 0) b = c; else a = c;
            prev_guess = c;

            if (fabs(fc) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "brent") == 0) {
        double a = val1, b = val2, c = a, d = 0, e = 0;
        double fa = f(a), fb = f(b), fc = fa;

        for (int i = 0; i < max_iterations; i++) {
            if (fb * fc > 0.0) {
                c = a; fc = fa;
                d = b - a; e = d;
            }
            if (fabs(fc) < fabs(fb)) {
                a = b; b = c; c = a;
                fa = fb; fb = fc; fc = fa;
            }

            double tol_val = 2.0 * 1e-12 * fabs(b) + 1e-12;
            double m = 0.5 * (c - b);

            if (fabs(m) <= tol_val || fabs(fb) < 1e-14) {
                if (step_count == 0) {
                    res_buffer[step_count] = fabs(fb);
                    sprintf(step_buffer[step_count++], "STEP,0,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00", a, c, b);
                }
                break;
            }

            if (fabs(e) >= tol_val && fabs(fa) > fabs(fb)) {
                double s = fb / fa, p, q, r;
                if (a == c) {
                    p = 2.0 * m * s; q = 1.0 - s;
                } else {
                    q = fa / fc; r = fb / fc;
                    p = s * (2.0 * m * q * (q - r) - (b - a) * (r - 1.0));
                    q = (q - 1.0) * (r - 1.0) * (s - 1.0);
                }
                if (p > 0) q = -q; else p = -p;

                if (2.0 * p < fmin(3.0 * m * q - fabs(tol_val * q), fabs(e * q))) {
                    e = d; d = p / q;
                } else { d = m; e = m; }
            } else { d = m; e = m; }

            a = b; fa = fb;
            double b_prev = b;
            if (fabs(d) > tol_val) b += d; else b += (m > 0 ? tol_val : -tol_val);
            fb = f(b);
            if (isnan(fb) || isinf(fb) || (fabs(c - b) < 1e-3 && fabs(fb) > 1e5 * fmax(1.0, init_endpoint_mag))) {
                printf("ERROR,Discontinuity or vertical asymptote (pole) detected inside [a, b].\n");
                return;
            }

            min_x = fmin(min_x, b); max_x = fmax(max_x, b);
            double approx = safe_rel_err(b, b_prev);
            double tr_err = found_ref ? fabs(ref_root - b) : 0.0;

            res_buffer[step_count] = fabs(fb);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%e,%e", i, a, c, b, approx, tr_err);
            if (fabs(fb) < 1e-14 || (approx * 100.0) < tol) break;
        }
    }
    else if (strcmp(method, "newton") == 0) {
        double x = val1;
        for (int i = 0; i < max_iterations; i++) {
            double fx = f(x);
            if (isnan(fx) || isinf(fx)) {
                printf("ERROR,Domain error: f(x) evaluated to NaN/Inf.\n");
                return;
            }
            if (fabs(fx) < 1e-14) {
                res_buffer[step_count] = fabs(fx);
                sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00", i, x, fx, x);
                break;
            }
            double der = df(x);
            if (fabs(der) < 1e-6) {
                if (step_count == 0) {
                    printf("ERROR,Zero derivative f'(x) = 0 at initial guess.\n");
                    return;
                }
                break;
            }

            double x_next = x - fx / der;
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : safe_rel_err(x_next, x);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            double fx_next = f(x_next);
            if (isnan(fx_next) || isinf(fx_next)) {
                printf("ERROR,Domain error: Newton step landed outside function domain.\n");
                return;
            }

            res_buffer[step_count] = fabs(fx_next);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%e,%e", i, x, fx, x_next, approx, tr_err);
            x = x_next;
            if (fabs(fx_next) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "modified_newton") == 0) {
        double x = val1;
        for (int i = 0; i < max_iterations; i++) {
            double fx = f(x);
            if (isnan(fx) || isinf(fx)) {
                printf("ERROR,Domain error: f(x) evaluated to NaN/Inf.\n");
                return;
            }
            if (fabs(fx) < 1e-14) {
                res_buffer[step_count] = fabs(fx);
                sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00", i, x, fx, x);
                break;
            }
            double der1 = df(x), der2 = d2f(x);
            double denom = (der1 * der1) - (fx * der2);
            if (fabs(denom) < 1e-14) {
                if (step_count == 0) {
                    printf("ERROR,Zero denominator in Modified Newton at initial guess.\n");
                    return;
                }
                break;
            }

            double x_next = x - (fx * der1) / denom;
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : safe_rel_err(x_next, x);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            double fx_next = f(x_next);

            res_buffer[step_count] = fabs(fx_next);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%e,%e", i, x, fx, x_next, approx, tr_err);
            x = x_next;
            if (fabs(fx_next) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "secant") == 0) {
        double x0 = val1, x1 = val2;
        for (int i = 0; i < max_iterations; i++) {
            double f0 = f(x0), f1 = f(x1);
            if (isnan(f0) || isinf(f0) || isnan(f1) || isinf(f1)) {
                printf("ERROR,Domain error: f(x) evaluated to NaN/Inf in Secant.\n");
                return;
            }
            if (fabs(f1) < 1e-14) {
                res_buffer[step_count] = fabs(f1);
                sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00", i, x0, f0, x1, f1, x1);
                break;
            }
            if (fabs(f1 - f0) < 1e-14) {
                if (step_count == 0) {
                    printf("ERROR,Zero secant slope f(x1) - f(x0) = 0.\n");
                    return;
                }
                break;
            }

            double x2 = x1 - f1 * (x1 - x0) / (f1 - f0);
            min_x = fmin(min_x, fmin(x0, x2)); max_x = fmax(max_x, fmax(x0, x2));
            double approx = (i == 0) ? 0.0 : safe_rel_err(x2, x1);
            double tr_err = found_ref ? fabs(ref_root - x2) : 0.0;
            double f2 = f(x2);

            res_buffer[step_count] = fabs(f2);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%e,%e", i, x0, f0, x1, f1, x2, approx, tr_err);
            x0 = x1; x1 = x2;
            if (fabs(f2) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "modified_secant") == 0) {
        double x = val1;
        double delta = (val2 == 0.0) ? 0.01 : val2;
        for (int i = 0; i < max_iterations; i++) {
            double fx = f(x);
            if (isnan(fx) || isinf(fx)) {
                printf("ERROR,Domain error: f(x) evaluated to NaN/Inf.\n");
                return;
            }
            if (fabs(fx) < 1e-14) {
                res_buffer[step_count] = fabs(fx);
                sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%.12g,%.12g,0.000000e+00,0.000000e+00", i, x, fx, x, fx, x);
                break;
            }
            double dx = delta * x;
            if (dx == 0.0) dx = delta;

            double fxdx = f(x + dx);
            if (fabs(fxdx - fx) < 1e-14) break;

            double x_next = x - (dx * fx) / (fxdx - fx);
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : safe_rel_err(x_next, x);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            double fx_next = f(x_next);

            res_buffer[step_count] = fabs(fx_next);
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%e,%e", i, x, fx, x + dx, fxdx, x_next, approx, tr_err);
            x = x_next;
            if (fabs(fx_next) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "fixed_point") == 0) {
        double x = val1;
        for (int i = 0; i < max_iterations; i++) {
            double x_next = f(x);
            if (isnan(x_next) || isinf(x_next) || fabs(x_next) > 1e12) {
                printf("ERROR,Fixed-Point iteration diverged (|g'(x)| >= 1 or domain error).\n");
                return;
            }
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : safe_rel_err(x_next, x);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            double res = fabs(f(x_next) - x_next);

            res_buffer[step_count] = res;
            sprintf(step_buffer[step_count++], "STEP,%d,%.12g,%.12g,%.12g,%e,%e", i, x, x_next, 0.0, approx, tr_err);
            if (fabs(x_next - x) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) { x = x_next; break; }
            x = x_next;
        }
    } else {
        printf("ERROR,Unknown root solver method: %s\n", method);
        return;
    }

    // Graph Curve Output
    double range = max_x - min_x;
    if (range == 0) range = 10.0;
    double start = min_x - range * 0.2;
    double end = max_x + range * 0.2;
    double step = (end - start) / 200.0;

    for (double x = start; x <= end; x += step) {
        double y = f(x);
        if (!isnan(y) && !isinf(y) && fabs(y) < 1e8) printf("CURVE,%.10g,%.10g\n", x, y);
    }

    if (found_ref) printf("TRUEROOT,%.12g\n", ref_root);
    else printf("TRUEROOT,NAN\n");

    for (int i = 0; i < step_count; i++) {
        printf("%s\n", step_buffer[i]);
        printf("RESIDUAL,%d,%.10e\n", i, res_buffer[i]);
    }
}

void run_curve_preview(double xmin, double xmax, double a_val, double b_val, int has_a, int has_b) {
    if (xmax <= xmin) {
        xmin -= 5.0;
        xmax += 5.0;
    }
    int n_pts = 200;
    double step = (xmax - xmin) / (double)(n_pts - 1);
    for (int i = 0; i < n_pts; i++) {
        double x = xmin + i * step;
        double y = f(x);
        if (!isnan(y) && !isinf(y) && fabs(y) < 1e8) {
            printf("CURVE,%.8f,%.8f\n", x, y);
        }
    }
    if (has_a) {
        double fa = f(a_val);
        printf("EVAL_A,%.8f,%.8f\n", a_val, fa);
        if (has_b) {
            double fb = f(b_val);
            printf("EVAL_B,%.8f,%.8f\n", b_val, fb);
            printf("BRACKET,%.8e,%.8e,%.8e\n", fa, fb, fa * fb);
        }
    }
}

static void horner_eval(const double* c, int deg, double x0, double* b_out, double* d_out, double* px_out, double* dpx_out) {
    b_out[0] = c[0];
    for (int i = 1; i <= deg; i++) {
        b_out[i] = c[i] + x0 * b_out[i - 1];
    }
    *px_out = b_out[deg];
    if (deg >= 1) {
        d_out[0] = b_out[0];
        for (int i = 1; i < deg; i++) {
            d_out[i] = b_out[i] + x0 * d_out[i - 1];
        }
        *dpx_out = d_out[deg - 1];
    } else {
        *dpx_out = 0.0;
    }
}

void run_horner_lab(double x0, int deg, const double* coeffs) {
    double* b = (double*)calloc(deg + 1, sizeof(double));
    double* d = (double*)calloc(deg + 1, sizeof(double));
    double px = 0.0, dpx = 0.0;

    horner_eval(coeffs, deg, x0, b, d, &px, &dpx);
    double nr_next = (fabs(dpx) > 1e-14) ? (x0 - px / dpx) : NAN;

    printf("HORNER_EVAL,%.12g,%.12g,%.12g\n", px, dpx, nr_next);
    printf("HORNER_B");
    for (int i = 0; i <= deg; i++) printf(",%.12g", b[i]);
    printf("\n");
    printf("HORNER_D");
    for (int i = 0; i < deg; i++) printf(",%.12g", d[i]);
    printf("\n");

    // Polynomial Deflation via Newton-Horner in C
    double* work = (double*)malloc((deg + 1) * sizeof(double));
    double* wb = (double*)malloc((deg + 1) * sizeof(double));
    double* wd = (double*)malloc((deg + 1) * sizeof(double));
    for (int i = 0; i <= deg; i++) work[i] = coeffs[i];

    double min_r = x0 - 3.0, max_r = x0 + 3.0;
    int cur_deg = deg;
    int root_idx = 0;

    while (cur_deg > 2) {
        double guess = (root_idx == 0) ? x0 : (0.37 * root_idx - 1.1);
        int converged = 0;
        for (int attempt = 0; attempt < 5 && !converged; attempt++) {
            double z = guess + attempt * 1.3;
            for (int it = 0; it < 120; it++) {
                double pz, dpz;
                horner_eval(work, cur_deg, z, wb, wd, &pz, &dpz);
                if (fabs(pz) < 1e-11) {
                    converged = 1;
                    guess = z;
                    break;
                }
                if (fabs(dpz) < 1e-14) {
                    z += 0.25;
                    continue;
                }
                z -= pz / dpz;
            }
        }
        double pz_final, dpz_final;
        horner_eval(work, cur_deg, guess, wb, wd, &pz_final, &dpz_final);
        if (converged || fabs(pz_final) < 1e-5) {
            printf("POLY_ROOT,%d,REAL,%.12g,0.0\n", root_idx++, guess);
            if (guess < min_r) min_r = guess;
            if (guess > max_r) max_r = guess;
            for (int i = 0; i < cur_deg; i++) work[i] = wb[i];
            cur_deg--;
        } else {
            break;
        }
    }

    if (cur_deg == 2 && fabs(work[0]) > 1e-14) {
        double A = work[0], B = work[1], C = work[2];
        double disc = B * B - 4.0 * A * C;
        if (disc >= 0.0) {
            double r1 = (-B + sqrt(disc)) / (2.0 * A);
            double r2 = (-B - sqrt(disc)) / (2.0 * A);
            printf("POLY_ROOT,%d,REAL,%.12g,0.0\n", root_idx++, r1);
            printf("POLY_ROOT,%d,REAL,%.12g,0.0\n", root_idx++, r2);
            if (r1 < min_r) min_r = r1;
            if (r1 > max_r) max_r = r1;
            if (r2 < min_r) min_r = r2;
            if (r2 > max_r) max_r = r2;
        } else {
            double re = -B / (2.0 * A);
            double im = sqrt(-disc) / fabs(2.0 * A);
            printf("POLY_ROOT,%d,COMPLEX,%.12g,%.12g\n", root_idx++, re, im);
            printf("POLY_ROOT,%d,COMPLEX,%.12g,%.12g\n", root_idx++, re, -im);
        }
    } else if (cur_deg == 1 && fabs(work[0]) > 1e-14) {
        double r1 = -work[1] / work[0];
        printf("POLY_ROOT,%d,REAL,%.12g,0.0\n", root_idx++, r1);
        if (r1 < min_r) min_r = r1;
        if (r1 > max_r) max_r = r1;
    }

    double span = fmax(2.0, (max_r - min_r) * 0.25);
    double x_start = min_r - span;
    double x_end = max_r + span;
    int n_pts = 220;
    for (int i = 0; i < n_pts; i++) {
        double xv = x_start + (x_end - x_start) * i / (double)(n_pts - 1);
        double pv, dpv;
        horner_eval(coeffs, deg, xv, wb, wd, &pv, &dpv);
        printf("CURVE,%.8f,%.8f\n", xv, pv);
    }

    free(b);
    free(d);
    free(work);
    free(wb);
    free(wd);
}
