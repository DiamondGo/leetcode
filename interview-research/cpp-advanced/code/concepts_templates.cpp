// 实验 11：模板与元编程的现代写法（C++20）。全部在编译期验证——编译通过就说明断言成立。
#include <concepts>
#include <cstdio>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

// --- constexpr：编译期计算 ---
constexpr long long fib(int n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
static_assert(fib(20) == 6765);
consteval int sq(int x) { return x * x; }        // consteval：必须在编译期求值
constinit int g_table = sq(12);                  // constinit：保证静态初始化（避免初始化顺序问题）

// --- Concepts 取代 SFINAE ---
template <class T> concept Numeric = std::integral<T> || std::floating_point<T>;
template <class T> concept HasSize = requires(const T& t) { { t.size() } -> std::convertible_to<std::size_t>; };
template <Numeric T> T twice(T x) { return x + x; }
template <HasSize C> std::size_t count_of(const C& c) { return c.size(); }
static_assert(Numeric<int> && !Numeric<std::string>);
static_assert(HasSize<std::vector<int>> && !HasSize<int>);

// 老式 SFINAE，用来对比可读性
template <class T, std::enable_if_t<std::is_integral_v<T>, int> = 0> T old_twice(T x) { return x + x; }

// --- if constexpr：编译期分支（不满足的分支不会被实例化）---
template <class T> std::string describe(const T& v) {
  if constexpr (std::is_pointer_v<T>) return "pointer";
  else if constexpr (std::is_integral_v<T>) return "integer " + std::to_string(v);
  else if constexpr (requires { v.size(); }) return "sized container of " + std::to_string(v.size());
  else return "other";
}

// --- 折叠表达式与变参模板 ---
template <class... Ts> auto sum(Ts... xs) { return (xs + ...); }
template <class... Ts> constexpr bool all_same_v = (std::is_same_v<Ts, std::tuple_element_t<0, std::tuple<Ts...>>> && ...);
static_assert(all_same_v<int, int, int> && !all_same_v<int, long>);
template <class F, class... Args> void for_each_arg(F&& f, Args&&... args) { (f(std::forward<Args>(args)), ...); }

// --- CRTP：静态多态 ---
template <class D> struct Printable { void print() const { std::printf("%s\n", static_cast<const D*>(this)->name()); } };
struct Dog : Printable<Dog> { const char* name() const { return "Dog"; } };

// --- 类型推导 ---
int g = 1; int& ref() { return g; }
static_assert(std::is_same_v<decltype(auto(ref())), int>);          // C++23 的 auto(x) 退化拷贝；GCC 13 支持
static_assert(std::is_same_v<decltype(ref()), int&>);
static_assert(std::is_same_v<decltype((g)), int&>);                 // 带括号的变量名是左值表达式，decltype 给出引用
static_assert(std::is_same_v<decltype(g), int>);
template <class T> void deduce(T&&) {}                              // 转发引用
template <class T> constexpr bool is_lvalue_deduced(T&&) { return std::is_lvalue_reference_v<T>; }

int main() {
  int a = 3; const int& cr = a;
  std::printf("twice(21)=%d  twice(1.5)=%.1f  old_twice(4)=%d  count_of(vector)=%zu\n", twice(21), twice(1.5), old_twice(4), count_of(std::vector<int>(5)));
  std::printf("describe: %s | %s | %s | %s\n", describe(&a).c_str(), describe(7).c_str(), describe(std::string("abc")).c_str(), describe(2.5).c_str());
  std::printf("sum(1,2,3,4)=%d  g_table=%d\n", sum(1, 2, 3, 4), g_table);
  Dog().print();
  std::printf("is_lvalue_deduced(a)=%d  (cr)=%d  (7)=%d  (std::move(a))=%d\n", is_lvalue_deduced(a), is_lvalue_deduced(cr), is_lvalue_deduced(7), is_lvalue_deduced(std::move(a)));
  for_each_arg([](auto&& x) { std::printf("[%s] ", describe(x).c_str()); }, 1, std::string("hi"), 3.5);
  std::puts("");
}
