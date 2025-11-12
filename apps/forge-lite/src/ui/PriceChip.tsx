import React, { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, Text, View } from 'react-native';
import { useTokens } from './tokens';

type Props = {
  price: number;
  change: number; // absolute change
  changePercent: number; // percent change
};

export function PriceChip({ price, change, changePercent }: Props) {
  const { colors, radius } = useTokens();
  const isUp = change >= 0;
  const flash = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // flash on update
    flash.setValue(0.6);
    Animated.timing(flash, {
      toValue: 0,
      duration: 550,
      easing: Easing.out(Easing.quad),
      useNativeDriver: true,
    }).start();
  }, [price, change, changePercent]);

  return (
    <View style={[styles.container, { borderRadius: radius.pill, borderColor: colors.border }]}> 
      <Animated.View
        pointerEvents="none"
        style={[
          StyleSheet.absoluteFillObject,
          {
            backgroundColor: isUp ? '#30D158' : '#FF3B30',
            opacity: flash,
            borderRadius: radius.pill,
          },
        ]}
      />
      <Text style={[styles.price, { color: colors.text }]}>${price.toFixed(2)}</Text>
      <Text style={[styles.delta, { color: isUp ? '#30D158' : '#FF3B30' }]}>
        {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{change.toFixed(2)} ({isUp ? '+' : ''}{changePercent.toFixed(2)}%)
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  price: {
    fontWeight: '600',
    marginRight: 8,
  },
  delta: {
    fontSize: 12,
    fontWeight: '600',
  },
});

export default PriceChip;

