#include <numeric>
#include <vector>

using namespace std;

int main() {
    vector<double> v(240000, 0);
    iota(v.begin(), v.end(), 0);
    return 0;
}