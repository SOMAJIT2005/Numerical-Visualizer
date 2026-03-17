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
        for (int j = 0; j < mat->cols; j++) printf(",%f", mat->data[i][j]);
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
            printf("ELIMINATE,%d,%d,%d,%f\n", k, i, k, factor);
            for (int j = k; j <= n; j++) aug->data[i][j] -= factor * aug->data[k][j];
            matrix_print(aug, "step");
        }
    }
    
    Vector* x = vector_create(n);
    printf("INFO,Back-Substitution Phase\n");
    for (int i = n - 1; i >= 0; i--) {
        double sum = 0.0;
        for (int j = i + 1; j < n; j++) sum += aug->data[i][j] * x->data[j];
        x->data[i] = (aug->data[i][n] - sum) / aug->data[i][i];
        printf("BACKSOLVE,%d,%f\n", i, x->data[i]);
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
        printf("NORMALIZE,%d,%f\n", k, diag);
        matrix_print(aug, "step");
        for (int i = 0; i < n; i++) {
            if (i != k) {
                double factor = aug->data[i][k];
                for (int j = k; j <= n; j++) aug->data[i][j] -= factor * aug->data[k][j];
                printf("ELIMINATE,%d,%d,%d,%f\n", k, i, k, factor);
                matrix_print(aug, "step");
            }
        }
    }
    Vector* x = vector_create(n);
    for (int i = 0; i < n; i++) x->data[i] = aug->data[i][n];
    matrix_free(aug); return x;
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
            printf("ELIMINATE,%d,%d,%d,%f\n", k, i, k, factor);
            for (int j = k + 1; j < n; j++) aug->data[i][j] -= factor * aug->data[k][j];
            aug->data[i][k] = factor;
            matrix_print(aug, "step");
        }
    }
    
    Matrix* L_aug = matrix_create(n, n+1);
    for(int i=0; i<n; i++) {
        L_aug->data[i][i] = 1.0;
        for(int j=0; j<i; j++) L_aug->data[i][j] = aug->data[i][j];
        L_aug->data[i][n] = aug->data[i][n];
    }
    printf("INFO,Forward Substitution Setup (Ly = Pb)\n");
    matrix_print(L_aug, "step");
    for(int i=0; i<n; i++) {
        double sum = 0.0;
        for(int j=0; j<i; j++) sum += L_aug->data[i][j] * L_aug->data[j][n];
        L_aug->data[i][n] -= sum;
        for(int j=0; j<i; j++) L_aug->data[i][j] = 0.0;
        printf("FORWARDSOLVE,%d,%f\n", i, L_aug->data[i][n]);
        matrix_print(L_aug, "step");
    }
    
    Matrix* U_aug = matrix_create(n, n+1);
    for(int i=0; i<n; i++) {
        for(int j=i; j<n; j++) U_aug->data[i][j] = aug->data[i][j];
        U_aug->data[i][n] = L_aug->data[i][n];
    }
    printf("INFO,Back Substitution Setup (Ux = y)\n");
    matrix_print(U_aug, "step");
    
    Vector* x = vector_create(n);
    for(int i=n-1; i>=0; i--) {
        double sum = 0.0;
        for(int j=i+1; j<n; j++) sum += U_aug->data[i][j] * U_aug->data[j][n];
        U_aug->data[i][n] = (U_aug->data[i][n] - sum) / U_aug->data[i][i];
        for(int j=i+1; j<n; j++) U_aug->data[i][j] = 0.0;
        U_aug->data[i][i] = 1.0;
        x->data[i] = U_aug->data[i][n];
        printf("BACKSOLVE,%d,%f\n", i, x->data[i]);
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
    for(int i=0; i<n; i++) {
        printf("GS_EQ,$x_{%d} = 0$\n", i+1);
    }
    printf("GS_ITER_END,0,0.0\n");

    for (int iter = 1; iter <= max_iter; iter++) {
        double max_ea = 0.0; // Strictly track % error
        
        printf("GS_ITER_START,%d\n", iter);
        
        for (int i = 0; i < n; i++) {
            double sum = 0.0;
            char eq_buffer[2048];
            char temp[128];
            eq_buffer[0] = '\0';
            
            sprintf(eq_buffer, "GS_EQ,$x_{%d} = \\frac{1}{%.4g}[%.4g", i+1, A->data[i][i], b->data[i]);
            
            double x_old = x->data[i];

            for (int j = 0; j < n; j++) {
                if (j != i) {
                    sum += A->data[i][j] * x->data[j]; 
                    sprintf(temp, " - (%.4g)(%.4g)", A->data[i][j], x->data[j]);
                    strcat(eq_buffer, temp);
                }
            }
            
            double x_new = (b->data[i] - sum) / A->data[i][i];
            double diff = fabs(x_new - x_old);
            x->data[i] = x_new;
            
            double approx_err = 0.0;
            if (iter == 1 && x_old == 0.0 && x_new != 0.0) {
                approx_err = 100.0;
            } else if (fabs(x_new) > 1e-14) {
                approx_err = (diff / fabs(x_new)) * 100.0;
            }
            
            if (approx_err > max_ea) {
                max_ea = approx_err;
            }
            
            // Output value explicitly as a percentage!
            sprintf(temp, "] = %.4g \\quad (\\\\epsilon_a = %.2f)$", x_new, approx_err);
            strcat(eq_buffer, temp);
            
            printf("%s\n", eq_buffer); 
        }
        
        printf("GS_ITER_END,%d,%e\n", iter, max_ea);
        
        if (iter > 1 && max_ea < tolerance) {
            printf("INFO,Gauss-Seidel Converged successfully in %d iterations!\n", iter);
            break;
        } else if (iter == max_iter) {
            printf("INFO,Halted at %d steps. Matrix may be diverging!\n", max_iter);
        }
    }
    return x;
}