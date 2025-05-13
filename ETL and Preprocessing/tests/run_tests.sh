#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

echo -e "${YELLOW}Starting system tests...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt

# Run pytest with coverage
echo -e "${YELLOW}Running tests with coverage...${NC}"
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
    
    # Start the Flask application in the background
    echo -e "${YELLOW}Starting Flask application...${NC}"
    python app.py &
    APP_PID=$!
    
    # Wait for the application to start
    sleep 2
    
    # Test live endpoints
    echo -e "${YELLOW}Testing live endpoints...${NC}"
    
    # Test valuation ratios endpoint
    echo "Testing valuation ratios endpoint..."
    curl -X POST -H "Content-Type: application/json" -d '{"company":"RELIANCE.NS","duration":"1d"}' http://localhost:5000/valuation_ratios
    
    # Test company overview endpoint
    echo -e "\n\nTesting company overview endpoint..."
    curl http://localhost:5000/company_overview/RELIANCE.NS
    
    # Test peer comparison endpoint
    echo -e "\n\nTesting peer comparison endpoint..."
    curl http://localhost:5000/peer_comparison/RELIANCE.NS
    
    # Test quarterly results endpoint
    echo -e "\n\nTesting quarterly results endpoint..."
    curl http://localhost:5000/quarterly_results/RELIANCE.NS
    
    # Kill the Flask application
    kill $APP_PID
    
    echo -e "\n${GREEN}System verification complete!${NC}"
else
    echo -e "${RED}Tests failed! Please check the output above.${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate 