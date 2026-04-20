# Developer Guide

Notes for working on the Foxglove interface app.

## Layout

```
src/foxglove_iface/
  __init__.py            # main() entrypoint - run_app(FoxgloveIfaceApplication())
  application.py         # FoxgloveIfaceApplication: wires config -> FoxgloveConverter
  app_config.py          # FoxgloveIfaceConfig: host, port, channels, separate_levels, parameter_publish_interval
  foxglove_converter.py  # FoxgloveConverter + FoxgloveParameterManager: core bridge logic

simulators/
  docker-compose.yml     # local stack: device_agent + this app (+ optional sample simulator)
  app_config.json        # sample deployment config
  sample/                # standalone simulator emitting random tag_values updates
    main.py              # SampleSimulator using doover-2 Tags API

tests/
  test_imports.py        # import + config schema sanity
  test_converter.py      # converter wiring across separate_levels values

doover_config.json       # generated from app_config.py via `uv run export-config`
Dockerfile               # multi-stage build on spaneng/doover_device_base
.github/workflows/       # CI: build-image (main), lint-and-test (PRs)
```

## How the bridge works

1. `FoxgloveIfaceApplication.setup()` reads config and constructs a `FoxgloveConverter`, passing the device agent so it can subscribe and write back.
2. The converter calls `device_agent.add_event_callback(channel, handler, EventSubscription.aggregate_update)` for each subscribed channel.
3. On every aggregate update, `handle_values` walks the payload up to `separate_levels` deep, then for each leaf:
   - Computes a schema fingerprint; if the shape changed (or it's new) it (re)creates a `foxglove.Channel` with a freshly-derived JSON schema.
   - Logs the value to that Foxglove channel.
   - Mirrors every primitive value into a Foxglove **parameter** via `FoxgloveParameterManager`.
4. Periodically (every `parameter_publish_interval` seconds) the parameter list is republished to connected clients.
5. When a client edits a parameter, `update_value_from_parameter` reconstructs the nested dict and calls `device_agent.update_channel_aggregate` to persist the change back to Doover.

Schemas always coerce booleans and integers to `number` (Foxglove plot panels reject non-numeric series).

## Local development

The pydoover dependency is the published PyPI release; no git checkout needed.

```bash
# install everything (including the dev group)
uv sync

# run the test suite
uv run pytest tests -v

# regenerate doover_config.json after editing app_config.py
uv run export-config

# run the full simulator stack (device_agent + sample simulator + this app)
doover app run
```

Once `doover app run` is up, point Foxglove Studio at `ws://localhost:8765` (see README).

## Editing config

Add or change fields in `src/foxglove_iface/app_config.py` as class-level attributes on `FoxgloveIfaceConfig`. After editing:

```bash
uv run export-config
```

This regenerates the `config_schema` block inside `doover_config.json`. Commit both files.

### No UI export

This app has no `app_ui.py`. `doover_config.json` carries `"export_ui_command": "NO_EXPORT"` so that `doover app publish` (which otherwise runs `uv run export-ui`) skips the UI export step. If a UI is ever added, remove that field and add an `export-ui` script in `pyproject.toml`.

### Config values

When you reference config values in `application.py`, remember:

- Scalars: `self.config.host.value`, `self.config.port.value`
- Arrays: iterate `self.config.channels.elements` and read `.value` on each
- Cast integers loaded from JSON with `int(...)` if you pass them to APIs that strictly require `int`

## Updating the simulator

`simulators/sample/main.py` is on the doover-2 declarative API:

- `tags_cls = SampleSimulatorTags` declares the tags
- `setup()` and `main_loop()` are async
- Set tags with `await self.tags.<name>.set(value)`

Add new tags by extending `SampleSimulatorTags` and emitting them from `main_loop`.

## CI

- **Pull requests** trigger `lint-and-test.yml` (ruff lint/format + pytest).
- **Push to main** triggers `build-image.yml` which lints, tests, then builds and pushes the image to `ghcr.io/getdoover/foxglove-iface:main` for `linux/amd64` and `linux/arm64`.

## Publishing

```bash
# refresh metadata
uv run export-config

# publish the app config to Doover
doover app publish --profile dv2
```
