import { useEffect, useRef, useState } from 'react';

const DAYS_OF_WEEK = [
  { value: 1, label: 'Monday', short: 'Mon' },
  { value: 2, label: 'Tuesday', short: 'Tue' },
  { value: 3, label: 'Wednesday', short: 'Wed' },
  { value: 4, label: 'Thursday', short: 'Thu' },
  { value: 5, label: 'Friday', short: 'Fri' },
  { value: 6, label: 'Saturday', short: 'Sat' },
  { value: 7, label: 'Sunday', short: 'Sun' }
];

const AirportSearch = ({ label, value, onChange, onSelect, suggestions, loading }) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    onChange(e.target.value);
    setShowSuggestions(true);
  };

  const handleSuggestionClick = (airport) => {
    onSelect(airport);
    setShowSuggestions(false);
  };

  return (
    <div className="form-group">
      <label>{label}</label>
      <div className="airport-input-container" ref={containerRef}>
        <input
          type="text"
          value={value}
          onChange={handleInputChange}
          onFocus={() => setShowSuggestions(true)}
          placeholder="Type to search for airports..."
          autoComplete="off"
        />
        {showSuggestions && suggestions.length > 0 && (
          <div className="airport-suggestions">
            {suggestions.map((airport) => (
              <div
                key={airport.id}
                className="airport-suggestion"
                onClick={() => handleSuggestionClick(airport)}
              >
                <div className="airport-name">{airport.name}</div>
                <div className="airport-location">{airport.city}, {airport.state}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const PredictionResult = ({ result }) => {
  if (!result) return null;

  const getRiskLevel = (probability) => {
    if (probability === 0) return 'no-data';
    if (probability < 15) return 'low-risk';
    if (probability < 30) return 'moderate-risk';
    return 'high-risk';
  };

  const riskLevel = getRiskLevel(result.delayProbability || 0);

  return (
    <div className={`prediction-result ${riskLevel}`}>
      <div className="route-info">
        <strong>{result.origin}</strong> → <strong>{result.destination}</strong> on {result.dayOfWeek}
      </div>
      
      <div className="result-title">
        {result.delayProbability === 0 ? 'No Historical Data' : 'Delay Probability'}
      </div>
      
      <div className="result-probability">
        {result.delayProbability === 0 ? 'N/A' : `${result.delayProbability}%`}
      </div>
      
      <div className="result-message">
        {result.message || 'No historical flights found for this route and day combination'}
      </div>

      {result.totalFlights > 0 && (
        <div className="result-details">
          <div className="result-stats">
            <div className="result-stat">
              <span className="result-stat-value">{result.totalFlights}</span>
              <div className="result-stat-label">Total Flights</div>
            </div>
            <div className="result-stat">
              <span className="result-stat-value">{result.delayedFlights}</span>
              <div className="result-stat-label">Delayed Flights</div>
            </div>
            <div className="result-stat">
              <span className="result-stat-value">{result.confidence}</span>
              <div className="result-stat-label">Confidence</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  const [departureQuery, setDepartureQuery] = useState('');
  const [arrivalQuery, setArrivalQuery] = useState('');
  const [selectedDeparture, setSelectedDeparture] = useState(null);
  const [selectedArrival, setSelectedArrival] = useState(null);
  const [selectedDay, setSelectedDay] = useState(1); // Default to Monday
  const [departureSuggestions, setDepartureSuggestions] = useState([]);
  const [arrivalSuggestions, setArrivalSuggestions] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [error, setError] = useState('');

  // Debounce search queries
  useEffect(() => {
    if (departureQuery.length >= 2) {
      const timeoutId = setTimeout(() => {
        searchAirports(departureQuery, setDepartureSuggestions);
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      setDepartureSuggestions([]);
    }
  }, [departureQuery]);

  useEffect(() => {
    if (arrivalQuery.length >= 2) {
      const timeoutId = setTimeout(() => {
        searchAirports(arrivalQuery, setArrivalSuggestions);
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      setArrivalSuggestions([]);
    }
  }, [arrivalQuery]);

  const searchAirports = async (query, setSuggestions) => {
    try {
      setSearchLoading(true);
      const response = await fetch(`/api/airports/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error('Failed to search airports');
      }
      const data = await response.json();
      setSuggestions(data.results || []);
    } catch (err) {
      console.error('Error searching airports:', err);
      setSuggestions([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleDepartureSelect = (airport) => {
    setSelectedDeparture(airport);
    setDepartureQuery(airport.name);
    setDepartureSuggestions([]);
  };

  const handleArrivalSelect = (airport) => {
    setSelectedArrival(airport);
    setArrivalQuery(airport.name);
    setArrivalSuggestions([]);
  };

  const handlePredict = async () => {
    if (!selectedDeparture || !selectedArrival) {
      setError('Please select both departure and arrival airports');
      return;
    }

    if (selectedDeparture.id === selectedArrival.id) {
      setError('Departure and arrival airports cannot be the same');
      return;
    }

    setError('');
    setPredictionLoading(true);
    setPredictionResult(null);

    try {
      const params = new URLSearchParams({
        origin: selectedDeparture.name,
        destination: selectedArrival.name,
        dayOfWeek: selectedDay.toString()
      });

      const response = await fetch(`/api/delay-prediction?${params}`);
      if (!response.ok) {
        throw new Error('Failed to get prediction');
      }

      const data = await response.json();
      if (data.success) {
        setPredictionResult(data.data);
      } else {
        setError(data.message || 'Failed to get prediction');
      }
    } catch (err) {
      console.error('Error getting prediction:', err);
      setError('Failed to get prediction. Please try again.');
    } finally {
      setPredictionLoading(false);
    }
  };

  const canPredict = selectedDeparture && selectedArrival && !predictionLoading;

  return (
    <div className="app">
      <div className="header">
        <h1>✈️ Flight Delay Predictor</h1>
        <p>Get delay probability predictions based on historical flight data</p>
      </div>

      <div className="prediction-form">
        <AirportSearch
          label="🛫 Departure Airport"
          value={departureQuery}
          onChange={setDepartureQuery}
          onSelect={handleDepartureSelect}
          suggestions={departureSuggestions}
          loading={searchLoading}
        />

        <AirportSearch
          label="🛬 Arrival Airport"
          value={arrivalQuery}
          onChange={setArrivalQuery}
          onSelect={handleArrivalSelect}
          suggestions={arrivalSuggestions}
          loading={searchLoading}
        />

        <div className="form-group">
          <label>📅 Day of Week</label>
          <div className="day-grid">
            {DAYS_OF_WEEK.map((day) => (
              <div
                key={day.value}
                className={`day-option ${selectedDay === day.value ? 'selected' : ''}`}
                onClick={() => setSelectedDay(day.value)}
              >
                <div>{day.short}</div>
              </div>
            ))}
          </div>
        </div>

        <button
          className="predict-button"
          onClick={handlePredict}
          disabled={!canPredict}
        >
          {predictionLoading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              Predicting...
            </div>
          ) : (
            '🔮 Predict Delay Probability'
          )}
        </button>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <PredictionResult result={predictionResult} />
      </div>
    </div>
  );
}

export default App;
