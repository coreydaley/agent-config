---
name: orbstack
description: "Manage OrbStack — a macOS Docker Desktop replacement and Linux VM manager. Use when working with OrbStack Linux machines (create, start, stop, delete, shell access, file transfer), Docker containers and images via the docker CLI (OrbStack provides a full Docker-compatible alias), Docker Compose, Kubernetes (OrbStack's built-in k8s), or OrbStack configuration. Triggers on orbstack, orb, orbctl, OrbStack machine/VM management, or any Docker/Kubernetes task on a system where OrbStack is the container runtime."
---

# OrbStack

OrbStack is a fast, lightweight Docker Desktop replacement for macOS. It provides:
- **Docker engine** — full `docker` CLI compatibility (OrbStack IS the Docker runtime)
- **Linux machines** — lightweight ARM/AMD64 VMs managed via `orb`/`orbctl`
- **Kubernetes** — built-in single-node k8s cluster

## CLI Tools

| Command | Purpose |
|---------|---------|
| `docker` | All container/image/compose/buildx operations — use this for everything Docker |
| `orb` | Shell into the default Linux machine OR run a command on Linux |
| `orbctl` | Manage OrbStack itself: machines, config, status, k8s |

`orb` and `orbctl` are aliases for the same binary.

## Docker (Containers & Images)

OrbStack registers itself as the `orbstack` Docker context. Use `docker` exactly as you would with Docker Desktop — all subcommands work identically.

```bash
# Containers
docker ps -a
docker run -it --rm ubuntu bash
docker exec -it <container> bash
docker logs -f <container>
docker stop <container> && docker rm <container>

# Images
docker images
docker pull <image>
docker build -t <tag> .
docker rmi <image>

# Compose
docker compose up -d
docker compose down
docker compose logs -f

# System
docker system df
docker system prune -f
```

## Linux Machines

```bash
# List machines
orbctl list

# Create (distros: ubuntu, debian, fedora, alpine, arch, and more)
orbctl create ubuntu                        # latest ubuntu, default name
orbctl create ubuntu:22.04 myvm             # specific version + name
orbctl create -a amd64 fedora              # explicit architecture

# Shell access
orb                                         # shell into default machine
orb -m <name>                               # shell into named machine
orb -m <name> -u root                       # as root

# Run a command on Linux without entering a shell
orb uname -a
orb -m <name> cat /etc/os-release

# Lifecycle
orbctl start <name>
orbctl stop <name>
orbctl restart <name>
orbctl delete <name>

# File transfer
orbctl push ./local/path /remote/path       # macOS → Linux
orbctl pull /remote/path ./local/path       # Linux → macOS

# Info
orbctl info <name>
orbctl status
```

## Kubernetes

OrbStack includes a built-in single-node Kubernetes cluster. Enable it via config or the UI.

```bash
# Show k8s instructions and kubeconfig details
orbctl k8s

# Enable/disable
orbctl config set k8s.enable true
orbctl config set k8s.enable false

# Use kubectl as normal once enabled — kubeconfig is set automatically
kubectl get nodes
kubectl get pods -A
```

## Configuration

```bash
orbctl config show                          # all settings
orbctl config get <key>                     # single value
orbctl config set <key> <value>             # update setting

# Common settings
orbctl config set k8s.enable true
orbctl config set docker.set_context true   # auto-set docker context
orbctl config set memory_mib 8192
orbctl config set cpu 12
```

## OrbStack Lifecycle

```bash
orbctl start        # start OrbStack
orbctl stop         # stop OrbStack (stops all machines and Docker)
orbctl status       # check if running
orbctl version      # show version
orbctl doctor       # diagnose issues
orbctl update       # update OrbStack
```

## Docker Extension Commands

```bash
# Migrate from Docker Desktop
orbctl docker migrate

# Volume management extensions
orbctl docker volume --help
```

## Key Behaviors

- **Docker context**: OrbStack auto-sets the `orbstack` Docker context. If `docker` commands go to the wrong engine, run `docker context use orbstack`.
- **Networking**: Containers and Linux machines are on the same subnet (`192.168.138.0/23` by default). Containers can reach macOS at `host.internal`.
- **Ports**: By default, container ports bound to `localhost` are accessible from macOS directly. LAN exposure is configurable.
- **Rosetta**: AMD64 images run on Apple Silicon via Rosetta 2 (enabled by default).
- **No `sudo` needed**: OrbStack manages its own privileged helper; `docker` and `orbctl` commands run as your macOS user.
