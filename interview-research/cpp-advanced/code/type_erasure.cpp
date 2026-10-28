// 实验 15：类型擦除（type erasure）——std::function 的原理。
// 目标：把“任何可以被调用的东西”装进同一个类型里，调用方不需要知道具体类型，也不需要继承关系。
// 做法：外层是普通类（值语义），内部持有一个抽象基类指针，具体类型在模板派生类里。
// 再加一个“小对象优化”：足够小的可调用对象直接放在内部缓冲区，避免堆分配。
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>
#include <string>
#include <type_traits>
#include <utility>

static int g_allocs = 0;
void* operator new(std::size_t n) { ++g_allocs; if (void* p = std::malloc(n)) return p; throw std::bad_alloc(); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

template <class Sig> class Function;
template <class R, class... A>
class Function<R(A...)> {
  struct Concept {
    virtual R call(A...) = 0;
    virtual Concept* clone(void* buf) const = 0;          // buf 为空 -> 堆上拷贝
    virtual Concept* move_to(void* buf) noexcept = 0;     // 把自己搬到 buf（用于内联存储的搬迁）
    virtual ~Concept() = default;
  };
  template <class F> struct Model final : Concept {
    F f;
    explicit Model(F f) : f(std::move(f)) {}
    R call(A... a) override { return f(std::forward<A>(a)...); }
    Concept* clone(void* buf) const override { return buf ? new (buf) Model(f) : new Model(f); }
    Concept* move_to(void* buf) noexcept override { return new (buf) Model(std::move(f)); }
  };
  static constexpr size_t kSmall = 32;
  alignas(std::max_align_t) unsigned char buf_[kSmall];
  Concept* p_ = nullptr;
  bool inline_ = false;
  void reset() noexcept { if (p_) { if (inline_) p_->~Concept(); else delete p_; p_ = nullptr; } }
 public:
  Function() = default;
  template <class F> Function(F f) {
    if constexpr (sizeof(Model<F>) <= kSmall && alignof(Model<F>) <= alignof(std::max_align_t) && std::is_nothrow_move_constructible_v<F>) {
      p_ = new (buf_) Model<F>(std::move(f)); inline_ = true;       // 小对象优化：不分配堆内存
    } else p_ = new Model<F>(std::move(f));
  }
  Function(const Function& o) { if (o.p_) { p_ = o.p_->clone(o.inline_ ? buf_ : nullptr); inline_ = o.inline_; } }
  Function(Function&& o) noexcept {
    if (!o.p_) return;
    if (o.inline_) { p_ = o.p_->move_to(buf_); inline_ = true; o.reset(); }
    else { p_ = std::exchange(o.p_, nullptr); }                      // 堆上的直接过户指针
  }
  Function& operator=(Function o) noexcept { reset(); if (o.p_) { if (o.inline_) { p_ = o.p_->move_to(buf_); inline_ = true; o.reset(); } else p_ = std::exchange(o.p_, nullptr), inline_ = false; } return *this; }
  ~Function() { reset(); }
  R operator()(A... a) { return p_->call(std::forward<A>(a)...); }
  explicit operator bool() const { return p_ != nullptr; }
  bool is_inline() const { return inline_; }
};

int add1(int x) { return x + 1; }
int main() {
  g_allocs = 0;
  int k = 10;
  Function<int(int)> f1 = [k](int x) { return x + k; };           // 捕获一个 int：很小
  std::printf("小 lambda：f1(5)=%d，内联存储=%d，堆分配 %d 次\n", f1(5), f1.is_inline(), g_allocs);
  std::string big(100, 'x');
  g_allocs = 0;
  Function<size_t(int)> f2 = [big](int x) { return big.size() + x; };  // 捕获 std::string(32 字节)：放不进缓冲区
  std::printf("大 lambda：f2(1)=%zu，内联存储=%d，堆分配 %d 次（lambda 捕获的 string 副本 + Model 对象）\n", f2(1), f2.is_inline(), g_allocs);
  Function<int(int)> f3 = add1;                                    // 函数指针
  Function<int(int)> f4 = f1;                                      // 拷贝：用 clone 复制具体类型
  Function<int(int)> f5 = std::move(f1);                           // 移动：内联对象要搬到新缓冲区
  Function<size_t(int)> f6 = std::move(f2);                        // 移动：堆上的对象只过户指针
  std::printf("函数指针 f3(1)=%d；拷贝 f4(5)=%d；移动后 f5(5)=%d，f6(1)=%zu，被移动的 f1 为空=%d\n", f3(1), f4(5), f5(5), f6(1), !f1);
}
