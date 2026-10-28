// 实验 18：正文里出现的、不属于前面实验的短代码片段，集中在这里编译并运行，保证它们不是“看起来对”。
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <expected>
#include <memory>
#include <memory_resource>
#include <mutex>
#include <optional>
#include <ranges>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

// ---- 片段 A：void_t 检测惯用法（C++17 以前的写法，C++20 可用 requires 代替）----
template <class, class = void> struct has_size : std::false_type {};
template <class T> struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};
static_assert(has_size<std::vector<int>>::value && !has_size<int>::value);

// ---- 片段 B：转发引用的构造函数“劫持”拷贝构造 ----
struct Person {
  std::string name;
  template <class T> explicit Person(T&&) { std::puts("  调用了模板构造函数（实际工作中这里会 name(std::forward<T>(n))；传入 Person& 时它会编译失败）"); }
  Person(const Person& o) : name(o.name) { std::puts("  调用了拷贝构造函数"); }
};
struct PersonFixed {
  std::string name;
  template <class T, class = std::enable_if_t<!std::is_same_v<std::remove_cvref_t<T>, PersonFixed>>>
  explicit PersonFixed(T&& n) : name(std::forward<T>(n)) { std::puts("  调用了模板构造函数"); }
  PersonFixed(const PersonFixed& o) : name(o.name) { std::puts("  调用了拷贝构造函数"); }
};

// ---- 片段 C：unique_ptr 自定义删除器管理 C 资源 ----
using FilePtr = std::unique_ptr<std::FILE, decltype([](std::FILE* f) { if (f) std::fclose(f); })>;

// ---- 片段 D：变体与 overloaded 惯用法 ----
template <class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template <class... Ts> overloaded(Ts...) -> overloaded<Ts...>;     // CTAD 推导指引（C++20 起聚合体可以自动推导，写出来更兼容）

// ---- 片段 E：std::expected 做错误处理（C++23）----
enum class Err { Empty, NotNumber };
std::expected<int, Err> parse(std::string_view s) {
  if (s.empty()) return std::unexpected(Err::Empty);
  int v = 0;
  for (char c : s) { if (c < '0' || c > '9') return std::unexpected(Err::NotNumber); v = v * 10 + (c - '0'); }
  return v;
}

// ---- 片段 F：魔法静态变量（C++11 起线程安全的局部静态初始化）----
struct Config { Config() { std::puts("  Config 只构造一次"); } int v = 42; };
Config& config() { static Config c; return c; }

int main() {
  std::puts("== B：转发引用劫持拷贝构造 ==");
  { Person p("alice"); std::puts(" Person q(p)  （p 是非 const 左值）："); Person q(p); (void)q; }
  { PersonFixed p("alice"); std::puts(" PersonFixed q(p)（加了约束）："); PersonFixed q(p); (void)q; }

  std::puts("== C：unique_ptr + lambda 删除器，大小 ==");
  std::printf("  sizeof(FilePtr)=%zu（无状态删除器不占空间）\n", sizeof(FilePtr));
  { FilePtr f(std::fopen("/dev/null", "r")); std::printf("  打开成功=%d\n", f != nullptr); }

  std::puts("== D：variant + visit ==");
  std::variant<int, std::string, double> v = std::string("hi");
  std::visit(overloaded{[](int i) { std::printf("  int %d\n", i); }, [](const std::string& s) { std::printf("  string %s\n", s.c_str()); }, [](double d) { std::printf("  double %f\n", d); }}, v);
  std::printf("  sizeof(variant<int,string,double>)=%zu（= 最大成员 + 判别位 + 对齐）\n", sizeof(v));

  std::puts("== E：expected ==");
  for (std::string_view s : {"123", "", "12a"}) {
    auto r = parse(s);
    if (r) std::printf("  \"%.*s\" -> %d\n", (int)s.size(), s.data(), *r); else std::printf("  \"%.*s\" -> 错误码 %d\n", (int)s.size(), s.data(), (int)r.error());
  }
  std::printf("  monadic：parse(\"20\").transform(x*2) = %d\n", parse("20").transform([](int x) { return x * 2; }).value_or(-1));

  std::puts("== F：魔法静态 ==");
  config(); config();

  std::puts("== G：std::bit_cast 与 memcpy 做类型双关（避免严格别名违规）==");
  float f = 1.0f; auto bits = std::bit_cast<std::uint32_t>(f);
  std::uint32_t bits2; std::memcpy(&bits2, &f, sizeof f);
  std::printf("  1.0f 的位模式：0x%08x，memcpy 结果相同=%d\n", bits, bits == bits2);

  std::puts("== H：pmr 单调缓冲区：用栈上缓冲代替堆 ==");
  std::array<std::byte, 4096> buf;
  std::pmr::monotonic_buffer_resource pool(buf.data(), buf.size(), std::pmr::null_memory_resource());  // 用完就失败，而不是退回堆
  std::pmr::vector<int> pv(&pool);
  for (int i = 0; i < 100; ++i) pv.push_back(i);
  std::printf("  100 个 int 放进 pmr::vector，没有触碰全局堆；capacity=%zu\n", pv.capacity());

  std::puts("== I：ranges 视图是惰性的，也可能悬空 ==");
  std::vector<int> nums{1, 2, 3, 4, 5, 6};
  auto evens_sq = nums | std::views::filter([](int x) { return x % 2 == 0; }) | std::views::transform([](int x) { return x * x; });
  std::printf("  偶数的平方：");
  for (int x : evens_sq) std::printf("%d ", x);
  std::puts("");
  auto it = std::ranges::find(std::vector<int>{1, 2, 3}, 2);   // 对临时容器调用 ranges 算法，返回 dangling
  static_assert(std::is_same_v<decltype(it), std::ranges::dangling>);
  std::puts("  对临时 vector 做 ranges::find 的返回类型是 std::ranges::dangling（编译期拦住了悬空迭代器）");

  std::puts("== J：scoped_lock 同时锁多个互斥量（避免死锁）==");
  std::mutex m1, m2; { std::scoped_lock lk(m1, m2); std::puts("  已同时持有 m1 和 m2"); }
}
