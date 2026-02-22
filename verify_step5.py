#!/usr/bin/env python3
"""STAP 5: Elementaire Agents Check"""

import os
import asyncio
os.environ['TRADING_MODE'] = 'paper'

print('='*60)
print('STAP 5: Elementaire Agents Check')
print('='*60)

from backend.agents.elemental_orchestrator import ElementalOrchestrator
from backend.agents.elemental_research import ElementalResearch
from backend.agents.elemental_risk_guardian import ElementalRiskGuardian
from backend.agents.elemental_macro import ElementalMacro
from backend.agents.elemental_valuation import ElementalValuation

# Initializeer alle agents
agents = {
    'ether': ElementalOrchestrator(),
    'air': ElementalResearch(),
    'fire': ElementalRiskGuardian(),
    'water': ElementalMacro(),
    'earth': ElementalValuation(),
}

print('\n1. PRANA CHECK (>= 80 vereist):')
all_prana_ok = True
for name, agent in agents.items():
    status = 'OK' if agent.prana >= 80 else 'FAIL'
    if agent.prana < 80:
        all_prana_ok = False
    print(f'   [{status}] {name:8}: prana={agent.prana:.1f} (min: 80)')

print('\n2. TATTVA LAYER VERIFICATIE:')
expected_tattvas = {'ether': 32, 'air': 33, 'fire': 34, 'water': 35, 'earth': 36}
all_tattva_ok = True
for name, agent in agents.items():
    expected = expected_tattvas[name]
    status = 'OK' if agent.tattva_layer == expected else 'FAIL'
    if agent.tattva_layer != expected:
        all_tattva_ok = False
    print(f'   [{status}] {name:8}: tattva={agent.tattva_layer} (expected: {expected})')

print('\n3. GUNA BALANS VERIFICATIE:')
for name, agent in agents.items():
    guna = agent.guna_balance
    total = sum(guna.values())
    status = 'OK' if abs(total - 1.0) < 0.01 else 'FAIL'
    dominant = agent.get_dominant_guna()
    sattva = guna['sattva']
    rajas = guna['rajas']
    tamas = guna['tamas']
    print(f'   [{status}] {name:8}: sattva={sattva:.1f}, rajas={rajas:.1f}, tamas={tamas:.1f} | dominant: {dominant}')

print('\n4. HARMONY SCORE BEREKENING TEST:')
async def test_harmony():
    orchestrator = agents['ether']
    inputs = {
        'air': {'signal': 0.7, 'confidence': 0.8},
        'fire': {'signal': 0.6, 'confidence': 0.9},
        'water': {'signal': 0.5, 'confidence': 0.7},
        'earth': {'signal': 0.8, 'confidence': 0.75},
    }
    
    result = await orchestrator.process_signal({
        'inputs': inputs,
        'soul_context': {'market_regime': 'expansion'}
    })
    
    harmony = result.get('harmony_score', 0)
    print(f'   Harmony Score: {harmony:.2f}')
    
    if harmony < 0.2:
        print('   WARNING: Harmony < 0.2 - trading zou gestopt moeten zijn')
    else:
        print('   OK: Harmony > 0.2 - trading toegestaan')
    
    return harmony

harmony = asyncio.run(test_harmony())

print('\n5. PRANA DECAY TEST:')
async def test_prana_decay():
    agent = agents['fire']
    initial_prana = agent.prana
    
    # Consume prana
    success = await agent.consume_prana()
    new_prana = agent.prana
    
    print(f'   Initial prana: {initial_prana:.1f}')
    print(f'   After consume: {new_prana:.1f}')
    print(f'   Decay rate: {initial_prana - new_prana:.1f}')
    print(f'   [OK] Prana consumption working' if success else '   [FAIL] Prana consumption failed')

asyncio.run(test_prana_decay())

print('\n' + '='*60)
if all_prana_ok and all_tattva_ok:
    print('STAP 5: ALLE CHECKS SUCCESSVOL')
else:
    print('STAP 5: ER ZIJN FAILURES')
print('='*60)
