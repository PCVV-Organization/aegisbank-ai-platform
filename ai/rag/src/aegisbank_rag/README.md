# Retrieval-Augmented Generation Package

This package prepares and retrieves document context for grounded answers. Retrieved content is untrusted input: it can inform an answer but cannot authorize tools or override deterministic policy.

## Responsibilities

- Corpus loading, parsing, and chunking prepare source material.
- Lexical, dense, and hybrid retrieval locate candidate evidence.
- Vector and cache adapters connect the package to configured stores.
- Context assembly and prompting provide bounded evidence to generation.
- Provider adapters isolate model-service integration.

Keep evaluation data separate from tuning data, preserve source provenance where available, and use synthetic data only. Verify runtime claims against tests and current configuration.
