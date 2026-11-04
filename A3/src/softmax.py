"""作业中的五步 Softmax 和按列递推的 Online Softmax。"""

import torch


def naive_softmax(x: torch.Tensor) -> torch.Tensor:
    x_max = x.max(dim=1)[0]
    z = x - x_max[:, None]
    numerator = torch.exp(z)
    denominator = numerator.sum(dim=1)
    ret = numerator / denominator[:, None]
    return ret


def online_softmax(x: torch.Tensor) -> torch.Tensor:
    n_rows, n_cols = x.shape
    m = torch.full((n_rows,), -float("inf"), dtype=x.dtype, device=x.device)
    d = torch.zeros((n_rows,), dtype=x.dtype, device=x.device)

    for j in range(n_cols):
        x_j = x[:, j]
        new_m = torch.maximum(m, x_j)
        # d 的更新仍使用旧 m，再更新 m。
        d = d * torch.exp(m - new_m) + torch.exp(x_j - new_m)
        m = new_m

    return torch.exp(x - m[:, None]) / d[:, None]
