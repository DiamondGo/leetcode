// 实验 3：内存序的可观察后果——“存储缓冲”（store buffering）测试。
//   线程 1: x=1; r1=y;      线程 2: y=1; r2=x;
// 在顺序一致的世界里，r1 和 r2 不可能同时为 0。但每个核心有存储缓冲，store 可能晚于后面的 load 对别人可见。
// relaxed 下 (0,0) 是允许的结果，x86 上也真的会出现；seq_cst 禁止它（编译器会在 store 后加 mfence 或用 xchg）。
// 本机的结果取决于 CPU 与调度；(0,0) 出现的次数每次都不同，但 seq_cst 应该始终为 0。
#include <atomic>
#include <cstdio>
#include <thread>

template <std::memory_order STORE, std::memory_order LOAD>
long run(int iters) {
  std::atomic<int> x{0}, y{0}, go{0}, done{0};
  int r1 = 0, r2 = 0;
  long both_zero = 0;
  std::thread t1([&] {
    for (int i = 0; i < iters; ++i) {
      while (go.load(std::memory_order_acquire) != 2 * i + 1) {}
      x.store(1, STORE); r1 = y.load(LOAD);
      done.fetch_add(1, std::memory_order_acq_rel);
    }
  });
  std::thread t2([&] {
    for (int i = 0; i < iters; ++i) {
      while (go.load(std::memory_order_acquire) != 2 * i + 1) {}
      y.store(1, STORE); r2 = x.load(LOAD);
      done.fetch_add(1, std::memory_order_acq_rel);
    }
  });
  for (int i = 0; i < iters; ++i) {
    x.store(0, std::memory_order_relaxed); y.store(0, std::memory_order_relaxed);
    done.store(0, std::memory_order_relaxed);
    go.store(2 * i + 1, std::memory_order_release);
    while (done.load(std::memory_order_acquire) != 2) {}
    if (r1 == 0 && r2 == 0) ++both_zero;
  }
  t1.join(); t2.join();
  return both_zero;
}

int main() {
  const int N = 300000;
  long a = run<std::memory_order_relaxed, std::memory_order_relaxed>(N);
  long b = run<std::memory_order_release, std::memory_order_acquire>(N);
  long c = run<std::memory_order_seq_cst, std::memory_order_seq_cst>(N);
  std::printf("%d 轮中 r1==0 且 r2==0 的次数：\n", N);
  std::printf("  relaxed store / relaxed load : %ld\n", a);
  std::printf("  release store / acquire load : %ld   (release/acquire 也不禁止它)\n", b);
  std::printf("  seq_cst store / seq_cst load : %ld\n", c);
}
