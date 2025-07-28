# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a logistics optimization system for warehouse automation, specifically designed to optimize the routing of autonomous vehicles (小车) in a warehouse environment. The system handles:

- Shelf-to-delivery zone routing optimization
- Task assignment through random mapping of shelves to boxes and stacks to zones
- Path visualization with matplotlib
- Cost calculation including rotation penalties for specific zones

## Architecture

### Main Components

**Path Planning & Cost Calculation** (`main.py:25-53`)
- `calculate_distance()`: Euclidean distance calculation
- `calculate_total_cost()`: Total route cost including rotation penalties
- `get_path_coordinates()`: Generates coordinate sequence for visualization

**Task Assignment Logic** (`main.py:74-123`)
- `generate_task_mapping()`: Random assignment of shelves→boxes→zones with one empty zone
- `get_delivery_zone_order()`: Fixed delivery sequence excluding empty zone
- `insert_special_shelf()`: Handles special case where a shelf has no corresponding zone
- `get_delivery_order()`: Reverses pickup order in two groups for delivery

**Visualization** (`main.py:124-152`)
- Uses matplotlib with Chinese font support (SimHei)
- Shows warehouse layout, paths, and zone boundaries
- Distinguishes between pickup points, delivery zones, and special stacking points

### Key Configuration

- **Pickup Points**: 3 access points (左/中/右) at x=180, different y coordinates
- **Delivery Zones**: 6 zones (a-f) in the right half of warehouse (x≥2000)
- **Rotation Cost**: 2000 units penalty for zones 'a' and 'f'
- **Warehouse Layout**: 4000×2000 coordinate system with center line at x=2000

## Development Commands

### Running the Application
```bash
# Install dependencies first
pip install matplotlib

# Run the main optimization program
python main.py
```

### Dependencies
The project requires:
- `matplotlib` - For path visualization and plotting
- `random` - For task assignment randomization
- `math` - For distance calculations

Note: No package management files (requirements.txt, setup.py) are present. Dependencies must be installed manually.

## Code Structure Notes

- Single-file application with clear functional separation
- Chinese language support for UI elements and zone names
- Deterministic algorithm with randomized initial conditions
- Fixed warehouse layout and zone configurations
- No test suite or linting configuration present