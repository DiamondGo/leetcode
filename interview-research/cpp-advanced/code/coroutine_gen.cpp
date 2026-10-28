// 实验 10：C++20 协程的最小实现——一个 generator。
// 协程是“可以暂停和恢复的函数”。编译器把它改写成：堆上的协程帧（保存局部变量和暂停点）+ promise 对象 + 句柄。
// 这里重载 promise 的 operator new 来观察协程帧确实分配在堆上（编译器有时可以省略分配，但不能依赖）。
#include <coroutine>
#include <cstdio>
#include <exception>
#include <new>
#include <utility>

static int g_frame_allocs = 0; static size_t g_frame_bytes = 0;

template <class T>
class Generator {
 public:
  struct promise_type {
    T value;
    Generator get_return_object() { return Generator{std::coroutine_handle<promise_type>::from_promise(*this)}; }
    std::suspend_always initial_suspend() noexcept { return {}; }   // 创建后先挂起，等调用者来取值
    std::suspend_always final_suspend() noexcept { return {}; }     // 结束时不销毁帧，由 Generator 析构负责
    std::suspend_always yield_value(T v) noexcept { value = std::move(v); return {}; }
    void return_void() noexcept {}
    void unhandled_exception() { std::terminate(); }
    static void* operator new(size_t n) { ++g_frame_allocs; g_frame_bytes += n; return ::operator new(n); }
    static void operator delete(void* p) noexcept { ::operator delete(p); }
  };
  explicit Generator(std::coroutine_handle<promise_type> h) : h_(h) {}
  Generator(Generator&& o) noexcept : h_(std::exchange(o.h_, {})) {}
  Generator(const Generator&) = delete;
  ~Generator() { if (h_) h_.destroy(); }
  bool next() { h_.resume(); return !h_.done(); }
  const T& value() const { return h_.promise().value; }
 private:
  std::coroutine_handle<promise_type> h_;
};

Generator<long> fib(int n) {
  long a = 0, b = 1;
  for (int i = 0; i < n; ++i) { co_yield a; long t = a + b; a = b; b = t; }
}

int main() {
  std::printf("创建前 g_frame_allocs=%d\n", g_frame_allocs);
  auto g = fib(10);
  std::printf("创建协程后（函数体还没开始执行）：协程帧分配 %d 次，%zu 字节\n", g_frame_allocs, g_frame_bytes);
  std::printf("前 10 个斐波那契数：");
  while (g.next()) std::printf("%ld ", g.value());
  std::puts("");
}
