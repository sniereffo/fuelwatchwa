# Contributing to FuelWatch WA

Thank you for considering contributing to this project!

## Development Principles

- **Async-first**: No blocking calls in Home Assistant event loop
- **Stateless API layer**: Coordinator manages refresh lifecycle
- **Extensible data model**: Designed for future analytics
- **User-focused outputs**: Practical sensors over raw data
- **Git-first workflow**: No manual server edits

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/sniereffo/fuelwatchwa/issues)
2. If not, create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Home Assistant version
   - Relevant logs from `home-assistant.log`

### Suggesting Features

1. Check existing [Issues](https://github.com/sniereffo/fuelwatchwa/issues) for similar suggestions
2. Create a new issue with:
   - Clear use case description
   - How it aligns with the roadmap (see `docs/README.md`)
   - Any implementation ideas

### Pull Requests

1. Fork the repository
2. Create a feature branch from `feature/hacs-integration-scaffold`
3. Make your changes following the code style
4. Test thoroughly in a live Home Assistant instance
5. Update documentation if needed
6. Submit a pull request with:
   - Clear description of changes
   - Link to related issue(s)
   - Test results

## Development Setup

### Manual Testing

1. Copy `custom_components/fuelwatchwa` to your HA `config/custom_components/`
2. Restart Home Assistant
3. Add integration via UI
4. Monitor logs: `docker logs homeassistant -f | grep fuelwatch`

### Code Style

- Follow Home Assistant development guidelines
- Use type hints
- Add docstrings to public methods
- Keep async operations in executor jobs
- Handle errors gracefully

### Testing Checklist

- [ ] Integration loads without errors
- [ ] Sensors populate with data
- [ ] Config flow works end-to-end
- [ ] No blocking calls detected
- [ ] Handles FuelWatch API failures gracefully
- [ ] Multiple fuel types work correctly

## Code of Conduct

- Be respectful and constructive
- Focus on the technical merit of contributions
- Help newcomers get started

## Questions?

Open an issue or discussion on GitHub.

Thank you for contributing! 🎉
