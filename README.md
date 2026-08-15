# Zyxel NR5103E 5G Model Connectivity Monitor

A small FastAPI service, packaged as a Docker container, that watches your internet
connectivity and automatically reboots a Zyxel NR5103E 5G hotspot/router when it
gets stuck.

> [!TIP]
>
> **Is this AI?**
>
> This README is written by Claude, but nothing else in the repo is. I wrote this on an edge
> node that has a slim distro without DE, and I couldn't be bothered setting up Claude or
> anything.
>
> This README was written afterwards.


## Why this exists

5G hotspots like the NR5103E can silently lose their cellular connection — the
Wi-Fi/LAN side stays up, so nothing tells you the link to the internet is dead
until you notice it yourself. This container runs unattended alongside the
router and:

- Continuously pings a set of public IP addresses to measure real internet
  reachability (not just "is the router up").
- Tracks the recent success rate of those pings.
- If the success rate drops below a threshold for long enough, logs into the
  NR5103E's web admin interface and issues a reboot of the cellular module —
  the same recovery step you'd do by hand if you noticed the outage.
- Exposes a small HTTP API so you can check current health, ping ad-hoc
  hosts, inspect the modem's cellular status, or trigger a reboot manually.

It's meant to run as a "set and forget" watchdog on a home network / lab
where the NR5103E is the sole path to the internet.

Since most carriers put 5G connections behind CGNAT, you typically can't
reach anything on this network from the outside (e.g. to hit this service's
API remotely, or SSH into the host). This container is commonly run
alongside [Tailscale](https://tailscale.com/) on the same host so you get a
stable, routable address into the network regardless of CGNAT — useful for
checking `/health` or triggering `/modem/reboot` while away from home.

## How it works

- On startup, the service launches two background loops:
  - A **ping loop** that pings `PING_TARGETS` on a fixed interval and keeps a
    rolling history of results per host.
  - A **monitor loop** that periodically checks the ping success rate for the
    monitored hosts and, if connectivity looks dead, logs into the NR5103E
    and reboots it.
- A FastAPI app exposes the current state and lets you interact with the
  device directly (see [API](#api) below).
- The container uses `network_mode: host` in `docker-compose.yml` so pings
  reflect the host's actual network path, and so it can reach the router on
  its LAN address.

## Usage

1. Copy the environment template and fill in your router credentials:

   ```bash
   cp .env.example .env
   ```

2. Build and start the container:

   ```bash
   docker compose up -d --build
   ```

3. Check that it's healthy:

   ```bash
   curl http://localhost:16080/health
   ```

> [!NOTE]
> `docker-compose.yml` mounts `./logs:/app/logs`, but the app
> currently only logs to stderr (visible via `docker compose logs`) — nothing
> is written to `/app/logs` yet, so this mount is a no-op for now.

## Environment variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `MODE` | No | `release` | Build mode for the Docker image. `release` runs the app with `uvicorn`; `dev` runs `fastapi dev` with autoreload. |
| `NR5103E_HOST` | No | `192.168.1.1` | LAN IP address of the NR5103E's admin interface. |
| `NR5103E_USERNAME` | No | `admin` | Admin username for the NR5103E web UI. |
| `NR5103E_PASSWORD` | **Yes** | *(empty)* | Admin password for the NR5103E web UI. The service can't log in without this. |
| `PING_TARGETS` | No | `1.1.1.1,8.8.8.8` | Comma-separated list of IPs to ping for connectivity checks. |
| `PING_INTERVAL` | No | `60` | Seconds between ping attempts per target. |
| `PING_TIMEOUT` | No | `15` | Timeout in seconds for each ping attempt. |
| `PING_SOURCE` | No | *(unset)* | Source IP to ping from, if you want to pin checks to a specific interface. Leave unset to let the OS choose. |
| `MONITORED_IPS` | No | `1.1.1.1,8.8.8.8` | Comma-separated subset of `PING_TARGETS` that the reboot decision is based on. Must be a subset of `PING_TARGETS` — the service aborts on startup if it isn't. |
| `MONITORING_INTERVAL` | No | `150` | Seconds between cellular-health checks (the loop that decides whether to reboot). |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Overall health status plus recent ping history for the monitored hosts. |
| `GET` | `/ping/{host}` | On-demand ping of an arbitrary IP address. |
| `GET` | `/modem/cellular` | Current cellular status reported by the NR5103E. |
| `GET` | `/modem/session` | Current login session state for the NR5103E. |
| `POST` | `/modem/reboot` | Manually trigger a reboot of the NR5103E's cellular module. |

Interactive API docs are available at `/docs` while the container is running.

## Security notes

- The NR5103E uses a self-signed TLS certificate, so certificate verification
  is disabled when the service talks to it. Only point `NR5103E_HOST` at a
  device on your trusted LAN.
- `NR5103E_PASSWORD` is your router's admin password — keep `.env` out of
  version control (it's already gitignored) and don't expose this service's
  port to an untrusted network, since `/modem/reboot` requires no
  authentication of its own.
