import math
from typing import Optional, Tuple

Point = Tuple[float, float]
BBox = Tuple[float, float, float, float]

def center(box: BBox) -> Point:
    x1,y1,x2,y2=box
    return ((x1+x2)/2.0,(y1+y2)/2.0)

def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

def iou(a: BBox, b: BBox) -> float:
    ax1,ay1,ax2,ay2=a; bx1,by1,bx2,by2=b
    ix1,iy1=max(ax1,bx1),max(ay1,by1); ix2,iy2=min(ax2,bx2),min(ay2,by2)
    iw,ih=max(0,ix2-ix1),max(0,iy2-iy1)
    inter=iw*ih
    if inter<=0:return 0.0
    aa=max(0,ax2-ax1)*max(0,ay2-ay1); bb=max(0,bx2-bx1)*max(0,by2-by1)
    return inter/max(aa+bb-inter,1e-9)

def direction(dx: float, dy: float, deadzone: float=2.0) -> str:
    if abs(dx)<deadzone and abs(dy)<deadzone:return 'NONE'
    horiz='RIGHT' if dx>0 else 'LEFT' if dx<0 else ''
    vert='DOWN' if dy>0 else 'UP' if dy<0 else ''
    return f'{vert}-{horiz}' if vert and horiz else vert or horiz
