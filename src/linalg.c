#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "linalg.h"

Matrix* matrix_create(int rows, int cols) {
    Matrix* mat = (Matrix*)malloc(sizeof(Matrix));
    mat->rows = rows; mat->cols = cols;
    mat->data = (double**)malloc(rows * sizeof(double*));
    for (int i = 0; i < rows; i++) mat->data[i] = (double*)calloc(cols, sizeof(double));
    return mat;
}

void matrix_free(Matrix* mat) {
    if (!mat) return;
    for (int i = 0; i < mat->rows; i++) free(mat->data[i]);
    free(mat->data); free(mat);
}

Vector* vector_create(int size) {
    Vector* vec = (Vector*)malloc(sizeof(Vector));
    vec->size = size; vec->data = (double*)calloc(size, sizeof(double));
    return vec;
}

void vector_free(Vector* vec) {
    if (!vec) return;
    free(vec->data); free(vec);
}

void matrix_print(Matrix* mat, const char* label) {
    printf("MATRIX,%s,%d,%d\n", label, mat->rows, mat->cols);
    for (int i = 0; i < mat->rows; i++) {
        printf("ROW,%d", i);
        for (int j = 0; j < mat->cols; j++) printf(",%.10g", mat->data[i][j]);
        printf("\n");
    }
}

Matrix* create_augmented_matrix(Matrix* A, Vector* b) {
    int n = A->rows;
    Matrix* aug = matrix_create(n, n + 1);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) aug->data[i][j] = A->data[i][j];
        aug->data[i][n] = b->data[i];
    }
    return aug;
}

void swap_rows(Matrix* mat, int row1, int row2) {
    double* temp = mat->data[row1];
    mat->data[row1] = mat->data[row2];
    mat->data[row2] = temp;
}

static double matrix_inf_norm(Matrix* M) {
    double max_row = 0.0;
    for (int i = 0; i < M->rows; i++) {
        double s = 0.0;
        for (int j = 0; j < M->cols; j++) s += fabs(M->data[i][j]);
        if (s > max_row) max_row = s;
    }
    return max_row;
}

static double compute_determinant_and_inv_norm(Matrix* A, double* inv_norm_out) {
    int n = A->rows;
    Matrix* W = matrix_create(n, 2 * n);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) W->data[i][j] = A->data[i][j];
        W->data[i][n + i] = 1.0;
    }
    double det = 1.0;
    for (int k = 0; k < n; k++) {
        int piv = k;
        double max_v = fabs(W->data[k][k]);
        for (int i = k + 1; i < n; i++) {
            if (fabs(W->data[i][k]) > max_v) {
                max_v = fabs(W->data[i][k]);
                piv = i;
            }
        }
        if (piv != k) {
            swap_rows(W, k, piv);
            det = -det;
        }
        double diag = W->data[k][k];
        if (fabs(diag) < 1e-14) {
            *inv_norm_out = INFINITY;
            matrix_free(W);
            return 0.0;
        }
        det *= diag;
        for (int j = k; j < 2 * n; j++) W->data[k][j] /= diag;
        for (int i = 0; i < n; i++) {
            if (i != k) {
                double f = W->data[i][k];
                for (int j = k; j < 2 * n; j++) W->data[i][j] -= f * W->data[k][j];
            }
        }
    }
    double max_inv_row = 0.0;
    for (int i = 0; i < n; i++) {
        double s = 0.0;
        for (int j = 0; j < n; j++) s += fabs(W->data[i][n + j]);
        if (s > max_inv_row) max_inv_row = s;
    }
    *inv_norm_out = max_inv_row;
    matrix_free(W);
    return det;
}

static int check_spd_sylvester(Matrix* A) {
    int n = A->rows;
    for (int m = 1; m <= n; m++) {
        Matrix* sub = matrix_create(m, m);
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < m; j++) sub->data[i][j] = A->data[i][j];
        }
        double dummy = 0.0;
        double minor_det = compute_determinant_and_inv_norm(sub, &dummy);
        matrix_free(sub);
        if (minor_det <= 1e-11) return 0;
    }
    return 1;
}

void matrix_diagnostics(Matrix* A) {
    int n = A->rows;
    int is_sym = 1;
    int is_dd = 1;
    for (int i = 0; i < n; i++) {
        double diag = fabs(A->data[i][i]);
        double off_sum = 0.0;
        for (int j = 0; j < n; j++) {
            if (fabs(A->data[i][j] - A->data[j][i]) > 1e-8) is_sym = 0;
            if (i != j) off_sum += fabs(A->data[i][j]);
        }
        if (diag < off_sum || diag < 1e-14) is_dd = 0;
    }
    double inv_norm = INFINITY;
    double det = compute_determinant_and_inv_norm(A, &inv_norm);
    double a_norm = matrix_inf_norm(A);
    double cond = (isinf(inv_norm) || fabs(det) < 1e-13) ? INFINITY : (a_norm * inv_norm);
    int is_spd = is_sym ? check_spd_sylvester(A) : 0;
    printf("DIAG,%.10g,%.10g,%d,%d,%d\n", det, cond, is_sym, is_dd, is_spd);
}

static double compute_residual_inf(Matrix* A, Vector* b, Vector* x) {
    int n = A->rows;
    double max_res = 0.0;
    for (int i = 0; i < n; i++) {
        double ax_i = 0.0;
        for (int j = 0; j < n; j++) ax_i += A->data[i][j] * x->data[j];
        double r = fabs(ax_i - b->data[i]);
        if (r > max_res) max_res = r;
    }
    return max_res;
}

void print_solution_and_residual(Matrix* A, Vector* b, Vector* x) {
    if (!x) return;
    int n = A->rows;
    printf("SOLUTION");
    for (int i = 0; i < n; i++) printf(",%.10g", x->data[i]);
    printf("\n");

    double max_res = compute_residual_inf(A, b, x);
    printf("RESIDUAL,%.10e\n", max_res);
}

Vector* gaussian_elimination(Matrix* A, Vector* b) {
    int n = A->rows;
    Matrix* aug = create_augmented_matrix(A, b);
    matrix_print(aug, "initial");

    for (int k = 0; k < n - 1; k++) {
        int pivot_row = k;
        double max_val = fabs(aug->data[k][k]);
        for (int i = k + 1; i < n; i++) {
            if (fabs(aug->data[i][k]) > max_val) { max_val = fabs(aug->data[i][k]); pivot_row = i; }
        }
        if (pivot_row != k) {
            swap_rows(aug, k, pivot_row);
            printf("SWAP,%d,%d,%d\n", k, k, pivot_row);
            matrix_print(aug, "step");
        }
        if (fabs(aug->data[k][k]) < 1e-12) {
            printf("ERROR,Zero pivot encountered at row %d\n", k);
            matrix_free(aug); return NULL;
        }
        for (int i = k + 1; i < n; i++) {
            double factor = aug->data[i][k] / aug->data[k][k];
            printf("ELIMINATE,%d,%d,%d,%.10g\n", k, i, k, factor);
            for (int j = k; j <= n; j++) aug->data[i][j] -= factor * aug->data[k][j];
            matrix_print(aug, "step");
        }
    }

    if (fabs(aug->data[n - 1][n - 1]) < 1e-12) {
        printf("ERROR,Zero pivot encountered at row %d\n", n - 1);
        matrix_free(aug); return NULL;
    }

    Vector* x = vector_create(n);
    printf("INFO,Back-Substitution Phase\n");
    for (int i = n - 1; i >= 0; i--) {
        double sum = 0.0;
        for (int j = i + 1; j < n; j++) sum += aug->data[i][j] * x->data[j];
        x->data[i] = (aug->data[i][n] - sum) / aug->data[i][i];
        printf("BACKSOLVE,%d,%.10g\n", i, x->data[i]);
    }
    matrix_free(aug); return x;
}

Vector* gauss_jordan(Matrix* A, Vector* b) {
    int n = A->rows;
    Matrix* aug = create_augmented_matrix(A, b);
    matrix_print(aug, "initial");
    for (int k = 0; k < n; k++) {
        int pivot_row = k;
        double max_val = fabs(aug->data[k][k]);
        for (int i = k + 1; i < n; i++) {
            if (fabs(aug->data[i][k]) > max_val) { max_val = fabs(aug->data[i][k]); pivot_row = i; }
        }
        if (pivot_row != k) {
            swap_rows(aug, k, pivot_row);
            printf("SWAP,%d,%d,%d\n", k, k, pivot_row);
            matrix_print(aug, "step");
        }
        if (fabs(aug->data[k][k]) < 1e-12) {
            printf("ERROR,Zero pivot at row %d\n", k);
            matrix_free(aug); return NULL;
        }
        double diag = aug->data[k][k];
        for (int j = k; j <= n; j++) aug->data[k][j] /= diag;
        printf("NORMALIZE,%d,%.10g\n", k, diag);
        matrix_print(aug, "step");
        for (int i = 0; i < n; i++) {
            if (i != k) {
                double factor = aug->data[i][k];
                for (int j = k; j <= n; j++) aug->data[i][j] -= factor * aug->data[k][j];
                printf("ELIMINATE,%d,%d,%d,%.10g\n", k, i, k, factor);
                matrix_print(aug, "step");
            }
        }
    }
    Vector* x = vector_create(n);
    for (int i = 0; i < n; i++) x->data[i] = aug->data[i][n];
    matrix_free(aug); return x;
}

Matrix* matrix_inversion(Matrix* A) {
    int n = A->rows;
    Matrix* aug = matrix_create(n, 2 * n);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) aug->data[i][j] = A->data[i][j];
        aug->data[i][n + i] = 1.0;
    }
    matrix_print(aug, "initial");
    for (int k = 0; k < n; k++) {
        int pivot_row = k;
        double max_val = fabs(aug->data[k][k]);
        for (int i = k + 1; i < n; i++) {
            if (fabs(aug->data[i][k]) > max_val) { max_val = fabs(aug->data[i][k]); pivot_row = i; }
        }
        if (pivot_row != k) {
            swap_rows(aug, k, pivot_row);
            printf("SWAP,%d,%d,%d\n", k, k, pivot_row);
            matrix_print(aug, "step");
        }
        if (fabs(aug->data[k][k]) < 1e-12) {
            printf("ERROR,Singular matrix: zero pivot at row %d prevents inversion\n", k);
            matrix_free(aug); return NULL;
        }
        double diag = aug->data[k][k];
        for (int j = k; j < 2 * n; j++) aug->data[k][j] /= diag;
        printf("NORMALIZE,%d,%.10g\n", k, diag);
        matrix_print(aug, "step");
        for (int i = 0; i < n; i++) {
            if (i != k && fabs(aug->data[i][k]) > 1e-14) {
                double factor = aug->data[i][k];
                for (int j = k; j < 2 * n; j++) aug->data[i][j] -= factor * aug->data[k][j];
                printf("ELIMINATE,%d,%d,%d,%.10g\n", k, i, k, factor);
                matrix_print(aug, "step");
            }
        }
    }
    printf("INFO,Gauss-Jordan [A | I] -> [I | A^-1] Complete!\n");
    matrix_print(aug, "step");

    // Verify residual ||A * A^-1 - I||_inf in C
    double max_err = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            for (int k = 0; k < n; k++) s += A->data[i][k] * aug->data[k][n + j];
            double target = (i == j) ? 1.0 : 0.0;
            double err = fabs(s - target);
            if (err > max_err) max_err = err;
        }
    }
    printf("RESIDUAL,%.10e\n", max_err);
    return aug;
}

Vector* lu_decomposition(Matrix* A, Vector* b) {
    int n = A->rows;
    Matrix* aug = create_augmented_matrix(A, b);
    printf("INFO,Initial Matrix for LU Factorization\n");
    matrix_print(aug, "step");
    for (int k = 0; k < n - 1; k++) {
        int pivot_row = k;
        double max_val = fabs(aug->data[k][k]);
        for (int i = k + 1; i < n; i++) {
            if (fabs(aug->data[i][k]) > max_val) { max_val = fabs(aug->data[i][k]); pivot_row = i; }
        }
        if (pivot_row != k) {
            swap_rows(aug, k, pivot_row);
            printf("SWAP,%d,%d,%d\n", k, k, pivot_row);
            matrix_print(aug, "step");
        }
        if (fabs(aug->data[k][k]) < 1e-12) {
            printf("ERROR,Zero pivot encountered at row %d\n", k);
            matrix_free(aug); return NULL;
        }
        for (int i = k + 1; i < n; i++) {
            double factor = aug->data[i][k] / aug->data[k][k];
            printf("ELIMINATE,%d,%d,%d,%.10g\n", k, i, k, factor);
            for (int j = k + 1; j < n; j++) aug->data[i][j] -= factor * aug->data[k][j];
            aug->data[i][k] = factor;
            matrix_print(aug, "step");
        }
    }

    if (fabs(aug->data[n - 1][n - 1]) < 1e-12) {
        printf("ERROR,Zero pivot encountered at row %d\n", n - 1);
        matrix_free(aug); return NULL;
    }

    Matrix* L_aug = matrix_create(n, n + 1);
    for (int i = 0; i < n; i++) {
        L_aug->data[i][i] = 1.0;
        for (int j = 0; j < i; j++) L_aug->data[i][j] = aug->data[i][j];
        L_aug->data[i][n] = aug->data[i][n];
    }
    printf("INFO,Forward Substitution Setup (Ly = Pb)\n");
    matrix_print(L_aug, "step");
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j < i; j++) sum += L_aug->data[i][j] * L_aug->data[j][n];
        L_aug->data[i][n] -= sum;
        for (int j = 0; j < i; j++) L_aug->data[i][j] = 0.0;
        printf("FORWARDSOLVE,%d,%.10g\n", i, L_aug->data[i][n]);
        matrix_print(L_aug, "step");
    }

    Matrix* U_aug = matrix_create(n, n + 1);
    for (int i = 0; i < n; i++) {
        for (int j = i; j < n; j++) U_aug->data[i][j] = aug->data[i][j];
        U_aug->data[i][n] = L_aug->data[i][n];
    }
    printf("INFO,Back Substitution Setup (Ux = y)\n");
    matrix_print(U_aug, "step");

    Vector* x = vector_create(n);
    for (int i = n - 1; i >= 0; i--) {
        double sum = 0.0;
        for (int j = i + 1; j < n; j++) sum += U_aug->data[i][j] * U_aug->data[j][n];
        U_aug->data[i][n] = (U_aug->data[i][n] - sum) / U_aug->data[i][i];
        for (int j = i + 1; j < n; j++) U_aug->data[i][j] = 0.0;
        U_aug->data[i][i] = 1.0;
        x->data[i] = U_aug->data[i][n];
        printf("BACKSOLVE,%d,%.10g\n", i, x->data[i]);
        matrix_print(U_aug, "step");
    }
    matrix_free(L_aug); matrix_free(U_aug); matrix_free(aug);
    return x;
}

Vector* gauss_seidel(Matrix* A, Vector* b, double tolerance, int max_iter) {
    int n = A->rows;
    for (int i = 0; i < n; i++) {
        if (fabs(A->data[i][i]) < 1e-12) {
            printf("ERROR,Zero diagonal element at row %d prevents Gauss-Seidel convergence.\n", i);
            return NULL;
        }
    }

    Vector* x = vector_create(n);

    printf("GS_ITER_START,0\n");
    for (int i = 0; i < n; i++) {
        printf("GS_EQ,$x_{%d} = 0$\n", i + 1);
    }
    printf("GS_ITER_END,0,0.0\n");

    for (int iter = 1; iter <= max_iter; iter++) {
        double max_ea = 0.0;

        printf("GS_ITER_START,%d\n", iter);

        for (int i = 0; i < n; i++) {
            double sum = 0.0;
            char eq_buffer[2048];
            char temp[128];
            eq_buffer[0] = '\0';

            snprintf(eq_buffer, sizeof(eq_buffer), "GS_EQ,$x_{%d} = \\frac{1}{%.4g}[%.4g", i + 1, A->data[i][i], b->data[i]);

            double x_old = x->data[i];

            for (int j = 0; j < n; j++) {
                if (j != i) {
                    sum += A->data[i][j] * x->data[j];
                    snprintf(temp, sizeof(temp), " - (%.4g)(%.4g)", A->data[i][j], x->data[j]);
                    strncat(eq_buffer, temp, sizeof(eq_buffer) - strlen(eq_buffer) - 1);
                }
            }

            double x_new = (b->data[i] - sum) / A->data[i][i];
            double diff = fabs(x_new - x_old);
            x->data[i] = x_new;

            double approx_err = 0.0;
            if (fabs(x_new) > 1e-14) {
                approx_err = (diff / fabs(x_new)) * 100.0;
            } else {
                approx_err = diff * 100.0;
            }

            if (approx_err > max_ea) {
                max_ea = approx_err;
            }

            snprintf(temp, sizeof(temp), "] = %.4g \\quad (\\epsilon_a = %.2f)$", x_new, approx_err);
            strncat(eq_buffer, temp, sizeof(eq_buffer) - strlen(eq_buffer) - 1);

            printf("%s\n", eq_buffer);
        }

        printf("GS_ITER_END,%d,%e\n", iter, max_ea);

        double res_inf = compute_residual_inf(A, b, x);
        if (isnan(res_inf) || isinf(res_inf) || res_inf > 1e14) {
            printf("ERROR,Gauss-Seidel diverged (residual ||Ax - b|| exceeded 1e14).\n");
            vector_free(x);
            return NULL;
        }

        if ((iter > 1 && max_ea < tolerance && res_inf < fmax(tolerance, 1e-4)) || res_inf < 1e-12) {
            printf("INFO,Gauss-Seidel Converged successfully in %d iterations!\n", iter);
            break;
        } else if (iter == max_iter) {
            printf("INFO,Halted at %d steps. Matrix may be diverging!\n", max_iter);
        }
    }
    return x;
}

Vector* jacobi_iteration(Matrix* A, Vector* b, double tolerance, int max_iter) {
    int n = A->rows;
    for (int i = 0; i < n; i++) {
        if (fabs(A->data[i][i]) < 1e-12) {
            printf("ERROR,Zero diagonal element at row %d prevents Jacobi convergence.\n", i);
            return NULL;
        }
    }

    Vector* x = vector_create(n);
    Vector* x_next = vector_create(n);

    printf("GS_ITER_START,0\n");
    for (int i = 0; i < n; i++) {
        printf("GS_EQ,$x_{%d}^{(0)} = 0$\n", i + 1);
    }
    printf("GS_ITER_END,0,0.0\n");

    for (int iter = 1; iter <= max_iter; iter++) {
        double max_ea = 0.0;
        printf("GS_ITER_START,%d\n", iter);

        for (int i = 0; i < n; i++) {
            double sum = 0.0;
            char eq_buffer[2048];
            char temp[128];
            eq_buffer[0] = '\0';

            snprintf(eq_buffer, sizeof(eq_buffer), "GS_EQ,$x_{%d}^{(%d)} = \\frac{1}{%.4g}[%.4g", i + 1, iter, A->data[i][i], b->data[i]);

            for (int j = 0; j < n; j++) {
                if (j != i) {
                    sum += A->data[i][j] * x->data[j];
                    snprintf(temp, sizeof(temp), " - (%.4g)(%.4g)", A->data[i][j], x->data[j]);
                    strncat(eq_buffer, temp, sizeof(eq_buffer) - strlen(eq_buffer) - 1);
                }
            }

            double val_new = (b->data[i] - sum) / A->data[i][i];
            double diff = fabs(val_new - x->data[i]);
            x_next->data[i] = val_new;

            double approx_err = (fabs(val_new) > 1e-14) ? ((diff / fabs(val_new)) * 100.0) : (diff * 100.0);
            if (approx_err > max_ea) max_ea = approx_err;

            snprintf(temp, sizeof(temp), "] = %.4g \\quad (\\epsilon_a = %.2f)$", val_new, approx_err);
            strncat(eq_buffer, temp, sizeof(eq_buffer) - strlen(eq_buffer) - 1);
            printf("%s\n", eq_buffer);
        }

        for (int i = 0; i < n; i++) x->data[i] = x_next->data[i];
        printf("GS_ITER_END,%d,%e\n", iter, max_ea);

        double res_inf = compute_residual_inf(A, b, x);
        if (isnan(res_inf) || isinf(res_inf) || res_inf > 1e14) {
            printf("ERROR,Jacobi iteration diverged (residual ||Ax - b|| exceeded 1e14).\n");
            vector_free(x);
            vector_free(x_next);
            return NULL;
        }

        if ((iter > 1 && max_ea < tolerance && res_inf < fmax(tolerance, 1e-4)) || res_inf < 1e-12) {
            printf("INFO,Jacobi Converged successfully in %d iterations!\n", iter);
            break;
        } else if (iter == max_iter) {
            printf("INFO,Halted at %d steps. Matrix may be diverging!\n", max_iter);
        }
    }
    vector_free(x_next);
    return x;
}
