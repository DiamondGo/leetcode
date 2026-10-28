// 实验 14：线程池 + 条件变量的正确写法，用 TSan 检查。
// 要点：1) wait 必须带谓词（防虚假唤醒和丢失唤醒）；2) 关闭时先置标志再 notify_all；3) 任务在锁外执行；
//       4) 析构要 join；5) 用 packaged_task + future 把返回值和异常带回调用方。
#include <condition_variable>
#include <cstdio>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>

class ThreadPool {
 public:
  explicit ThreadPool(unsigned n) { for (unsigned i = 0; i < n; ++i) workers_.emplace_back([this] { loop(); }); }
  ~ThreadPool() {
    { std::lock_guard<std::mutex> lk(m_); stop_ = true; }       // 先置标志（在锁里），再唤醒
    cv_.notify_all();
    for (auto& t : workers_) t.join();
  }
  template <class F, class... A>
  auto submit(F&& f, A&&... a) -> std::future<std::invoke_result_t<F, A...>> {
    using R = std::invoke_result_t<F, A...>;
    auto task = std::make_shared<std::packaged_task<R()>>(std::bind(std::forward<F>(f), std::forward<A>(a)...));
    auto fut = task->get_future();
    { std::lock_guard<std::mutex> lk(m_); if (stop_) throw std::runtime_error("pool stopped"); q_.push([task] { (*task)(); }); }
    cv_.notify_one();
    return fut;
  }
 private:
  void loop() {
    for (;;) {
      std::function<void()> job;
      {
        std::unique_lock<std::mutex> lk(m_);
        cv_.wait(lk, [this] { return stop_ || !q_.empty(); });   // 带谓词的 wait
        if (q_.empty()) return;                                    // stop_ 且已排空
        job = std::move(q_.front()); q_.pop();
      }
      job();                                                       // 锁外执行
    }
  }
  std::vector<std::thread> workers_; std::queue<std::function<void()>> q_;
  std::mutex m_; std::condition_variable cv_; bool stop_ = false;
};

int main() {
  ThreadPool pool(4);
  std::vector<std::future<long>> fs;
  for (int i = 1; i <= 8; ++i) fs.push_back(pool.submit([](int n) { long s = 0; for (int k = 1; k <= n * 100000; ++k) s += k; return s; }, i));
  long total = 0; for (auto& f : fs) total += f.get();
  std::printf("8 个任务的结果之和 = %ld\n", total);
  auto bad = pool.submit([]() -> int { throw std::runtime_error("任务里抛出的异常"); });
  try { bad.get(); } catch (const std::exception& e) { std::printf("异常通过 future 传回调用方：%s\n", e.what()); }
}
