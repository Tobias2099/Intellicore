"""Minimal training example using TraceEnv and RLEvictionAgent.

This script demonstrates the sliding-window training flow:
- Load a CSV trace
- Create TraceEnv and RLEvictionAgent
- For each step: get observation, query env for candidate features (if miss),
  ask agent to select an action, call env.step(action), and update agent with
  the observed reward and next state.

This is a simple online training loop suitable for small traces.
"""
from rl_eviction import TraceEnv, RLEvictionAgent
import numpy as np


def train_on_trace(trace_csv_path, episodes=1):
    env = TraceEnv(trace_csv_path, window_size=64, history=256)
    agent = RLEvictionAgent({"mode": "tabular", "epsilon": 0.1})

    for ep in range(episodes):
        obs = env.reset()
        done = False
        step = 0
        while not done:
            # agent can inspect upcoming access to decide action
            is_miss, candidate_feats, set_idx = env.get_current_info()
            action = None
            if is_miss and candidate_feats is not None:
                # prepare a compact state for tabular agent: use env observation's mean age/freq
                # here we crudely summarize with zeros; in practice compute meaningful state
                state = np.array([0.0, 0.0])
                action_idx = agent.select_action(state, candidate_feats)
                action = int(action_idx)
            # perform step with chosen action (None allowed)
            next_obs, reward, done, info = env.step(action)

            # If agent acted, update it using simple next-state target
            if is_miss and candidate_feats is not None:
                next_is_miss, next_cands, _ = env.get_current_info()
                next_state = np.array([0.0, 0.0])
                agent.update(state, action_idx, reward, next_state, next_cands if next_cands is not None else [])

            obs = next_obs
            step += 1
        print(f"Episode {ep} finished, steps={step}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python train_trace.py trace.csv")
        sys.exit(1)
    train_on_trace(sys.argv[1])
