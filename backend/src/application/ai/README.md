# AI Module

This module contains neural components of the Neuro-Symbolic architecture.

## Components

### EmbeddingService
- **Purpose**: Generates vector embeddings for text using `sentence-transformers`.
- **Model**: `all-MiniLM-L6-v2` (default).
- **Caching**: LRU Cache (max 1024 items).
- **Usage**:
  ```python
  service = EmbeddingService()
  vector = service.encode("Expense description")
  similarity = service.similarity(v1, v2)
  ```

### Predictor (Coming Soon)
- Uses embeddings for k-NN classification.

### SimulatorAI (Coming Soon)
- LLM-based intent parsing for "What-If" scenarios.
