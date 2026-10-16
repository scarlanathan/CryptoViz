'use client'

import { useEffect, useRef, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import 'chartjs-adapter-date-fns'
import { fr } from 'date-fns/locale'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PriceHistory } from '@/types/crypto'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Tooltip,
  Legend,
  Filler
)

interface CryptoChartProps {
  symbol: string
  name: string
  currentPrice: number
  changePercent: number
  history: PriceHistory[]
}

export function CryptoChart({ symbol, name, currentPrice, changePercent, history }: CryptoChartProps) {
  const chartRef = useRef<ChartJS<'line'>>(null)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  // Mettre à jour le graphique quand l'historique ou le prix change
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.update('none') // 'none' pour mise à jour sans animation
    }
  }, [history, currentPrice])

  const data = {
    labels: history.map(h => h.timestamp),
    datasets: [
      {
        label: `${symbol} Prix`,
        data: history.map(h => h.price || h.close),
        borderColor: changePercent >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
        backgroundColor: changePercent >= 0 
          ? 'rgba(34, 197, 94, 0.2)' 
          : 'rgba(239, 68, 68, 0.2)',
        borderWidth: 3,
        fill: true,
        tension: 0.3,
        pointRadius: 1,
        pointBackgroundColor: changePercent >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
        pointHoverRadius: 8,
        pointHoverBackgroundColor: 'white',
        pointHoverBorderWidth: 3,
        pointHoverBorderColor: changePercent >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
      },
    ],
  }

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(59, 130, 246, 0.5)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: false,
        padding: 12,
        callbacks: {
          title: (context) => {
            const xValue = context[0].parsed.x;
            const date = xValue != null ? new Date(xValue) : null;
            return date ? date.toLocaleString('fr-FR', {
              day: '2-digit',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
<<<<<<< HEAD
=======
              second: '2-digit',
>>>>>>> e19921cc2dae995eb4dc9466228d616898f2749d
            }) : "" ;
          },
          label: (context) => {
            const value = context.parsed.y
            return value != null
              ? `Prix: $${value.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}`
              : ''
          },
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'minute',
          displayFormats: {
            minute: 'HH:mm:ss',
            hour: 'HH:mm',
            day: 'dd MMM',
          },
          tooltipFormat: 'dd MMM HH:mm:ss',
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.7)',
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 6,
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
      },
      y: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.7)',
          callback: function(value) {
            return `$${Number(value).toLocaleString('en-US', { 
              minimumFractionDigits: 0,
              maximumFractionDigits: 0 
            })}`
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          // drawBorder: false,
        },
      },
    },
  }

  const isPositive = changePercent >= 0

  return (
    <Card className="hover:border-white/30 transition-all duration-300">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl">{symbol}</CardTitle>
            <p className="text-sm text-gray-400 mt-1">{name}</p>
          </div>
          <div className="text-right">
            <div 
              key={currentPrice}
              className="text-2xl font-mono font-bold"
              style={{
                animation: 'priceChange 0.4s ease-in-out',
                color: isPositive ? '#22c55e' : '#ef4444'
              }}
            >
              ${currentPrice.toLocaleString('en-US', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2 
              })}
            </div>
            <div className={`text-sm font-medium mt-1 ${
              isPositive ? 'text-green-400' : 'text-red-400'
            }`}>
              {isPositive ? '↗' : '↘'} {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          {isClient && <Line ref={chartRef} data={data} options={options} />}
        </div>
      </CardContent>
    </Card>
  )
}

