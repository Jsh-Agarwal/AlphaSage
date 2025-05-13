import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Layout from "@/components/layout/Layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, PieChart, TrendingUp, FileText, DollarSign, BarChart4, Building, Users, FileOutput } from "lucide-react";
import { 
  LineChart as RechartsLineChart, 
  AreaChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend,
  Bar,
  BarChart
} from 'recharts';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchStockReport, generateStockPDF } from "@/lib/pdfUtils";
import { useToast } from "@/components/ui/use-toast";

// API base URL
const API_BASE_URL = 'http://localhost:9000'; // Using port 9000 for the main ETL pipeline server

// Add these utility functions to handle currency formatting
const formatCurrency = (value: number, isIndian = false) => {
  if (isIndian) {
    // Format as Indian currency (₹) in crores
    return `₹${value.toLocaleString('en-IN')} Cr`;
  } else {
    // Format as US currency ($) in millions
    return `$${value.toLocaleString('en-US')} M`;
  }
};

const formatValue = (value: number, isIndian = false) => {
  return value.toLocaleString(isIndian ? 'en-IN' : 'en-US');
};

const StockDetail = () => {
  const { symbol: urlSymbol } = useParams();
  const [inputValue, setInputValue] = useState(""); // For tracking input without triggering API calls
  const [stockSymbol, setStockSymbol] = useState(urlSymbol || "AAPL"); // Default to Apple as a popular US stock
  const [timeDuration, setTimeDuration] = useState("1d");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();

  // Determine if it's an Indian or American stock
  const isIndianStock = stockSymbol.endsWith('.NS') || stockSymbol.endsWith('.BO') || stockSymbol.endsWith('.BSE');

  // Effect to update stock symbol when URL changes
  useEffect(() => {
    if (urlSymbol) {
      setStockSymbol(urlSymbol);
      setInputValue(urlSymbol);
    }
  }, [urlSymbol]);

  // Fetch valuation ratios
  const { data: valuationData, isLoading: valuationLoading, error: valuationError, refetch: refetchValuation } = useQuery({
    queryKey: ['valuation', stockSymbol, timeDuration],
    queryFn: async () => {
      setIsLoading(true);
      setError(null);
      try {
        console.log('Fetching valuation data for:', stockSymbol);
        const response = await fetch(`${API_BASE_URL}/valuation_ratios`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            company: stockSymbol,
            duration: timeDuration
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch valuation ratios');
        }

        return response.json();
      } catch (error) {
        setError(error instanceof Error ? error.message : 'An error occurred');
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    enabled: !!stockSymbol && !!timeDuration,
  });

  // Fetch company overview
  const { data: overviewData, isLoading: overviewLoading, refetch: refetchOverview } = useQuery({
    queryKey: ['overview', stockSymbol],
    queryFn: async () => {
      console.log('Fetching overview for:', stockSymbol);
      const response = await fetch(`${API_BASE_URL}/company_overview/${stockSymbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch company overview');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Fetch peer comparison
  const { data: peerData, isLoading: peerLoading, refetch: refetchPeers } = useQuery({
    queryKey: ['peers', stockSymbol],
    queryFn: async () => {
      console.log('Fetching peers for:', stockSymbol);
      const response = await fetch(`${API_BASE_URL}/peer_comparison/${stockSymbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch peer comparison');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Fetch quarterly results
  const { data: quarterlyData, isLoading: quarterlyLoading, refetch: refetchQuarterly } = useQuery({
    queryKey: ['quarterly', stockSymbol],
    queryFn: async () => {
      console.log('Fetching quarterly data for:', stockSymbol);
      const response = await fetch(`${API_BASE_URL}/quarterly_results/${stockSymbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch quarterly results');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Fetch shareholding pattern
  const { data: shareholdingData, isLoading: shareholdingLoading, refetch: refetchShareholding } = useQuery({
    queryKey: ['shareholding', stockSymbol],
    queryFn: async () => {
      console.log('Fetching shareholding for:', stockSymbol);
      const response = await fetch(`${API_BASE_URL}/shareholding_pattern/${stockSymbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch shareholding pattern');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Fetch cash flow data
  const { data: cashFlowData, isLoading: cashFlowLoading, refetch: refetchCashFlow } = useQuery({
    queryKey: ['cashflow', stockSymbol],
    queryFn: async () => {
      console.log('Fetching cash flow for:', stockSymbol);
      const response = await fetch(`${API_BASE_URL}/cash_flow/${stockSymbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch cash flow data');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Fetch balance sheet data
  const { data: balanceSheetData, isLoading: balanceSheetLoading, refetch: refetchBalanceSheet } = useQuery({
    queryKey: ['balancesheet', stockSymbol],
    queryFn: async () => {
      console.log('Fetching balance sheet for:', stockSymbol);
      const response = await fetch(`${API_BASE_URL}/balance_sheet/${stockSymbol}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch balance sheet data');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Fetch stock price data
  const { data: priceData, isLoading: priceLoading, refetch: refetchPrice } = useQuery({
    queryKey: ['price', stockSymbol, timeDuration],
    queryFn: async () => {
      console.log('Fetching price data for:', stockSymbol, 'duration:', timeDuration);
      const response = await fetch(`${API_BASE_URL}/stock_price/${stockSymbol}?duration=${timeDuration}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch stock price data');
      }
      return response.json();
    },
    enabled: !!stockSymbol,
  });

  // Handle search submission
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Searching for stock:', inputValue);
    setStockSymbol(inputValue.toUpperCase());
    
    // Refetch all data with the new symbol
    refetchValuation();
    refetchOverview();
    refetchPeers();
    refetchQuarterly();
    refetchShareholding();
    refetchCashFlow();
    refetchBalanceSheet();
    refetchPrice();
  };

  // Create a debounced search function with a delay
  const debouncedSearch = useCallback(
    (value: string) => {
      const timer = setTimeout(() => {
        if (value.length >= 2) { // Only search if at least 2 characters are typed
          setStockSymbol(value.toUpperCase());
        }
      }, 1000); // 1 second delay

      return () => {
        clearTimeout(timer); // Clear the timeout if the component unmounts or value changes
      };
    },
    [] // No dependencies needed
  );

  // Effect to handle input changes for search
  useEffect(() => {
    // No-op for empty string
    if (!inputValue) return;
    
    // Call debounced search and get the cleanup function
    const cleanup = debouncedSearch(inputValue);
    
    // Return cleanup function to clear timeout when inputValue changes
    return cleanup;
  }, [inputValue, debouncedSearch]);

  // Export Stock Report to PDF
  const handleExportReport = async () => {
    try {
      setIsExporting(true);
      toast({
        title: "Generating report",
        description: "Please wait while we generate a comprehensive stock analysis report...",
      });

      // Fetch stock report data
      const reportData = await fetchStockReport(stockSymbol);
      
      if (!reportData) {
        throw new Error('Failed to fetch report data');
      }
      
      // Generate PDF with the report data
      await generateStockPDF(reportData);
      
      toast({
        title: "Report generated successfully",
        description: "Your stock analysis report has been downloaded.",
        variant: "success"
      });
    } catch (error) {
      console.error('Error exporting report:', error);
      toast({
        title: "Error generating report",
        description: "Failed to generate the stock report. Please try again later.",
        variant: "destructive"
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Calculate percentage change
  const latestPrice = priceData?.[priceData.length - 1]?.value;
  const previousPrice = priceData?.[priceData.length - 2]?.value;
  const percentageChange = latestPrice && previousPrice
    ? (((latestPrice - previousPrice) / previousPrice) * 100).toFixed(2)
    : '0.00';

  // Check if all main data is loading
  const isAllLoading = valuationLoading || overviewLoading || priceLoading;

  // Loading states
  if (isAllLoading) {
    return (
      <Layout>
        <div className="container py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-lg">Loading stock data...</div>
          </div>
        </div>
      </Layout>
    );
  }

  // Error states
  if (error || valuationError) {
    return (
      <Layout>
        <div className="container py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-red-500">
              {error || valuationError instanceof Error ? (valuationError as Error).message : 'Error loading data. Please try again.'}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  // Get current ratios from valuation data
  const currentRatios = valuationData?.current_ratios || {
    volume: 'N/A',
    currentPrice: 'N/A',
    highLow: 'N/A',
    stockPE: 'N/A',
    evbyrevenue: 'N/A',
    roa: 'N/A',
    evbyebita: 'N/A',
    roe: 'N/A',
    grossmargin: 'N/A'
  };

  return (
    <Layout>
      <div className="container py-8 space-y-6">
        {/* Search Bar and Time Duration */}
        <form onSubmit={handleSearch} className="flex gap-4 mb-6">
          <Input
            type="text"
            placeholder="Enter stock symbol (e.g., AAPL, MSFT, RELIANCE.NS)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.toUpperCase())}
            className="w-full max-w-sm"
          />
          <Select value={timeDuration} onValueChange={setTimeDuration}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select duration" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">1 Day</SelectItem>
              <SelectItem value="7d">7 Days</SelectItem>
              <SelectItem value="1mo">1 Month</SelectItem>
              <SelectItem value="6mo">6 Months</SelectItem>
              <SelectItem value="1y">1 Year</SelectItem>
              <SelectItem value="5y">5 Years</SelectItem>
            </SelectContent>
          </Select>
          <Button type="submit">
            {isLoading ? 'Searching...' : 'Search'}
          </Button>
        </form>

        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold">{stockSymbol}</h1>
              <span className="px-2 py-0.5 bg-primary/10 text-primary rounded-full text-sm">
                {overviewData?.name || stockSymbol}
              </span>
              <span className="px-2 py-0.5 bg-gray-100 text-gray-800 rounded-full text-sm">
                {overviewData?.exchange || '-'}
              </span>
            </div>
            <div className="flex items-center gap-4 mt-2">
              <span className="text-2xl font-medium">{currentRatios.currentPrice}</span>
              <span className={`flex items-center gap-1 ${parseFloat(percentageChange) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                <TrendingUp size={16} />
                {percentageChange}%
              </span>
            </div>
          </div>
          <div className="flex gap-3">
            <Button 
              onClick={handleExportReport} 
              disabled={isExporting}
              className="flex items-center gap-2"
            >
              {isExporting ? "Generating..." : "Export Report"}
              <FileOutput size={16} />
            </Button>
          </div>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid grid-cols-7 w-full max-w-4xl">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="peers">Peers</TabsTrigger>
            <TabsTrigger value="quarterly">Quarterly</TabsTrigger>
            <TabsTrigger value="shareholding">Shareholding</TabsTrigger>
            <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
            <TabsTrigger value="balancesheet">Balance Sheet</TabsTrigger>
            <TabsTrigger value="chart">Performance</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building size={18} />
                  Company Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">
                        {overviewData?.exchange || '-'}: {stockSymbol}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Volume</p>
                        <p className="text-lg font-medium">{currentRatios.volume}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Current Price</p>
                        <p className="text-lg font-medium">{currentRatios.currentPrice}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">High / Low</p>
                        <p className="text-lg font-medium">{currentRatios.highLow}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Stock P/E</p>
                        <p className="text-lg font-medium">{currentRatios.stockPE}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">EV/Revenue</p>
                        <p className="text-lg font-medium">{currentRatios.evbyrevenue}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">ROA</p>
                        <p className="text-lg font-medium">{currentRatios.roa}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">EV/EBITA</p>
                        <p className="text-lg font-medium">{currentRatios.evbyebita}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">ROE</p>
                        <p className="text-lg font-medium">{currentRatios.roe}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Gross Margin</p>
                        <p className="text-lg font-medium">{currentRatios.grossmargin}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="bg-muted p-4 rounded-lg">
                      <h3 className="text-lg font-semibold mb-2">ABOUT</h3>
                      <p className="text-muted-foreground">
                        {overviewData?.description || "No description available."}
                      </p>
                      <h3 className="text-lg font-semibold mt-4 mb-2">KEY POINTS</h3>
                      <p className="text-muted-foreground">
                        <strong>{overviewData?.sector || "N/A"}</strong><br />
                        {overviewData?.industry || "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Peers Tab */}
          <TabsContent value="peers" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users size={18} />
                  Peer Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="p-2">Name</th>
                        <th className="p-2">CMP Rs.</th>
                        <th className="p-2">P/E</th>
                        <th className="p-2">Div Yield %</th>
                        <th className="p-2">NP Qt</th>
                        <th className="p-2">Qtr Profit Var %</th>
                        <th className="p-2">Sales Qt</th>
                        <th className="p-2">Qtr Sales Var %</th>
                        <th className="p-2">ROCE %</th>
                        <th className="p-2">EV/EBITDA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {peerData?.map((peer, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-2">{peer.name}</td>
                          <td className="p-2">{peer.cmp.toFixed(2)}</td>
                          <td className="p-2">{peer.pe.toFixed(2)}</td>
                          <td className="p-2">{peer.divYield.toFixed(2)}</td>
                          <td className="p-2">{peer.npQt.toFixed(2)}</td>
                          <td className="p-2">{peer.qtrProfitVar.toFixed(2)}</td>
                          <td className="p-2">{peer.salesQt.toFixed(2)}</td>
                          <td className="p-2">{peer.qtrSalesVar.toFixed(2)}</td>
                          <td className="p-2">{peer.roce.toFixed(2)}</td>
                          <td className="p-2">{peer.evEbitda.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="h-[300px] mt-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={peerData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="cmp" fill="#8884d8" name="CMP" />
                      <Bar dataKey="roce" fill="#82ca9d" name="ROCE" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Quarterly Results Tab */}
          <TabsContent value="quarterly" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart4 size={18} />
                  Quarterly Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="p-2">Quarter</th>
                        <th className="p-2">Sales</th>
                        <th className="p-2">Expenses</th>
                        <th className="p-2">Profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quarterlyData?.map((data, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-2">{data.quarter}</td>
                          <td className="p-2">{data.sales.toLocaleString()}</td>
                          <td className="p-2">{data.expenses.toLocaleString()}</td>
                          <td className="p-2">{data.profit.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="h-[300px] mt-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={quarterlyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="quarter" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="sales" fill="#8884d8" name="Sales" />
                      <Bar dataKey="profit" fill="#82ca9d" name="Profit" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Shareholding Pattern Tab */}
          <TabsContent value="shareholding" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users size={18} />
                  Shareholding Pattern
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="p-2">Date</th>
                        <th className="p-2">Promoters %</th>
                        <th className="p-2">FIIs %</th>
                        <th className="p-2">DIIs %</th>
                        <th className="p-2">Government %</th>
                        <th className="p-2">Public %</th>
                        <th className="p-2">No. of Shareholders</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shareholdingData?.map((data, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-2">{data.date}</td>
                          <td className="p-2">{data.promoters.toFixed(2)}</td>
                          <td className="p-2">{data.fils.toFixed(2)}</td>
                          <td className="p-2">{data.dils.toFixed(2)}</td>
                          <td className="p-2">{data.government.toFixed(2)}</td>
                          <td className="p-2">{data.public.toFixed(2)}</td>
                          <td className="p-2">{data.shareholders.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="h-[300px] mt-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={shareholdingData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="promoters" fill="#8884d8" name="Promoters" />
                      <Bar dataKey="fils" fill="#82ca9d" name="FIIs" />
                      <Bar dataKey="dils" fill="#ffc658" name="DIIs" />
                      <Bar dataKey="public" fill="#ff7300" name="Public" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cash Flow Tab */}
          <TabsContent value="cashflow" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign size={18} />
                  Cash Flows
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="p-2">Year</th>
                        <th className="p-2">Operating {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                        <th className="p-2">Investing {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                        <th className="p-2">Financing {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                        <th className="p-2">Net {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cashFlowData?.map((data, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-2">{data.year}</td>
                          <td className="p-2">{formatValue(data.operating, isIndianStock)}</td>
                          <td className="p-2">{formatValue(data.investing, isIndianStock)}</td>
                          <td className="p-2">{formatValue(data.financing, isIndianStock)}</td>
                          <td className="p-2">{formatValue(data.net, isIndianStock)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="h-[300px] mt-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={cashFlowData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="operating" fill="#8884d8" name="Operating" />
                      <Bar dataKey="investing" fill="#82ca9d" name="Investing" />
                      <Bar dataKey="financing" fill="#ffc658" name="Financing" />
                      <Bar dataKey="net" fill="#ff7300" name="Net" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Balance Sheet Tab */}
          <TabsContent value="balancesheet" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText size={18} />
                  Balance Sheet
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="p-2">Year</th>
                        <th className="p-2">Equity {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                        <th className="p-2">Reserves {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                        <th className="p-2">Borrowings {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                        <th className="p-2">Fixed Assets {isIndianStock ? "(₹ Cr)" : "($ M)"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {balanceSheetData?.map((data, index) => (
                        <tr key={index} className="border-t">
                          <td className="p-2">{data.year}</td>
                          <td className="p-2">{formatValue(data.equity, isIndianStock)}</td>
                          <td className="p-2">{formatValue(data.reserves, isIndianStock)}</td>
                          <td className="p-2">{formatValue(data.borrowings, isIndianStock)}</td>
                          <td className="p-2">{formatValue(data.fixedAssets, isIndianStock)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="h-[300px] mt-6">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={balanceSheetData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="equity" fill="#8884d8" name="Equity" />
                      <Bar dataKey="reserves" fill="#82ca9d" name="Reserves" />
                      <Bar dataKey="borrowings" fill="#ffc658" name="Borrowings" />
                      <Bar dataKey="fixedAssets" fill="#ff7300" name="Fixed Assets" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Chart Tab */}
          <TabsContent value="chart" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart size={18} />
                  Stock Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={priceData}>
                      <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                          <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" />
                      <YAxis />
                      <CartesianGrid strokeDasharray="3 3" />
                      <Tooltip />
                      <Area type="monotone" dataKey="value" stroke="#8884d8" fillOpacity={1} fill="url(#colorValue)" />
                      <Line type="monotone" dataKey="value" stroke="#8884d8" dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default StockDetail;