#!/bin/bash

# IntellectScout Trading Bot Management Script
# Usage: isbot [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PID files
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

# Default Ports
DEFAULT_BACKEND_PORT=5002
DEFAULT_FRONTEND_PORT=5173

# Actual ports (may be different if defaults are busy)
BACKEND_PORT=$DEFAULT_BACKEND_PORT
FRONTEND_PORT=$DEFAULT_FRONTEND_PORT

# Port configuration files
BACKEND_PORT_FILE="$PROJECT_ROOT/.backend.port"
FRONTEND_PORT_FILE="$PROJECT_ROOT/.frontend.port"

# Check if port is in use
is_port_in_use() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Find available port starting from a given port
find_available_port() {
    local start_port=$1
    local port=$start_port
    local max_attempts=100
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if ! is_port_in_use "$port"; then
            echo "$port"
            return 0
        fi
        port=$((port + 1))
        attempt=$((attempt + 1))
    done

    echo ""
    return 1
}

# Load saved ports or find available ones
load_ports() {
    # Load backend port
    if [ -f "$BACKEND_PORT_FILE" ]; then
        BACKEND_PORT=$(cat "$BACKEND_PORT_FILE")
    else
        if is_port_in_use "$DEFAULT_BACKEND_PORT"; then
            echo -e "${YELLOW}Default backend port $DEFAULT_BACKEND_PORT is in use, finding alternative...${NC}"
            local alt_port=$(find_available_port $DEFAULT_BACKEND_PORT)
            if [ -n "$alt_port" ]; then
                BACKEND_PORT=$alt_port
                echo "$BACKEND_PORT" > "$BACKEND_PORT_FILE"
                echo -e "${GREEN}Using backend port: $BACKEND_PORT${NC}"
            else
                echo -e "${RED}Could not find available port for backend${NC}"
                return 1
            fi
        else
            echo "$DEFAULT_BACKEND_PORT" > "$BACKEND_PORT_FILE"
        fi
    fi

    # Load frontend port
    if [ -f "$FRONTEND_PORT_FILE" ]; then
        FRONTEND_PORT=$(cat "$FRONTEND_PORT_FILE")
    else
        if is_port_in_use "$DEFAULT_FRONTEND_PORT"; then
            echo -e "${YELLOW}Default frontend port $DEFAULT_FRONTEND_PORT is in use, finding alternative...${NC}"
            local alt_port=$(find_available_port $DEFAULT_FRONTEND_PORT)
            if [ -n "$alt_port" ]; then
                FRONTEND_PORT=$alt_port
                echo "$FRONTEND_PORT" > "$FRONTEND_PORT_FILE"
                echo -e "${GREEN}Using frontend port: $FRONTEND_PORT${NC}"
            else
                echo -e "${RED}Could not find available port for frontend${NC}"
                return 1
            fi
        else
            echo "$DEFAULT_FRONTEND_PORT" > "$FRONTEND_PORT_FILE"
        fi
    fi

    return 0
}

# Check if process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Get process info
get_process_info() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "$pid"
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Start backend
start_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        local existing_pid=$(cat "$BACKEND_PID_FILE")
        echo -e "${YELLOW}⚠️  Backend is already running (PID: $existing_pid)${NC}"
        return 1
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🚀 Starting Backend Server${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Load or find available port
    echo -e "${BLUE}📡 Checking port availability...${NC}"
    if ! load_ports; then
        echo -e "${RED}❌ Failed to find available port for backend${NC}"
        return 1
    fi

    if [ "$BACKEND_PORT" != "$DEFAULT_BACKEND_PORT" ]; then
        echo -e "${YELLOW}   ℹ️  Default port $DEFAULT_BACKEND_PORT is busy, using port $BACKEND_PORT${NC}"
    else
        echo -e "${GREEN}   ✓ Port $BACKEND_PORT is available${NC}"
    fi

    cd "$BACKEND_DIR"

    # Activate virtual environment if it exists
    echo -e "${BLUE}🐍 Activating Python environment...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}   ✓ Virtual environment activated (venv)${NC}"
    elif [ -d "venv310" ]; then
        source venv310/bin/activate
        echo -e "${GREEN}   ✓ Virtual environment activated (venv310)${NC}"
    else
        echo -e "${YELLOW}   ⚠️  No virtual environment found, using system Python${NC}"
    fi

    # Set port as environment variable for Flask
    export FLASK_RUN_PORT=$BACKEND_PORT

    # Start Flask app in background
    echo -e "${BLUE}⚙️  Launching Flask application...${NC}"
    nohup python run.py > "$PROJECT_ROOT/backend.log" 2>&1 &
    local backend_pid=$!
    echo $backend_pid > "$BACKEND_PID_FILE"

    # Wait and check if it started successfully with progress indicator
    echo -e "${BLUE}⏳ Waiting for backend to initialize...${NC}"
    local max_wait=15
    local waited=0
    local i=0
    while [ $i -lt $max_wait ]; do
        # First check if process is still running
        if ! ps -p "$backend_pid" > /dev/null 2>&1; then
            break
        fi

        # Check if port is listening (this means Flask has bound to the port)
        if is_port_in_use "$BACKEND_PORT"; then
            # Give it one more second to fully initialize
            sleep 1
            echo ""
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}✅ Backend started successfully!${NC}"
            echo -e "${GREEN}   PID: $backend_pid${NC}"
            echo -e "${GREEN}   Port: $BACKEND_PORT${NC}"
            echo -e "${GREEN}   URL: http://localhost:$BACKEND_PORT${NC}"
            echo -e "${BLUE}   Logs: $PROJECT_ROOT/backend.log${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            return 0
        fi

        sleep 0.5
        echo -n "."
        i=$((i + 1))
    done
    echo ""

    rm -f "$BACKEND_PID_FILE"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo -e "${RED}   Check logs: $PROJECT_ROOT/backend.log${NC}"
    if [ -f "$PROJECT_ROOT/backend.log" ]; then
        echo -e "${YELLOW}   Last 10 lines of log:${NC}"
        tail -n 10 "$PROJECT_ROOT/backend.log" | sed 's/^/   /'
    fi
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    return 1
}

# Start frontend
start_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        local existing_pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "${YELLOW}⚠️  Frontend is already running (PID: $existing_pid)${NC}"
        return 1
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🚀 Starting Frontend Server${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Load or find available port
    echo -e "${BLUE}📡 Checking port availability...${NC}"
    if ! load_ports; then
        echo -e "${RED}❌ Failed to find available port for frontend${NC}"
        return 1
    fi

    if [ "$FRONTEND_PORT" != "$DEFAULT_FRONTEND_PORT" ]; then
        echo -e "${YELLOW}   ℹ️  Default port $DEFAULT_FRONTEND_PORT is busy, using port $FRONTEND_PORT${NC}"
    else
        echo -e "${GREEN}   ✓ Port $FRONTEND_PORT is available${NC}"
    fi

    cd "$FRONTEND_DIR"

    # Check if node_modules exists
    echo -e "${BLUE}📦 Checking dependencies...${NC}"
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   ⚠️  node_modules not found, installing dependencies...${NC}"
        npm install
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}   ✓ Dependencies installed${NC}"
        else
            echo -e "${RED}   ❌ Failed to install dependencies${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}   ✓ Dependencies found${NC}"
    fi

    # Set port environment variables
    export VITE_PORT=$FRONTEND_PORT
    export PORT=$FRONTEND_PORT

    # Start Vite dev server in background with port flag
    echo -e "${BLUE}⚙️  Launching Vite development server...${NC}"
    nohup npm run dev -- --port $FRONTEND_PORT > "$PROJECT_ROOT/frontend.log" 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > "$FRONTEND_PID_FILE"

    # Wait and check if it started successfully with progress indicator
    echo -e "${BLUE}⏳ Waiting for frontend to initialize...${NC}"
    local max_wait=20
    local i=0
    while [ $i -lt $max_wait ]; do
        # First check if process is still running
        if ! ps -p "$frontend_pid" > /dev/null 2>&1; then
            break
        fi

        # Check if port is listening (this means Vite has bound to the port)
        if is_port_in_use "$FRONTEND_PORT"; then
            # Give it a moment to fully initialize
            sleep 1
            echo ""
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}✅ Frontend started successfully!${NC}"
            echo -e "${GREEN}   PID: $frontend_pid${NC}"
            echo -e "${GREEN}   Port: $FRONTEND_PORT${NC}"
            echo -e "${GREEN}   URL: http://localhost:$FRONTEND_PORT${NC}"
            echo -e "${BLUE}   Logs: $PROJECT_ROOT/frontend.log${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            return 0
        fi

        sleep 0.5
        echo -n "."
        i=$((i + 1))
    done
    echo ""

    rm -f "$FRONTEND_PID_FILE"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Frontend failed to start${NC}"
    echo -e "${RED}   Check logs: $PROJECT_ROOT/frontend.log${NC}"
    if [ -f "$PROJECT_ROOT/frontend.log" ]; then
        echo -e "${YELLOW}   Last 10 lines of log:${NC}"
        tail -n 10 "$PROJECT_ROOT/frontend.log" | sed 's/^/   /'
    fi
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    return 1
}

# Stop backend
stop_backend() {
    if ! is_running "$BACKEND_PID_FILE"; then
        echo -e "${YELLOW}⚠️  Backend is not running${NC}"
        return 1
    fi

    local pid=$(cat "$BACKEND_PID_FILE")
    echo -e "${BLUE}🛑 Stopping backend server (PID: $pid)...${NC}"

    # Try graceful shutdown first
    kill "$pid" 2>/dev/null

    # Wait up to 5 seconds for graceful shutdown with progress
    for i in {1..5}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$BACKEND_PID_FILE"
            echo -e "${GREEN}   ✓ Backend stopped gracefully${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}   ⚠️  Process still running, force killing...${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    rm -f "$BACKEND_PID_FILE"
    echo -e "${GREEN}   ✓ Backend stopped${NC}"
    return 0
}

# Stop frontend
stop_frontend() {
    if ! is_running "$FRONTEND_PID_FILE"; then
        echo -e "${YELLOW}⚠️  Frontend is not running${NC}"
        return 1
    fi

    local pid=$(cat "$FRONTEND_PID_FILE")
    echo -e "${BLUE}🛑 Stopping frontend server (PID: $pid)...${NC}"

    # Try graceful shutdown first
    kill "$pid" 2>/dev/null

    # Wait up to 5 seconds for graceful shutdown with progress
    for i in {1..5}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$FRONTEND_PID_FILE"
            echo -e "${GREEN}   ✓ Frontend stopped gracefully${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}   ⚠️  Process still running, force killing...${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    rm -f "$FRONTEND_PID_FILE"
    echo -e "${GREEN}   ✓ Frontend stopped${NC}"
    return 0
}

# Show status
show_status() {
    # Load saved ports
    if [ -f "$BACKEND_PORT_FILE" ]; then
        BACKEND_PORT=$(cat "$BACKEND_PORT_FILE")
    else
        BACKEND_PORT=$DEFAULT_BACKEND_PORT
    fi
    if [ -f "$FRONTEND_PORT_FILE" ]; then
        FRONTEND_PORT=$(cat "$FRONTEND_PORT_FILE")
    else
        FRONTEND_PORT=$DEFAULT_FRONTEND_PORT
    fi

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   IntellectScout Trading Bot - Service Status             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Backend status
    echo -e "${BLUE}Backend Server:${NC}"
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        echo -e "  ${GREEN}● Status:${NC} Running"
        echo -e "  ${GREEN}● PID:${NC}    $backend_pid"
        echo -e "  ${GREEN}● Port:${NC}   $BACKEND_PORT"
        echo -e "  ${GREEN}● URL:${NC}    http://localhost:$BACKEND_PORT"
        if [ "$BACKEND_PORT" != "$DEFAULT_BACKEND_PORT" ]; then
            echo -e "  ${YELLOW}● Note:${NC}   Using alternative port (default $DEFAULT_BACKEND_PORT was busy)"
        fi
    else
        # Check if port is actually in use (backend might be running without PID file)
        if is_port_in_use "$BACKEND_PORT"; then
            local port_pid=$(lsof -ti:$BACKEND_PORT | head -1)
            if [ -n "$port_pid" ] && ps -p "$port_pid" > /dev/null 2>&1; then
                # Backend is running but PID file is missing - recreate it
                echo "$port_pid" > "$BACKEND_PID_FILE"
                echo -e "  ${GREEN}● Status:${NC} Running (detected on port, PID file restored)"
                echo -e "  ${GREEN}● PID:${NC}    $port_pid"
                echo -e "  ${GREEN}● Port:${NC}   $BACKEND_PORT"
                echo -e "  ${GREEN}● URL:${NC}    http://localhost:$BACKEND_PORT"
            else
                echo -e "  ${RED}● Status:${NC} Not running"
                echo -e "  ${BLUE}● Port:${NC}   $BACKEND_PORT (default: $DEFAULT_BACKEND_PORT)"
                echo -e "  ${YELLOW}● Note:${NC}   Port $BACKEND_PORT is in use by another process"
            fi
        else
            echo -e "  ${RED}● Status:${NC} Not running"
            echo -e "  ${BLUE}● Port:${NC}   $BACKEND_PORT (default: $DEFAULT_BACKEND_PORT)"
        fi
    fi

    echo ""

    # Frontend status
    echo -e "${BLUE}Frontend Server:${NC}"
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "  ${GREEN}● Status:${NC} Running"
        echo -e "  ${GREEN}● PID:${NC}    $frontend_pid"
        echo -e "  ${GREEN}● Port:${NC}   $FRONTEND_PORT"
        echo -e "  ${GREEN}● URL:${NC}    http://localhost:$FRONTEND_PORT"
        if [ "$FRONTEND_PORT" != "$DEFAULT_FRONTEND_PORT" ]; then
            echo -e "  ${YELLOW}● Note:${NC}   Using alternative port (default $DEFAULT_FRONTEND_PORT was busy)"
        fi
    else
        echo -e "  ${RED}● Status:${NC} Not running"
        echo -e "  ${BLUE}● Port:${NC}   $FRONTEND_PORT (default: $DEFAULT_FRONTEND_PORT)"
        if is_port_in_use "$DEFAULT_FRONTEND_PORT"; then
            echo -e "  ${YELLOW}● Note:${NC}   Default port $DEFAULT_FRONTEND_PORT is in use"
        fi
    fi

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Show logs
show_logs() {
    local service=${1:-"both"}

    case "$service" in
        backend|b)
            if [ -f "$PROJECT_ROOT/backend.log" ]; then
                tail -f "$PROJECT_ROOT/backend.log"
            else
                echo -e "${RED}Backend log file not found${NC}"
            fi
            ;;
        frontend|f)
            if [ -f "$PROJECT_ROOT/frontend.log" ]; then
                tail -f "$PROJECT_ROOT/frontend.log"
            else
                echo -e "${RED}Frontend log file not found${NC}"
            fi
            ;;
        both|all|*)
            echo -e "${BLUE}Showing logs for both services (Ctrl+C to exit)${NC}"
            if [ -f "$PROJECT_ROOT/backend.log" ] && [ -f "$PROJECT_ROOT/frontend.log" ]; then
                tail -f "$PROJECT_ROOT/backend.log" "$PROJECT_ROOT/frontend.log"
            else
                echo -e "${RED}Log files not found${NC}"
            fi
            ;;
    esac
}

# Main command handler
case "${1:-}" in
    start)
        echo ""
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   IntellectScout Trading Bot - Starting Services          ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        backend_started=0
        frontend_started=0

        if start_backend; then
            backend_started=1
        fi
        echo ""
        if start_frontend; then
            frontend_started=1
        fi
        echo ""

        # Summary
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   Startup Summary                                          ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        if [ "$backend_started" = "1" ]; then
            echo -e "${GREEN}✅ Backend:  Running on http://localhost:$BACKEND_PORT${NC}"
        else
            echo -e "${RED}❌ Backend:  Failed to start${NC}"
        fi

        if [ "$frontend_started" = "1" ]; then
            echo -e "${GREEN}✅ Frontend: Running on http://localhost:$FRONTEND_PORT${NC}"
        else
            echo -e "${RED}❌ Frontend: Failed to start${NC}"
        fi
        echo ""

        if [ "$backend_started" = "1" ] && [ "$frontend_started" = "1" ]; then
            echo -e "${GREEN}🎉 All services started successfully!${NC}"
            echo ""
            echo -e "${BLUE}Quick Links:${NC}"
            echo -e "  Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
            echo -e "  Backend:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
            echo ""
        fi
        ;;
    stop)
        echo ""
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   IntellectScout Trading Bot - Stopping Services          ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        stop_backend
        echo ""
        stop_frontend
        echo ""
        echo -e "${GREEN}✓ All services stopped${NC}"
        echo ""
        ;;
    restart)
        echo ""
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   IntellectScout Trading Bot - Restarting Services        ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        echo -e "${YELLOW}🛑 Stopping existing services...${NC}"
        stop_backend
        echo ""
        stop_frontend
        echo ""

        echo -e "${BLUE}⏳ Waiting 2 seconds before restart...${NC}"
        sleep 2
        echo ""

        backend_started=0
        frontend_started=0

        if start_backend; then
            backend_started=1
        fi
        echo ""
        if start_frontend; then
            frontend_started=1
        fi
        echo ""

        # Summary
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   Restart Summary                                          ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        if [ "$backend_started" = "1" ]; then
            echo -e "${GREEN}✅ Backend:  Running on http://localhost:$BACKEND_PORT${NC}"
        else
            echo -e "${RED}❌ Backend:  Failed to start${NC}"
        fi

        if [ "$frontend_started" = "1" ]; then
            echo -e "${GREEN}✅ Frontend: Running on http://localhost:$FRONTEND_PORT${NC}"
        else
            echo -e "${RED}❌ Frontend: Failed to start${NC}"
        fi
        echo ""

        if [ "$backend_started" = "1" ] && [ "$frontend_started" = "1" ]; then
            echo -e "${GREEN}🎉 All services restarted successfully!${NC}"
            echo ""
            echo -e "${BLUE}Quick Links:${NC}"
            echo -e "  Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
            echo -e "  Backend:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
            echo ""
        fi
        ;;
    status|st)
        show_status
        ;;
    logs)
        show_logs "${2:-both}"
        ;;
    reset-ports)
        echo -e "${BLUE}Resetting port configuration...${NC}"
        rm -f "$BACKEND_PORT_FILE" "$FRONTEND_PORT_FILE"
        echo -e "${GREEN}Port configuration reset. Next start will use default ports or find alternatives.${NC}"
        ;;
    migrate)
        echo ""
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║   Running Database Migration                             ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        cd "$BACKEND_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d "venv310" ]; then
            source venv310/bin/activate
        fi
        python scripts/migrate_db.py
        ;;
    reset-db)
        echo ""
        echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║   WARNING: Database Reset                                 ║${NC}"
        echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${RED}This will DELETE ALL DATA from the database!${NC}"
        echo -e "${YELLOW}All users, credentials, and trading data will be lost.${NC}"
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo -e "${GREEN}Database reset cancelled.${NC}"
            exit 0
        fi
        echo ""
        echo -e "${BLUE}Resetting database...${NC}"
        cd "$BACKEND_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d "venv310" ]; then
            source venv310/bin/activate
        fi

        # Run reset script (it handles everything through migrations)
        # Note: reset_db.py will drop all tables and recreate via migrations
        # SQLite files will be handled automatically
        python scripts/reset_db.py

        echo ""
        echo -e "${GREEN}✅ Database reset complete!${NC}"
        echo -e "${BLUE}All tables have been dropped and recreated.${NC}"
        echo -e "${BLUE}Default admin user will be created on next app startup.${NC}"
        ;;
    help|--help|-h)
        echo -e "${BLUE}IntellectScout Trading Bot Management Script${NC}"
        echo ""
        echo "Usage: isbot [command] [options]"
        echo ""
        echo "Commands:"
        echo "  start              Start both backend and frontend servers"
        echo "  stop               Stop both backend and frontend servers"
        echo "  restart            Restart both backend and frontend servers"
        echo "  status (or st)     Show status of both servers"
        echo "  logs [service]     Show logs (backend, frontend, or both)"
        echo "  reset-ports        Reset port configuration to defaults"
        echo "  migrate            Run database migration"
        echo "  reset-db           Reset database (WARNING: deletes all data)"
        echo "  help               Show this help message"
        echo ""
        echo "Port Management:"
        echo "  The script automatically finds available ports if defaults are busy:"
        echo "  - Backend default: 5002"
        echo "  - Frontend default: 5173"
        echo "  - Ports are saved in .backend.port and .frontend.port files"
        echo "  - Use 'isbot reset-ports' to reset and use defaults on next start"
        echo ""
        echo "Examples:"
        echo "  isbot start                    # Start both services"
        echo "  isbot stop                     # Stop both services"
        echo "  isbot restart                  # Restart both services"
        echo "  isbot status                   # Check status"
        echo "  isbot logs                     # Show all logs"
        echo "  isbot logs backend             # Show backend logs only"
        echo "  isbot logs frontend            # Show frontend logs only"
        echo "  isbot reset-ports              # Reset port configuration"
        ;;
    *)
        if [ -z "$1" ]; then
            show_status
        else
            echo -e "${RED}Unknown command: $1${NC}"
            echo "Run 'isbot help' for usage information"
            exit 1
        fi
        ;;
esac
