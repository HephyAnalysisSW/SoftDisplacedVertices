#!/usr/bin/env python3

import math
import os
import random
import matplotlib.pyplot as plt


observations = [0.5, -0.2, -0.8, 1.2, -1.2, -2.0]
n_toys = 100_000
alpha = 0.05
seed = 12345
plot_file = os.path.join(os.path.dirname(__file__), "lrt_test_statistic_distribution.pdf")


def log_likelihood(x, mean, sigma):
    n = len(x)
    chi2 = sum((xi - mean) ** 2 for xi in x) / sigma**2
    return -0.5 * n * math.log(2.0 * math.pi) - n * math.log(sigma) - 0.5 * chi2


def lrt_statistic(x):
    n = len(x)
    mean_hat = sum(x) / n
    sigma_hat = math.sqrt(sum((xi - mean_hat) ** 2 for xi in x) / n)

    log_l0 = log_likelihood(x, mean=0.0, sigma=1.0)
    log_l1 = log_likelihood(x, mean=mean_hat, sigma=sigma_hat)
    return -2.0 * (log_l0 - log_l1)


random.seed(seed)
n = len(observations)
observed_q = lrt_statistic(observations)
toy_q = [lrt_statistic([random.gauss(0.0, 1.0) for _ in range(n)]) for _ in range(n_toys)]
p_value = sum(q >= observed_q for q in toy_q) / n_toys

plt.hist(toy_q, bins=80, density=True, histtype="stepfilled", alpha=0.6, label="Toys under H0")
plt.axvline(observed_q, color="red", linewidth=2, label="Observed")
plt.xlabel("-2 log(L0 / L1)")
plt.ylabel("Density")
plt.legend()
plt.tight_layout()
plt.savefig(plot_file)

print(f"observations = {observations}")
print(f"N = {n}")
print(f"toys = {n_toys}")
print(f"test statistic = {observed_q:.6f}")
print(f"p-value = {p_value:.6f}")
print(f"plot = {plot_file}")

if p_value < alpha:
    print(f"Reject H0 at alpha = {alpha}.")
else:
    print(f"Do not reject H0 at alpha = {alpha}.")
