// 实验 9：几个“凭直觉会猜错”的性能微基准。-O2。数字取决于机器，只看相对大小。
// 微基准容易被编译器优化掉或测错，这里用 asm volatile 阻止结果被删除；严肃测量请用 Google Benchmark。
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <functional>
#include <list>
#include <numeric>
#include <random>
#include <vector>

template <class F> double ms(F&& f) { auto t = std::chrono::steady_clock::now(); f(); return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t).count(); }
template <class T> inline void keep(T&& v) { asm volatile("" : : "g"(v) : "memory"); }

// --- 1. 分支预测 ---
long branchy(const std::vector<int>& a) {
  long s = 0;
  for (int r = 0; r < 20; ++r) for (int x : a) if (x >= 128) { s += x; asm volatile(""); }   // asm 防止编译器把分支改成无分支的 cmov/向量化
  return s;
}

// --- 2. 虚函数 / CRTP / std::function / 函数指针 ---
struct IShape { virtual ~IShape() = default; virtual int f(int) const = 0; };
struct Sq : IShape { int f(int x) const override { return x * 2 + 1; } };
struct Cu : IShape { int f(int x) const override { return x * 3 + 1; } };   // 第二个实现：编译器不能再推测只有一种动态类型
struct SqCRTP { int f(int x) const { return x * 2 + 1; } };
template <class D> struct Base { int call(int x) const { return static_cast<const D*>(this)->f(x); } };
struct Derived : Base<Derived> { int f(int x) const { return x * 2 + 1; } };
__attribute__((noinline)) int plain(int x) { return x * 2 + 1; }

int main() {
  std::mt19937 rng(1); std::vector<int> a(1 << 20); for (int& x : a) x = rng() % 256;
  keep(branchy(a));
  double unsorted = ms([&] { keep(branchy(a)); });
  std::sort(a.begin(), a.end());
  double sorted = ms([&] { keep(branchy(a)); });
  std::printf("[分支预测] 同一个循环：随机数据 %.1f ms，先排序 %.1f ms（%.1f 倍）\n", unsorted, sorted, unsorted / sorted);

  const int N = 1 << 20;
  std::vector<int> v2(N); std::iota(v2.begin(), v2.end(), 0);
  std::list<int> seq(v2.begin(), v2.end());                       // 节点按顺序分配，内存里大体相邻
  std::vector<int> r2 = v2; std::shuffle(r2.begin(), r2.end(), rng);
  std::list<int> scat(r2.begin(), r2.end()); scat.sort();          // sort 只重连指针：遍历顺序与内存位置无关
  double tv = ms([&] { long s = 0; for (int r = 0; r < 20; ++r) for (int x : v2) s += x; keep(s); });
  double tl = ms([&] { long s = 0; for (int r = 0; r < 20; ++r) for (int x : seq) s += x; keep(s); });
  double ts = ms([&] { long s = 0; for (int r = 0; r < 20; ++r) for (int x : scat) s += x; keep(s); });
  std::printf("[缓存局部性] 求和 %d 个 int：vector %.1f ms | list(节点相邻) %.1f ms | list(节点分散) %.1f ms（分散的比 vector 慢 %.0f 倍）\n", N, tv, tl, ts, ts / tv);

  const long K = 300'000'000;   // 每次调用的结果是下一次的输入，防止被向量化或算出闭式解
  Sq sq; Cu cu; IShape* ip = (rng() % 2) ? (IShape*)&sq : (IShape*)&cu; asm volatile("" : "+r"(ip));   // 运行时才知道动态类型
  Derived dd; SqCRTP cr; int (*fp)(int) = plain; asm volatile("" : "+r"(fp));
  std::function<int(int)> sf = [](int x) { return x * 2 + 1; };
  double t1 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = ip->f(x); keep(x); });
  double t2 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = dd.call(x); keep(x); });
  double t3 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = fp(x); keep(x); });
  double t4 = ms([&] { int x = 1; for (long i = 0; i < K; ++i) x = sf(x); keep(x); });
  std::printf("[调用方式] %ld 次调用：虚函数 %.0f ms | CRTP(可内联) %.0f ms | 函数指针 %.0f ms | std::function %.0f ms\n", K, t1, t2, t3, t4);
  (void)cr;
}
