# Contributing

Thanks for helping improve Android Icon Compliance Resizer.

## Good First Contributions

- Add another real Android icon example.
- Improve beginner documentation.
- Add validation checks for Android resource edge cases.
- Report launcher mask cropping cases with input artwork and generated previews.
- Add tests for project layouts such as Flutter, React Native, Expo, or Capacitor.

## Development Setup

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests
```

For editable command-line testing:

```bash
python -m pip install -e .
android-icon-pack --help
android-icon-validate --help
android-icon-previews --help
```

## Pull Request Checklist

- Keep changes focused and small.
- Add or update tests when behavior changes.
- Run `python -m unittest discover -s tests`.
- Include before/after previews when changing icon packing or mask rendering behavior.
- Do not include private app assets, secrets, tokens, or unreleased production configuration.

## Reporting Bugs

Please include:

- Operating system and Python version.
- Command you ran.
- Input artwork type: single source, foreground/background, monochrome.
- Project layout: native Android, Flutter, React Native, Expo, Capacitor, or other.
- Relevant warning/error output.
- Preview images when the issue is visual.
