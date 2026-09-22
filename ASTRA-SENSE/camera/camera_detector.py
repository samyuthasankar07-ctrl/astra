import cv2
from config import LOCAL_CAMERA_SCAN_LIMIT

def scan_local(max_index=LOCAL_CAMERA_SCAN_LIMIT):
    found=[]
    for i in range(max_index):
        cap=cv2.VideoCapture(i)
        ok=cap.isOpened()
        if ok:
            ret,frame=cap.read(); ok=bool(ret and frame is not None and frame.size>0)
        cap.release()
        if ok: found.append({'id':f'local:{i}','name':f'Local Camera {i}','source':i,'type':'local','label':f'Local Camera {i} [index={i}]'})
    return found
