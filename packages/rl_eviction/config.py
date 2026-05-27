"""Default configuration and hyperparameters for RL eviction agent."""
DEFAULT_CONFIG = {
    "mode": "tabular",  # 'tabular' or 'nn'
    "alpha": 0.1,
    "gamma": 0.99,
    "epsilon": 0.1,
    "min_epsilon": 0.01,
    "epsilon_decay": 0.9999,
    "age_bins": 8,
    "freq_bins": 8,
    "dram_penalty": 1.0,
    "hit_reward": 1.0,
    "nn_hidden": 32,
    "seed": 0,
    # PARSEC/cpu-workload features
    "use_pc": True,
    "pc_buckets": 64,
    "use_reuse": True,
    "reuse_sample_window": 128,
    "reuse_bins": 5,
    "use_ewma_miss": True,
    "ewma_alpha": 0.01,
    # NN input dim (state + action). Set to 7 to cover: [age,freq,ewma_miss] + [age,freq,pc_bucket,reuse_bin]
    "nn_input_dim": 7,
}
