from __future__ import annotations

import numpy as np


class WalkForwardSplitter:
    def __init__(
        self,
        min_train: int = 60,
        test_size: int = 20,
        gap: int = 5,
        expanding: bool = True,
    ) -> None:
        self.min_train = min_train
        self.test_size = test_size
        self.gap = gap
        self.expanding = expanding

    def split(self, n_samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
        splits: list[tuple[np.ndarray, np.ndarray]] = []
        indices = np.arange(n_samples)
        start = 0
        train_end = self.min_train
        while train_end + self.gap + self.test_size <= n_samples:
            test_start = train_end + self.gap
            test_end = test_start + self.test_size
            if self.expanding:
                train_idx = indices[start:train_end]
            else:
                train_idx = indices[max(0, train_end - self.min_train) : train_end]
            test_idx = indices[test_start:test_end]
            splits.append((train_idx, test_idx))
            train_end += self.test_size
        return splits
