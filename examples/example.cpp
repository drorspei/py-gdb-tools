#include <vector>
#include <numeric>
int main() {
	std::vector<double> v(240000, 0);
	std::iota(v.begin(), v.end(), 0);
	return 0;
}
