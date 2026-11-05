#ifndef ROOTS_H
#define ROOTS_H

// Math Parser Management
int init_math_parser(const char* equation);
void cleanup_math_parser(void);

// Mathematical Evaluations
double f(double x);
double df(double x);
double d2f(double x);

// Core Solver Orchestrator
void run_root_solver(const char* method, double val1, double val2, double tol);

// Live Function & Bracket Preview (Evaluated in C)
void run_curve_preview(double xmin, double xmax, double a_val, double b_val, int has_a, int has_b);

// Horner's Method & Polynomial Root Deflation Lab (Evaluated in C)
void run_horner_lab(double x0, int deg, const double* coeffs);

#endif
