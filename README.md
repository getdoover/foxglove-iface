# Foxglove Interface

<img src="https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png" alt="Doover Logo" style="max-width: 300px;">

**Bridge Doover channel data to [Foxglove Studio](https://foxglove.dev) for live visualisation, debugging, and bidirectional editing of values.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/getdoover/foxglove-iface)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/getdoover/foxglove-iface/blob/main/LICENSE)

[Configuration](#configuration) · [Connecting Foxglove Studio](#connecting-foxglove-studio) · [Developer](DEVELOPMENT.md) · [Need Help?](#need-help)

## Overview

This device app runs a [Foxglove WebSocket server](https://docs.foxglove.dev/docs/connecting-to-data/frameworks/custom#foxglove-websocket) on the Doover device. It subscribes to one or more Doover channels (defaults: `tag_values` and `ui_cmds`), watches their aggregate updates, and republishes the values as Foxglove topics. JSON schemas are derived automatically from the first observed payload and are re-derived if the shape of the data changes.

It also exposes every primitive value as a Foxglove **parameter**, so you can edit values live from Foxglove Studio and the change is written back to the source Doover channel.

## Features

- Auto-discovers Foxglove topics and JSON schemas from the data flowing through subscribed channels
- Re-derives schemas on shape change (no restart required)
- Bidirectional: edits to Foxglove parameters propagate back to Doover via `update_channel_aggregate`
- Configurable host, port, channel list, topic-splitting depth, and parameter publish interval
- All booleans/integers in derived schemas are normalised to numbers so Foxglove plot panels accept them

## Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `host` | string | `0.0.0.0` | Interface the websocket server binds to |
| `port` | integer | `8765` | Port the websocket server listens on |
| `channels` | array&lt;string&gt; | `["tag_values", "ui_cmds"]` | Doover channels to subscribe to |
| `separate_levels` | integer | `1` | Depth at which nested data is split into separate Foxglove topics. `1` means each top-level key becomes its own topic |
| `parameter_publish_interval` | number | `6.0` | Seconds between parameter republishes to connected clients |

## Connecting Foxglove Studio

1. Open [Foxglove Studio](https://app.foxglove.dev/) (web or desktop).
2. **Open connection** → **Foxglove WebSocket**.
3. Enter `ws://<device-ip>:8765` (or whatever you set `port` to).
4. Topics derived from the subscribed channels appear in the topic browser (see [Topic structure](#topic-structure) below).
5. To edit values live, open the **Parameters** panel — primitive values from the data appear as editable parameters; setting them writes back to the source Doover channel via a deep-merge update (sibling keys are preserved).

### Topic structure

How channel data maps to Foxglove topics depends on `separate_levels` (default `1`) and the shape of the channel aggregate.

For the `tag_values` channel under doover-2, every app on the device writes its tags namespaced under its own app key, so the aggregate looks like:

```json
{
  "<app_key_1>": { "tag_a": 1, "tag_b": 2 },
  "<app_key_2>": { "tag_c": 3 }
}
```

With the default `separate_levels=1`, you get **one Foxglove topic per app**, each carrying that app's tag dict as its message payload:

- `/tag_values/<app_key_1>` → `{ "tag_a": 1, "tag_b": 2 }`
- `/tag_values/<app_key_2>` → `{ "tag_c": 3 }`

Foxglove panels can plot or display fields within a topic (e.g. plot path `/tag_values/<app_key_1>.tag_a`). If you'd rather have one topic per individual tag, set `separate_levels` to `2` in your deployment config — the bridge will split one level deeper across every subscribed channel.

## Integrations

Standalone — no dependencies on other Doover apps. Subscribes to whatever channels exist on the device.

## Need Help?

- Email: support@doover.com
- [Community Forum](https://doover.com/community)
- [Full Documentation](https://docs.doover.com)
- [Developer Documentation](DEVELOPMENT.md)

## Version History

### v1.0.0

- Initial release; doover-2 declarative API; configurable server host, port, channels, depth, and publish interval; Foxglove parameter write-back to channels.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
