# LiveKit Server Setup & Compatibility

## Local Development

The project includes a pre-configured local LiveKit Server running via Docker Compose.

### Starting the Server

```bash
docker compose up -d livekit
```

This starts:

- LiveKit Server (Port 7880, 7881)
- Redis (Port 6380) - Used by LiveKit for room storage

### Configuration

The server is configured in `docker/livekit.yaml`.

- **API Key:** `devkey`
- **API Secret:** `devsecret`
- **Webhooks:** Sent to `http://host.docker.internal:8000/api/webhooks/livekit`

## Compatibility Matrix

| Component         | Package                   | Version                |
| ----------------- | ------------------------- | ---------------------- |
| LiveKit Server    | `livekit/livekit-server`  | `v1.9.0`               |
| Backend SDK       | `livekit-api` (Python)    | `^1.1.0`               |
| Agent Runtime SDK | `livekit-agents` (Python) | `*` (latest)           |
| Frontend SDK      | `livekit-client` (JS)     | `^2.0.0` (Recommended) |

## LiveKit Cloud vs Self-Hosted

For production, we recommend evaluating LiveKit Cloud to avoid managing scaling, TURN servers, and global distribution. However, self-hosted is fully supported for:

- Development
- Testing
- Low-scale deployments

## Troubleshooting

### Container not starting (Port conflict)

Check if port 7880 or 7881 is in use:

```bash
lsof -i :7880
```

### Authentication Failed

Ensure your `.env` file matches the `docker/livekit.yaml` keys:

- `LIVEKIT_API_KEY=devkey`
- `LIVEKIT_API_SECRET=devsecret`

### Webhook failures

On Linux, ensure `host.docker.internal` is resolving. We use `extra_hosts: host-gateway` in `docker-compose.yml` to support this.
