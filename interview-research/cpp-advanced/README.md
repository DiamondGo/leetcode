# 高级 C++ 面试：原理、陷阱与深度问答

- `cpp-advanced-interview.md`：正文（对象模型、值类别与移动语义、模板、内存管理与智能指针、并发与内存模型、未定义行为、异常、STL 内部与性能、现代 C++、构建与 ABI、陷阱题与工程场景；113 道带答案要点的面试题）
- `code/`：18 个实验，全部在 g++ 13.3 / clang++ 18.1（x86-64 Linux）上编译运行过，并发代码用 TSan、内存代码用 ASan/UBSan 检查过
  - 运行：`cd code && ./run_all.sh`（全部）或 `./run_all.sh layout`（单个，名字见脚本里的 `exp_` 函数）
  - 需要 g++ 13+ 或 clang++ 17+；脚本里的 sanitizer 需要系统带有对应的运行库
- `sample_output/`：我运行时的输出（耗时和并发实验里的计数每次不同）

说明：C++26 的内容（反射、契约、`std::execution`、hazard pointer 等）未验证；其他平台（MSVC、ARM、macOS）的行为只提到差异、未实测；没有真实的、带日期的某公司面经。详见正文附录 A。
