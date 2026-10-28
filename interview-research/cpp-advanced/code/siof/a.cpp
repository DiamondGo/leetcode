// 实验 16：静态初始化顺序问题（static initialization order fiasco）。
// 不同翻译单元里的全局对象，动态初始化的先后顺序没有规定。这里 a.cpp 的全局变量在初始化时读取 b.cpp 的全局变量。
#include <cstdio>
extern int b_value;
int a_copy = b_value + 1;       // 动态初始化：依赖另一个翻译单元里的 b_value
int main() { std::printf("a_copy = %d（期望 b_value+1 = 101）\n", a_copy); }
