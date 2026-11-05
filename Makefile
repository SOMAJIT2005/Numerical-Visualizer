CC = gcc
CFLAGS = -Wall -Wextra -Iinclude -O2
LDFLAGS = -lm

ROOT_TARGET = build/engine.exe
MATRIX_TARGET = build/matrix_engine.exe
NUMLAB_TARGET = build/numlab_engine.exe

all: $(ROOT_TARGET) $(MATRIX_TARGET) $(NUMLAB_TARGET)

# Unit 2: Root Finding & Horner Engine
$(ROOT_TARGET): src/engine_main.c src/roots.c src/tinyexpr.c include/roots.h include/tinyexpr.h
	@mkdir -p build
	$(CC) src/engine_main.c src/roots.c src/tinyexpr.c $(CFLAGS) -o $(ROOT_TARGET) $(LDFLAGS)

# Unit 3: Linear Algebra & Matrix Inversion Engine
$(MATRIX_TARGET): src/matrix_main.c src/linalg.c include/linalg.h
	@mkdir -p build
	$(CC) src/matrix_main.c src/linalg.c $(CFLAGS) -o $(MATRIX_TARGET) $(LDFLAGS)

# Units 1, 4, 5, 6A, 6B: Errors, Optimization, Interpolation, Quadrature & ODE Engine
$(NUMLAB_TARGET): src/numlab_main.c src/numlab.c src/tinyexpr.c include/numlab.h include/tinyexpr.h
	@mkdir -p build
	$(CC) src/numlab_main.c src/numlab.c src/tinyexpr.c $(CFLAGS) -o $(NUMLAB_TARGET) $(LDFLAGS)

test: all
	python -m unittest discover -s tests -p "test_suite.py" -v

clean:
	rm -rf build/*
