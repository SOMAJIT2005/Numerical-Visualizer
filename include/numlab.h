#ifndef NUMLAB_H
#define NUMLAB_H

// Unit 1: Errors, Taylor Series, Cancellation & IEEE-754 Bit Analysis
int run_errors_h_sweep(const char* eq, double x0);
int run_errors_taylor(const char* eq, double x0, double x_eval, int order);
int run_errors_cancellation(void);
int run_errors_ieee754(double val, double approx, int sig_figs);

// Unit 4: 1D & 2D Optimization
int run_opt_1d(const char* method, const char* eq, double v1, double v2, double tol);
int run_opt_2d(const char* method, const char* eq, double x0, double y0, double param);

// Unit 5: Interpolation & Least-Squares Curve Fitting
int run_interpolation(const char* mode, double x_q, int deg, int n, const double* xs, const double* ys);

// Unit 6A: Numerical Integration (Quadrature)
int run_quadrature(const char* method, const char* eq, double a, double b, int n);

// Unit 6B: ODE Initial-Value Problems
int run_ode_solver(const char* method, const char* eq1, const char* eq2,
                   double t0, double y0, double z0, double t_end, double h);

#endif
