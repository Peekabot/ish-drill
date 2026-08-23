#!/usr/bin/env python3
"""
Minimal live attention graph + selective LLM call.
Designed to run in iSH / Alpine and Pythonista.
"""

import json
from collections import defaultdict

# ---------- simple live state ----------
class LiveState:
    def __init__(self):
        self.attention = defaultdict(float)
        self.history = []
        self.step = 0

    def bump(self, item, amount=0.4):
        self.attention[item] += amount
        self.step += 1

    def decay(self, factor=0.85):
        for k in list(self.attention):
            self.attention[k] *= factor
            if self.attention[k] < 0.05:
                del self.attention[k]

    def top(self, k=4):
        return sorted(self.attention.items(), key=lambda x: x[1], reverse=True)[:k]

    def summary(self):
        top = self.top()
        return {
            "step": self.step,
            "attention": {k: round(v, 2) for k, v in top}
        }

state = LiveState()

# ---------- fake / real LLM call ----------
def ask_llm(prompt: str) -> str:
    """
    Replace this with a real API call later.
    Right now it just echoes so the test runs offline.
    """
    return f"[LLM would answer]: {prompt[:80]}..."

# ---------- main loop ----------
def run_test():
    print("=== Live Attention Graph Test ===")
    print("Type items to bump attention. Type 'decide' to call LLM. Type 'q' to quit.\n")

    while True:
        try:
            cmd = input("> ").strip()
        except EOFError:
            break
        if not cmd:
            continue
        if cmd.lower() in ("q", "quit", "exit"):
            break

        if cmd.lower() == "decide":
            top = state.top()
            context = ", ".join(f"{k}({v:.2f})" for k, v in top) or "nothing"
            prompt = f"Current attention: {context}. What should the agent focus on next?"
            answer = ask_llm(prompt)
            print(answer)
            state.bump("llm_decision")
            state.history.append(answer)
        else:
            # treat input as an item to attend to
            state.bump(cmd)
            print(f"Bumped '{cmd}'. Current top: {state.top()}")

        state.decay()
        print("State:", json.dumps(state.summary(), indent=2))
        print()

if __name__ == "__main__":
    run_test()
