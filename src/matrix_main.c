#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include "linalg.h"

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
    if (argc < 3) {
        printf("ERROR,Insufficient arguments for matrix_engine.\n");
        return 1;
    }
    const char* method = argv[1];
    int n = 0;
    if (!parse_int_strict(argv[2], &n) || n < 1 || n > 20 || argc < 3 + n * n) {
        printf("ERROR,Invalid matrix dimension or insufficient matrix entries.\n");
        return 1;
    }

    Matrix* A = matrix_create(n, n);
    int arg_idx = 3;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (!parse_double_strict(argv[arg_idx++], &A->data[i][j])) {
                printf("ERROR,Invalid numeric entry in matrix A.\n");
                matrix_free(A);
                return 1;
            }
        }
    }

    // Always emit C-computed matrix diagnostics first
    matrix_diagnostics(A);

    if (strcmp(method, "diagnostics") == 0) {
        matrix_free(A);
        return 0;
    }

    if (strcmp(method, "inverse") == 0) {
        Matrix* inv_aug = matrix_inversion(A);
        if (inv_aug) matrix_free(inv_aug);
        matrix_free(A);
        return 0;
    }

    if (argc < 3 + n * n + n) {
        printf("ERROR,Insufficient entries for right-hand side vector b.\n");
        matrix_free(A);
        return 1;
    }

    Vector* b = vector_create(n);
    for (int i = 0; i < n; i++) {
        if (!parse_double_strict(argv[arg_idx++], &b->data[i])) {
            printf("ERROR,Invalid numeric entry in vector b.\n");
            matrix_free(A);
            vector_free(b);
            return 1;
        }
    }

    Vector* solution = NULL;

    if (strcmp(method, "gaussian") == 0) solution = gaussian_elimination(A, b);
    else if (strcmp(method, "gauss_jordan") == 0) solution = gauss_jordan(A, b);
    else if (strcmp(method, "lu") == 0) solution = lu_decomposition(A, b);
    else if (strcmp(method, "gauss_seidel") == 0 || strcmp(method, "jacobi") == 0) {
        double tol = 1e-6;
        int max_it = 100;
        if (argc > arg_idx && !parse_double_strict(argv[arg_idx++], &tol)) {
            printf("ERROR,Invalid tolerance argument for iterative solver.\n");
            matrix_free(A); vector_free(b); return 1;
        }
        if (argc > arg_idx && !parse_int_strict(argv[arg_idx++], &max_it)) {
            printf("ERROR,Invalid max_iter argument for iterative solver.\n");
            matrix_free(A); vector_free(b); return 1;
        }
        if (strcmp(method, "jacobi") == 0) solution = jacobi_iteration(A, b, tol, max_it);
        else solution = gauss_seidel(A, b, tol, max_it);
    } else {
        printf("ERROR,Unknown matrix solver method: %s\n", method);
        matrix_free(A);
        vector_free(b);
        return 1;
    }

    if (solution) {
        print_solution_and_residual(A, b, solution);
        vector_free(solution);
    }
    matrix_free(A);
    vector_free(b);

    return 0;
}
