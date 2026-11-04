-- Original assignment query. Perfetto stores slice.dur in nanoseconds.
SELECT AVG(dur) / 1e9
FROM slice
WHERE name = 'aten::exp';

SELECT category, COUNT(*) AS event_count, SUM(dur) AS duration_ns
FROM slice
GROUP BY category
ORDER BY category;

SELECT name, ts, dur
FROM slice
WHERE category = 'kernel';

-- Real trace flow edges, resolved by Perfetto's importer.
SELECT launch.name AS launch_name, kernel.name AS kernel_name,
       launch.ts AS launch_ts_ns, kernel.ts AS kernel_ts_ns,
       kernel.dur AS kernel_dur_ns
FROM flow
JOIN slice AS launch ON launch.id = flow.slice_out
JOIN slice AS kernel ON kernel.id = flow.slice_in
WHERE kernel.category = 'kernel';

-- Parent chains establish the actual Python frame -> ATen/launch relationship.
WITH RECURSIVE chain(leaf_id, id, parent_id, name, category, level) AS (
  SELECT id, id, parent_id, name, category, 0
  FROM slice
  WHERE name IN ('aten::exp', 'cuLaunchKernel', 'cudaLaunchKernel')
  UNION ALL
  SELECT chain.leaf_id, parent.id, parent.parent_id, parent.name,
         parent.category, chain.level + 1
  FROM chain
  JOIN slice AS parent ON parent.id = chain.parent_id
  WHERE chain.level < 32
)
SELECT leaf_id, level, name, category
FROM chain
WHERE category IN ('cpu_op', 'python_function') OR level = 0
ORDER BY leaf_id, level;

SELECT name, value, severity
FROM stats
WHERE value <> 0 AND severity IN ('error', 'data_loss');
