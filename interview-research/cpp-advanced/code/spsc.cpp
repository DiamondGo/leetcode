// 实验 4：单生产者单消费者（SPSC）无锁环形队列。
// 正确版本：生产者对 tail 做 release 存储，消费者对 tail 做 acquire 读取，从而保证“先写数据，后发布下标”。
// 错误版本（-DWRONG）：下标全用 relaxed——在 x86 上多半也能跑对，但 ThreadSanitizer 会指出数据竞争，
// 在 ARM 等弱内存序平台上则会真的读到未写好的数据。
#include <atomic>
#include <cstdio>
#include <thread>
#include <vector>

#ifdef WRONG
constexpr auto REL = std::memory_order_relaxed, ACQ = std::memory_order_relaxed;
#else
constexpr auto REL = std::memory_order_release, ACQ = std::memory_order_acquire;
#endif

template <class T, size_t N>   // N 必须是 2 的幂
class SpscQueue {
  static_assert((N & (N - 1)) == 0, "N must be power of two");
  alignas(64) std::atomic<size_t> head_{0};  // 消费者推进
  alignas(64) std::atomic<size_t> tail_{0};  // 生产者推进
  alignas(64) T buf_[N];
 public:
  bool push(const T& v) {
    size_t t = tail_.load(std::memory_order_relaxed);        // 只有自己写 tail，自己读可以 relaxed
    if (t - head_.load(ACQ) == N) return false;               // 满
    buf_[t & (N - 1)] = v;                                    // 先写数据
    tail_.store(t + 1, REL);                                  // 再发布
    return true;
  }
  bool pop(T& out) {
    size_t h = head_.load(std::memory_order_relaxed);
    if (h == tail_.load(ACQ)) return false;                   // 空
    out = buf_[h & (N - 1)];                                  // 先读数据
    head_.store(h + 1, REL);                                  // 再归还槽位
    return true;
  }
};

int main() {
  constexpr int COUNT = 200000;
  SpscQueue<int, 1024> q;
  long long sum = 0;
  std::thread prod([&] { for (int i = 1; i <= COUNT; ++i) while (!q.push(i)) {} });
  std::thread cons([&] { int v, got = 0; while (got < COUNT) if (q.pop(v)) { sum += v; ++got; } });
  prod.join(); cons.join();
  std::printf("sum=%lld 期望=%lld\n", sum, (long long)COUNT * (COUNT + 1) / 2);
}
