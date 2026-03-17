#include <stdio.h>
#include <stdlib.h>
#include "roots.h"

int main(int argc, char* argv[]) {
    if (argc < 5) {
        printf("ERROR,Insufficient arguments.\n");
        return 1;
    }

    const char* method = argv[1];
    const char* equation = argv[2];
    double val1 = atof(argv[3]);
    double val2 = atof(argv[4]);

    // Initialize the Math Parser
    if (init_math_parser(equation) != 0) {
        printf("ERROR,Invalid equation syntax.\n");
        return 1;
    }

    // Hand off to the Core Solver Module
    run_root_solver(method, val1, val2);

    // Memory Cleanup
    cleanup_math_parser();
    return 0;
}
