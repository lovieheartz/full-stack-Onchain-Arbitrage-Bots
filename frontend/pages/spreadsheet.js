import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function Spreadsheet() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [worksheets, setWorksheets] = useState([]);
  const [selectedWorksheet, setSelectedWorksheet] = useState('');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);

  useEffect(() => {
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      fetchStrategyData();
    }
  }, [selectedStrategy]);

  // Remove this useEffect to prevent infinite loops

  const fetchStrategies = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      console.log('Fetching strategies from:', `${apiUrl}/api/spreadsheet/strategies`);
      
      const response = await fetch(`${apiUrl}/api/spreadsheet/strategies`);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Strategies result:', result);
      
      setStrategies(result.strategies || []);
      setError('');
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setError(`Failed to fetch strategies: ${error.message}`);
      // Set fallback strategies
      setStrategies([
        'DEX_to_DEX_Arbitrage',
        'Cross_Chain_Arbitrage', 
        'Triangular_Arbitrage',
        'Flashloan_Arbitrage',
        'Sandwich_Arbitrage',
        'StableCoin_Arbitrage',
        'Latency_Arbitrage'
      ]);
    }
  };

  const fetchStrategyData = async () => {
    if (!selectedStrategy) return;
    
    setLoading(true);
    setError('');
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${apiUrl}/api/spreadsheet/data/${selectedStrategy}`;
      console.log('Fetching data from:', url);
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Strategy data result:', result);
      
      if (result.status === 'success') {
        const worksheetList = result.worksheets || [];
        const dataObj = result.data || {};
        
        console.log('Worksheets:', worksheetList);
        console.log('Data object:', dataObj);
        
        setWorksheets(worksheetList);
        setData(dataObj);
        
        // Auto-select first worksheet when strategy changes
        if (worksheetList.length > 0 && !selectedWorksheet) {
          const firstWorksheet = worksheetList[0];
          console.log('Auto-selecting worksheet:', firstWorksheet);
          setSelectedWorksheet(firstWorksheet);
        }
        
        setError('');
      } else {
        console.error('API returned error:', result);
        setError(`API Error: ${result.message || 'Unknown error'}`);
        setData({});
        setWorksheets([]);
      }
    } catch (error) {
      console.error('Error fetching strategy data:', error);
      setError(`Failed to fetch data: ${error.message}`);
      setData({});
      setWorksheets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    const direction = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortDirection(direction);
  };

  const handleExport = async (format) => {
    try {
      // Strategy to Google Sheets mapping with correct sheet IDs
      const strategySheets = {
        'DEX_to_DEX_Arbitrage': '1MLkSz43NI7R_-GYkhDvx7fg07cS6A_jF2KJutWs5sV4',
        'Cross_Chain_Arbitrage': '1TcW2S9jnoIRSxyb-vZYJyqP2xVG-wHZhQkQWmVkxcuw',
        'Triangular_Arbitrage': '1KLWtnqwM4AKPyOuEDuQoOZ1rZJGfQZAt4MF-JdgaPiM',
        'Flashloan_Arbitrage': '1qInbTXpO8kfxhJ0k6mc_rmf6-qN7mUGABM6r436212g',
        'Sandwich_Arbitrage': '1dXN3bGNrWHldLGrxuwr5vUS68-jqG2JHauP1kHOxFE0',
        'StableCoin_Arbitrage': '1R7Qa7nLPykDKhEQQF0cypHIp2K90ZtO4CnkijxHBL3s',
        'Latency_Arbitrage': '1fZ_aMLvZI7HFfM-7k1xscxl64NImlnwNDJQvhgLmY_8'
      };

      const sheetId = strategySheets[selectedStrategy];
      if (!sheetId) {
        console.error('No sheet ID found for strategy:', selectedStrategy);
        return;
      }

      let exportUrl;
      let fileName;
      
      if (format === 'csv') {
        // Export as Excel file with all sheets (CSV doesn't support multiple sheets)
        exportUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=xlsx`;
        fileName = `${selectedStrategy}_AllSheets.xlsx`;
      } else {
        // Export as Excel file with all sheets
        exportUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=xlsx`;
        fileName = `${selectedStrategy}_Complete.xlsx`;
      }
      
      // Create download link
      const link = document.createElement('a');
      link.href = exportUrl;
      link.download = fileName;
      link.target = '_blank';
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`Downloading ${selectedStrategy} spreadsheet with all subsheets`);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  // Get current data based on worksheet selection
  const getCurrentData = () => {
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) return [];
    
    if (selectedWorksheet && data[selectedWorksheet]) {
      return Array.isArray(data[selectedWorksheet]) ? data[selectedWorksheet] : [];
    }
    
    // If no specific worksheet selected, combine all data
    const allData = [];
    Object.entries(data).forEach(([sheetName, sheetData]) => {
      if (Array.isArray(sheetData)) {
        sheetData.forEach(row => {
          allData.push({ ...row, _worksheet: sheetName });
        });
      }
    });
    return allData;
  };

  const currentData = getCurrentData();
  
  // Get headers from current data
  const getCurrentHeaders = () => {
    if (currentData.length === 0) return [];
    const headerSet = new Set();
    currentData.forEach(row => {
      Object.keys(row).forEach(key => {
        if (key !== '_worksheet') headerSet.add(key);
      });
    });
    return Array.from(headerSet);
  };
  
  const currentHeaders = getCurrentHeaders();

  // Filter and sort data
  const filteredData = currentData.filter(row =>
    Object.values(row).some(value =>
      value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortField) return 0;
    
    const aVal = a[sortField]?.toString() || '';
    const bVal = b[sortField]?.toString() || '';
    
    if (sortDirection === 'asc') {
      return aVal.localeCompare(bVal);
    } else {
      return bVal.localeCompare(aVal);
    }
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-7xl mx-auto"
        >
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
            <h1 className="text-4xl font-bold text-white mb-8 text-center">
              Strategy Data Viewer
            </h1>

            {/* Strategy Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-white text-sm font-medium mb-2">
                  Select Strategy
                </label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => {
                    const newStrategy = e.target.value;
                    console.log('Strategy selected:', newStrategy);
                    setSelectedStrategy(newStrategy);
                    setSelectedWorksheet('');
                    setCurrentPage(1);
                    setData({});
                    setWorksheets([]);
                    setError('');
                  }}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a strategy...</option>
                  {strategies.map(strategy => (
                    <option key={strategy} value={strategy} className="bg-gray-800">
                      {strategy.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {worksheets.length > 0 && (
                <div>
                  <label className="block text-white text-sm font-medium mb-2">
                    Select Worksheet
                  </label>
                  <select
                    value={selectedWorksheet}
                    onChange={(e) => {
                      setSelectedWorksheet(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="" className="bg-gray-800">All Worksheets</option>
                    {worksheets.map(worksheet => (
                      <option key={worksheet} value={worksheet} className="bg-gray-800">
                        {worksheet.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {selectedStrategy && (
              <>
                {/* Controls */}
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Search data..."
                      value={searchTerm}
                      onChange={(e) => {
                        setSearchTerm(e.target.value);
                        setCurrentPage(1);
                      }}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleExport('xlsx')}
                      className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                      Download Excel
                    </button>
                    <button
                      onClick={fetchStrategyData}
                      className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                    >
                      Refresh
                    </button>
                  </div>
                </div>

                {/* Data Table */}
                {loading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
                    <p className="text-white mt-4">Loading data...</p>
                  </div>
                ) : (
                  <>
                    <div className="overflow-x-auto bg-white/5 rounded-lg border border-white/10">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-white/10">
                            {currentHeaders.map((header, index) => (
                              <th
                                key={header}
                                onClick={() => handleSort(header)}
                                className={`px-4 py-3 text-white font-medium cursor-pointer hover:bg-white/10 transition-colors min-w-[120px] ${
                                  index === 0 ? 'text-left' : 'text-center'
                                }`}
                              >
                                <div className={`flex items-center gap-2 ${
                                  index === 0 ? 'justify-start' : 'justify-center'
                                }`}>
                                  {header.replace(/_/g, ' ')}
                                  {sortField === header && (
                                    <span className="text-blue-400">
                                      {sortDirection === 'asc' ? '↑' : '↓'}
                                    </span>
                                  )}
                                </div>
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {paginatedData.length > 0 ? (
                            paginatedData.map((row, index) => (
                              <tr
                                key={index}
                                className="border-b border-white/5 hover:bg-white/5 transition-colors"
                              >
                                {currentHeaders.map((header, colIndex) => (
                                  <td 
                                    key={header} 
                                    className={`px-4 py-3 text-white/80 min-w-[120px] whitespace-nowrap ${
                                      colIndex === 0 ? 'text-left' : 'text-center'
                                    }`}
                                  >
                                    <div className="truncate max-w-[200px]" title={row[header]?.toString() || '-'}>
                                      {row[header] !== undefined && row[header] !== null && row[header] !== '' ? row[header].toString() : '-'}
                                    </div>
                                  </td>
                                ))}
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={currentHeaders.length} className="px-4 py-8 text-center text-white/60">
                                No data available for this selection
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex justify-center items-center gap-4 mt-6">
                        <button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          className="px-4 py-2 bg-white/10 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-colors"
                        >
                          Previous
                        </button>
                        
                        <span className="text-white">
                          Page {currentPage} of {totalPages} ({sortedData.length} records)
                        </span>
                        
                        <button
                          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                          disabled={currentPage === totalPages}
                          className="px-4 py-2 bg-white/10 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-colors"
                        >
                          Next
                        </button>
                      </div>
                    )}

                    {/* Data Summary */}
                    <div className="mt-6 text-center text-white/60">
                      <p>
                        Showing {paginatedData.length} of {sortedData.length} records
                        {selectedWorksheet && ` from ${selectedWorksheet.replace(/_/g, ' ')} worksheet`}
                      </p>
                    </div>
                  </>
                )}
              </>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
                <div className="text-red-200 font-medium">Error:</div>
                <div className="text-red-100">{error}</div>
              </div>
            )}
            


            {!selectedStrategy && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📊</div>
                <h2 className="text-2xl font-bold text-white mb-4">
                  Select a Strategy to View Data
                </h2>
                <p className="text-white/60">
                  Choose from {strategies.length} available arbitrage strategies to view their spreadsheet data
                </p>
              </div>
            )}
            
            {selectedStrategy && getCurrentData().length === 0 && !loading && (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">⚠️</div>
                <h2 className="text-xl font-bold text-white mb-4">
                  No Data Available
                </h2>
                <p className="text-white/60">
                  No data found for {selectedStrategy.replace(/_/g, ' ')}
                  {selectedWorksheet && ` in worksheet ${selectedWorksheet.replace(/_/g, ' ')}`}
                </p>
                <button
                  onClick={fetchStrategyData}
                  className="mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Retry Loading Data
                </button>
              </div>
            )}
          </div>
        </motion.div>
      </div>
  );
}