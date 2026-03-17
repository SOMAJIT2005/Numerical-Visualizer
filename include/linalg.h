#ifndef LINALG_H
#define LINALG_H

// Data Structures
typedef struct { int rows; int cols; double** data; } Matrix;
typedef struct { int size; double* data; } Vector;

// Memory Management & Utils
Matrix* matrix_create(int rows, int cols);
void matrix_free(Matrix* mat);
Vector* vector_create(int size);
void vector_free(Vector* vec);
void matrix_print(Matrix* mat, const char* label);
Matrix* create_augmented_matrix(Matrix* A, Vector* b);
void swap_rows(Matrix* mat, int row1, int row2);

// Mathematical Solvers
Vector* gaussian_elimination(Matrix* A, Vector* b);
Vector* gauss_jordan(Matrix* A, Vector* b);
Vector* lu_decomposition(Matrix* A, Vector* b);
Vector* gauss_seidel(Matrix* A, Vector* b, double tolerance, int max_iter);

#endif