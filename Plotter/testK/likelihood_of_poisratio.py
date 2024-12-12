""" import ROOT
from ROOT import Math

# Function to calculate the profile likelihood ratio for Poisson yields
def profile_likelihood_errors(y1, y2, cl=0.954):
    if y2 == 0:
        return 0, 0, 0

    ratio = y1 / y2

    # Define the negative log-likelihood function
    class NLL:
        def __call__(self, vecIn):
            r = vecIn if type(vecIn) == float else vecIn[0]
            if r <= 0:
                return 1e9  # Penalize invalid ratios
            return -y1 * ROOT.TMath.Log(y2 * r) + (y1 + y2 * r)

    nll = NLL()

    # Create a ROOT::Math::Minimizer
    minimizer = Math.Factory.CreateMinimizer("Minuit2", "")
    minimizer.SetMaxFunctionCalls(10000)
    minimizer.SetTolerance(1e-6)

    # Define the function to minimize
    func = Math.Functor(nll, 1)
    minimizer.SetFunction(func)

    # Set the initial parameter value and range
    minimizer.SetVariable(0, "r", ratio, 0.1)

    # Perform the minimization
    if not minimizer.Minimize():
        raise RuntimeError("Minimization failed.")

    r_best = minimizer.X()[0]
    min_nll = nll(r_best)

    # Determine the confidence interval threshold
    delta_nll_threshold = min_nll + 1.92  # For 95.4% CL

    # Find the lower bound
    def find_bound(start, direction):
        step = 0.01 * direction
        r = start
        while True:
            r += step
            if nll(r) > delta_nll_threshold:
                return r

    low_r = find_bound(r_best, -1)
    high_r = find_bound(r_best, 1)

    err_low = r_best - low_r
    err_high = high_r - r_best

    return (r_best, err_low, err_high), (low_r, r_best, high_r)

# Example usage
yields1 = [3, 30, 300]
yields2 = [2, 20, 200]

for y1, y2 in zip(yields1, yields2):
    (ratio, err_low, err_high), (low_r, _, high_r) = profile_likelihood_errors(y1, y2)
    print(f"Ratio: {ratio:.3f}, Lower Error: {err_low:.3f}, Upper Error: {err_high:.3f} -- CI: [{low_r:.3f},{high_r:.3f}]")
 """

import ROOT
from ROOT import Math
import numpy as np
import scipy.stats as st

# Function to calculate profile likelihood errors without large-sample hypothesis
def profile_likelihood_errors_no_large_sample(y1, y2, cl=0.954):
    if y2 == 0:
        return 0, 0, 0

    ratio = y1 / y2

    # Define the negative log-likelihood
    class NLL:
        def __call__(self, vecIn):
            r = vecIn if type(vecIn) == float else vecIn[0]
            if r <= 0:
                return 1e9  # Penalize invalid ratios
            return -y1 * ROOT.TMath.Log(r) + (y1 + y2) * r

    nll = NLL()

    # Create a minimizer
    minimizer = Math.Factory.CreateMinimizer("Minuit2", "")
    minimizer.SetMaxFunctionCalls(10000)
    minimizer.SetTolerance(1e-6)

    # Define the function to minimize
    func = Math.Functor(nll, 1)
    minimizer.SetFunction(func)
    minimizer.SetVariable(0, "r", ratio, 0.1)

    # Minimize the NLL to find the best-fit ratio
    if not minimizer.Minimize():
        raise RuntimeError("Minimization failed.")

    r_best = minimizer.X()[0]
    min_nll = nll(r_best)

    # Monte Carlo simulation to find the confidence threshold
    n_simulations = 100000
    simulated_ratios = []

    for _ in range(n_simulations):
        y1_sim = np.random.poisson(y1)
        y2_sim = np.random.poisson(y2)
        if y2_sim > 0:
            r_sim = y1_sim / y2_sim
            simulated_ratios.append(nll(r_sim))

    simulated_ratios.sort()
    threshold = simulated_ratios[int((1 - cl) * len(simulated_ratios))]

    # Scan for lower and upper bounds using the threshold
    def find_bound(start, direction):
        step = 0.01 * direction
        r = start
        while True:
            r += step
            if nll(r) > threshold:
                return r

    low_r = find_bound(r_best, -1)
    high_r = find_bound(r_best, 1)

    err_low = r_best - low_r
    err_high = high_r - r_best

    return (r_best, err_low, err_high), (low_r, r_best, high_r)

# Example usage
yields1 = [3, 30, 300]
yields2 = [2, 20, 200]

for y1, y2 in zip(yields1, yields2):
    print('y1:', y1, 'y2:', y2)
    (ratio, err_low, err_high), (low_r, _, high_r) = profile_likelihood_errors_no_large_sample(y1, y2)
    print(f"Ratio: {ratio:.3f}, Lower Error: {err_low:.3f}, Upper Error: {err_high:.3f} -- CI: [{low_r:.3f},{high_r:.3f}]")
