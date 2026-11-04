-- 每个正式 trace 均可执行：GPU kernel 与 CPU→GPU 关联，排除父子 ATen 重复。
SELECT category, COUNT(*) AS slices, SUM(dur)/1e3 AS total_us
FROM slice WHERE dur>=0 GROUP BY category ORDER BY slices DESC;

SELECT COUNT(*) AS kernel_count, SUM(dur)/1e3 AS kernel_total_us,
       AVG(dur)/1e3 AS avg_one_kernel_us
FROM slice WHERE category='kernel' AND dur>=0;

SELECT COUNT(*) AS kernels_with_launch
FROM slice k
WHERE k.category='kernel' AND EXISTS (
    SELECT 1 FROM flow f JOIN slice launch ON launch.id=f.slice_out
    WHERE f.slice_in=k.id AND launch.name GLOB '*LaunchKernel*'
);

SELECT COUNT(*) AS cpu_aten_calls
FROM slice WHERE category='cpu_op' AND name GLOB 'aten::*';
