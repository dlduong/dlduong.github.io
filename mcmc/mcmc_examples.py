"""Small, independently implemented MCMC examples for the crash course.

Run: python mcmc_examples.py
Dependencies: numpy, scipy, matplotlib.
Modern R-hat is implemented for teaching; use maintained diagnostic software
such as ArviZ for research. MCSE/mean ESS below use non-overlapping batch means,
not rank-based bulk ESS. All chains must first be assessed for exploration.
"""
from pathlib import Path
import json
import time
import numpy as np
from scipy.stats import norm, rankdata
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def log_target(x):
    return -0.5*x*x - 0.5*((2.0-x)/0.5)**2


def rwm(logp, x0, scale, draws=10_000, warmup=2_000, seed=42):
    """Scalar Gaussian random-walk MH; repeats rejected states."""
    if scale <= 0 or draws < 1 or warmup < 0:
        raise ValueError("Require scale > 0, draws >= 1, warmup >= 0")
    rng = np.random.default_rng(seed)
    x = float(x0)
    lp = float(logp(x))
    if not np.isfinite(lp):
        raise ValueError("Initial state must have finite log density")
    samples = np.empty(draws)
    accepted = 0
    for t in range(warmup + draws):
        z = x + scale*rng.normal()
        lz = float(logp(z))
        if np.isnan(lz) or np.isposinf(lz):
            raise ValueError("Invalid proposed log density")
        take = np.log(rng.uniform()) < min(0.0, lz-lp)
        if take:
            x, lp = z, lz
        if t >= warmup:
            samples[t-warmup] = x
            accepted += int(take)
    return samples, accepted/draws


def classical_rhat(chains):
    """Variance-ratio formula; not the recommended final diagnostic alone."""
    chains = np.asarray(chains, dtype=float)
    m, n = chains.shape
    if m < 2 or n < 2:
        raise ValueError("Need at least two chains and two draws")
    w = np.var(chains, axis=1, ddof=1).mean()
    b = n*np.var(chains.mean(axis=1), ddof=1)
    if w == 0:
        return float("inf") if b > 0 else float("nan")
    return float(np.sqrt(((n-1)/n*w + b/n)/w))


def rank_split_rhat(chains):
    """Maximum of rank-normalized split and folded-split R-hat."""
    chains = np.asarray(chains, dtype=float)
    half = chains.shape[1]//2
    if half < 2:
        raise ValueError("Need at least four draws per chain")
    split = np.concatenate([chains[:, :half], chains[:, -half:]], axis=0)

    def rank_normalize(a):
        ranks = rankdata(a.ravel(), method="average")
        z = norm.ppf((ranks-3/8)/(ranks.size+1/4))
        return z.reshape(a.shape)

    ranked = classical_rhat(rank_normalize(split))
    folded = classical_rhat(rank_normalize(np.abs(split-np.median(split))))
    return max(ranked, folded)


def batch_summary(chains, batch_size=None):
    """MCSE and mean ESS via non-overlapping batch means.

    Estimates a long-run variance per chain, then pools independent chains.
    Does not detect all initialization or mode-exploration problems.
    Batch length must be adequate relative to the dependence timescale.
    """
    chains = np.asarray(chains, dtype=float)
    if chains.ndim != 2:
        raise ValueError("Expected (chain, draw) array")
    m, n = chains.shape
    b = int(np.sqrt(n)) if batch_size is None else int(batch_size)
    batches = n//b
    if b < 1 or batches < 10:
        raise ValueError("Need positive batch size and at least ten batches")
    n_used = batches*b
    x = chains[:, :n_used]
    means = x.reshape(m, batches, b).mean(axis=2)
    long_run_var = b*np.var(means, axis=1, ddof=1).mean()
    posterior_var = np.var(x.ravel(), ddof=1)
    mcse = np.sqrt(long_run_var/(m*n_used))
    ess = m*n_used*posterior_var/long_run_var
    return {
        "mean": float(x.mean()),
        "posterior_variance": float(posterior_var),
        "mcse_mean_batch": float(mcse),
        "ess_mean_batch": float(ess),
        "rank_split_rhat": rank_split_rhat(x),
        "batch_size": b,
        "draws_used_total": int(m*n_used),
    }


def acf_fft(x, max_lag=100):
    """Biased sample ACF for plotting, not a full ESS estimator."""
    x = np.asarray(x, dtype=float)-np.mean(x)
    n = len(x)
    fft_n = 1 << (2*n-1).bit_length()
    f = np.fft.rfft(x, n=fft_n)
    cov = np.fft.irfft(f*np.conjugate(f), n=fft_n)[:n]
    return cov[:max_lag+1]/cov[0]


def gibbs_gaussian(rho, draws=20_000, warmup=2_000, seed=42, x0=None):
    if abs(rho) >= 1:
        raise ValueError("Require abs(rho) < 1")
    rng = np.random.default_rng(seed)
    x = np.zeros(2) if x0 is None else np.array(x0, dtype=float).copy()
    conditional_sd = np.sqrt(1-rho*rho)
    out = np.empty((draws, 2))
    for t in range(warmup+draws):
        x[0] = rho*x[1]+conditional_sd*rng.normal()
        x[1] = rho*x[0]+conditional_sd*rng.normal()
        if t >= warmup:
            out[t-warmup] = x
    return out


def leapfrog(x, p, grad_u, step_size, steps, mass_inv):
    """Deterministic integrator without final momentum flip."""
    x, p = np.array(x, dtype=float).copy(), np.array(p, dtype=float).copy()
    p -= 0.5*step_size*grad_u(x)
    for j in range(steps):
        x += step_size*(mass_inv@p)
        if j < steps-1:
            p -= step_size*grad_u(x)
    p -= 0.5*step_size*grad_u(x)
    return x, p


def hmc(u, grad_u, x0, step_size=0.15, steps=6,
        mass=None, draws=10_000, warmup=2_000, seed=42):
    """Fixed-length HMC, full momentum refresh, MH correction, no adaptation."""
    x = np.atleast_1d(np.array(x0, dtype=float)).copy()
    d = len(x)
    mass = np.eye(d) if mass is None else np.asarray(mass, dtype=float)
    mass_chol = np.linalg.cholesky(mass)
    mass_inv = np.linalg.inv(mass)
    rng = np.random.default_rng(seed)
    out = np.empty((draws, d))
    energy_errors = np.empty(draws)
    accepted = 0
    for t in range(warmup+draws):
        p = mass_chol@rng.normal(size=d)
        z, pz = leapfrog(x, p, grad_u, step_size, steps, mass_inv)
        pz = -pz  # makes the deterministic proposal involutive
        h0 = float(u(x)+0.5*p@mass_inv@p)
        h1 = float(u(z)+0.5*pz@mass_inv@pz)
        take = np.isfinite(h1) and np.log(rng.uniform()) < min(0.0, h0-h1)
        if take:
            x = z
        if t >= warmup:
            out[t-warmup] = x
            energy_errors[t-warmup] = h1-h0
            accepted += int(take)
    return out, accepted/draws, energy_errors


def pcn(phi, prior_chol, x0, beta=0.3, draws=20_000, warmup=3_000, seed=42):
    """Zero-mean Gaussian-prior pCN; phi is the negative log likelihood."""
    if not 0 < beta <= 1:
        raise ValueError("Require 0 < beta <= 1")
    rng = np.random.default_rng(seed)
    x = np.asarray(x0, dtype=float).copy()
    prior_chol = np.asarray(prior_chol, dtype=float)
    phix = float(phi(x))
    out = np.empty((draws, len(x)))
    accepted = 0
    for t in range(warmup+draws):
        xi = prior_chol@rng.normal(size=len(x))
        z = np.sqrt(1-beta*beta)*x+beta*xi
        phiz = float(phi(z))
        take = np.log(rng.uniform()) < min(0.0, phix-phiz)
        if take:
            x, phix = z, phiz
        if t >= warmup:
            out[t-warmup] = x
            accepted += int(take)
    return out, accepted/draws


def deterministic_checks():
    """Small meaningful checks of balance, MH direction, and HMC integration."""
    pi = np.array([0.2, 0.8])
    p = np.array([[0.1, 0.9], [0.225, 0.775]])
    np.testing.assert_allclose(pi@p, pi, atol=1e-14)
    np.testing.assert_allclose(pi[:, None]*p, (pi[:, None]*p).T, atol=1e-14)
    np.testing.assert_allclose(np.exp(log_target(2.1)-log_target(1.6)), np.exp(-0.625))
    grad = lambda x: 5*(x-1.6)
    x, pz = leapfrog([1.6], [1.0], grad, 0.2, 1, np.eye(1))
    np.testing.assert_allclose(x, [1.8], atol=1e-14)
    np.testing.assert_allclose(pz, [0.9], atol=1e-14)
    a, b = leapfrog(x, -pz, grad, 0.2, 1, np.eye(1))
    np.testing.assert_allclose(a, [1.6], atol=1e-14)
    np.testing.assert_allclose(b, [-1.0], atol=1e-14)
    # Constant and iid chains exercise the diagnostic logic.
    rng = np.random.default_rng(900)
    good = rng.normal(size=(4, 10_000))
    bad = good+np.arange(4)[:, None]*3
    assert rank_split_rhat(good) < 1.01
    assert rank_split_rhat(bad) > 1.1


def main(output_dir=None):
    output_dir = Path(__file__).parent/"results" if output_dir is None else Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    deterministic_checks()
    results = {"notes": "MCSE and mean ESS use batch means. Timing is machine dependent."}
    scales = [0.05, 1.0, 5.0]
    starts = [-3., 0., 3., 6.]
    rwm_results, saved = [], {}
    fig, axes = plt.subplots(3, 2, figsize=(11, 9), constrained_layout=True)
    for row, scale in enumerate(scales):
        start_time = time.perf_counter()
        runs = [rwm(log_target, start, scale, seed=100+j) for j, start in enumerate(starts)]
        seconds = time.perf_counter()-start_time
        chains = np.stack([r[0] for r in runs])
        stats = batch_summary(chains)
        stats.update({"scale": scale, "acceptance": float(np.mean([r[1] for r in runs])),
                      "seconds": seconds, "ess_mean_per_second": stats["ess_mean_batch"]/seconds,
                      "exact_stationary_acceptance": float(2/np.pi*np.arctan(2*np.sqrt(0.2)/scale))})
        stats["probability_gt_2"] = batch_summary((chains > 2).astype(float))
        rwm_results.append(stats)
        saved[f"rwm_{scale}"] = chains
        for j, chain in enumerate(chains):
            axes[row, 0].plot(chain[:1500], alpha=0.65, lw=0.5, label=f"Chain {j+1}")
        axes[row, 0].axhline(1.6, color="black", ls="--", lw=1)
        axes[row, 0].set(title=f"RWM scale {scale}: acceptance {stats['acceptance']:.3f}",
                         xlabel="Retained iteration", ylabel="x")
        axes[row, 1].plot(acf_fft(chains[0], 100), color="#156a8a")
        axes[row, 1].axhline(0, color="black", lw=0.5)
        axes[row, 1].set(title="Autocorrelation of chain 1", xlabel="Lag", ylabel="ACF")
    axes[0, 0].legend(ncol=4, fontsize=8)
    fig.savefig(output_dir/"rwm_traces_and_acf.png", dpi=160)
    plt.close(fig)
    results["rwm"] = rwm_results
    # A statistical sanity check, expressed in estimated MCSE units.
    medium = rwm_results[1]
    assert abs(medium["mean"]-1.6) < 6*medium["mcse_mean_batch"]
    assert abs(medium["posterior_variance"]-0.2) < 0.02

    gibbs_results = []
    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    for rho in [0., 0.9, 0.99]:
        runs = np.stack([gibbs_gaussian(rho, seed=200+j, x0=[j-2., 2.-j]) for j in range(4)])
        chains = runs[:, :, 1]
        stats = batch_summary(chains)
        stats.update({"rho": rho, "theoretical_tau": (1+rho*rho)/(1-rho*rho),
                      "theoretical_ess_mean": chains.size*(1-rho*rho)/(1+rho*rho)})
        gibbs_results.append(stats)
        ax.plot(acf_fft(chains[0], 150), label=f"rho={rho}")
        ax.plot(np.arange(151), rho**(2*np.arange(151)), color="black", lw=0.5, alpha=0.5)
    ax.set(xlabel="Lag in complete Gibbs sweeps", ylabel="ACF of second coordinate",
           title="Gibbs sampling: 100% conditional acceptance can still mix slowly")
    ax.legend()
    fig.savefig(output_dir/"gibbs_autocorrelation.png", dpi=160)
    plt.close(fig)
    results["gibbs"] = gibbs_results

    u = lambda x: 2.5*np.sum((x-1.6)**2)
    grad = lambda x: 5*(x-1.6)
    runs = [hmc(u, grad, [start], seed=300+j) for j, start in enumerate(starts)]
    chains = np.stack([r[0][:, 0] for r in runs])
    stats = batch_summary(chains)
    stats["acceptance"] = float(np.mean([r[1] for r in runs]))
    stats["step_size"], stats["leapfrog_steps"] = 0.15, 6
    stats["squared_deviation"] = batch_summary((chains-1.6)**2)
    stats["note"] = "Fixed-length HMC, not NUTS; tuning is specific to this Gaussian example."
    assert abs(stats["mean"]-1.6) < 6*stats["mcse_mean_batch"]
    sq = stats["squared_deviation"]
    assert abs(sq["mean"]-0.2) < 6*sq["mcse_mean_batch"]
    results["hmc_scalar"] = stats
    saved["hmc_scalar"] = chains

    # Two-dimensional inverse problem, observed sum and unobserved difference.
    a = np.ones((1, 2))
    cov = np.eye(2)-a.T@a/2.01
    mean = np.ones(2)/2.01
    precision = np.linalg.inv(cov)
    u2 = lambda x: 0.5*(x-mean)@precision@(x-mean)
    grad2 = lambda x: precision@(x-mean)
    # Under p~N(0,M), M=C^{-1} equalizes the Gaussian dynamics.
    runs = [hmc(u2, grad2, mean+np.array([j-1.5, 1.5-j]), step_size=0.2,
                steps=8, mass=precision, seed=400+j) for j in range(4)]
    samples = np.stack([r[0] for r in runs])
    sum_stats = batch_summary(samples.sum(axis=2))
    diff_stats = batch_summary(samples[:, :, 0]-samples[:, :, 1])
    results["two_parameter_inverse_problem"] = {
        "exact_mean": mean.tolist(), "exact_covariance": cov.tolist(),
        "estimated_mean": samples.mean(axis=(0, 1)).tolist(),
        "estimated_covariance": np.cov(samples.reshape(-1, 2).T).tolist(),
        "sum": sum_stats, "difference": diff_stats,
        "exact_sum_variance": (a@cov@a.T).item(), "exact_difference_variance": 2.,
        "acceptance": float(np.mean([r[1] for r in runs])),
    }
    assert abs(sum_stats["mean"]-2/2.01) < 6*sum_stats["mcse_mean_batch"]
    assert abs(diff_stats["mean"]) < 6*diff_stats["mcse_mean_batch"]
    fig, ax = plt.subplots(figsize=(6.5, 6), constrained_layout=True)
    ax.scatter(samples[0, ::5, 0], samples[0, ::5, 1], s=3, alpha=0.25)
    grid = np.linspace(-2., 3., 200)
    ax.plot(grid, 1-grid, "k--", label="Noise-free fit u1 + u2 = 1")
    ax.set(xlabel="u1", ylabel="u2", title="A Bayesian inverse problem: the posterior ridge")
    ax.legend()
    fig.savefig(output_dir/"inverse_problem_ridge.png", dpi=160)
    plt.close(fig)
    saved["two_parameter_inverse_problem"] = samples

    # Coordinate-dependent prior, scalar observation: finite-dimensional pCN example.
    d = 6
    prior_vars = 1/np.arange(1, d+1, dtype=float)**2
    prior_cov = np.diag(prior_vars)
    prior_chol = np.diag(np.sqrt(prior_vars))
    obs = 1/np.arange(1, d+1, dtype=float)
    noise_var, y = 0.25, 1.
    phi = lambda x: 0.5*(y-obs@x)**2/noise_var
    gain = prior_cov@obs/(noise_var+obs@prior_cov@obs)
    mean_pcn = gain*y
    cov_pcn = prior_cov-np.outer(gain, obs@prior_cov)
    runs = [pcn(phi, prior_chol, np.zeros(d), beta=0.5, seed=500+j) for j in range(4)]
    samples = np.stack([r[0] for r in runs])
    functional = batch_summary(samples@obs)
    exact_qmean = float(obs@mean_pcn)
    assert abs(functional["mean"]-exact_qmean) < 6*functional["mcse_mean_batch"]
    results["pcn"] = {"exact_mean": mean_pcn.tolist(),
                      "estimated_mean": samples.mean(axis=(0, 1)).tolist(),
                      "functional": functional, "exact_functional_mean": exact_qmean,
                      "acceptance": float(np.mean([r[1] for r in runs]))}

    results["validation"] = "Deterministic balance/reversibility checks and Gaussian moment sanity checks passed."
    (output_dir/"results.json").write_text(json.dumps(results, indent=2)+"\n")
    np.savez_compressed(output_dir/"samples.npz", **saved)
    print("Scale  Acceptance  Mean     MCSE    ESS(mean)  R-hat")
    for r in rwm_results:
        print(f"{r['scale']:5.2f}  {r['acceptance']:10.3f}  {r['mean']:.4f}  "
              f"{r['mcse_mean_batch']:.4f}  {r['ess_mean_batch']:9.0f}  {r['rank_split_rhat']:.4f}")
    print("Gaussian checks passed; results saved in", output_dir)
    return results


if __name__ == "__main__":
    main()
