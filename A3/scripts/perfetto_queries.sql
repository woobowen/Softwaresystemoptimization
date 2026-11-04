-- 2.3 第2问：dur 的单位 ns，结果为秒。
SELECT AVG(dur) / 1e9
FROM slice
WHERE name = 'aten::exp';

-- 先检查 category / track，确认当前加载的是该次 CPU 正式 trace。
SELECT category, track_id, COUNT(*) AS slices, SUM(dur) / 1e6 AS sum_ms
FROM slice
WHERE dur >= 0
GROUP BY category, track_id
ORDER BY slices DESC;

-- 检查实际嵌套，Python 栈不作为 cpu_op 的分母重复累加。
SELECT s.id, s.name, s.category, s.track_id, s.depth, s.parent_id,
       p.name AS parent_name, p.category AS parent_category, s.dur
FROM slice s LEFT JOIN slice p ON s.parent_id = p.id
WHERE s.name = 'aten::exp'
LIMIT 5;

-- 2.3 第3问。对无用户 annotation 的 CPU naive trace，
-- cpu_op 的根区间之和 = 全部 ATen Self CPU 之和。
-- 原因是各 cpu_op 父区间的 self + 其子区间 self 之和等于父 dur。
-- 查询中的 ancestor_slice 排除任意深度的 cpu_op 祖先；Python 祖先不计入。
-- 必须与该次 Profiler 表底部 Self CPU time total 交叉核对后使用百分比。
WITH cpu_roots AS (
    SELECT s.id, s.dur
    FROM slice s
    WHERE s.category = 'cpu_op' AND s.dur >= 0
      AND NOT EXISTS (
          SELECT 1 FROM ancestor_slice(s.id) a WHERE a.category = 'cpu_op'
      )
), exp_calls AS (
    SELECT COUNT(*) AS calls, SUM(dur) AS total_ns, AVG(dur) AS avg_ns
    FROM slice
    WHERE category = 'cpu_op' AND name = 'aten::exp' AND dur >= 0
), cpu_total AS (
    SELECT SUM(dur) AS total_ns FROM cpu_roots
)
SELECT e.calls, e.total_ns / 1e6 AS exp_total_ms,
       e.avg_ns / 1e3 AS exp_avg_us,
       t.total_ns / 1e6 AS all_self_cpu_ms,
       100.0 * e.total_ns / t.total_ns AS exp_cpu_total_pct
FROM exp_calls e CROSS JOIN cpu_total t;
