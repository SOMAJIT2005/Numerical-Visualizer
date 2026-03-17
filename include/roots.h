#ifndef ROOTS_H
#define ROOTS_H

// Math Parser Management
int init_math_parser(const char* equation);
void cleanup_math_parser();

// Mathematical Evaluations
double f(double x);
double df(double x);
double d2f(double x);

// Core Solver Orchestrator
void run_root_solver(const char* method, double val1, double val2);

#endif