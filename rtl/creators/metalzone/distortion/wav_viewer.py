from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import numpy as np

sr_in, x = read("run/export_wav_distortion/icarus/input.wav")
sr_out, y = read("run/export_wav_distortion/icarus/output.wav")

# Use first 1000 samples so you can actually see the wave shape
n = 1000
t = np.arange(n) / sr_in

plt.figure(figsize=(10, 4))
plt.plot(t, x[:n], label="Input")
plt.plot(t, y[:n], label="Output", alpha=0.8)
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.title("Before vs After Clipping")
plt.legend()
plt.grid(True)
plt.show()