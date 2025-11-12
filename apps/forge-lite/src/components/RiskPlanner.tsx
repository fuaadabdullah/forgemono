import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { useTheme } from '../theme';
import { api, type RiskCalcRequest } from '../services/api';
import type { RiskCalcParams, RiskCalcResult } from '../types';
import * as Haptics from 'expo-haptics';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

interface RiskPlannerProps {
  onTradePlanned?: (params: RiskCalcParams, result: RiskCalcResult) => void;
  initial?: Partial<FormState>;
}

// Form state uses strings for TextInput compatibility
type FormState = {
  entry: string;
  stop: string;
  equity: string;
  riskPercent: string;
  target: string;
  direction: 'long' | 'short';
};

export function RiskPlanner({ onTradePlanned, initial }: RiskPlannerProps) {
  const { colors } = useTheme();
  const [params, setParams] = useState<FormState>({
    entry: initial?.entry ?? '',
    stop: initial?.stop ?? '',
    equity: initial?.equity ?? '',
    riskPercent: initial?.riskPercent ?? '',
    target: initial?.target ?? '',
    direction: (initial?.direction as any) ?? 'long',
  });
  const [result, setResult] = useState<RiskCalcResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateParam = (key: keyof FormState, value: string) => {
    setParams(prev => ({ ...prev, [key]: value }));
    setError(null);
    setResult(null);
  };

  const calculateRisk = async () => {
    try { await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    // Validate inputs
    const { entry, stop, equity, riskPercent, target, direction } = params;

    if (!entry || !stop || !equity || !riskPercent) {
      try { await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
      Alert.alert('Missing Fields', 'Please fill in entry, stop, equity, and risk percentage.');
      return;
    }

    const entryNum = parseFloat(entry);
    const stopNum = parseFloat(stop);
    const equityNum = parseFloat(equity);
    const riskPctNum = parseFloat(riskPercent) / 100;
    const targetNum = target ? parseFloat(target) : undefined;

    if (isNaN(entryNum) || isNaN(stopNum) || isNaN(equityNum) || isNaN(riskPctNum)) {
      try { await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
      Alert.alert('Invalid Numbers', 'Please enter valid numbers for all fields.');
      return;
    }

    if (direction === 'long' && entryNum <= stopNum) {
      try { await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
      Alert.alert('Invalid Stop', 'For long trades, stop loss must be below entry price.');
      return;
    }

    if (direction === 'short' && entryNum >= stopNum) {
      try { await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
      Alert.alert('Invalid Stop', 'For short trades, stop loss must be above entry price.');
      return;
    }

    if (riskPctNum <= 0 || riskPctNum > 1) {
      try { await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning); } catch {}
      Alert.alert('Invalid Risk', 'Risk percentage must be between 0.01% and 100%.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const apiParams: RiskCalcRequest = {
        entry: entryNum,
        stop: stopNum,
        equity: equityNum,
        risk_pct: riskPctNum,
        target: targetNum,
        direction: direction as 'long' | 'short',
      };

      const apiResponse = await api.risk.calc(apiParams);

      // Convert snake_case API response to camelCase RiskCalcResult
      const calcResult: RiskCalcResult = {
        direction: apiResponse.direction,
        riskPerShare: apiResponse.risk_per_share,
        riskAmount: apiResponse.risk_amount,
        positionSize: apiResponse.position_size,
        rMultipleStop: apiResponse.r_multiple_stop,
        rMultipleTarget: apiResponse.r_multiple_target,
        projectedPnl: apiResponse.projected_pnl,
      };

      setResult(calcResult);

      if (onTradePlanned) {
        // Convert form params to RiskCalcParams for callback
        const riskParams: RiskCalcParams = {
          entry: entryNum,
          stop: stopNum,
          equity: equityNum,
          riskPercent: riskPctNum * 100, // Convert back to percentage
          target: targetNum,
          direction,
        };
        onTradePlanned(riskParams, calcResult);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to calculate risk');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setParams({
      entry: '',
      stop: '',
      equity: '',
      riskPercent: '',
      target: '',
      direction: 'long',
    });
    setResult(null);
    setError(null);
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Risk Calculator</Text>
        <Text style={[styles.subtitle, { color: colors.muted }]}>
          Calculate position size based on your risk tolerance
        </Text>
      </View>

      {/* Direction Toggle */}
      <Card style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Trade Direction</Text>
        <View style={styles.directionContainer}>
          <TouchableOpacity
            style={[
              styles.directionButton,
              params.direction === 'long' && { backgroundColor: colors.tint },
            ]}
            onPress={() => updateParam('direction', 'long')}
          >
            <Text
              style={[
                styles.directionText,
                { color: params.direction === 'long' ? 'white' : colors.text },
              ]}
            >
              Long
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.directionButton,
              params.direction === 'short' && { backgroundColor: colors.tint },
            ]}
            onPress={() => updateParam('direction', 'short')}
          >
            <Text
              style={[
                styles.directionText,
                { color: params.direction === 'short' ? 'white' : colors.text },
              ]}
            >
              Short
            </Text>
          </TouchableOpacity>
        </View>
      </Card>

      {/* Input Fields */}
      <Card style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Trade Parameters</Text>

        <View style={styles.inputRow}>
          <Text style={[styles.inputLabel, { color: colors.text }]}>Entry Price</Text>
          <TextInput
            style={[styles.input, { color: colors.text, borderColor: colors.border }]}
            placeholder="100.00"
            placeholderTextColor={colors.muted}
            value={params.entry}
            onChangeText={(value) => updateParam('entry', value)}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.inputRow}>
          <Text style={[styles.inputLabel, { color: colors.text }]}>Stop Loss</Text>
          <TextInput
            style={[styles.input, { color: colors.text, borderColor: colors.border }]}
            placeholder="95.00"
            placeholderTextColor={colors.muted}
            value={params.stop}
            onChangeText={(value) => updateParam('stop', value)}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.inputRow}>
          <Text style={[styles.inputLabel, { color: colors.text }]}>Target (Optional)</Text>
          <TextInput
            style={[styles.input, { color: colors.text, borderColor: colors.border }]}
            placeholder="110.00"
            placeholderTextColor={colors.muted}
            value={params.target}
            onChangeText={(value) => updateParam('target', value)}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.inputRow}>
          <Text style={[styles.inputLabel, { color: colors.text }]}>Account Equity</Text>
          <TextInput
            style={[styles.input, { color: colors.text, borderColor: colors.border }]}
            placeholder="10000"
            placeholderTextColor={colors.muted}
            value={params.equity}
            onChangeText={(value) => updateParam('equity', value)}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.inputRow}>
          <Text style={[styles.inputLabel, { color: colors.text }]}>Risk %</Text>
          <TextInput
            style={[styles.input, { color: colors.text, borderColor: colors.border }]}
            placeholder="1.0"
            placeholderTextColor={colors.muted}
            value={params.riskPercent}
            onChangeText={(value) => updateParam('riskPercent', value)}
            keyboardType="decimal-pad"
          />
        </View>
      </Card>

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        <Button title={loading ? 'Calculating…' : 'Calculate Position'} onPress={calculateRisk} disabled={loading} loading={loading} />
        <Button title="Reset" variant="ghost" size="sm" onPress={resetForm} style={{ marginTop: 8 }} />
      </View>

      {/* Results */}
      {error && (
        <Card variant="outline" style={styles.resultContainer}>
          <Text style={[styles.errorText, { color: '#dc2626' }]}>{error}</Text>
        </Card>
      )}

      {result && (
        <Card style={styles.resultContainer}>
          <Text style={[styles.resultTitle, { color: colors.text }]}>Position Details</Text>

          <View style={styles.resultRow}>
            <Text style={[styles.resultLabel, { color: colors.muted }]}>Direction:</Text>
            <Text style={[styles.resultValue, { color: colors.text }]}>
              {result.direction.toUpperCase()}
            </Text>
          </View>

          <View style={styles.resultRow}>
            <Text style={[styles.resultLabel, { color: colors.muted }]}>Risk per Share:</Text>
            <Text style={[styles.resultValue, { color: colors.text }]}>
              ${result.riskPerShare.toFixed(2)}
            </Text>
          </View>

          <View style={styles.resultRow}>
            <Text style={[styles.resultLabel, { color: colors.muted }]}>Risk Amount:</Text>
            <Text style={[styles.resultValue, { color: colors.text }]}>
              ${result.riskAmount.toFixed(2)}
            </Text>
          </View>

          <View style={styles.resultRow}>
            <Text style={[styles.resultLabel, { color: colors.muted }]}>Position Size:</Text>
            <Text style={[styles.resultValue, { color: '#30D158', fontWeight: '600' }]}> 
              {result.positionSize.toFixed(0)} shares
            </Text>
          </View>

          <View style={styles.resultRow}>
            <Text style={[styles.resultLabel, { color: colors.muted }]}>R Multiple (Stop):</Text>
            <Text style={[styles.resultValue, { color: colors.text }]}>
              {result.rMultipleStop.toFixed(2)}R
            </Text>
          </View>

          {result.rMultipleTarget && (
            <View style={styles.resultRow}>
              <Text style={[styles.resultLabel, { color: colors.muted }]}>R Multiple (Target):</Text>
              <Text style={[styles.resultValue, { color: '#30D158' }]}> 
                {result.rMultipleTarget.toFixed(2)}R
              </Text>
            </View>
          )}

          {result.projectedPnl && (
            <View style={styles.resultRow}>
              <Text style={[styles.resultLabel, { color: colors.muted }]}>Projected P&L:</Text>
              <Text style={[styles.resultValue, { color: result.projectedPnl >= 0 ? '#30D158' : '#FF3B30' }]}> 
                ${result.projectedPnl.toFixed(2)}
              </Text>
            </View>
          )}
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 24,
  },
  section: {
    margin: 16,
    marginTop: 0,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  directionContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  directionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  directionText: {
    fontSize: 16,
    fontWeight: '600',
  },
  inputRow: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  buttonContainer: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  calculateButton: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  calculateButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  resetButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
  },
  resetButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  resetLink: {
    textAlign: 'center',
    fontSize: 14,
    marginTop: 8,
  },
  resultContainer: {
    margin: 16,
    marginTop: 0,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  resultLabel: {
    fontSize: 16,
  },
  resultValue: {
    fontSize: 16,
    fontWeight: '500',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
});
