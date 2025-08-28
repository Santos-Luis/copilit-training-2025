# Flight Delay Prediction Backend API

A Node.js/Express API server that predicts flight delays based on historical flight data from 2013. The API uses SQLite database and provides endpoints to search airports and predict delay probabilities.

## Features

- 🏢 **Airport Search**: Search airports by name or city
- 📊 **Delay Prediction**: Get delay probability for specific routes and days
- 📈 **Route Statistics**: Weekly delay statistics for any route
- 🗃️ **SQLite Database**: Local database with automatic data migration
- 🔄 **Auto-Migration**: Automatically loads data from CSV on first startup

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- The `clean-flights.csv` file should be in the parent directory

## Quick Start Script

To start the project quickly, you can use this command:

```bash
# From the root directory (/Users/luis.henriques/Documents/Projects/copilot-training-2025)
npm start --prefix backend
```

Or create a simple start script `start-backend.sh`:

```bash
#!/bin/bash
echo "🚀 Starting Flight Delay API Backend..."
npm start --prefix backend
```

Make it executable and run:
```bash
chmod +x start-backend.sh
./start-backend.sh
```

## Installation & Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the server:**
   ```bash
   npm start
   ```

   Or for development:
   ```bash
   npm run dev
   ```

4. **First startup**: The server will automatically:
   - Create SQLite database (`flights.db`)
   - Create necessary tables and indexes
   - Load data from `../clean-flights.csv` (271,940+ flight records)
   - This process may take 1-2 minutes on first run

5. **Server ready**: Once you see the success message, the API is ready at `http://localhost:3000`

## API Endpoints

### Health Check
```http
GET /health
```
Returns server status.

### Search Airports
```http
GET /api/airports/search?q=<query>
```
Search airports by name or city.
- **Parameters**: `q` (string, min 2 characters)
- **Example**: `/api/airports/search?q=kennedy`

### Get All Airports
```http
GET /api/airports
```
Returns all unique airports in the database.

### Predict Flight Delay
```http
GET /api/delay-prediction?origin=<airport>&destination=<airport>&dayOfWeek=<1-7>
```
Predicts delay probability for a specific route and day.
- **Parameters**:
  - `origin` (string): Origin airport name
  - `destination` (string): Destination airport name  
  - `dayOfWeek` (number): 1=Monday, 2=Tuesday, ..., 7=Sunday
- **Example**: `/api/delay-prediction?origin=John F. Kennedy International&destination=Los Angeles International&dayOfWeek=1`

### Route Statistics
```http
GET /api/route-stats?origin=<airport>&destination=<airport>
```
Get weekly delay statistics for a route.
- **Parameters**:
  - `origin` (string): Origin airport name
  - `destination` (string): Destination airport name
- **Example**: `/api/route-stats?origin=John F. Kennedy International&destination=Los Angeles International`

## Example Usage

### 1. Search for airports containing "angeles":
```bash
curl "http://localhost:3000/api/airports/search?q=angeles"
```

### 2. Check delay probability for JFK to LAX on Monday:
```bash
curl "http://localhost:3000/api/delay-prediction?origin=John%20F.%20Kennedy%20International&destination=Los%20Angeles%20International&dayOfWeek=1"
```

### 3. Get weekly stats for a route:
```bash
curl "http://localhost:3000/api/route-stats?origin=John%20F.%20Kennedy%20International&destination=Los%20Angeles%20International"
```

## Sample API Response

### Delay Prediction Response:
```json
{
  "success": true,
  "data": {
    "origin": "John F. Kennedy International",
    "destination": "Los Angeles International", 
    "dayOfWeek": "Monday",
    "totalFlights": 156,
    "delayedFlights": 32,
    "delayProbability": 20.51,
    "confidence": "High",
    "message": "Moderate delay risk"
  }
}
```

## Database Schema

### Flights Table
- Contains all flight records with delay information
- Indexes on: origin_airport, dest_airport, day_of_week, arr_del_15

### Airports Table  
- Unique airports with ID, name, city, state
- Automatically populated from flight data

## Error Handling

The API includes comprehensive error handling:
- 400: Bad Request (missing/invalid parameters)
- 404: Not Found (invalid endpoints)
- 500: Internal Server Error (database/server issues)

## Performance Notes

- Database file size: ~50MB
- Initial data load: 1-2 minutes
- Query response time: < 100ms
- Batch processing: 1000 records per transaction

## Stopping the Server

Use `Ctrl+C` to gracefully shutdown the server. The database connection will be properly closed.

## Troubleshooting

### "CSV file not found" error:
- Ensure `clean-flights.csv` exists in the parent directory
- Check file path: `../clean-flights.csv`

### Database permission errors:
- Ensure write permissions in the backend directory
- The `flights.db` file will be created automatically

### Port already in use:
- Change the PORT environment variable: `PORT=3001 npm start`
- Or kill the process using port 3000

### Memory issues during data load:
- This is normal for large datasets
- Wait for the "Data loading completed successfully!" message

## Development

For development with auto-restart, consider installing nodemon:
```bash
npm install -g nodemon
nodemon server.js
```

## License

ISC
