import express from 'express';
import cors from 'cors';
import { ComprehensiveDataFetcher } from './dataFetcher.js';

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Server is running' });
});

// Main stock data fetch endpoint
app.post('/api/fetch-stock', async (req, res) => {
  try {
    const { ticker, startDate, endDate, includeBenchmark } = req.body;

    if (!ticker) {
      return res.status(400).json({ error: 'Ticker symbol is required' });
    }

    console.log(`\n${'='.repeat(50)}`);
    console.log(`Fetching data for: ${ticker}`);
    console.log(`Date range: ${startDate} to ${endDate}`);
    console.log(`Include benchmark: ${includeBenchmark}`);
    console.log('='.repeat(50));

    const fetcher = new ComprehensiveDataFetcher(ticker, {
      startDate: startDate || '2020-01-01',
      endDate: endDate || new Date().toISOString().split('T')[0],
      enableCache: true,
      rateLimit: 150
    });

    const data = await fetcher.fetchAllData(includeBenchmark);

    console.log(`✓ Successfully fetched data for ${ticker}\n`);
    res.json(data);

  } catch (error) {
    console.error(`✗ Error:`, error.message);
    res.status(500).json({ 
      error: error.message,
      ticker: req.body.ticker 
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════════╗
║   Stock Data Fetcher API Server                       ║
║   Running on: http://localhost:${PORT}                   ║
║                                                        ║
║   Endpoints:                                           ║
║   - GET  /health                                       ║
║   - POST /api/fetch-stock                              ║
║                                                        ║
║   Open index.html in your browser to use the UI       ║
╚════════════════════════════════════════════════════════╝
  `);
});