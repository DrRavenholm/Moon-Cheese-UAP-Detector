"""Optional Raspberry Pi-friendly foreground and single-frame transient detectors.

These algorithms are only created if enabled. They operate on the detector's
masked configurable-resolution greyscale image and never modify recorded footage.
"""
import cv2
import numpy as np

class AdaptiveBackground:
    def __init__(self, variance=24, min_area=6, confirm_frames=2, area_scale=1.0):
        self.variance=int(variance);self.min_area=int(min_area)
        self.confirm_frames=max(1,int(confirm_frames));self.max_area=max(self.min_area,round(1500*area_scale));self.hits=0;self.frames=0
        self.bg=cv2.createBackgroundSubtractorMOG2(history=160,varThreshold=float(self.variance),detectShadows=False)
    def clear(self):
        self.bg=cv2.createBackgroundSubtractorMOG2(history=160,varThreshold=float(self.variance),detectShadows=False)
        self.hits=0;self.frames=0
    def feed(self, gray, mask):
        foreground=self.bg.apply(gray, learningRate=0.012)
        self.frames+=1
        if self.frames<12:return False,0
        foreground=cv2.bitwise_and(foreground,mask)
        foreground=cv2.morphologyEx(foreground,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
        count,_,stats,_=cv2.connectedComponentsWithStats(foreground,connectivity=8)
        areas=[int(stats[i,cv2.CC_STAT_AREA]) for i in range(1,count)]
        score=sum(a for a in areas if self.min_area<=a<=self.max_area)
        self.hits=(self.hits+1) if score>=self.min_area else 0
        return self.hits>=self.confirm_frames,score

class TransientDetector:
    def __init__(self, threshold=45,min_area=2,min_length=7,area_scale=1.0):
        self.threshold=int(threshold);self.min_area=int(min_area);self.min_length=int(min_length);self.max_area=max(250,round(250*area_scale));self.max_flash_area=max(120,round(120*area_scale))
        self.previous=None;self.background=None
    def clear(self):
        self.previous=None;self.background=None
    def feed(self,gray,mask):
        if self.previous is None:
            self.previous=gray.copy();self.background=gray.astype(np.float32)
            return False,0
        # A positive change AND high local contrast limits dark-cloud and noise triggers.
        old=cv2.convertScaleAbs(self.background)
        delta=cv2.subtract(gray,old)
        change=cv2.threshold(delta,self.threshold,255,cv2.THRESH_BINARY)[1]
        change=cv2.bitwise_and(change,mask)
        n,_,stats,_=cv2.connectedComponentsWithStats(change,connectivity=8)
        positive=[int(stats[i,cv2.CC_STAT_AREA]) for i in range(1,n) if self.min_area<=int(stats[i,cv2.CC_STAT_AREA])<=self.max_area]
        # Isolated single-point changes can be sensor noise: demand either a streak
        # or a compact multi-pixel bright transient on an otherwise quiet frame.
        lines=cv2.HoughLinesP(change,1,np.pi/180,threshold=max(3,self.min_length//2),
                             minLineLength=self.min_length,maxLineGap=2)
        streak=bool(lines is not None and len(lines)>0)
        flash=bool(positive and max(positive)>=max(3,self.min_area) and sum(positive)<=self.max_flash_area)
        triggered=streak or flash
        score=sum(positive)
        if streak:score=max(score,self.min_length)
        cv2.accumulateWeighted(gray,self.background,0.015)
        self.previous=gray.copy()
        return triggered,score
