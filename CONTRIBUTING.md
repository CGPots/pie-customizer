# Contributing to Pie Customizer

Thanks for helping improve Pie Customizer.

## Reporting Bugs

Use the public
[GitHub issue tracker](https://github.com/CGPots/pie-customizer/issues) and
include:

1. Blender version and operating system.
2. Exact steps to reproduce the problem.
3. Expected and actual behavior.
4. A screenshot or complete Blender error message, if available.

## Development

The extension source is in `pie_customizer/`. Blender must unregister and
register the add-on when scripts are reloaded. Keep the import structure in
`pie_customizer/__init__.py` consistent with Blender's
[Reloading Scripts guide](https://developer.blender.org/docs/handbook/extensions/addon_dev_setup/#reloading-scripts).

Run unit tests from the repository root:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Validate and build with Blender's official extension commands:

```bash
blender --command extension validate pie_customizer
blender --command extension build \
  --source-dir pie_customizer \
  --output-filepath dist/pie_customizer-<version>.zip
```

See Blender's
[Extension command-line documentation](https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html#subcommand-build)
for current options.

## Release Package

Do not place tests, development scripts, diagnostics, caches, or existing ZIP
archives in the extension source directory. The published package must be
created with Blender's command-line build tool.
