export interface Crypto {
  id?: number
  symbol: string
  name: string
  logo?: string
  price: number
  change24h?: number
  changePercent24h: number
  volume24h: number
  marketCap: number
  high24h: number
  low24h: number
  lastUpdate: Date | string
  indicators?: TechnicalIndicators
}

export interface TechnicalIndicators {
  rsi?: number
  macd?: {
    value: number
    signal: number
    histogram: number
  }
  bollingerBands?: {
    upper: number
    middle: number
    lower: number
  }
  ma?: {
    sma20?: number
    sma50?: number
    ema12?: number
    ema26?: number
  }
}

export interface PriceHistory {
  timestamp: number | Date
  open: number
  high: number
  low: number
  close: number
  volume: number
  price?: number
}

export interface MarketData {
  crypto: Crypto
  history: PriceHistory[]
}

export interface ApiCrypto {
  id: number
  symbol: string
  name: string
  logo: string
}

export interface ApiMarketData {
  symbol: string
  name: string
  currentPrice: number
  change24h: number
  volume24h: number
  high24h: number
  low24h: number
  marketCap: number
  lastUpdate: string
  indicators?: TechnicalIndicators
}

