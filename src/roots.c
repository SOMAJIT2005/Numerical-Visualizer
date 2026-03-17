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
    te_variable vars[] = {{"x", &x_var}};
    int err;
    expr = te_compile(equation, vars, 1, &err);
    return (expr == NULL) ? 1 : 0;
}

void cleanup_math_parser() {
    if (expr) te_free(expr);
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
    double h = 1e-8 * (1.0 + fabs(x));
    return (f(x + h) - 2.0 * f(x) + f(x - h)) / (h * h);
}

void run_root_solver(const char* method, double val1, double val2, double tol) {
    int max_iterations = 100;
    
    char step_buffer[MAX_STEPS][256];
    int step_count = 0;
    
    double min_x = val1;
    double max_x = val2;

    if (strcmp(method, "newton") == 0 || strcmp(method, "modified_newton") == 0 || 
        strcmp(method, "fixed_point") == 0 || strcmp(method, "modified_secant") == 0) {
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

    if (strcmp(method, "bisection") == 0) {
        double a = val1, b = val2;
        for (int i = 0; i < max_iterations; i++) {
            double c = (a + b) / 2.0;
            min_x = fmin(min_x, fmin(a, b)); max_x = fmax(max_x, fmax(a, b));
            double approx = (i == 0) ? 0.0 : fabs((c - prev_guess) / c);
            double tr_err = found_ref ? fabs(ref_root - c) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%e,%e", i, a, b, c, approx, tr_err);
            if (f(a) * f(c) < 0) b = c; else a = c;
            prev_guess = c;
            
            // ── COMPARES AS PERCENTAGE ──
            if (fabs(f(c)) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "false_position") == 0) {
        double a = val1, b = val2;
        for (int i = 0; i < max_iterations; i++) {
            double fa = f(a), fb = f(b);
            if (fabs(fb - fa) < 1e-14) break;
            
            double c = b - fb * (b - a) / (fb - fa);
            min_x = fmin(min_x, fmin(a, b)); max_x = fmax(max_x, fmax(a, b));
            double approx = (i == 0) ? 0.0 : fabs((c - prev_guess) / c);
            double tr_err = found_ref ? fabs(ref_root - c) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%e,%e", i, a, b, c, approx, tr_err);
            if (fa * f(c) < 0) b = c; else a = c;
            prev_guess = c;
            
            if (fabs(f(c)) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "brent") == 0) {
        double a = val1, b = val2, c = a, d = 0, e = 0;
        double fa = f(a), fb = f(b), fc = fa;
        
        for (int i = 0; i < max_iterations; i++) {
            if (fabs(fb) < fabs(fa)) { 
                double tmp = a; a = b; b = tmp; 
                tmp = fa; fa = fb; fb = tmp;
                c = a; fc = fa;
            }
            if (fabs(fc) < fabs(fb)) {
                double tmp = b; b = c; c = tmp; 
                tmp = fb; fb = fc; fc = tmp;
            }
            
            double tol_val = 2.0 * 1e-12 * fabs(b) + 1e-12;
            double m = 0.5 * (c - b);
            
            double approx = (i == 0) ? 0.0 : fabs((b - prev_guess) / b);
            
            if (fabs(m) <= tol_val || fb == 0.0 || (i > 0 && (approx * 100.0) < tol)) break;
            
            if (fabs(e) >= tol_val && fabs(fa) > fabs(fb)) {
                double s = fb/fa, p, q, r;
                if (a == c) {
                    p = 2.0 * m * s; q = 1.0 - s;
                } else {
                    q = fa/fc; r = fb/fc;
                    p = s * (2.0 * m * q * (q - r) - (b - a) * (r - 1.0));
                    q = (q - 1.0) * (r - 1.0) * (s - 1.0);
                }
                if (p > 0) q = -q; else p = -p;
                
                if (2.0 * p < fmin(3.0 * m * q - fabs(tol_val * q), fabs(e * q))) {
                    e = d; d = p/q;
                } else { d = m; e = m; }
            } else { d = m; e = m; }
            
            a = b; fa = fb;
            if (fabs(d) > tol_val) b += d; else b += (m > 0 ? tol_val : -tol_val);
            fb = f(b);
            
            min_x = fmin(min_x, b); max_x = fmax(max_x, b);
            double tr_err = found_ref ? fabs(ref_root - b) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%e,%e", i, a, b, c, approx, tr_err);
            prev_guess = b;
        }
    }
    else if (strcmp(method, "newton") == 0) {
        double x = val1;
        for (int i = 0; i < max_iterations; i++) {
            double fx = f(x), der = df(x);
            if (fabs(der) < 1e-14) break;
            
            double x_next = x - fx / der;
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : fabs((x_next - x) / x_next);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%e,%e", i, x, fx, x_next, approx, tr_err);
            x = x_next;
            if (fabs(fx) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "modified_newton") == 0) {
        double x = val1;
        for (int i = 0; i < max_iterations; i++) {
            double fx = f(x), der1 = df(x), der2 = d2f(x);
            double denom = (der1 * der1) - (fx * der2);
            if (fabs(denom) < 1e-14) break;
            
            double x_next = x - (fx * der1) / denom;
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : fabs((x_next - x) / x_next);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%e,%e", i, x, fx, x_next, approx, tr_err);
            x = x_next;
            if (fabs(fx) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "secant") == 0) {
        double x0 = val1, x1 = val2;
        for (int i = 0; i < max_iterations; i++) {
            double f0 = f(x0), f1 = f(x1);
            if (fabs(f1 - f0) < 1e-14) break;
            
            double x2 = x1 - f1 * (x1 - x0) / (f1 - f0);
            min_x = fmin(min_x, fmin(x0, x2)); max_x = fmax(max_x, fmax(x0, x2));
            double approx = (i == 0) ? 0.0 : fabs((x2 - x1) / x2);
            double tr_err = found_ref ? fabs(ref_root - x2) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%f,%f,%e,%e", i, x0, f0, x1, f1, x2, approx, tr_err);
            x0 = x1; x1 = x2;
            if (fabs(f1) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "modified_secant") == 0) {
        double x = val1;
        double delta = (val2 == 0.0) ? 0.01 : val2; 
        for (int i = 0; i < max_iterations; i++) {
            double fx = f(x);
            double dx = delta * x;
            if (dx == 0.0) dx = delta; 
            
            double fxdx = f(x + dx);
            if (fabs(fxdx - fx) < 1e-14) break;
            
            double x_next = x - (dx * fx) / (fxdx - fx);
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : fabs((x_next - x) / x_next);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%f,%f,%e,%e", i, x, fx, x+dx, fxdx, x_next, approx, tr_err);
            x = x_next;
            if (fabs(fx) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) break;
        }
    }
    else if (strcmp(method, "fixed_point") == 0) {
        double x = val1;
        for (int i = 0; i < max_iterations; i++) {
            double x_next = f(x);
            min_x = fmin(min_x, fmin(x, x_next)); max_x = fmax(max_x, fmax(x, x_next));
            double approx = (i == 0) ? 0.0 : fabs((x_next - x) / x_next);
            double tr_err = found_ref ? fabs(ref_root - x_next) : 0.0;
            
            sprintf(step_buffer[step_count++], "STEP,%d,%f,%f,%f,%e,%e", i, x, x_next, 0.0, approx, tr_err);
            if (fabs(x_next - x) < 1e-14 || (i > 0 && (approx * 100.0) < tol)) { x = x_next; break; }
            x = x_next;
        }
    }

    // Graph Curve Output
    double range = max_x - min_x;
    if (range == 0) range = 10.0;
    double start = min_x - range * 0.2;
    double end = max_x + range * 0.2;
    double step = (end - start) / 200.0;

    for (double x = start; x <= end; x += step) {
        double y = f(x);
        if (!isnan(y) && !isinf(y)) printf("CURVE,%f,%f\n", x, y);
    }

    if (found_ref) printf("TRUEROOT,%f\n", ref_root);
    else printf("TRUEROOT,NAN\n");

    for (int i = 0; i < step_count; i++) printf("%s\n", step_buffer[i]);
}