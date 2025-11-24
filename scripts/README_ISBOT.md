# IntellectScout Trading Bot Management Script

The `isbot` command provides an easy way to manage both the backend and frontend servers.

## Quick Setup

Run the setup script to add the alias to your shell:

```bash
./scripts/setup_alias.sh
```

Then reload your shell configuration:

```bash
# For zsh
source ~/.zshrc

# For bash
source ~/.bashrc
```

Or simply open a new terminal window.

## Manual Setup

If you prefer to set up the alias manually, add this line to your `~/.zshrc` or `~/.bashrc`:

```bash
alias isbot='/path/to/trading_bot/scripts/isbot.sh'
```

Replace `/path/to/trading_bot` with the actual path to your project.

## Usage

### Start Services
```bash
isbot start
```
Starts both backend (Flask on port 5002) and frontend (Vite on port 5173).

### Stop Services
```bash
isbot stop
```
Stops both backend and frontend servers gracefully.

### Restart Services
```bash
isbot restart
```
Stops and then starts both services.

### Check Status
```bash
isbot status
# or
isbot st
```
Shows the current status of both servers, including PIDs and URLs.

### View Logs
```bash
isbot logs              # Show logs from both services
isbot logs backend      # Show only backend logs
isbot logs frontend     # Show only frontend logs
```

### Get Help
```bash
isbot help
```

## Features

- **Process Management**: Tracks running processes using PID files
- **Graceful Shutdown**: Attempts graceful shutdown before force killing
- **Log Files**: Logs are saved to `backend.log` and `frontend.log` in the project root
- **Status Checking**: Verifies if processes are actually running
- **Port Checking**: Warns if ports are already in use
- **Color Output**: Color-coded status messages for easy reading

## Log Files

- Backend logs: `backend.log` (in project root)
- Frontend logs: `frontend.log` (in project root)

## Troubleshooting

### Port Already in Use
If you see a message that a port is in use, you can:
1. Stop the service: `isbot stop`
2. Find and kill the process manually: `lsof -ti:5002 | xargs kill` (for backend)
3. Or change the port in the script or configuration

### Process Not Stopping
If a process doesn't stop gracefully:
1. The script will automatically force kill after 5 seconds
2. You can manually kill: `kill -9 <PID>`
3. Or remove the PID file: `rm .backend.pid` or `rm .frontend.pid`

### Virtual Environment Not Found
The script automatically detects and activates:
- `venv/` directory
- `venv310/` directory

If you use a different virtual environment name, edit the `start_backend()` function in `scripts/isbot.sh`.
