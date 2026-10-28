// 实验 5：伪共享（false sharing）。4 个线程各自递增“自己的”计数器，互不共享数据，
// 但如果计数器挤在同一个缓存行（通常 64 字节）里，缓存一致性协议会让这一行在核心之间来回搬运。
#include <atomic>
#include <chrono>
#include <cstdio>
#include <thread>
#include <vector>

struct Packed { std::atomic<long> v{0}; };                   // 相邻放置，8 字节一个
struct alignas(64) Padded { std::atomic<long> v{0}; };       // 每个独占一条缓存行

template <class C>
double run(int threads, long iters) {
  std::vector<C> c(threads);
  auto t0 = std::chrono::steady_clock::now();
  std::vector<std::thread> ts;
  for (int i = 0; i < threads; ++i)
    ts.emplace_back([&, i] { for (long k = 0; k < iters; ++k) c[i].v.fetch_add(1, std::memory_order_relaxed); });
  for (auto& t : ts) t.join();
  return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
}

int main() {
  const long N = 20'000'000;
  std::printf("sizeof(Packed)=%zu sizeof(Padded)=%zu，CPU 核数=%u\n", sizeof(Packed), sizeof(Padded), std::thread::hardware_concurrency());
  for (int th : {1, 2, 4}) {
    double a = run<Packed>(th, N), b = run<Padded>(th, N);
    std::printf("线程数 %d：紧挨着 %7.1f ms | 各占缓存行 %7.1f ms | 慢 %.1f 倍\n", th, a, b, a / b);
  }
}
