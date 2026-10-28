// 实验 11b：这个文件故意编译失败，用来对比“不满足约束”的报错有多清楚。
#include <concepts>
#include <string>
template <std::integral T> T twice(T x) { return x + x; }
int main() { return twice(std::string("a")).size(); }
