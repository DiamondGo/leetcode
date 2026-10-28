// 实验 17：面试里常见的“代码输出题”陷阱，每一条都在真实编译器上运行过，输出写在注释外面由程序打印。
#include <cstdio>
#include <initializer_list>
#include <map>
#include <string>
#include <typeinfo>
#include <vector>

// 1. 默认实参是静态绑定的，虚函数是动态绑定的
struct B1 { virtual void f(int x = 1) { std::printf("B1::f(%d)\n", x); } virtual ~B1() = default; };
struct D1 : B1 { void f(int x = 2) override { std::printf("D1::f(%d)\n", x); } };

// 2. 名字隐藏：派生类声明了同名函数，基类的所有重载都被隐藏
struct B2 { void g(int) { std::puts("B2::g(int)"); } void g(double) { std::puts("B2::g(double)"); } };
struct D2 : B2 { void g(const char*) { std::puts("D2::g(const char*)"); } };
struct D2b : B2 { using B2::g; void g(const char*) { std::puts("D2b::g(const char*)"); } };

// 3. 重载决议：字符串字面量更愿意变成 bool 而不是 std::string
void h(bool) { std::puts("h(bool)"); }
void h(const std::string&) { std::puts("h(const std::string&)"); }

// 4. 初始化列表构造函数优先
struct S { S(int, int) { std::puts("S(int,int)"); } S(std::initializer_list<int>) { std::puts("S(initializer_list)"); } };

// 5. 切片
struct Animal { virtual const char* name() const { return "Animal"; } virtual ~Animal() = default; };
struct Cat : Animal { const char* name() const override { return "Cat"; } };
void by_value(Animal a) { std::printf("按值传递：%s\n", a.name()); }
void by_ref(const Animal& a) { std::printf("按引用传递：%s\n", a.name()); }

// 6. 构造函数中的虚调用 / 7. 静态局部变量只初始化一次
int next_id() { static int id = 100; return ++id; }

// 8. 析构顺序
struct Noisy { const char* n; explicit Noisy(const char* n) : n(n) { std::printf("构造 %s\n", n); } ~Noisy() { std::printf("析构 %s\n", n); } };
struct Holder { Noisy a{"成员a"}; Noisy b{"成员b"}; Holder() { std::puts("Holder 构造体"); } ~Holder() { std::puts("Holder 析构体"); } };

int main() {
  std::puts("--1 默认实参静态绑定--");  { B1* p = new D1; p->f(); delete p; }
  std::puts("--2 名字隐藏--");  { D2 d; d.g("x"); /* d.g(1) 在这里无法通过编译：g++ 报 invalid conversion from int to const char*，因为 B2::g 被隐藏了 */ }
  std::puts("--2b using 声明恢复重载--");  { D2b d; d.g(1); d.g(1.5); d.g("x"); }
  std::puts("--3 字符串字面量重载--");  h("hello"); h(std::string("hello"));
  std::puts("--4 花括号与圆括号--");  { S a(1, 2); S b{1, 2}; S c = {1, 2}; (void)a; (void)b; (void)c; }
  { std::vector<int> v1(3, 4), v2{3, 4}; std::printf("vector<int> v1(3,4) 大小 %zu；v2{3,4} 大小 %zu\n", v1.size(), v2.size()); }
  std::puts("--5 切片--");  { Cat c; by_value(c); by_ref(c); }
  std::puts("--6 有符号与无符号比较--");
  { int a = -1; unsigned b = 1; std::printf("-1 < 1u 的结果：%d（-1 被转成很大的无符号数）\n", a < b); }
  { std::vector<int> v; std::printf("v.size() - 1 = %zu （空 vector 上的无符号下溢）\n", v.size() - 1); }
  std::puts("--7 auto 与花括号--");
  { auto a = {1}; auto b = 1; std::printf("auto a = {1}: %s；auto b = 1: %s\n", typeid(a).name(), typeid(b).name()); }
  std::puts("--8 map::operator[] 会插入--");
  { std::map<std::string, int> m; if (m["missing"] == 0) {} std::printf("只是读了一下，map 大小变成 %zu\n", m.size()); }
  std::puts("--9 静态局部变量只初始化一次；同一个调用里多个实参的求值顺序未指定--");  std::printf("%d %d %d\n", next_id(), next_id(), next_id());   // GCC 通常从右往左求值，Clang 从左往右
  std::puts("--10 成员的构造与析构顺序--");  { Holder h; }
  std::puts("--11 数组退化--");
  { int arr[10]; auto f = [](int a[10]) { return sizeof(a); }; std::printf("sizeof(arr)=%zu；传给 int a[10] 参数后 sizeof(a)=%zu\n", sizeof(arr), f(arr)); }
  std::puts("--12 vector<bool> 不是容器--");
  { std::vector<bool> vb{true}; auto x = vb[0]; vb[0] = false; std::printf("auto x = vb[0]; 然后 vb[0]=false；x 现在是 %d（x 是代理对象，仍然引用着 vector 里的那一位）\n", (bool)x); }
  std::puts("--13 临时对象的生命周期--");
  { const std::string& r = std::string("临时对象被延长生命周期"); std::printf("%s\n", r.c_str()); }
}
