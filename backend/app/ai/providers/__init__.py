"""AI provider adapters (one module per provider, registered in ../factory.py).

Adding a provider: implement app/ai/base.AIProvider in a new module here, then
add a branch to get_provider() in app/ai/factory.py. Optionally implement
embed() if the provider has an embeddings API (Ollama does; see base.py for
the optional-capability contract).
"""