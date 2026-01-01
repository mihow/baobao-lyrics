# Task 1: Update CLAUDE.md with Template Structure

**Status**: Ready to implement
**Complexity**: Low
**Dependencies**: None

## Objective

Replace the current CLAUDE.md with a comprehensive version based on CLAUDE.template.md that includes all the template's best practices plus Baobao-specific project details.

## Current State

- **Current CLAUDE.md**: `/home/michael/Projects/Leon/baobao/CLAUDE.md` (7,856 bytes, last updated Dec 20)
- **Template**: `/home/michael/Projects/Leon/baobao/CLAUDE.template.md` (8,882 bytes)
- Current file has good project-specific content but lacks template's organizational structure

## Implementation Plan

### 1. Preserve Existing Content

Extract project-specific sections from current CLAUDE.md:
- Project Overview (lines 1-20)
- Architecture (lines 22-109)
- Output Formats (lines 111-149)
- Development Workflow (lines 151-195)
- Key Design Decisions (lines 237-242)
- Performance Characteristics (lines 244-247)
- Known Limitations (lines 249-254)

### 2. Merge Template Structure

Use CLAUDE.template.md as base and populate project sections:

**From Template (lines 1-189)** - Keep as-is:
- Cost Optimization
- Efficient Development Practices
- Python Type Annotations
- Think Holistically
- Development Best Practices
- Using Subagents
- Documentation Organization
- Command Line Shortcuts

**Fill in Template Sections (lines 190-329)** with Baobao data:
- Project Overview → Use existing content
- Quick Stats → Add metrics (1,199 production lines, 857 test lines, etc.)
- Key Technologies → Python 3.12+, Whisper, Ollama, Typer, Pydantic
- Architecture Overview → Current module structure
- Key Files to Understand → List critical files with line numbers
- Development Workflow → Setup commands, common commands
- Testing Strategy → Pytest markers, coverage
- Third-Party Integrations → Ollama, stable-ts, faster-whisper
- Learnings and Gotchas → TBD (populate as discovered)
- Common Tasks → Add new output format, new LLM provider, etc.

### 3. Add Baobao-Specific Details

**New sections to add**:
- Model sizes and performance characteristics
- Output format examples (FULL, EMOJI, LEARN)
- Enhancement pipeline details
- Caching strategy
- File naming conventions

### 4. Update Last Modified Date

Add footer: `*Last updated: 2025-12-31*`

## Critical Files

- `/home/michael/Projects/Leon/baobao/CLAUDE.md` (existing, to replace)
- `/home/michael/Projects/Leon/baobao/CLAUDE.template.md` (source template)

## Validation

- [ ] All template sections present
- [ ] All existing project-specific content preserved
- [ ] File paths and line numbers included for key components
- [ ] Quick Stats section accurate
- [ ] Common Tasks reflect actual codebase patterns

## Notes

- Keep file under 10KB for quick loading
- Prioritize file:line references over lengthy explanations
- Update this doc as architecture changes (especially after tasks 2-5)
