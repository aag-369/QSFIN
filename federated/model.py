"""
A tiny logistic regression implemented from scratch in numpy — deliberately
simple and fully transparent (no framework black box) so the federated
averaging logic in fedavg.py is easy to follow line by line. In a
production system the local model per agency could be anything
(gradient-boosted trees, a neural net) as long as its parameters can be
represented as a vector and meaningfully averaged (which is why linear/
logistic models are also what most real FedAvg tutorials start with).
"""
import numpy as np


class LogisticRegression:
    def __init__(self, n_features: int, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0, 0.05, size=n_features)
        self.b = 0.0

    def get_params(self):
        return np.concatenate([self.w, [self.b]])

    def set_params(self, params):
        self.w = params[:-1].copy()
        self.b = float(params[-1])

    def predict_proba(self, X):
        z = X @ self.w + self.b
        return 1 / (1 + np.exp(-np.clip(z, -30, 30)))

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)

    def train_epochs(self, X, y, epochs=20, lr=0.2, l2=0.001):
        n = X.shape[0]
        for _ in range(epochs):
            p = self.predict_proba(X)
            grad_z = (p - y) / n
            grad_w = X.T @ grad_z + l2 * self.w
            grad_b = grad_z.sum()
            self.w -= lr * grad_w
            self.b -= lr * grad_b
        return self

    def accuracy(self, X, y):
        return float(np.mean(self.predict(X) == y))

    def loss(self, X, y, l2=0.001):
        p = np.clip(self.predict_proba(X), 1e-9, 1 - 1e-9)
        bce = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        return float(bce + l2 * 0.5 * np.sum(self.w ** 2))
