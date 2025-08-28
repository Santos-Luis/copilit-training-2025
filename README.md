# Flight Delay Prediction Application

A full-stack application that predicts flight delays based on historical FAA data from 2013. Users can select departure and arrival airports along with a day of the week to get delay probability predictions.

## 🚀 Features

- **Data Processing**: Automated cleaning and processing of 271,940+ flight records
- **Backend API**: Express.js server with SQLite database and comprehensive REST API
- **Frontend Interface**: Modern React application with real-time airport search
- **Prediction Engine**: Statistical analysis based on historical delay patterns
- **Responsive Design**: Mobile-friendly interface with intuitive controls

## 📋 Project Structure

```
flight-delay-app/
├── backend/                 # Express.js API server
│   ├── server.js           # Main server file
│   ├── database.js         # Database manager and migration
│   ├── package.json        # Backend dependencies
│   └── README.md           # Backend documentation
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── App.jsx         # Main application component
│   │   ├── main.jsx        # Application entry point
│   │   └── index.css       # Styling
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite configuration
├── clean-flights.csv       # Processed flight data
├── flights.csv            # Original flight data (FAA)
├── data_cleaner.py        # Data cleaning script
├── start-backend.sh       # Backend startup script
└── start-frontend.sh      # Frontend startup script
```

## 🛠️ Quick Start

### Prerequisites
- Node.js (v16 or higher)
- Python 3.x (for data processing)
- npm or yarn

### 1. Clone and Setup
```bash
git clone <repository-url>
cd flight-delay-prediction
```

### 2. Start Backend (Terminal 1)
```bash
# Method 1: Using startup script
./start-backend.sh

# Method 2: Direct npm command
npm start --prefix backend

# Method 3: Manual way
cd backend && npm install && npm start
```

The backend will:
- Install dependencies automatically
- Create SQLite database
- Load and process flight data (first time only)
- Start server on http://localhost:3000

### 3. Start Frontend (Terminal 2)
```bash
# Method 1: Using startup script
./start-frontend.sh

# Method 2: Direct npm command
npm run dev --prefix frontend

# Method 3: Manual way
cd frontend && npm install && npm run dev
```

The frontend will start on http://localhost:3001

### 4. Access Application
Open your browser and navigate to http://localhost:3001

## 🎯 How to Use

1. **Search Departure Airport**: Type in the departure airport field to see suggestions
2. **Search Arrival Airport**: Type in the arrival airport field to see suggestions  
3. **Select Day of Week**: Click on the desired day (Monday-Sunday)
4. **Get Prediction**: Click "Predict Delay Probability" to see results

## 📊 API Endpoints

The backend provides the following REST API endpoints:

### Health Check
```http
GET /health
```

### Search Airports
```http
GET /api/airports/search?q=<query>
```

### Get Delay Prediction
```http
GET /api/delay-prediction?origin=<airport>&destination=<airport>&dayOfWeek=<1-7>
```

### Get Route Statistics
```http
GET /api/route-stats?origin=<airport>&destination=<airport>
```

## 📈 Example Usage

### Searching for Airports
```bash
curl "http://localhost:3000/api/airports/search?q=kennedy"
```

### Getting Delay Prediction
```bash
curl "http://localhost:3000/api/delay-prediction?origin=John%20F.%20Kennedy%20International&destination=Los%20Angeles%20International&dayOfWeek=1"
```

## 🗄️ Database Schema

### Flights Table
- **271,940 records** from 2013 FAA data
- Columns: origin/destination airports, delay information, day of week, carrier, etc.
- Indexes: optimized for quick lookups by airport and day

### Airports Table  
- **70 unique airports** across the US
- Columns: airport ID, name, city, state

## 🎨 Frontend Features

- **Real-time Search**: Airport suggestions as you type
- **Day Selection**: Visual day-of-week picker
- **Risk Visualization**: Color-coded results (green/yellow/red)
- **Detailed Statistics**: Flight counts, confidence levels
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: User-friendly error messages

## 🔧 Development

### Backend Development
```bash
cd backend
npm install
npm run dev  # If you have nodemon installed
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Data Processing
```bash
# Clean the original flights.csv data
python3 data_cleaner.py
```

## 🚀 Deployment

### Backend
- Can be deployed to any Node.js hosting service
- SQLite database file is created automatically
- Set PORT environment variable for custom port

### Frontend
- Build for production: `npm run build --prefix frontend`
- Deploy the `dist/` folder to any static hosting service
- Update API URLs for production environment

## 📝 Environment Variables

### Backend
- `PORT`: Server port (default: 3000)
- `NODE_ENV`: Environment (development/production)

### Frontend
- Vite proxy configured to forward `/api` calls to backend

## 🔍 Troubleshooting

### Backend Issues
- **Port in use**: Change PORT in environment or kill existing process
- **Database locked**: Restart the backend server
- **CSV not found**: Ensure `clean-flights.csv` exists in project root

### Frontend Issues
- **API calls failing**: Ensure backend is running on port 3000
- **Build fails**: Clear node_modules and reinstall dependencies

### Data Issues
- **Missing data**: Run `python3 data_cleaner.py` to regenerate clean data
- **Database errors**: Delete `backend/flights.db` to force regeneration

## 📊 Performance

- **Initial Load**: 1-2 minutes (data import on first run)
- **Query Response**: < 100ms average
- **Database Size**: ~50MB SQLite file
- **Memory Usage**: ~200MB for backend

## 🛡️ Security

- CORS enabled for cross-origin requests
- Input validation on all API endpoints
- SQL injection prevention with parameterized queries
- Error handling without exposing internal details

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review backend/frontend logs
3. Open an issue on GitHub

---

**🎉 Enjoy predicting flight delays!** ✈️
