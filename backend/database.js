const sqlite3 = require('sqlite3').verbose();
const csv = require('csv-parser');
const fs = require('fs');
const path = require('path');

class DatabaseManager {
    constructor(dbPath = './flights.db') {
        this.dbPath = dbPath;
        this.db = null;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            this.db = new sqlite3.Database(this.dbPath, (err) => {
                if (err) {
                    console.error('Error connecting to database:', err);
                    reject(err);
                } else {
                    console.log('Connected to SQLite database');
                    resolve();
                }
            });
        });
    }

    async createTables() {
        const createFlightsTable = `
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                day_of_month INTEGER,
                day_of_week INTEGER,
                carrier TEXT,
                origin_airport_id INTEGER,
                origin_airport_name TEXT,
                origin_city TEXT,
                origin_state TEXT,
                dest_airport_id INTEGER,
                dest_airport_name TEXT,
                dest_city TEXT,
                dest_state TEXT,
                crs_dep_time INTEGER,
                dep_delay REAL,
                dep_del_15 INTEGER,
                crs_arr_time INTEGER,
                arr_delay REAL,
                arr_del_15 INTEGER,
                cancelled INTEGER
            )
        `;

        const createAirportsTable = `
            CREATE TABLE IF NOT EXISTS airports (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                city TEXT,
                state TEXT
            )
        `;

        const createIndexes = [
            'CREATE INDEX IF NOT EXISTS idx_origin_airport ON flights(origin_airport_name)',
            'CREATE INDEX IF NOT EXISTS idx_dest_airport ON flights(dest_airport_name)',
            'CREATE INDEX IF NOT EXISTS idx_day_of_week ON flights(day_of_week)',
            'CREATE INDEX IF NOT EXISTS idx_arr_del_15 ON flights(arr_del_15)'
        ];

        return new Promise((resolve, reject) => {
            this.db.serialize(() => {
                this.db.run(createFlightsTable, (err) => {
                    if (err) {
                        console.error('Error creating flights table:', err);
                        reject(err);
                        return;
                    }
                    console.log('Flights table created successfully');
                });

                this.db.run(createAirportsTable, (err) => {
                    if (err) {
                        console.error('Error creating airports table:', err);
                        reject(err);
                        return;
                    }
                    console.log('Airports table created successfully');
                });

                // Create indexes
                const indexesPromise = Promise.all(createIndexes.map(indexSQL => {
                    return new Promise((resolveIndex, rejectIndex) => {
                        this.db.run(indexSQL, (err) => {
                            if (err) {
                                console.error('Error creating index:', err);
                                rejectIndex(err);
                            } else {
                                resolveIndex();
                            }
                        });
                    });
                }));

                indexesPromise.then(() => {
                    console.log('All indexes created successfully');
                    resolve();
                }).catch(reject);
            });
        });
    }

    async loadDataFromCSV(csvPath) {
        console.log(`Loading data from ${csvPath}...`);
        
        // First, check if data already exists
        const countResult = await this.getFlightCount();
        if (countResult > 0) {
            console.log(`Database already contains ${countResult} flights. Skipping data load.`);
            return;
        }

        const csvFilePath = path.resolve(csvPath);
        if (!fs.existsSync(csvFilePath)) {
            throw new Error(`CSV file not found: ${csvFilePath}`);
        }

        return new Promise((resolve, reject) => {
            const flights = [];
            const airports = new Map(); // Use Map to avoid duplicates

            fs.createReadStream(csvFilePath)
                .pipe(csv())
                .on('data', (row) => {
                    // Process flight data
                    const flight = {
                        year: parseInt(row.Year) || 0,
                        month: parseInt(row.Month) || 0,
                        day_of_month: parseInt(row.DayofMonth) || 0,
                        day_of_week: parseInt(row.DayOfWeek) || 0,
                        carrier: row.Carrier || '',
                        origin_airport_id: parseInt(row.OriginAirportID) || 0,
                        origin_airport_name: row.OriginAirportName || '',
                        origin_city: row.OriginCity || '',
                        origin_state: row.OriginState || '',
                        dest_airport_id: parseInt(row.DestAirportID) || 0,
                        dest_airport_name: row.DestAirportName || '',
                        dest_city: row.DestCity || '',
                        dest_state: row.DestState || '',
                        crs_dep_time: parseInt(row.CRSDepTime) || 0,
                        dep_delay: parseFloat(row.DepDelay) || 0,
                        dep_del_15: parseInt(row.DepDel15) || 0,
                        crs_arr_time: parseInt(row.CRSArrTime) || 0,
                        arr_delay: parseFloat(row.ArrDelay) || 0,
                        arr_del_15: parseInt(row.ArrDel15) || 0,
                        cancelled: parseInt(row.Cancelled) || 0
                    };
                    
                    flights.push(flight);

                    // Collect unique airports
                    if (flight.origin_airport_name && !airports.has(flight.origin_airport_id)) {
                        airports.set(flight.origin_airport_id, {
                            id: flight.origin_airport_id,
                            name: flight.origin_airport_name,
                            city: flight.origin_city,
                            state: flight.origin_state
                        });
                    }

                    if (flight.dest_airport_name && !airports.has(flight.dest_airport_id)) {
                        airports.set(flight.dest_airport_id, {
                            id: flight.dest_airport_id,
                            name: flight.dest_airport_name,
                            city: flight.dest_city,
                            state: flight.dest_state
                        });
                    }
                })
                .on('end', async () => {
                    try {
                        console.log(`Parsed ${flights.length} flights and ${airports.size} unique airports`);
                        
                        // Insert airports first
                        await this.insertAirports(Array.from(airports.values()));
                        
                        // Insert flights in batches
                        await this.insertFlights(flights);
                        
                        console.log('Data loading completed successfully!');
                        resolve();
                    } catch (error) {
                        reject(error);
                    }
                })
                .on('error', reject);
        });
    }

    async insertAirports(airports) {
        console.log('Inserting airports...');
        const stmt = this.db.prepare(`
            INSERT OR IGNORE INTO airports (id, name, city, state) 
            VALUES (?, ?, ?, ?)
        `);

        return new Promise((resolve, reject) => {
            this.db.serialize(() => {
                this.db.run('BEGIN TRANSACTION', (err) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    airports.forEach(airport => {
                        stmt.run([airport.id, airport.name, airport.city, airport.state]);
                    });
                    
                    stmt.finalize((err) => {
                        if (err) {
                            this.db.run('ROLLBACK');
                            reject(err);
                            return;
                        }
                        
                        this.db.run('COMMIT', (err) => {
                            if (err) {
                                reject(err);
                            } else {
                                console.log(`Inserted ${airports.length} airports`);
                                resolve();
                            }
                        });
                    });
                });
            });
        });
    }

    async insertFlights(flights) {
        console.log('Inserting flights...');
        const batchSize = 1000;
        const totalBatches = Math.ceil(flights.length / batchSize);

        for (let i = 0; i < totalBatches; i++) {
            const start = i * batchSize;
            const end = Math.min(start + batchSize, flights.length);
            const batch = flights.slice(start, end);

            await this.insertFlightBatch(batch);
            console.log(`Inserted batch ${i + 1}/${totalBatches} (${end}/${flights.length} flights)`);
        }
    }

    async insertFlightBatch(flights) {
        const stmt = this.db.prepare(`
            INSERT INTO flights (
                year, month, day_of_month, day_of_week, carrier,
                origin_airport_id, origin_airport_name, origin_city, origin_state,
                dest_airport_id, dest_airport_name, dest_city, dest_state,
                crs_dep_time, dep_delay, dep_del_15, crs_arr_time, arr_delay, arr_del_15, cancelled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);

        return new Promise((resolve, reject) => {
            this.db.serialize(() => {
                this.db.run('BEGIN TRANSACTION', (err) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    flights.forEach(flight => {
                        stmt.run([
                            flight.year, flight.month, flight.day_of_month, flight.day_of_week, flight.carrier,
                            flight.origin_airport_id, flight.origin_airport_name, flight.origin_city, flight.origin_state,
                            flight.dest_airport_id, flight.dest_airport_name, flight.dest_city, flight.dest_state,
                            flight.crs_dep_time, flight.dep_delay, flight.dep_del_15, flight.crs_arr_time, 
                            flight.arr_delay, flight.arr_del_15, flight.cancelled
                        ]);
                    });
                    
                    stmt.finalize((err) => {
                        if (err) {
                            this.db.run('ROLLBACK');
                            reject(err);
                            return;
                        }
                        
                        this.db.run('COMMIT', (err) => {
                            if (err) {
                                reject(err);
                            } else {
                                resolve();
                            }
                        });
                    });
                });
            });
        });
    }

    async getFlightCount() {
        return new Promise((resolve, reject) => {
            this.db.get('SELECT COUNT(*) as count FROM flights', (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row.count);
                }
            });
        });
    }

    async searchAirports(query) {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT DISTINCT id, name, city, state 
                FROM airports 
                WHERE name LIKE ? OR city LIKE ? 
                ORDER BY name
                LIMIT 20
            `;
            const searchQuery = `%${query}%`;
            
            this.db.all(sql, [searchQuery, searchQuery], (err, rows) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
        });
    }

    async getDelayProbability(originAirportName, destAirportName, dayOfWeek) {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT 
                    COUNT(*) as total_flights,
                    SUM(arr_del_15) as delayed_flights,
                    ROUND(
                        CASE 
                            WHEN COUNT(*) > 0 THEN (SUM(arr_del_15) * 100.0 / COUNT(*))
                            ELSE 0 
                        END, 2
                    ) as delay_percentage
                FROM flights 
                WHERE origin_airport_name = ? 
                AND dest_airport_name = ? 
                AND day_of_week = ?
                AND cancelled = 0
            `;
            
            this.db.get(sql, [originAirportName, destAirportName, dayOfWeek], (err, row) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(row);
                }
            });
        });
    }

    async close() {
        return new Promise((resolve) => {
            if (this.db) {
                this.db.close((err) => {
                    if (err) {
                        console.error('Error closing database:', err);
                    } else {
                        console.log('Database connection closed');
                    }
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }
}

module.exports = DatabaseManager;
