"""Analyze V11 Conscious Agent Performance."""
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('backend/data/audit_csv/agent_decisions.csv')

print('=== V11 CONSCIOUS AGENTS PERFORMANCE ===')
print()

# Harmony calculation (Sattva - Tamas)
df['harmony'] = df['guna_sattva'] - df['guna_tamas']

# Agent performance
print('1. AGENT ACTIVITY:')
agent_counts = df['agent_name'].value_counts()
print(agent_counts.head(10))
print()

print('2. HARMONY METRICS:')
print(f'   Average Harmony: {df["harmony"].mean():.3f}')
print(f'   High Harmony (>0.65): {(df["harmony"] > 0.65).sum() / len(df) * 100:.1f}%')
print()

print('3. CONFIDENCE DISTRIBUTION:')
print(f'   High Confidence (>0.7): {(df["confidence"] > 0.7).sum() / len(df) * 100:.1f}%')
print(f'   Avg Confidence: {df["confidence"].mean():.3f}')
print()

print('4. ACTION BREAKDOWN:')
print(df['action'].value_counts())
print()

print('5. ELEMENT PERFORMANCE:')
element_stats = df.groupby('agent_element')['confidence'].agg(['mean', 'count'])
print(element_stats)
print()

print('6. TOP PERFORMING AGENTS (by count & confidence):')
agent_performance = df.groupby('agent_name').agg({
    'confidence': 'mean',
    'harmony': 'mean',
    'timestamp': 'count'
}).rename(columns={'timestamp': 'decisions'})
agent_performance = agent_performance.sort_values('decisions', ascending=False)
print(agent_performance.head(10))
