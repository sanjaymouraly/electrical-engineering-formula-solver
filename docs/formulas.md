# Formula reference and assumptions

| Calculator | Formula(s) | Key assumptions |
|---|---|---|
| Ohm's law | V=IR; P=VI=I²R=V²/R | Passive resistor, R>0; short circuit (R=0) is not a finite solution |
| Series resistors | R_eq = ΣR | Same current through all |
| Parallel resistors | 1/R_eq = Σ(1/R) | Same voltage across all |
| Voltage divider | V_k = V_s·R_k/ΣR | No external load on the tap unless included as a resistor |
| Current divider | I_k = V/R_k, V=I_tot·R_eq | Parallel branches |
| Single-phase AC | S=VI; P=S·PF; Q=S·sinθ; θ=acos(PF) | RMS; Q>0 lagging (inductive), Q<0 leading |
| Three-phase AC | S=√3·V_L·I_L; P=S·PF; Q=S·sinθ | **Balanced only**; star: V_L=√3·V_ph, I_L=I_ph; Delta: V_L=V_ph, I_L=√3·I_ph |
| PF correction | Qc=P(tanθ₁−tanθ₂); C=Qc/(2πfV²) | Constant P; ideal capacitors; 3-ph capacitor voltage depends on bank connection |
| Voltage drop | DC/1-ph: 2IL(r·cosφ+x·sinφ); 3-ph: √3·IL(r·cosφ+x·sinφ) | One-way length L; r/x per km (or per m); approximate AC model, quadrature term neglected |
| Efficiency | η=P_out/P_in; P_loss=P_in−P_out | η ≤ 100%; efficiency ≠ power factor |
| Motor | P_in as AC above; P_shaft=η·P_in | Nameplate efficiency at the operating point |
| Transformer ratio | Vp/Vs=Np/Ns; VpIp=VsIs | Ideal (lossless) ratio relation |
| Transformer efficiency | η=P_out/(P_out+P_core+x²·P_cu,FL) | Core loss constant; copper loss ∝ (load fraction)² |
| Energy | E(kWh)=P(W)·h·duty/1000; Cost=E·tariff | Flat tariff; month=30 days, year=365 days; Decimal money, ROUND_HALF_UP cents |

References for independent verification: standard electrical technology texts
(e.g. Hughes' *Electrical and Electronic Technology*), manufacturer motor
nameplate conventions (IEC 60034), and the approximate voltage-drop method
found in common wiring-regulation guidance (e.g. BS 7671 Appendix 4 style
mV/A/m method, algebraically equivalent to the r/x form used here).
These calculations are for learning and preliminary analysis only.
