# Retirement Asset Projection

## Project Overview

This is a Monte Carlo simulation-based retirement planning tool that projects retirement asset trajectories over time. The application provides a web-based interactive interface for users to model their retirement finances under various scenarios, accounting for investment growth volatility and inflation uncertainty.

## Core Functionality

### Monte Carlo Simulation Engine

The application runs 100,000 Monte Carlo simulations to model retirement portfolio performance. Each simulation:

- Starts with an initial asset amount
- Applies annual expenses (adjusted for inflation)
- Models portfolio growth using S&P 500 historical volatility (20% standard deviation)
- Models inflation with 2% standard deviation
- Tracks asset balance year-over-year until retirement timeline ends

### Key Features

1. **Interactive Dashboard**: Built with Dash (Plotly) for real-time visualization
2. **Performance Optimized**: Uses Numba's JIT compilation (`@njit`) for fast computation
3. **Success Rate Analysis**: Calculates and displays probability of running out of money (ruin risk)
4. **Results-First UX**: Key metrics displayed prominently at the top with color-coded feedback
5. **Income Streams**: Support for Social Security, pension, and other guaranteed income sources
6. **Statistical Analysis**: Provides 10th, 50th (median), and 90th percentile outcomes
7. **Inflation Adjustment**: Shows both "Future Dollars" and "Today's Dollars" (inflation-adjusted)
8. **Scenario Analysis**: Displays average and median inflation/growth rates for different outcome groups

## Parameters

Users can adjust the following parameters via interactive sliders:

### Basic Parameters
- **Initial Total Assets**: $1M - $10M (default: $5M)
- **Annual Expense (First Year)**: $50K - $500K (default: $100K)
- **Years to Live**: 10-50 years (default: 35 years)

### Income Parameters (New!)
- **Annual Income**: $0 - $100K (default: $0) - For Social Security, pension, rental income, etc.
- **Income Start Year**: 0-20 years (default: 0) - When guaranteed income begins

### Advanced Parameters
- **Inflation Mean**: 0-10% (default: 2.5%)
- **Growth Mean**: 0-20% (default: 10.5%)

## Technical Implementation

### Architecture

- **Frontend**: Dash web framework with Bootstrap styling
- **Computation**: NumPy arrays with Numba JIT compilation
- **Visualization**: Plotly interactive charts
- **Performance**: Batch processing (1,000 simulations per batch)

### Key Components

#### Simulation Function (`retire.py:14-43`)
- `single_simulation_batch_numba()`: Numba-optimized batch simulation
- Tracks asset history for each year
- Handles portfolio depletion (assets < 0)

#### Main Simulation (`retire.py:45-101`)
- `simulate_asset_projection()`: Orchestrates batch simulations
- Computes percentile bands (10th, 50th, 90th)
- Extracts statistics for different outcome groups

#### Web Interface (`retire.py:106-225`)
- Interactive sliders for all parameters
- Real-time graph updates
- Summary tables showing nominal/real values and rate statistics
- Loading indicators for computation time

## Output

### Key Results Cards (New!)
Displayed prominently at the top of the page:

1. **Success Rate Card**
   - Percentage chance of retirement success (100% - ruin risk)
   - Risk of running out of money
   - Color-coded feedback (green/yellow/red)
   - Actionable guidance message

2. **Median Final Balance Card**
   - 50th percentile outcome
   - Shows both future dollars and today's dollars
   - Explains "50% chance of having more than this"

3. **Worst Case Card**
   - 10th percentile outcome
   - Shows both future dollars and today's dollars
   - Explains "90% chance of doing better"

### Visualization
- Line chart showing median trajectory
- Shaded area between 10th and 90th percentiles
- Interactive hover tooltips

### Detailed Outcome Analysis
- Final asset values for 10th/50th/90th percentiles
- Both "Future Dollars" and "Today's Dollars" (user-friendly terminology)
- Average and median inflation/growth rates for each scenario

### Advanced Details (Collapsible)
- Simulation execution time
- Number of simulation rounds

## Performance

The application uses Numba's JIT compilation to achieve high-performance simulation. With 100,000 simulation rounds, typical execution times are under a few seconds on modern hardware.

## Files

- `retire.py`: Main application file containing simulation engine and web interface
- `Dockerfile`: Container configuration for Docker deployment
- `requirements.txt`: Python dependencies with version constraints
- `CLAUDE.md`: This file - project documentation
- `IMPROVEMENTS.md`: Detailed documentation of recent UX improvements
- `.github/workflows/docker-publish.yml`: GitHub Actions workflow for CI/CD
- `tmp.py`: Unrelated algorithm (meeting room scheduling problem)

## Dependencies

- numpy
- dash
- plotly
- numba

## Usage

### Using Virtual Environment (Recommended)
```bash
# Activate the virtual environment
source venv/bin/activate

# Run the application
python retire.py

# Or run directly without activating
./venv/bin/python retire.py
```

### Using System Python
```bash
python3 retire.py
```

The dashboard will be available at `http://127.0.0.1:8050/` in debug mode.

### Using Docker

```bash
# Pull from Docker Hub
docker pull <dockerhub-username>/retirement-asset-projection:latest

# Run the container
docker run -p 8050:8050 <dockerhub-username>/retirement-asset-projection:latest
```

The dashboard will be available at `http://localhost:8050/`.

## CI/CD

### GitHub Actions

The project uses GitHub Actions for continuous integration and deployment. The workflow automatically builds and pushes Docker images to Docker Hub.

#### Workflow: Build and Push Docker Image

**Location**: `.github/workflows/docker-publish.yml`

**Triggers**:
- Push to `main` branch (when relevant files change)
- Manual trigger via `workflow_dispatch`

**Monitored Files**:
- `retire.py`
- `requirements.txt`
- `Dockerfile`
- `.github/workflows/docker-publish.yml`

**What It Does**:
1. Checks out the repository
2. Sets up Docker Buildx for efficient builds
3. Authenticates with Docker Hub
4. Builds the Docker image with layer caching
5. Pushes to Docker Hub with two tags:
   - `latest` (for main branch)
   - Git commit SHA (for version tracking)

**Required Secrets**:
- `DOCKERHUB_USERNAME`: Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token

### Docker Configuration

The `Dockerfile` uses Python 3.11-slim as the base image and:
- Installs gcc for Numba compilation
- Copies and installs Python dependencies
- Exposes port 8050
- Runs with debug mode disabled by default

## Recent Improvements (Jan 2026)

See `IMPROVEMENTS.md` for detailed documentation. Major UX enhancements include:

1. **Ruin Risk Calculation**: Now displays the probability of running out of money with color-coded feedback
2. **Results-First Layout**: Key metrics appear at the top in prominent cards before input controls
3. **Income Stream Support**: Can now model Social Security, pension, and other guaranteed income sources
4. **User-Friendly Terminology**: "Future Dollars" and "Today's Dollars" instead of "Nominal" and "Real"
5. **Progressive Disclosure**: Technical metrics hidden in collapsible section to reduce clutter

## Financial Model Assumptions

- **Investment Growth**: Modeled as normal distribution with user-defined mean and 20% std dev (based on S&P 500 historical volatility)
- **Inflation**: Modeled as normal distribution with user-defined mean and 2% std dev
- **Expenses**: Compound annually with inflation
- **Income**: Social Security/pension income compounds with inflation starting from specified year
- **Annual Cash Flow**: Assets grow by investment returns, income is added, expenses are withdrawn
- **Portfolio Failure**: Simulation shows $0 once assets are depleted
- **Success Criteria**: Retirement is successful if assets remain positive throughout the entire time horizon
