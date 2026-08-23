# ish-drill

iSH practice repo - clone, edit, push drills

## graph_agent_test.py

Minimal live attention graph test.

### Run in iSH
```bash
apk add python3
git clone https://github.com/Peekabot/ish-drill.git
cd ish-drill
python3 graph_agent_test.py
```

### Commands
- Type any word → bumps attention on that item
- `decide` → calls the (currently fake) LLM with current top attention
- `q` → quit

Works in both iSH and Pythonista.
