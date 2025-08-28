const express = require('express');
const cors = require('cors');
const path = require('path');
const axios = require('axios');
const DatabaseManager = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;
const ML_API_URL = process.env.ML_API_URL || 'http://localhost:5000';

// Middleware
app.use(cors());
app.use(express.json());

// Database instance
let db;

// ML API health check
let mlApiAvailable = false;

async function checkMLAPI() {
    try {
        const response = await axios.get(`${ML_API_URL}/health`, { timeout: 5000 });
        mlApiAvailable = response.data.model_loaded === true;
        if (mlApiAvailable) {
            console.log('✅ ML API is available and model is loaded');
        } else {
            console.log('⚠️  ML API is running but model is not loaded');
        }
    } catch (error) {
        mlApiAvailable = false;
        console.log('❌ ML API is not available, falling back to database queries');
    }
}

// Days of week mapping
const DAYS_OF_WEEK = {
    1: 'Monday',
    2: 'Tuesday', 
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday',
    7: 'Sunday'
};

// Routes

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'OK', 
        message: 'Flight Delay API is running',
        mlModel: {
            available: mlApiAvailable,
            url: ML_API_URL,
            status: mlApiAvailable ? 'Connected' : 'Disconnected'
        },
        features: {
            mlPredictions: mlApiAvailable,
            databaseFallback: true,
            airportSearch: true,
            routeStats: true
        }
    });
});

// Search airports by name
app.get('/api/airports/search', async (req, res) => {
    try {
        const { q } = req.query;
        
        if (!q || q.length < 2) {
            return res.status(400).json({ 
                error: 'Query parameter "q" is required and must be at least 2 characters long' 
            });
        }

        const airports = await db.searchAirports(q);
        res.json({
            success: true,
            query: q,
            results: airports,
            count: airports.length
        });
    } catch (error) {
        console.error('Error searching airports:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

// Get all unique airports
app.get('/api/airports', async (req, res) => {
    try {
        const airports = await db.searchAirports('');
        res.json({
            success: true,
            results: airports,
            count: airports.length
        });
    } catch (error) {
        console.error('Error fetching airports:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

// Predict flight delay using ML model or fallback to database
app.get('/api/delay-prediction', async (req, res) => {
    try {
        const { origin, destination, dayOfWeek } = req.query;
        
        // Validation
        if (!origin || !destination || !dayOfWeek) {
            return res.status(400).json({ 
                error: 'Parameters "origin", "destination", and "dayOfWeek" are required' 
            });
        }

        const dayNum = parseInt(dayOfWeek);
        if (isNaN(dayNum) || dayNum < 1 || dayNum > 7) {
            return res.status(400).json({ 
                error: 'dayOfWeek must be a number between 1 (Monday) and 7 (Sunday)' 
            });
        }

        let predictionResult;
        let usedMLModel = false;

        // Try ML API first if available
        if (mlApiAvailable) {
            try {
                const mlResponse = await axios.post(`${ML_API_URL}/predict`, {
                    origin: origin,
                    destination: destination,
                    dayOfWeek: dayNum
                }, { timeout: 10000 });

                if (mlResponse.data.success) {
                    usedMLModel = true;
                    const mlPrediction = mlResponse.data.prediction;
                    
                    predictionResult = {
                        origin,
                        destination,
                        dayOfWeek: DAYS_OF_WEEK[dayNum],
                        totalFlights: 'N/A (ML Prediction)',
                        delayedFlights: 'N/A (ML Prediction)',
                        delayProbability: mlPrediction.delayProbability,
                        confidence: mlPrediction.confidence,
                        message: mlPrediction.message,
                        source: 'ML Model',
                        modelInfo: {
                            type: mlPrediction.modelInfo.type,
                            accuracy: mlPrediction.modelInfo.accuracy,
                            dataAvailability: mlPrediction.dataAvailability
                        }
                    };
                }
            } catch (mlError) {
                console.log('ML API error, falling back to database:', mlError.message);
                mlApiAvailable = false; // Mark as unavailable for future requests
            }
        }

        // Fallback to database query if ML API failed or unavailable
        if (!usedMLModel) {
            const result = await db.getDelayProbability(origin, destination, dayNum);
            
            if (result.total_flights === 0) {
                return res.json({
                    success: true,
                    message: 'No historical data found for this route and day combination',
                    data: {
                        origin,
                        destination,
                        dayOfWeek: DAYS_OF_WEEK[dayNum],
                        totalFlights: 0,
                        delayedFlights: 0,
                        delayProbability: 0,
                        confidence: 'No data',
                        source: 'Database (No ML Model available)',
                        note: 'Consider using ML model for better predictions on unknown routes'
                    }
                });
            }

            // Determine confidence level based on sample size
            let confidence = 'Low';
            if (result.total_flights >= 100) confidence = 'High';
            else if (result.total_flights >= 50) confidence = 'Medium';

            predictionResult = {
                origin,
                destination,
                dayOfWeek: DAYS_OF_WEEK[dayNum],
                totalFlights: result.total_flights,
                delayedFlights: result.delayed_flights,
                delayProbability: result.delay_percentage,
                confidence,
                source: 'Historical Database',
                message: result.delay_percentage > 30 
                    ? 'High likelihood of delay - consider alternative flights'
                    : result.delay_percentage > 15 
                    ? 'Moderate delay risk'
                    : 'Low delay risk'
            };
        }

        res.json({
            success: true,
            data: predictionResult
        });

    } catch (error) {
        console.error('Error predicting delay:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

// Get route statistics
app.get('/api/route-stats', async (req, res) => {
    try {
        const { origin, destination } = req.query;
        
        if (!origin || !destination) {
            return res.status(400).json({ 
                error: 'Parameters "origin" and "destination" are required' 
            });
        }

        // Get stats for each day of the week
        const weeklyStats = [];
        for (let day = 1; day <= 7; day++) {
            const dayStats = await db.getDelayProbability(origin, destination, day);
            weeklyStats.push({
                dayOfWeek: day,
                dayName: DAYS_OF_WEEK[day],
                totalFlights: dayStats.total_flights,
                delayedFlights: dayStats.delayed_flights,
                delayProbability: dayStats.delay_percentage
            });
        }

        res.json({
            success: true,
            route: { origin, destination },
            weeklyStats
        });
    } catch (error) {
        console.error('Error fetching route stats:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ 
        error: 'Not found',
        message: 'The requested endpoint does not exist'
    });
});

// Initialize database and start server
async function startServer() {
    try {
        console.log('Starting Flight Delay API server...');
        
        // Initialize database
        db = new DatabaseManager();
        await db.connect();
        await db.createTables();
        
        // Load data from CSV
        const csvPath = path.join(__dirname, '..', 'clean-flights.csv');
        await db.loadDataFromCSV(csvPath);
        
        // Check ML API availability
        console.log('Checking ML API availability...');
        await checkMLAPI();
        
        // Start server
        app.listen(PORT, () => {
            console.log(`\n🚀 Flight Delay API server is running!`);
            console.log(`📍 Server URL: http://localhost:${PORT}`);
            console.log(`📊 Health check: http://localhost:${PORT}/health`);
            console.log(`🤖 ML API Status: ${mlApiAvailable ? '✅ Available' : '❌ Unavailable (using database fallback)'}`);
            console.log(`\n📋 Available endpoints:`);
            console.log(`   GET /api/airports/search?q=<query>    - Search airports`);
            console.log(`   GET /api/airports                     - Get all airports`);
            console.log(`   GET /api/delay-prediction             - Predict flight delay ${mlApiAvailable ? '(ML Enhanced)' : '(Database Only)'}`);
            console.log(`       ?origin=<airport>&destination=<airport>&dayOfWeek=<1-7>`);
            console.log(`   GET /api/route-stats                  - Get weekly route statistics`);
            console.log(`       ?origin=<airport>&destination=<airport>`);
            console.log(`\n📅 Day of week values: 1=Monday, 2=Tuesday, ..., 7=Sunday\n`);
        });
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nShutting down server...');
    if (db) {
        await db.close();
    }
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\nShutting down server...');
    if (db) {
        await db.close();
    }
    process.exit(0);
});

// Start the server
startServer();
