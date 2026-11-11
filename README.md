# Ultrasound M-mode Artery-Wall Tracking

An experimental simulation to practice the processing behind my wearable ultrasound blood-pressure work: turning raw echoes into an image over time, tracking the artery walls, and reading how the artery widens with each heartbeat.

![M-mode image with both artery walls tracked](figures/mmode_tracked.png)

A wearable ultrasound patch sends short pulses into the neck and listens to the echoes from the front and back walls of the carotid artery. The walls move with every heartbeat, and so do the echoes; following that motion is the first step toward estimating blood pressure without a cuff. Raw radio-frequency ultrasound from a real artery is not publicly available, so this project simulates it and runs the processing chain on the simulated echoes.

Each simulated frame is a pulse-echo line with reflections from two walls whose depths move at the heart rate. The Hilbert transform turns the RF oscillation into an envelope, which is log-compressed. Stacking envelopes over time gives a depth-versus-time M-mode image, the two strongest envelope peaks in each line give the wall positions, and their distance over time is the diameter waveform.

| One A-line: RF echo and envelope | Diameter waveform |
|---|---|
| ![RF and envelope](figures/rf_aline_envelope.png) | ![Distension waveform](figures/distension_waveform.png) |

Everything here is simulated. Real tissue adds speckle, attenuation, other reflectors and probe motion, which this model leaves out on purpose.

## Run

MATLAB (Signal Processing Toolbox):

```matlab
mmode_wall_tracking
```

Python port that renders the figures:

```bash
pip install -r requirements.txt
python make_figures.py
```

---

Yaşar Aykut Altuntop · Koç University · [LinkedIn](https://linkedin.com/in/aykutaltuntop) · [GitHub](https://github.com/Aykut0)
