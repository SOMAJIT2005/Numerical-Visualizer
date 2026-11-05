#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include "roots.h"

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
        printf("ERROR,Insufficient arguments.\n");
        return 1;
    }

    const char* method = argv[1];

    if (strcmp(method, "preview") == 0) {
        if (argc < 5) {
            printf("ERROR,Insufficient preview arguments.\n");
            return 1;
        }
        const char* equation = argv[2];
        double xmin = 0.0, xmax = 0.0;
        if (!parse_double_strict(argv[3], &xmin) || !parse_double_strict(argv[4], &xmax)) {
            printf("ERROR,Invalid numeric range for preview.\n");
            return 1;
        }
        int has_a = (argc >= 6 && strlen(argv[5]) > 0);
        int has_b = (argc >= 7 && strlen(argv[6]) > 0);
        double a_val = 0.0, b_val = 0.0;
        if (has_a && !parse_double_strict(argv[5], &a_val)) has_a = 0;
        if (has_b && !parse_double_strict(argv[6], &b_val)) has_b = 0;

        if (init_math_parser(equation) != 0) {
            printf("ERROR,Invalid equation syntax.\n");
            return 1;
        }
        run_curve_preview(xmin, xmax, a_val, b_val, has_a, has_b);
        cleanup_math_parser();
        return 0;
    }

    if (strcmp(method, "horner") == 0) {
        if (argc < 5) {
            printf("ERROR,Insufficient Horner arguments.\n");
            return 1;
        }
        double x0 = 0.0;
        int deg = 0;
        if (!parse_double_strict(argv[2], &x0) || !parse_int_strict(argv[3], &deg)) {
            printf("ERROR,Invalid numeric argument for Horner lab.\n");
            return 1;
        }
        if (deg < 1 || argc < 4 + deg + 1) {
            printf("ERROR,Polynomial degree mismatch.\n");
            return 1;
        }
        double* coeffs = (double*)malloc((deg + 1) * sizeof(double));
        for (int i = 0; i <= deg; i++) {
            if (!parse_double_strict(argv[4 + i], &coeffs[i])) {
                printf("ERROR,Invalid polynomial coefficient.\n");
                free(coeffs);
                return 1;
            }
        }
        run_horner_lab(x0, deg, coeffs);
        free(coeffs);
        return 0;
    }

    if (argc < 5) {
        printf("ERROR,Insufficient arguments.\n");
        return 1;
    }

    const char* equation = argv[2];
    double val1 = 0.0, val2 = 0.0;
    if (!parse_double_strict(argv[3], &val1) || !parse_double_strict(argv[4], &val2)) {
        printf("ERROR,Invalid numeric argument for initial guess or bracket.\n");
        return 1;
    }

    double tol = 0.0001;
    if (argc >= 6) {
        if (!parse_double_strict(argv[5], &tol) || tol <= 0.0) {
            printf("ERROR,Invalid tolerance argument (must be positive finite number).\n");
            return 1;
        }
    }

    if (init_math_parser(equation) != 0) {
        printf("ERROR,Invalid equation syntax.\n");
        return 1;
    }

    run_root_solver(method, val1, val2, tol);

    cleanup_math_parser();
    return 0;
}
