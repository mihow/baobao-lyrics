# Baobao Refactoring Plan - Overview

**Created**: 2025-12-31
**Status**: Planning phase - awaiting validation

## Summary

This plan outlines 5 major improvements to the Baobao Chinese lyrics transcription tool:

1. **Update CLAUDE.md** - Apply template best practices
2. **Simplify defaults** - Make transcription the core, enhancement optional
3. **TTML support** - Modern lyrics format with better structure
4. **Clean up structure** - Organize test files and modules
5. **Embed lyrics** - Support embedded time-synced lyrics in audio files

## Task Status Matrix

| Task | Complexity | Status | Dependencies | Needs Research |
|------|-----------|---------|--------------|----------------|
| 1. Update CLAUDE.md | Low | ✅ Ready | None | No |
| 2. Simplify defaults | Medium | ⚠️ Needs validation | None | User preferences |
| 3. TTML support | High | ⚠️ Needs research | Task 2 | Player compatibility |
| 4. Cleanup structure | Low | ✅ Ready | None | Test file analysis |
| 5. Embed lyrics | High | ⚠️ Needs testing | Tasks 2-3 | Player support |

## Task Dependencies

```
Task 1 (CLAUDE.md)
  └─> No dependencies (can do anytime, should update after others)

Task 2 (Simplify defaults)
  └─> No dependencies (foundational change)
      └─> Task 3 depends on this (affects default format)
      └─> Task 5 depends on this (affects workflow)

Task 3 (TTML support)
  └─> Depends on Task 2 (default format decision)
      └─> Task 5 uses TTML output (loose coupling)

Task 4 (Cleanup structure)
  └─> No dependencies (can do independently)

Task 5 (Embed lyrics)
  └─> Depends on Tasks 2-3 (needs final lyric format)
```

## Recommended Execution Order

### Phase 1: Foundation (Can parallelize)
- **Task 4**: Cleanup structure (independent, quick win)
- **Task 2**: Simplify defaults (foundational change)

### Phase 2: Core Features (Sequential)
- **Task 3**: TTML support (depends on Task 2 decisions)

### Phase 3: Advanced Features
- **Task 5**: Embed lyrics (depends on Tasks 2-3)

### Phase 4: Documentation
- **Task 1**: Update CLAUDE.md (after all changes, reflect final state)

## Critical Questions Requiring Validation

### Task 2: Simplify Defaults

**User preference questions**:
1. Should `baobao audio.mp3` work without subcommand, or require explicit `baobao transcribe audio.mp3`?
2. Keep or remove `process` command?
   - Remove entirely? (simplest)
   - Deprecate with warning? (gradual)
   - Rename to be more explicit? (backward compatible)
3. Default output format: TTML or SRT?
   - Depends on Task 3 player compatibility research

**Impact**: Changes CLI surface area, affects user workflows

### Task 3: TTML Support

**Player compatibility questions** (CRITICAL):
1. Does **mpv** support TTML? (used in `preview` command)
   - If no: Need fallback strategy
2. Does **VLC** support TTML?
3. Mobile player support (iOS/Android)?
4. Apple Music / iTunes compatibility?

**Technical questions**:
1. XML library: stdlib `xml.etree.ElementTree` or `lxml`?
   - Start with stdlib, add lxml if needed
2. TTML validation: Should we validate against W3C schema?
   - Basic validation sufficient for MVP
3. Word-level timing: Implement in Phase 1 or later?
   - Start with line-level, add word-level as enhancement

**Assumptions to validate**:
- TTML provides better structure than SRT (TRUE - verified in spec)
- Players widely support TTML (UNKNOWN - needs testing)
- TTML file size acceptable (larger than SRT due to XML verbosity)

### Task 4: Cleanup Structure

**File analysis questions**:
1. What do root test files contain?
   - `/home/michael/Projects/Leon/baobao/test_transcription.py` (24 KB - largest)
   - `/home/michael/Projects/Leon/baobao/test_e2e_transcription.py` (9.5 KB)
   - `/home/michael/Projects/Leon/baobao/test_english_transcription.py` (6 KB)
2. Are they superseded by organized tests in `tests/`?
3. Do they contain unique test coverage?

**Actions needed**:
- Read these files to understand content
- Compare with organized tests
- Decide: merge, archive, or delete

### Task 5: Embed Lyrics

**Player compatibility questions** (CRITICAL):
1. Which players support SYLT synchronized lyrics?
   - Desktop: mpv? VLC? MusicBee? iTunes?
   - Mobile: iOS Music app? Android players?
2. How do players display SYLT vs external .lrc files?
3. Is SYLT worth implementing given limited support?

**Technical questions**:
1. SYLT line format: All three lines (Chinese, pinyin, English) at same timestamp?
   - Or stagger slightly (+100ms)?
2. Multiple SYLT frames: One per language, or single combined frame?
3. Should we recommend MP3 over M4A for sync support?

**Assumptions to validate**:
- SYLT support is limited vs external .lrc files (TRUE - research confirms)
- External files are better primary solution (LIKELY)
- Embedded lyrics are "bonus feature" not main feature (RECOMMENDATION)

## Research Gaps

### High Priority

1. **TTML player compatibility** (Task 3)
   - Action: Test TTML files with mpv, VLC, mobile players
   - Impact: Determines if TTML should be default format
   - Timeline: Before implementing Task 3

2. **SYLT player compatibility** (Task 5)
   - Action: Test MP3 with SYLT in common players
   - Impact: Determines if embedding feature is worthwhile
   - Timeline: Before implementing Task 5

### Medium Priority

3. **Root test file contents** (Task 4)
   - Action: Read and analyze root-level test files
   - Impact: Determines merge vs delete strategy
   - Timeline: Before implementing Task 4

### Low Priority

4. **LRC vs TTML adoption** (Task 3)
   - Action: Research which format is more widely used
   - Impact: Informs default format decision
   - Timeline: During Task 3 planning

## Breaking Changes

### Task 2: Simplify Defaults
- **Breaking**: Removing `process` command
- **Breaking**: Changing `batch --skip-enhance` to `batch --enhance`
- **Mitigation**: Deprecation warnings, migration guide

### Task 3: TTML Support
- **Breaking**: Default output format changes from SRT to TTML
- **Mitigation**: Keep SRT available via `--format srt`

### None for Tasks 1, 4, 5 (additive changes only)

## Risk Assessment

| Task | Risk Level | Primary Risk | Mitigation |
|------|-----------|--------------|------------|
| 1 | Low | Lose important docs | Careful merge of existing content |
| 2 | Medium | Break user workflows | Deprecation period, clear docs |
| 3 | High | Limited player support | Keep SRT as option, test extensively |
| 4 | Low | Delete useful tests | Analyze before deleting |
| 5 | High | Limited SYLT support | External files as primary, SYLT as bonus |

## Success Metrics

**After all tasks complete**:
- [ ] Simpler CLI: `baobao audio.mp3` transcribes by default
- [ ] Modern format: TTML as default with structured metadata
- [ ] Clean structure: All tests in `tests/` directory
- [ ] Embedded option: MP3 files can have SYLT lyrics
- [ ] Compatibility: SRT still available for legacy support
- [ ] Documentation: CLAUDE.md reflects new architecture
- [ ] All tests pass with same or better coverage
- [ ] No functionality lost

## Next Steps

### Before Implementation

1. **Validate Task 2 decisions**:
   - User preference: simple command invocation?
   - Keep/remove/deprecate `process` command?

2. **Research Task 3 compatibility**:
   - Test TTML with mpv (critical for `preview`)
   - Test TTML with VLC
   - Test TTML with mobile players
   - Document findings

3. **Analyze Task 4 files**:
   - Read root test files
   - Compare with organized tests
   - Decide merge/archive/delete

4. **Research Task 5 player support**:
   - Test SYLT with common players
   - Document support matrix
   - Decide if feature worth implementing

### Implementation Priority

**Quick wins** (do first):
1. Task 4: Cleanup structure (low risk, immediate value)
2. Task 2: Simplify defaults (foundational for other tasks)

**After research** (do when validated):
3. Task 3: TTML support (after player compatibility confirmed)
4. Task 5: Embed lyrics (after SYLT support confirmed)

**Final step**:
5. Task 1: Update CLAUDE.md (after all changes, document final state)

## Open Questions for User

1. **CLI simplicity**: Do you want `baobao audio.mp3` to work, or prefer explicit `baobao transcribe audio.mp3`?

2. **Process command**: Should we remove, deprecate, or keep the `process` command?

3. **Default format**: After TTML research, should default be TTML or SRT?

4. **Embedded lyrics**: Is SYLT embedding worth implementing given limited player support? Or focus on external files only?

5. **Timeline**: Any urgency on specific tasks, or explore compatibility first?

## Planning Documents

- [task-1-update-claude-md.md](./task-1-update-claude-md.md) - Documentation improvements
- [task-2-simplify-defaults.md](./task-2-simplify-defaults.md) - CLI simplification
- [task-3-ttml-support.md](./task-3-ttml-support.md) - Modern lyrics format
- [task-4-cleanup-structure.md](./task-4-cleanup-structure.md) - File organization
- [task-5-embed-lyrics.md](./task-5-embed-lyrics.md) - Audio embedding feature
