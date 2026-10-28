// 实验 13：手写一个简化版 shared_ptr（引用计数 + weak 计数 + 控制块），用 ASan 和 TSan 检查。
// 面试常考“手写 shared_ptr”。要点：控制块独立于对象；计数用原子；最后一个强引用释放对象，
// 最后一个（强+弱）引用释放控制块；拷贝时的 relaxed 递增、释放时的 acq_rel 递减。
#include <atomic>
#include <cstdio>
#include <thread>
#include <utility>
#include <vector>

struct ControlBlock {
  std::atomic<long> strong{1};
  std::atomic<long> weak{1};      // 所有强引用合起来算 1 个弱引用，这样“最后一个弱引用”才是释放控制块的时机
  virtual void destroy_object() noexcept = 0;
  virtual ~ControlBlock() = default;
};
template <class T> struct PtrBlock : ControlBlock {
  T* p; explicit PtrBlock(T* p) : p(p) {}
  void destroy_object() noexcept override { delete p; }
};

template <class T> class Weak;
template <class T>
class Shared {
  T* p_ = nullptr; ControlBlock* cb_ = nullptr;
  friend class Weak<T>;
 public:
  Shared() = default;
  explicit Shared(T* p) : p_(p), cb_(new PtrBlock<T>(p)) {}      // 简化：不处理构造控制块时 new 抛异常的情况（标准库会 delete p）
  Shared(const Shared& o) : p_(o.p_), cb_(o.cb_) { if (cb_) cb_->strong.fetch_add(1, std::memory_order_relaxed); }
  Shared(Shared&& o) noexcept : p_(std::exchange(o.p_, nullptr)), cb_(std::exchange(o.cb_, nullptr)) {}
  Shared& operator=(Shared o) noexcept { std::swap(p_, o.p_); std::swap(cb_, o.cb_); return *this; }
  ~Shared() {
    if (!cb_) return;
    if (cb_->strong.fetch_sub(1, std::memory_order_acq_rel) == 1) {     // 我是最后一个强引用
      cb_->destroy_object();
      if (cb_->weak.fetch_sub(1, std::memory_order_acq_rel) == 1) delete cb_;
    }
  }
  T* get() const { return p_; }
  T& operator*() const { return *p_; }
  T* operator->() const { return p_; }
  long use_count() const { return cb_ ? cb_->strong.load(std::memory_order_relaxed) : 0; }
  explicit operator bool() const { return p_ != nullptr; }
};

template <class T>
class Weak {
  T* p_ = nullptr; ControlBlock* cb_ = nullptr;
 public:
  Weak() = default;
  Weak(const Shared<T>& s) : p_(s.p_), cb_(s.cb_) { if (cb_) cb_->weak.fetch_add(1, std::memory_order_relaxed); }
  Weak(const Weak& o) : p_(o.p_), cb_(o.cb_) { if (cb_) cb_->weak.fetch_add(1, std::memory_order_relaxed); }
  ~Weak() { if (cb_ && cb_->weak.fetch_sub(1, std::memory_order_acq_rel) == 1) delete cb_; }
  Weak& operator=(const Weak&) = delete;
  Shared<T> lock() const {   // 关键：只有 strong>0 时才能“复活”一个强引用——用 CAS 循环，不能先读后加
    Shared<T> r;
    if (!cb_) return r;
    long n = cb_->strong.load(std::memory_order_relaxed);
    while (n != 0) {
      if (cb_->strong.compare_exchange_weak(n, n + 1, std::memory_order_acq_rel, std::memory_order_relaxed)) { r.p_ = p_; r.cb_ = cb_; return r; }
    }
    return r;
  }
  bool expired() const { return !cb_ || cb_->strong.load(std::memory_order_relaxed) == 0; }
};

struct Probe { static inline std::atomic<int> alive{0}; Probe() { ++alive; } ~Probe() { --alive; } int v = 7; };

int main() {
  {
    Shared<Probe> a(new Probe); Weak<Probe> w(a);
    std::printf("单线程：use_count=%ld alive=%d expired=%d\n", a.use_count(), Probe::alive.load(), w.expired());
    { Shared<Probe> b = a; std::printf("拷贝后 use_count=%ld\n", a.use_count()); }
    a = Shared<Probe>();
    std::printf("释放最后一个强引用后：alive=%d expired=%d lock()=%s\n", Probe::alive.load(), w.expired(), w.lock() ? "非空" : "空");
  }
  Shared<Probe> shared(new Probe);
  std::vector<std::thread> ts;
  std::atomic<long> locked{0};
  for (int t = 0; t < 4; ++t) ts.emplace_back([&, w = Weak<Probe>(shared)] {
    for (int i = 0; i < 100000; ++i) { Shared<Probe> c = shared; Shared<Probe> d = c; if (auto s = w.lock()) locked += s->v; }
  });
  for (auto& t : ts) t.join();
  std::printf("4 个线程各拷贝/lock 十万次后：use_count=%ld alive=%d\n", shared.use_count(), Probe::alive.load());
}
