import math

N = 256
WIDTH = 24
MAXI = (1 << (WIDTH-1)) - 1  # 32767
DRIVE = 3.0                  # curve “steepness” inside tanh

# Normalize so y hits full-scale at x = ±1
norm = math.tanh(DRIVE)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

for addr in range(N):
    # map addr 0..255 -> x in [-1, +1]
    x = (addr - (N/2)) / (N/2)
    y = math.tanh(DRIVE * x) / norm

    yi = int(round(clamp(y, -1.0, 1.0) * MAXI))

    # print SV-friendly signed decimal
    if yi < 0:
        print(f"8'd{addr:3d} : out_signal = -{WIDTH}'sd{abs(yi)};")
    else:
        print(f"8'd{addr:3d} : out_signal = {WIDTH}'sd{yi};")