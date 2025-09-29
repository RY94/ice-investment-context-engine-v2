# ICE Task Completion Checklist

## Before Completing Any Task

### Code Quality Gates (CRITICAL)
- ✅ All tests pass
- ✅ No lint errors  
- ✅ No type errors
- ✅ Security best practices followed
- ✅ Performance considerations addressed

### Testing Commands
```bash
# Test LightRAG integration
python src/ice_lightrag/test_basic.py

# Validate API configuration
python test_api_key.py

# Run comprehensive test suite
python tests/test_runner.py

# Test simplified architecture
cd updated_architectures/tests && python test_architecture_structure.py
```

### Documentation Updates
- Update README.md for user-facing changes
- Update CLAUDE.md for development workflow changes
- Sync changes across linked documentation files
- Update PROJECT_CHANGELOG.md for significant changes

### Architecture Synchronization (MANDATORY)
When modifying ICE core architecture or logic:
1. **Update main notebook**: Modify `ice_main_notebook.ipynb` to reflect changes
2. **Test end-to-end**: Execute entire notebook to validate 6-section workflow
3. **Update documentation**: Sync with README.md, PROJECT_STRUCTURE.md if needed

### Git Workflow
- Never mention co-authored-by or AI tool usage in commits
- Only commit when explicitly requested by user
- Use clear, descriptive commit messages
- Ensure no secrets or API keys are committed

### File Management
- Check for existing similar files before creating new ones
- Archive old files with timestamp suffix (e.g., `old_file_2024-09-13.py`)
- Never delete critical files without explicit permission
- Use `tmp/` directory with `tmp_` prefix for development temp files

### Environment Verification
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check Python path
echo $PYTHONPATH

# Verify dependencies
pip list | grep lightrag
pip list | grep openai
```

## Post-Completion Actions
- Mark todos as completed immediately when done
- Clean up temporary files
- Report "✅ Temp files cleaned up" if applicable
- Validate cross-references remain intact after changes