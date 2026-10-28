// 没有约束的模板：错误发生在函数体深处
#include <string>
#include <vector>
#include <numeric>
int main() { std::vector<std::string> v{"a"}; std::string x = std::accumulate(v.begin(), v.end(), 0); }
