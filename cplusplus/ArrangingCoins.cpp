#include <cmath>
#include <iostream>

class Solution {
public:
    int arrangeCoins(int n) {
        // x*(x+1)/2 = n
        // x^2 + x -2n = 0
        // ((1 + 8n)^0.5 - 1) /2
        return floor((sqrt(8 * double(n) + 1) -1) / 2);
    }
};

int main() {
    Solution s;
    std::cout << s.arrangeCoins(5) << std::endl;
}