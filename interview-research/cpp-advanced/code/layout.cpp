// 实验 1：对象布局。关于 vptr、this 调整的观察依赖 Itanium C++ ABI（Linux/macOS 上的 GCC/Clang），
// 标准并不规定这些；MSVC 的布局不同。
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

struct Bad  { char a; double b; char c; int d; };      // 填充很多
struct Good { double b; int d; char a; char c; };      // 同样的成员，按对齐从大到小
struct Empty {};
struct WithEmptyMember { Empty e; int x; };
struct WithNoUnique { [[no_unique_address]] Empty e; int x; };
struct alignas(64) Cache { int x; };

struct V0 { int x; };
struct V1 { virtual void f() {} int x; };
struct A { virtual void fa() {} int a = 1; };
struct B { virtual void fb() {} int b = 2; };
struct C : A, B { int c = 3; void fa() override {} void fb() override {} };
struct VB { int vb = 7; };
struct D1 : virtual VB { int d1; };
struct D2 : virtual VB { int d2; };
struct E : D1, D2 { int e; };
struct Base1 { int x = 0; virtual ~Base1() = default; virtual void who() {} };
struct Der1 : Base1 { int y = 0; void who() override {} };
struct Der2 : Base1 { void who() override {} };

static std::uintptr_t vptr_of(const void* obj) { std::uintptr_t p; std::memcpy(&p, obj, sizeof p); return p; }

int main() {
  std::printf("== 填充与重排 ==\n");
  std::printf("Bad{char,double,char,int}  sizeof=%zu\n", sizeof(Bad));
  std::printf("Good{double,int,char,char} sizeof=%zu\n", sizeof(Good));
  std::printf("offsetof(Bad,b)=%zu offsetof(Bad,c)=%zu offsetof(Bad,d)=%zu\n", offsetof(Bad, b), offsetof(Bad, c), offsetof(Bad, d));
  std::printf("== 空类 ==\n");
  std::printf("sizeof(Empty)=%zu  成员为 Empty: %zu  [[no_unique_address]]: %zu\n", sizeof(Empty), sizeof(WithEmptyMember), sizeof(WithNoUnique));
  std::printf("alignas(64) struct: sizeof=%zu alignof=%zu\n", sizeof(Cache), alignof(Cache));
  std::printf("== 虚函数与继承 ==\n");
  std::printf("sizeof(V0)=%zu  sizeof(V1 有虚函数)=%zu  (8 字节 vptr + 4 字节 int + 4 字节对齐填充)\n", sizeof(V0), sizeof(V1));
  std::printf("sizeof(C : A, B 多重继承)=%zu  (两个 vptr)\n", sizeof(C));
  std::printf("sizeof(E 菱形虚继承)=%zu\n", sizeof(E));

  C c;
  A* pa = &c; B* pb = &c;
  std::printf("== 多重继承的 this 调整 ==\n");
  std::printf("(A*)==&c ? %s；B* 比 A* 多偏移 %td 字节（B 子对象在 C 对象内部，指针值不同）\n", (void*)pa == (void*)&c ? "是" : "否", (char*)pb - (char*)pa);
  std::printf("static_cast<C*>(pb)==&c ? %s\n", static_cast<C*>(pb) == &c ? "是（编译器减去偏移）" : "否");

  Der1 d1a, d1b; Der2 d2; Base1 b1;
  std::printf("== 同一动态类型共享 vtable 指针 ==\n");
  std::printf("Der1 对象甲 vptr==对象乙 vptr ? %s\n", vptr_of(&d1a) == vptr_of(&d1b) ? "是" : "否");
  std::printf("Der1 与 Der2 vptr 相同 ? %s\n", vptr_of(&d1a) == vptr_of(&d2) ? "是" : "否");
  std::printf("Base1 与 Der2 vptr 相同 ? %s (即使 Der2 没加成员，它也有自己的 vtable)\n", vptr_of(&b1) == vptr_of(&d2) ? "是" : "否");
  std::printf("== 构造期间动态类型 ==\n");
  struct P { P() { who(); } virtual void who() { std::puts("  P::who"); } };
  struct Q : P { void who() override { std::puts("  Q::who"); } };
  Q q; (void)q; // 基类构造函数里调用虚函数，只会调到 P::who
}
