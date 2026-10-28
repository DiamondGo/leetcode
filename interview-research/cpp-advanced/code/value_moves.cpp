// 实验 2：拷贝与移动到底发生了几次？值类别、返回值优化、noexcept 对 vector 扩容的影响、完美转发。
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct T {
  static inline int copies = 0, moves = 0, ctors = 0;
  int id;
  explicit T(int i = 0) : id(i) { ++ctors; }
  T(const T& o) : id(o.id) { ++copies; }
  T(T&& o) noexcept : id(o.id) { ++moves; }
  T& operator=(const T&) = default;
  T& operator=(T&&) noexcept = default;
  static void reset() { copies = moves = ctors = 0; }
  static void show(const char* what) { std::printf("%-46s 构造 %d  拷贝 %d  移动 %d\n", what, ctors, copies, moves); reset(); }
};

struct U {  // 移动构造没有 noexcept
  static inline int copies = 0, moves = 0;
  int id;
  explicit U(int i = 0) : id(i) {}
  U(const U& o) : id(o.id) { ++copies; }
  U(U&& o) : id(o.id) { ++moves; }
};

T make_prvalue() { return T(1); }                 // C++17 起保证不产生临时对象
T make_nrvo() { T t(2); return t; }                // NRVO：允许省略，GCC/Clang 通常会省略
T make_move_return() { T t(3); return std::move(t); }  // 画蛇添足：阻止了 NRVO
T make_conditional(bool b) { T x(4), y(5); if (b) return x; return y; }  // 两个候选，通常无法 NRVO，但仍会按移动处理

void sink(T) {}
template <class X> void fwd(X&& x) { sink(std::forward<X>(x)); }
template <class X> void no_fwd(X&& x) { sink(x); }  // 具名右值引用是左值：会拷贝

int main() {
  { T::reset(); T t = make_prvalue(); (void)t;           T::show("return T(1)   (prvalue，保证省略)"); }
  { T t = make_nrvo(); (void)t;                          T::show("T t; return t;   (NRVO)"); }
  { T t = make_move_return(); (void)t;                   T::show("return std::move(t)   (反而多一次移动)"); }
  { T t = make_conditional(true); (void)t;               T::show("两个局部变量按条件返回"); }
  { T a(1); T::reset(); T b = a; (void)b;                T::show("T b = a;"); }
  { T a(1); T::reset(); T b = std::move(a); (void)b;     T::show("T b = std::move(a);"); }
  { T a(1); T::reset(); sink(a);                         T::show("sink(T) 传左值"); }
  { T a(1); T::reset(); sink(std::move(a));              T::show("sink(T) 传 std::move"); }
  { T a(1); T::reset(); fwd(a);                          T::show("转发引用 fwd(a)，std::forward"); }
  { T::reset(); fwd(T(9));                               T::show("转发引用 fwd(T(9))，std::forward"); }
  { T::reset(); no_fwd(T(9));                            T::show("转发引用但忘了 std::forward"); }
  { const T c(1); T::reset(); T d = std::move(c); (void)d; T::show("std::move 一个 const 对象"); }

  std::puts("\n-- vector 扩容：移动构造有没有 noexcept 的区别 --");
  {
    std::vector<T> v; v.reserve(4); for (int i = 0; i < 4; ++i) v.emplace_back(i);
    T::reset(); v.push_back(T(99));  // 容量已满，触发扩容
    T::show("vector<T>   (noexcept 移动) 扩容并 push_back");
  }
  {
    std::vector<U> v; v.reserve(4); for (int i = 0; i < 4; ++i) v.emplace_back(i);
    U::copies = U::moves = 0; v.push_back(U(99));
    std::printf("%-46s 拷贝 %d  移动 %d\n", "vector<U>   (移动没有 noexcept) 扩容并 push_back", U::copies, U::moves);
  }

  std::puts("\n-- push_back 与 emplace_back --");
  { std::vector<T> v; v.reserve(8); T::reset(); v.push_back(T(1));      T::show("push_back(T(1))"); }
  { std::vector<T> v; v.reserve(8); T::reset(); v.emplace_back(1);      T::show("emplace_back(1)  (原地构造)"); }
  { std::vector<std::string> v; v.reserve(2);
    std::string s(40, 'x');  // 超过 SSO，拷贝要分配内存
    v.push_back(s); v.push_back(std::move(s));
    std::printf("std::move 之后源字符串 size=%zu（有效但未指定；libstdc++ 实际为空）\n", s.size()); }
}
