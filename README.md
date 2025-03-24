# Cluster Usage Dashboard

A web application for analyzing and visualizing IO usage logs and other metrics from the Arton computing cluster.

## Overview

This application processes IO usage logs, storing them in a SQLite database and providing a web interface for analyzing usage patterns. It helps us monitor resource utilization, identify heavy users, and track IO patterns across different machines and user groups.

Future: We will also include compute resource usage.

## Features

- **Log Parsing**: Automatically processes IO usage logs and stores them in a structured database
- **Incremental Updates**: Processes new log data while preserving historical information
- **Interactive Dashboard**: Visualize IO usage across various dimensions
- **User Analytics**: Track and compare usage patterns by user, role, and affiliation
- **Machine Analytics**: Analyze IO patterns across different machines and machine types
- **Time Series Analysis**: View trends and patterns over time
- **Size Distribution Analysis**: Understand IO operation size distributions

## Directory Structure

- `/backend`: Python-based API server and data processing
- `/frontend`: React-based web interface
- `/data`: Storage for database and log files
- `/tests`: Test suite for backend and frontend
- `/scripts`: Utility scripts for setup and maintenance
- `/docker`: Docker configuration for deployment

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- SQLite3
- Docker (optional, for containerized deployment)

### Installation (TODO)

1. Clone the repository:

```bash
git clone https://github.com/aplesner/cluster-usage
cd Cluster-usage
```

2. Set up the backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:

```bash
cd ../frontend
npm install
```

4. Initialize the database and import logs:

```bash
cd ..
mkdir -p data
python backend/app.py init
```

### Running the Application

#### Development Mode

1. Start the backend server:

```bash
cd backend
python app.py
```

2. In a separate terminal, start the frontend development server:

```bash
cd frontend
npm start
```

3. Access the application at http://localhost

#### Production Mode (with Docker)

```bash
./scripts/docker-run.sh start
```

## Log Processing

To process new logs:

```bash
python backend/app.py process_logs /path/to/io_usage.log
```

Or use the script:

```bash
./scripts/import_logs.sh
```

## API Endpoints

The backend provides the following API endpoints:

- `GET /api/stats`: General database statistics
- `GET /api/users`: List of all users
- `GET /api/machines`: List of all machines
- `GET /api/usage/user/{username}`: Usage statistics for a specific user
- `GET /api/usage/machine/{machine_name}`: Usage statistics for a specific machine
- `GET /api/usage/time`: Time-based usage statistics
- `GET /api/usage/size`: Size distribution statistics

## Database Schema

The application uses a normalized SQLite database with the following tables:

- `LogEntries`: Timestamp information
- `Users`: User information
- `Machines`: Machine information
- `IOSizeRanges`: IO size range information
- `UserSessions`: Links users, machines, and log entries
- `IOOperations`: Operation counts for each size range in a session

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project was developed to help system administrators understand IO usage patterns in computing clusters.
