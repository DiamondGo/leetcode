#!/usr/bin/env bash
# 编译并运行全部实验。需要 g++ 13+（或 clang++ 17+），支持 -fsanitize=address,undefined,thread 的环境。
# 用法：./run_all.sh 实验名      （例如 ./run_all.sh layout）；不带参数则全部运行。
# 输出里的耗时和并发实验的次数每次不同，只看相对大小和是否为 0。
set -u
cd "$(dirname "$0")"
OUT=${TMPDIR:-/tmp}/cppadv; mkdir -p "$OUT"
CXX=${CXX:-g++}
STD="-std=c++20"
trim() { sed -E 's#/[^ ]*/cpp-advanced/code/##g; s/0x[0-9a-f]{6,}/0xADDR/g; s/==[0-9]+==/==PID==/; s/pid=[0-9]+/pid=PID/'; }


exp_layout()        { $CXX $STD -O2 layout.cpp -o $OUT/layout && $OUT/layout; }
exp_value_moves()   { $CXX $STD -O2 -Wno-pessimizing-move value_moves.cpp -o $OUT/vm && $OUT/vm; }
exp_litmus_sb()     { $CXX $STD -O2 -pthread litmus_sb.cpp -o $OUT/sb && $OUT/sb; }
exp_spsc() {
  echo "== 正确版本（release/acquire），ThreadSanitizer =="
  $CXX $STD -O1 -g -fsanitize=thread -pthread spsc.cpp -o $OUT/spsc_ok && $OUT/spsc_ok 2>&1 | head -5 | trim
  echo "== 错误版本（全部 relaxed），ThreadSanitizer（只显示报告的前几行）=="
  $CXX $STD -O1 -g -fsanitize=thread -pthread -DWRONG spsc.cpp -o $OUT/spsc_bad && $OUT/spsc_bad 2>&1 | grep -E 'WARNING|Read of|Previous write|#0 ' | head -6 | trim
}
exp_false_sharing() { $CXX $STD -O2 -pthread false_sharing.cpp -o $OUT/fs && $OUT/fs; }
exp_ub() {
  for o in O0 O2; do $CXX $STD -$o ub_optimize.cpp -o $OUT/ub_$o; echo "-- $CXX -$o --"; $OUT/ub_$o; done
  echo "-- $CXX -O2 -fsanitize=undefined --"; $CXX $STD -O2 -fsanitize=undefined ub_optimize.cpp -o $OUT/ub_san && $OUT/ub_san 2>&1 | trim
  echo "-- ASan：vector 扩容后使用旧指针 --"
  $CXX $STD -g -fsanitize=address -fno-omit-frame-pointer asan_demo.cpp -o $OUT/asan1 && $OUT/asan1 2>&1 | grep -E 'ERROR|READ of|freed by|previously allocated|asan_demo' | head -6 | trim
  echo "-- ASan：string_view 悬空 --"; $OUT/asan1 a b 2>&1 | grep -E 'ERROR|READ of' | head -2 | trim
}
exp_smart_ptr()     { $CXX $STD -O2 -Wno-mismatched-new-delete smart_ptr.cpp -o $OUT/sp && $OUT/sp; }
exp_stl()           { $CXX $STD -O2 stl_internals.cpp -o $OUT/stl && $OUT/stl; }
exp_perf()          { $CXX $STD -O2 perf_micro.cpp -o $OUT/perf && $OUT/perf; }
exp_coroutine()     { $CXX $STD -O2 coroutine_gen.cpp -o $OUT/co && $OUT/co; }
exp_templates() {
  $CXX -std=c++23 -O2 concepts_templates.cpp -o $OUT/ct && $OUT/ct
  echo "--- concept 约束不满足的报错 ---"; $CXX $STD -c concept_error.cpp -o /dev/null 2>&1 | grep -E 'error|note: *(candidate|constraints)' | head -4 | cut -c1-160
  echo "--- 无约束模板误用：诊断总行数 ---"; $CXX $STD -c no_concept_error.cpp -o /dev/null 2>&1 | wc -l
  $CXX $STD -c no_concept_error.cpp -o /dev/null 2>&1 | grep -m1 -E 'error' | cut -c1-170
}
exp_exceptions()    { $CXX $STD -O2 exceptions.cpp -o $OUT/exc && $OUT/exc; }
exp_shared_ptr() {
  echo "-- ASan+UBSan --"; $CXX $STD -g -fsanitize=address,undefined -pthread mini_shared_ptr.cpp -o $OUT/msp_a && $OUT/msp_a 2>&1 | trim
  echo "-- TSan --"; $CXX $STD -g -O1 -fsanitize=thread -pthread mini_shared_ptr.cpp -o $OUT/msp_t && $OUT/msp_t 2>&1 | trim
}
exp_thread_pool()   { $CXX $STD -g -O1 -fsanitize=thread -pthread thread_pool.cpp -o $OUT/tp && $OUT/tp 2>&1 | trim; }
exp_type_erasure()  { $CXX $STD -g -fsanitize=address,undefined -Wno-mismatched-new-delete type_erasure.cpp -o $OUT/te && $OUT/te 2>&1 | trim; }
exp_traps()         { $CXX $STD -w traps.cpp -o $OUT/traps && $OUT/traps; echo "-- 同一个程序用 clang++ 编译，第 9 项 --"; clang++ $STD -w traps.cpp -o $OUT/traps_cl 2>/dev/null && $OUT/traps_cl | grep -A1 -- "--9"; }
exp_snippets()      { $CXX -std=c++23 -O1 snippets.cpp -o $OUT/snip && $OUT/snip; }
exp_siof() {
  echo "-- 链接顺序 a b --"; $CXX $STD siof/a.cpp siof/b.cpp -o $OUT/siof1 && $OUT/siof1
  echo "-- 链接顺序 b a --"; $CXX $STD siof/b.cpp siof/a.cpp -o $OUT/siof2 && $OUT/siof2
  echo "-- b 改为 constinit --"; $CXX $STD siof/a.cpp siof/b_fixed.cpp -o $OUT/siof3 && $OUT/siof3
}

ALL="layout value_moves litmus_sb spsc false_sharing ub smart_ptr stl perf coroutine templates exceptions shared_ptr thread_pool type_erasure siof traps snippets"
for e in ${@:-$ALL}; do echo "######## $e"; exp_$e; done
