import React, { useMemo, useState } from 'react';
import { View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { CartesianChart, Line } from 'victory-native';
import { ChartContainer } from '../ui/ChartContainer';
import { useTokens } from '../ui/tokens';
import { marketDataService } from '../services/marketData';
import type { Candle } from '../types';
import { Muted } from '../ui/Text';

type Props = { symbol: string; timeframe: '1D' | '1W' | '1M' };

export function ChartDemo({ symbol, timeframe }: Props) {
  const { colors } = useTokens();
  const [chartWidth, setChartWidth] = useState(0);

  const { data: candles = [] } = useQuery({
    queryKey: ['ohlc', symbol, timeframe, 'chart-demo'],
    queryFn: () => marketDataService.getOHLC(symbol, timeframe),
    staleTime: 60_000,
    enabled: Boolean(symbol),
  });

  const chartData: Array<{ date: number; close: number }> = useMemo(() => candles.map((c: Candle) => ({
    date: new Date(c.t).getTime(),
    close: c.c
  })), [candles]);

  return (
    <ChartContainer height={220}>
      <View style={{ flex: 1 }} onLayout={e => setChartWidth(e.nativeEvent.layout.width)}>
        {chartData.length && chartWidth ? (
          <CartesianChart
            data={chartData}
            xKey="date"
            yKeys={["close"] as const}
            padding={{ top: 20, bottom: 36, left: 52, right: 20 }}
            domainPadding={10}
          >
            {({ points, chartBounds, canvasSize }) => (
              <>
                <Line
                  points={points.close}
                  color={colors.tint}
                  strokeWidth={2}
                  curveType="monotoneX"
                />
              </>
            )}
          </CartesianChart>
        ) : (
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
            <Muted>No market data</Muted>
          </View>
        )}
      </View>
    </ChartContainer>
  );
}

export default ChartDemo;
