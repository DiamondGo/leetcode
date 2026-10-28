// 实验 6b：AddressSanitizer 抓“释放后使用”和“越界”。用法：g++ -fsanitize=address -g
#include <cstdio>
#include <string_view>
#include <string>
#include <vector>

int main(int argc, char**) {
  if (argc > 2) {   // 第 2 个演示：string_view 悬空
    std::string_view sv;
    { std::string tmp(100, 'x'); sv = tmp; }
    std::printf("%c\n", sv[0]);
    return 0;
  }
  std::vector<int> v{1, 2, 3};
  int* p = &v[0];
  v.push_back(4);        // 可能重新分配，p 悬空（迭代器/指针失效）
  v.push_back(5);
  std::printf("%d\n", *p);   // 释放后使用
}
