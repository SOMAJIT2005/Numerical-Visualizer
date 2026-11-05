#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include "numlab.h"

static int parse_double_strict(const char* s, double* out) {
    if (!s || *s == '\0') return 0;
    char* endptr = NULL;
    errno = 0;
    double val = strtod(s, &endptr);
    if (errno != 0 || endptr == s || *endptr != '\0' || !isfinite(val)) return 0;
    *out = val;
    return 1;
}

static int parse_int_strict(const char* s, int* out) {
    if (!s || *s == '\0') return 0;
    char* endptr = NULL;
    errno = 0;
    long val = strtol(s, &endptr, 10);
    if (errno != 0 || endptr == s || *endptr != '\0' || val < -1000000 || val > 1000000) return 0;
    *out = (int)val;
    return 1;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("ERROR,No command specified for numlab_engine.\n");
        return 1;
    }

    const char* cmd = argv[1];

    /* Unit 1: Errors & Approximations */
    if (strcmp(cmd, "errors_h_sweep") == 0) {
        double x0 = 0.0;
        if (argc < 4 || !parse_double_strict(argv[3], &x0)) {
            printf("ERROR,Invalid arguments for errors_h_sweep.\n");
            return 1;
        }
        return run_errors_h_sweep(argv[2], x0);
    }
    if (strcmp(cmd, "errors_taylor") == 0) {
        double x0 = 0.0, x_ev = 0.0;
        int ord = 1;
        if (argc < 6 || !parse_double_strict(argv[3], &x0) ||
            !parse_double_strict(argv[4], &x_ev) || !parse_int_strict(argv[5], &ord)) {
            printf("ERROR,Invalid arguments for errors_taylor.\n");
            return 1;
        }
        return run_errors_taylor(argv[2], x0, x_ev, ord);
    }
    if (strcmp(cmd, "errors_cancellation") == 0) {
        return run_errors_cancellation();
    }
    if (strcmp(cmd, "errors_ieee754") == 0) {
        double v = 0.0, ap = 0.0;
        int sf = 5;
        if (argc < 5 || !parse_double_strict(argv[2], &v) ||
            !parse_double_strict(argv[3], &ap) || !parse_int_strict(argv[4], &sf)) {
            printf("ERROR,Invalid arguments for errors_ieee754.\n");
            return 1;
        }
        return run_errors_ieee754(v, ap, sf);
    }

    /* Unit 4: 1D & 2D Optimization */
    if (strcmp(cmd, "opt_1d") == 0) {
        double v1 = 0.0, v2 = 0.0, tol = 1e-6;
        if (argc < 7 || !parse_double_strict(argv[4], &v1) ||
            !parse_double_strict(argv[5], &v2) || !parse_double_strict(argv[6], &tol)) {
            printf("ERROR,Invalid arguments for opt_1d.\n");
            return 1;
        }
        return run_opt_1d(argv[2], argv[3], v1, v2, tol);
    }
    if (strcmp(cmd, "opt_2d") == 0) {
        double x0 = 0.0, y0 = 0.0, p = 0.1;
        if (argc < 7 || !parse_double_strict(argv[4], &x0) ||
            !parse_double_strict(argv[5], &y0) || !parse_double_strict(argv[6], &p)) {
            printf("ERROR,Invalid arguments for opt_2d.\n");
            return 1;
        }
        return run_opt_2d(argv[2], argv[3], x0, y0, p);
    }

    /* Unit 5: Interpolation & Least-Squares Curve Fitting */
    if (strcmp(cmd, "interp") == 0) {
        double x_q = 0.0;
        int deg = 1, n = 0;
        if (argc < 6 || !parse_double_strict(argv[3], &x_q) ||
            !parse_int_strict(argv[4], &deg) || !parse_int_strict(argv[5], &n)) {
            printf("ERROR,Invalid arguments for interp.\n");
            return 1;
        }
        const char* mode = argv[2];
        if (n < 2 || argc < 6 + 2 * n) {
            printf("ERROR,Insufficient point arguments for interp.\n");
            return 1;
        }
        double* xs = (double*)malloc(n * sizeof(double));
        double* ys = (double*)malloc(n * sizeof(double));
        for (int i = 0; i < n; i++) {
            if (!parse_double_strict(argv[6 + 2 * i], &xs[i]) ||
                !parse_double_strict(argv[6 + 2 * i + 1], &ys[i])) {
                printf("ERROR,Invalid coordinate in interpolation table.\n");
                free(xs); free(ys);
                return 1;
            }
        }
        int rc = run_interpolation(mode, x_q, deg, n, xs, ys);
        free(xs);
        free(ys);
        return rc;
    }

    /* Unit 6A: Numerical Integration (Quadrature) */
    if (strcmp(cmd, "quad") == 0) {
        double a = 0.0, b = 0.0;
        int n = 4;
        if (argc < 7 || !parse_double_strict(argv[4], &a) ||
            !parse_double_strict(argv[5], &b) || !parse_int_strict(argv[6], &n)) {
            printf("ERROR,Invalid arguments for quad.\n");
            return 1;
        }
        return run_quadrature(argv[2], argv[3], a, b, n);
    }

    /* Unit 6B: ODE Initial-Value Problems */
    if (strcmp(cmd, "ode") == 0) {
        double t0 = 0.0, y0 = 0.0, z0 = 0.0, t_end = 1.0, h = 0.1;
        if (argc < 10 || !parse_double_strict(argv[5], &t0) ||
            !parse_double_strict(argv[6], &y0) || !parse_double_strict(argv[7], &z0) ||
            !parse_double_strict(argv[8], &t_end) || !parse_double_strict(argv[9], &h)) {
            printf("ERROR,Invalid arguments for ode.\n");
            return 1;
        }
        return run_ode_solver(argv[2], argv[3], argv[4], t0, y0, z0, t_end, h);
    }

    printf("ERROR,Unknown numlab command: %s\n", cmd);
    return 1;
}
