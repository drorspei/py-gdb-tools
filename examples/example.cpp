#include <cstddef>


int foo(size_t a) {
	return a + 5;
}

int main() {
	size_t b = 5;
	size_t c = foo(b);
	return c;
}
