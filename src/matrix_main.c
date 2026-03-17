#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "linalg.h" // Pull in our header

int main(int argc, char* argv[]) {
    // 1. Basic Argument Checks
    if (argc < 3) return 1;
    const char* method = argv[1];
    int n = atoi(argv[2]);
    if (argc < 3 + n*n + n) return 1;
    
    // 2. Build the Matrices from Python's string arguments
    Matrix* A = matrix_create(n, n);
    Vector* b = vector_create(n);
    int arg_idx = 3;
    for (int i = 0; i < n; i++) { 
        for (int j = 0; j < n; j++) A->data[i][j] = atof(argv[arg_idx++]); 
    }
    for (int i = 0; i < n; i++) b->data[i] = atof(argv[arg_idx++]);
    
    // 3. Route to the correct Mathematical Solver
    Vector* solution = NULL;
    
    if (strcmp(method, "gaussian") == 0) solution = gaussian_elimination(A, b);
    else if (strcmp(method, "gauss_jordan") == 0) solution = gauss_jordan(A, b);
    else if (strcmp(method, "lu") == 0) solution = lu_decomposition(A, b);
    else if (strcmp(method, "gauss_seidel") == 0) {
        double tol = (argc > arg_idx) ? atof(argv[arg_idx++]) : 1e-6;
        int max_it = (argc > arg_idx) ? atoi(argv[arg_idx++]) : 100;
        solution = gauss_seidel(A, b, tol, max_it);
    }
    
    // 4. Cleanup Memory
    if (solution) vector_free(solution);
    matrix_free(A); 
    vector_free(b);
    
    return 0;
}