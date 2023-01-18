# Expected outputs for the worked examples (independently derived)

| Scenario | Inputs | Expected |
|---|---|---|
| Heater (Ohm) | 230 V, 46 Ω | I = 230/46 = **5 A**; P = 230×5 = **1150 W** |
| Single-phase AC | 230 V, 10 A, PF 0.8 lagging | S = **2300 VA**; P = **1840 W**; Q = **+1380 VAR**; θ = 36.87° |
| Three-phase motor supply | 415 V (line), 20 A (line), PF 0.85, star | S = √3·415·20 = **14 376 VA**; P = **12 220 W**; Q ≈ **7573 VAR**; V_ph = 415/√3 = **239.6 V** |
| PF correction | 10 kW, PF 0.75→0.95, 230 V, 50 Hz, 1-ph | Qc = 10 000·(tan acos .75 − tan acos .95) ≈ **5537 VAR**; C ≈ **333 µF** |
| Voltage drop (1-ph) | 230 V, 20 A, 50 m, 1.2 Ω/km, PF 1 | Vd = 2·20·1.2·0.05 = **2.4 V (1.043%)**; V_recv = **227.6 V** |
| Energy | 1500 W, 8 h/day, 30 days, $0.15/kWh | **360 kWh**, **$54.00** |
| Efficiency | 1000 W in, 850 W out | **85%**, losses **150 W** |
| Transformer ratio | 415 V → 110 V (ideal ratio) | ratio **3.7727** |
| Series resistors | 10+20+30 Ω | **60 Ω** |
| Parallel resistors | 10 ∥ 20 ∥ 30 Ω | 1/(0.1+0.05+0.0333) = **5.4545 Ω** |
