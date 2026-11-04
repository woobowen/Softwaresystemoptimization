"""老师给出的 persistent Triton Softmax，设备属性延迟到首次调用读取。"""

import torch
import triton
import triton.language as tl
from triton.runtime import driver


_properties = {}


@triton.jit
def softmax_kernel(output_ptr, input_ptr, input_row_stride, output_row_stride,
                   n_rows, n_cols, BLOCK_SIZE: tl.constexpr,
                   num_stages: tl.constexpr):
    row_start = tl.program_id(0)
    row_step = tl.num_programs(0)
    for row_idx in tl.range(row_start, n_rows, row_step, num_stages=num_stages):
        row_start_ptr = input_ptr + row_idx * input_row_stride
        col_offsets = tl.arange(0, BLOCK_SIZE)
        mask = col_offsets < n_cols
        row = tl.load(row_start_ptr + col_offsets, mask=mask, other=-float("inf"))
        row_minus_max = row - tl.max(row, axis=0)
        numerator = tl.exp(row_minus_max)
        denominator = tl.sum(numerator, axis=0)
        softmax_output = numerator / denominator
        output_row_start_ptr = output_ptr + row_idx * output_row_stride
        tl.store(output_row_start_ptr + col_offsets, softmax_output, mask=mask)


def softmax(x):
    if not x.is_cuda or x.ndim != 2 or x.stride(1) != 1:
        raise ValueError("expected a CUDA matrix with contiguous columns")
    n_rows, n_cols = x.shape
    device = x.device.index
    if device not in _properties:
        _properties[device] = driver.active.utils.get_device_properties(device)
    properties = _properties[device]
    num_sm = properties["multiprocessor_count"]
    num_regs = properties["max_num_regs"]
    size_smem = properties["max_shared_mem"]
    warp_size = properties["warpSize"]

    BLOCK_SIZE = triton.next_power_of_2(n_cols)
    num_warps = 8
    num_stages = 4 if size_smem > 200000 else 2
    y = torch.empty_like(x)
    kernel = softmax_kernel.warmup(
        y, x, x.stride(0), y.stride(0), n_rows, n_cols, BLOCK_SIZE,
        num_stages=num_stages, num_warps=num_warps, grid=(1,),
    )
    kernel._init_handles()
    n_regs = kernel.n_regs
    shared = kernel.metadata.shared
    occupancy = num_regs // (n_regs * warp_size * num_warps)
    occupancy = min(occupancy, size_smem // shared)
    num_programs = min(num_sm * occupancy, n_rows)
    softmax_kernel[(num_programs, 1, 1)](
        y, x, x.stride(0), y.stride(0), n_rows, n_cols, BLOCK_SIZE,
        num_stages=num_stages, num_warps=num_warps,
    )
    return y
