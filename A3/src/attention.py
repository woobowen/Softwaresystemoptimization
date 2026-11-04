"""Single-head scaled dot-product attention."""

import math

import torch


def attention(q, k, v):
    scores = q @ k.T
    scores = scores / math.sqrt(q.shape[-1])
    probabilities = torch.softmax(scores, dim=-1)
    output = probabilities @ v
    return output
