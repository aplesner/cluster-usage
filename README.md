# Cluster Usage Dashboard

A web application for analyzing and visualizing IO usage logs and other metrics from the Arton computing cluster.

## Quick Start

### Local Development

```bash
# Start both backend and frontend locally
./scripts/local-dev.sh

# Or test without starting servers
./scripts/quick-test.sh
```

### Deploy to University VM

```bash
# Deploy to production VM
./scripts/local-deploy.sh
```

## Development Workflow

1. **Code locally** using your preferred editor
2. **Test locally** with `./scripts/local-dev.sh`
3. **Deploy when ready** with `./scripts/local-deploy.sh`
4. **GitLab CI/CD** automatically tests and deploys on push to main

## Architecture

- **Backend**: Python Flask API with SQLite database
- **Frontend**: React application with Chart.js visualizations
- **Deployment**: Docker containers on university VM
- **CI/CD**: GitLab pipeline with automated testing and deployment

## Features

- **Log Parsing**: Automatically processes IO usage logs
- **Interactive Dashboard**: Visualize IO usage across various dimensions
- **User Analytics**: Track usage patterns by user, role, and affiliation
- **Machine Analytics**: Analyze IO patterns across different machines
- **Time Series Analysis**: View trends and patterns over time
- **Historic Data**: Browse usage data across all log entries

## Production URL

The application is available at: http://ee-tik-vm057.ethz.ch

## Contributing

1. Make your changes locally
2. Test with `./scripts/quick-test.sh`
3. Deploy and verify with `./scripts/local-deploy.sh`
4. Commit and push - GitLab CI will handle the rest