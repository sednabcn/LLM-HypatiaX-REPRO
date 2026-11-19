# Core-295 research track moved to Improvements

The standalone Core-295 candidate-discovery, catalogue, review, planning, adapter and fail-closed shard tooling is being separated from the canonical reproducibility pipeline.

- Destination: [LLM-HypatiaX-REPRO-Improvements](https://github.com/sednabcn/LLM-HypatiaX-REPRO-Improvements)
- Transfer PR: [#1](https://github.com/sednabcn/LLM-HypatiaX-REPRO-Improvements/pull/1)
- Original repository-relative paths are preserved in the destination.
- The Core-295 shard driver remains planning-only unless `--execute` is explicitly supplied; no experiment was launched as part of this migration.

Merge order matters: accept the Improvements transfer before merging the matching source-removal PR. The canonical repository retains this pointer so the research track remains discoverable.
