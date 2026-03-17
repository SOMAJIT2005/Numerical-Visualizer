CC = gcc
CFLAGS = -Wall -Iinclude -O3

ROOT_TARGET = build/engine.exe
MATRIX_TARGET = build/matrix_engine.exe

all: $(ROOT_TARGET) $(MATRIX_TARGET)

# Root Finding Engine (Now Modular!)
$(ROOT_TARGET): src/engine_main.c src/roots.c src/tinyexpr.c
	@mkdir -p build
	$(CC) src/engine_main.c src/roots.c src/tinyexpr.c $(CFLAGS) -o $(ROOT_TARGET)

# Linear Algebra Engine
$(MATRIX_TARGET): src/matrix_main.c src/linalg.c
	@mkdir -p build
	$(CC) src/matrix_main.c src/linalg.c $(CFLAGS) -o $(MATRIX_TARGET)

clean:
	rm -rf build/*