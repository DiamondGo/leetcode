// 实验 6a：未定义行为（UB）会被编译器“利用”。
// 有符号整数溢出是 UB，编译器可以假设它不会发生。下面这个函数在 -O0 下按机器行为回绕，
// -O2 下编译器认为 n+10 不可能比 n 小，直接把循环次数当作 10。
#include <climits>
#include <cstdio>

__attribute__((noinline)) int count_steps(int n) {
  int c = 0;
  for (int i = n; i < n + 10; ++i) ++c;   // n 接近 INT_MAX 时，n + 10 溢出
  return c;
}
__attribute__((noinline)) int count_steps_unsigned(unsigned n) {   // 无符号回绕有明确定义
  int c = 0;
  for (unsigned i = n; i < n + 10; ++i) ++c;
  return c;
}

int main() {
  std::printf("count_steps(INT_MAX - 5)           = %d\n", count_steps(INT_MAX - 5));
  std::printf("count_steps_unsigned(UINT_MAX - 5) = %d\n", count_steps_unsigned(UINT_MAX - 5));
}
