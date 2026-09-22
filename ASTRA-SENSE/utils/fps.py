import time
from collections import deque
class FPSCounter:
    def __init__(self, window=20): self.times=deque(maxlen=window)
    def tick(self):
        now=time.monotonic(); self.times.append(now); return self.value()
    def value(self):
        if len(self.times)<2:return 0.0
        span=self.times[-1]-self.times[0]
        return (len(self.times)-1)/span if span>0 else 0.0
