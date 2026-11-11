"""
Figure generator for the Ultrasound M-mode Wall-Tracking project.

This is a faithful Python port of `mmode_wall_tracking.m` used to render the
portfolio figures (MATLAB is the primary implementation). Same processing chain:
simulate pulse-echo RF from two pulsating arterial walls -> Hilbert envelope ->
log-compressed M-mode -> peak-based wall tracking -> distension waveform.

    python make_figures.py   ->   figures/*.png
"""
import os
import numpy as np
from scipy.signal import hilbert, find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")

# acquisition parameters
c, fs, f0 = 1540.0, 40e6, 5e6
depth, prf, T = 20e-3, 500.0, 4.0
Nfast = round(2 * depth / c * fs)
Nslow = round(T * prf)
z = np.arange(Nfast) / fs * c / 2
tslow = np.arange(Nslow) / prf

# physiological wall motion
hr, d0, diam0 = 72 / 60.0, 6e-3, 6e-3
puls = 0.35e-3 * np.clip(np.sin(2 * np.pi * hr * tslow), 0, None) ** 1.5
d_ant = d0 - 0.5 * puls
d_post = d0 + diam0 + 0.5 * puls

# synthesize RF frames
rng = np.random.default_rng(0)
sigma = 1.5 / f0
tt = (np.arange(Nfast) / fs)[:, None]
rf = np.zeros((Nfast, Nslow))
for dwall in (d_ant, d_post):
    tau = 2 * dwall / c
    arg = tt - tau[None, :]
    rf += np.exp(-0.5 * (arg / sigma) ** 2) * np.cos(2 * np.pi * f0 * arg)
rf += 0.05 * rng.standard_normal(rf.shape)

# envelope + log compression
env = np.abs(hilbert(rf, axis=0))
mmode = 20 * np.log10(env / env.max() + 1e-3)

# wall tracking
min_dist = int(2e-3 / (c / 2) * fs)
ant = np.zeros(Nslow)
post = np.zeros(Nslow)
for k in range(Nslow):
    pk, props = find_peaks(env[:, k], distance=min_dist)
    top2 = np.sort(pk[np.argsort(env[pk, k])[-2:]])
    ant[k], post[k] = z[top2[0]], z[top2[1]]
diameter = post - ant

os.makedirs(FIG, exist_ok=True)

# figure 1: single RF A-line + envelope
k0 = int(0.25 * Nslow)
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(z * 1e3, rf[:, k0], color="#94a3b8", lw=0.8, label="RF echo")
ax.plot(z * 1e3, env[:, k0], color="#dc2626", lw=1.6, label="envelope (Hilbert)")
ax.set_xlabel("depth [mm]"); ax.set_ylabel("amplitude")
ax.set_title("Pulse-echo A-line: RF signal and detected envelope")
ax.legend(); fig.tight_layout()
fig.savefig(os.path.join(FIG, "rf_aline_envelope.png"), dpi=140); plt.close(fig)

# figure 2: M-mode with tracked walls
fig, ax = plt.subplots(figsize=(9, 4.2))
im = ax.imshow(mmode, aspect="auto", cmap="gray", vmin=-40, vmax=0,
               extent=[tslow[0], tslow[-1], z[-1] * 1e3, z[0] * 1e3])
ax.plot(tslow, ant * 1e3, color="#22d3ee", lw=1.3, label="anterior wall")
ax.plot(tslow, post * 1e3, color="#facc15", lw=1.3, label="posterior wall")
ax.set_xlabel("slow-time [s]"); ax.set_ylabel("depth [mm]")
ax.set_title("M-mode image with tracked arterial walls")
ax.legend(loc="upper right")
fig.colorbar(im, ax=ax, label="dB"); fig.tight_layout()
fig.savefig(os.path.join(FIG, "mmode_tracked.png"), dpi=140); plt.close(fig)

# figure 3: distension waveform
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.plot(tslow, diameter * 1e3, color="#2563eb", lw=1.6)
ax.set_xlabel("time [s]"); ax.set_ylabel("diameter [mm]")
ax.set_title("Recovered arterial distension (diameter) waveform")
ax.grid(alpha=0.3); fig.tight_layout()
fig.savefig(os.path.join(FIG, "distension_waveform.png"), dpi=140); plt.close(fig)

print(f"mean diameter : {diameter.mean()*1e3:.2f} mm")
print(f"distension    : {(diameter.max()-diameter.min())*1e6:.0f} um peak-to-peak")
