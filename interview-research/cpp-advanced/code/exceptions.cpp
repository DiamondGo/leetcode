// 实验 12：异常安全与异常的真实开销。
#include <chrono>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// --- 强异常保证：先在副本上做，最后用不会抛的 swap 提交（copy-and-swap）---
class Buffer {
  char* p_; size_t n_;
 public:
  static inline int fail_after = -1;   // 测试用：第 fail_after 次分配时抛异常
  static char* alloc(size_t n) { if (fail_after == 0) throw std::bad_alloc(); if (fail_after > 0) --fail_after; return new char[n]; }
  Buffer(const char* s) : p_(alloc(std::strlen(s) + 1)), n_(std::strlen(s)) { std::memcpy(p_, s, n_ + 1); }
  Buffer(const Buffer& o) : p_(alloc(o.n_ + 1)), n_(o.n_) { std::memcpy(p_, o.p_, n_ + 1); }
  Buffer(Buffer&& o) noexcept : p_(std::exchange(o.p_, nullptr)), n_(std::exchange(o.n_, 0)) {}
  ~Buffer() { delete[] p_; }
  void swap(Buffer& o) noexcept { std::swap(p_, o.p_); std::swap(n_, o.n_); }
  // 强保证：参数按值传递（拷贝可能抛，但此时 *this 还没动），然后 noexcept 的 swap
  Buffer& operator=(Buffer o) noexcept { swap(o); return *this; }
  // 对比：不安全的赋值——先释放旧的，再分配新的；分配失败时对象已损坏
  void bad_assign(const char* s) { delete[] p_; p_ = nullptr; n_ = 0; p_ = alloc(std::strlen(s) + 1); n_ = std::strlen(s); std::memcpy(p_, s, n_ + 1); }
  const char* c_str() const { return p_ ? p_ : "(null：对象已损坏)"; }
};

// --- 异常 vs 返回码 的成本 ---
__attribute__((noinline)) int thrower(int x, bool fail) { if (fail) throw std::runtime_error("x"); return x + 1; }
__attribute__((noinline)) int coder(int x, bool fail, int* out) { if (fail) return -1; *out = x + 1; return 0; }

int main() {
  std::puts("== 强异常保证 ==");
  { Buffer a("hello"), b("world"); Buffer::fail_after = 0;
    try { a = b; } catch (...) { std::printf("copy-and-swap 赋值：拷贝参数时分配失败，a 仍为 \"%s\"\n", a.c_str()); }   // 抛异常发生在按值参数的拷贝里，此时 a 还没被改动
    Buffer::fail_after = -1; }
  { Buffer a("hello"); Buffer::fail_after = 0;
    try { a.bad_assign("world"); } catch (...) { std::printf("先释放后分配的赋值，分配失败：a 变成 %s\n", a.c_str()); }
    Buffer::fail_after = -1; }

  std::puts("== 异常的开销：正常路径 vs 抛出路径 ==");
  const int N = 20'000'000;
  auto t0 = std::chrono::steady_clock::now(); long s = 0;
  for (int i = 0; i < N; ++i) { try { s += thrower(i, false); } catch (...) {} }
  double ok_exc = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / N;
  t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < N; ++i) { int o; if (coder(i, false, &o) == 0) s += o; }
  double ok_code = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / N;
  const int M = 200'000;
  t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < M; ++i) { try { s += thrower(i, true); } catch (...) { ++s; } }
  double fail_exc = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / M;
  t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < M; ++i) { int o; if (coder(i, true, &o) != 0) ++s; }
  double fail_code = std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - t0).count() / M;
  std::printf("不出错时：try/catch 包裹的调用 %.2f ns/次，返回码 %.2f ns/次（几乎没有差别：零开销模型）\n", ok_exc, ok_code);
  std::printf("出错时  ：抛异常 %.0f ns/次，返回码 %.2f ns/次（异常慢 %.0f 倍，所以别把异常用作常规控制流）\n", fail_exc, fail_code, fail_exc / (fail_code > 0.01 ? fail_code : 0.01));
  if (s == 42) std::puts("");
}
