import { useMemo } from 'react';
import { View, Text, StyleSheet, Linking, Pressable } from 'react-native';
import Constants from 'expo-constants';

const privacyUrl = process.env.EXPO_PUBLIC_PRIVACY_URL ?? 'https://example.com/privacy';
const termsUrl = process.env.EXPO_PUBLIC_TERMS_URL ?? 'https://example.com/terms';
const supportEmail = process.env.EXPO_PUBLIC_SUPPORT_EMAIL ?? 'goblinosrep@gmail.com';

export default function About() {
  const version = useMemo(() => {
    return (
      Constants?.expoConfig?.version || Constants?.expoConfig?.runtimeVersion || '0.0.0'
    );
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Forge Lite</Text>
      <Text style={styles.subtitle}>Version {String(version)}</Text>

      <Text style={styles.sectionTitle}>Stats</Text>
      <Text style={styles.stat}>Now: Independent day trader & freelance developer — building risk management tools, GoblinOS enhancements, and client projects.</Text>
      <Text style={styles.stat}>Next 1-2 years: Deepen my daytrading stack and lay the groundwork for a gold import/export venture while growing my personal brand.</Text>

            <Text style={styles.sectionTitle}>Career Highlights</Text>
            <View style={styles.timelineContainer}>
              <Text style={styles.timelineItem}>2001: Born in Saudi Arabia</Text>
              <Text style={styles.timelineItem}>2018: Moved to USA to complete high school</Text>
              <Text style={styles.timelineItem}>2020: Graduated from North Springs Charter High School</Text>
              <Text style={styles.timelineItem}>2020: Started GSU Finance</Text>
              <Text style={styles.timelineItem}>2022: Started independent trading/freelance work</Text>
              <Text style={styles.timelineItem}>2024: Building ForgeTM Lite and personal portfolio</Text>
            </View>      <Text style={styles.sectionTitle}>Legal</Text>
      <Pressable onPress={() => Linking.openURL(privacyUrl)}>
        <Text style={styles.link}>Privacy Policy</Text>
      </Pressable>
      <Pressable onPress={() => Linking.openURL(termsUrl)}>
        <Text style={styles.link}>Terms of Service</Text>
      </Pressable>

      <Text style={styles.sectionTitle}>Support</Text>
      <Pressable onPress={() => Linking.openURL(`mailto:${supportEmail}`)}>
        <Text style={styles.link}>{supportEmail}</Text>
      </Pressable>

      <Text style={styles.disclaimer}>
        Educational use only. Not investment advice. No execution. Trading involves risk of loss.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    gap: 12,
    justifyContent: 'flex-start',
  },
  title: { fontSize: 28, fontWeight: '700' },
  subtitle: { fontSize: 14, color: '#666' },
  sectionTitle: { marginTop: 16, fontSize: 16, fontWeight: '600' },
  stat: { fontSize: 14, color: '#666', marginBottom: 8 },
  timelineContainer: { marginTop: 8, marginBottom: 8 },
  timelineItem: { fontSize: 14, color: '#666', marginBottom: 6, lineHeight: 20 },
  link: { color: '#2563eb', fontSize: 16 },
  disclaimer: { marginTop: 24, color: '#444' },
});
