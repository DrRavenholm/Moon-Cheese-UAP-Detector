"""Optional post-solve catalogue/photo cross-check for visual calibration review.

These are *independently* correlated reference stars, NOT ASTAP's internal
quad matches. Only show a marker if catalogue astrometry predicts the location
and the photograph contains a compact local light-source centroid there.
Missing catalogue / noisy image produces an explicit empty result, never a
fabricated marker. No network or camera access; works in the plate worker.
"""
import math


def project_star(ra, dec, wcs):
    """Gnomonic RA/Dec to FITS-style 1-based WCS pixel coordinates."""
    a0=math.radians(float(wcs['CRVAL1']))
    d0=math.radians(float(wcs['CRVAL2']))
    a=math.radians(float(ra))
    d=math.radians(float(dec))
    da=(a-a0+math.pi)%(math.pi*2)-math.pi
    cosc=math.sin(d0)*math.sin(d)+math.cos(d0)*math.cos(d)*math.cos(da)
    if cosc<0.15:return None
    east=math.cos(d)*math.sin(da)/cosc
    north=(math.cos(d0)*math.sin(d)-math.sin(d0)*math.cos(d)*math.cos(da))/cosc
    xdeg=math.degrees(east);ydeg=math.degrees(north)
    a,b,c,d=[float(wcs[k]) for k in ('CD1_1','CD1_2','CD2_1','CD2_2')]
    det=a*d-b*c
    if not math.isfinite(det) or abs(det)<1e-14:return None
    return ((d*xdeg-b*ydeg)/det+float(wcs['CRPIX1'])-1,
            (-c*xdeg+a*ydeg)/det+float(wcs['CRPIX2'])-1)


def celestial_north(wcs):
    """Vector from centre toward celestial north, in image pixel coordinates."""
    a,b,c,d=[float(wcs[k]) for k in ('CD1_1','CD1_2','CD2_1','CD2_2')]
    det=a*d-b*c
    if abs(det)<1e-14:return None
    dx=-b/det;dy=a/det
    length=math.hypot(dx,dy)
    return [round(dx/length,5),round(dy/length,5)] if length>0 else None


def crosscheck(source, wcs, max_markers=80):
    """Crossmatch downloaded star catalogue against compact sources in photo.

    Actual image centroids must be within the tolerance of predicted catalogue
    positions; unmatched reference stars never receive circles. Restrict to
    central field where first-order WCS is reasonable for distorted wide lenses.
    """
    try:
        import cv2
        import numpy as np
        from sky_map_engine import catalogue
        stars=catalogue().get('stars') or []
        if not stars:
            return {'markers':[],'north':celestial_north(wcs),'note':'Download Stars and star names in Sky Maps Data & Updates to enable visual star cross-checks.'}
        image=cv2.imread(str(source),cv2.IMREAD_GRAYSCALE)
        if image is None or min(image.shape[:2])<300:
            return {'markers':[],'north':celestial_north(wcs),'note':'The image could not be analysed for star markers.'}
        height,width=image.shape[:2]
        scale=min(1.,1600./max(width,height))
        small=cv2.resize(image,(max(1,round(width*scale)),max(1,round(height*scale))),interpolation=cv2.INTER_AREA) if scale<1 else image
        # Background suppression reduces bright clouds, city lights and ISO grain.
        smooth=cv2.GaussianBlur(small,(3,3),0)
        background=cv2.medianBlur(smooth,31)
        delta=cv2.subtract(smooth,background)
        threshold=max(12.,float(np.percentile(delta,99.5)))
        mask=np.uint8(delta>=threshold)
        count,labels,stats,centroids=cv2.connectedComponentsWithStats(mask,8)
        detections=[]
        limit=max(2,round(55*scale*scale))
        for i in range(1,count):
            area=int(stats[i,cv2.CC_STAT_AREA])
            if not 1<=area<=limit:continue
            x,y=centroids[i]
            if x<6 or y<6 or x>small.shape[1]-6 or y>small.shape[0]-6:continue
            detections.append((float(x)/scale,float(y)/scale,area))
        if not detections:
            return {'markers':[],'north':celestial_north(wcs),'note':'No compact star-like sources were detected in this photograph; overlay markers are withheld.'}
        # Prefer identifiable bright catalogue stars; lock each detected source
        # to a single reference prediction. No marker when only WCS exists.
        used=set();matched=[]
        tolerance=min(22.,max(5.,float(width)*.0035))
        for row in stars:
            if len(row)<3 or float(row[2])>5.8:continue
            xy=project_star(row[0],row[1],wcs)
            if not xy:continue
            x,y=xy
            if not (width*.12<=x<=width*.88 and height*.12<=y<=height*.88):continue
            nearest=None;closest=tolerance*tolerance
            for j,(sx,sy,area) in enumerate(detections):
                if j in used:continue
                ds=(x-sx)**2+(y-sy)**2
                if ds<closest:
                    closest=ds;nearest=j
            if nearest is None:continue
            used.add(nearest)
            sx,sy,_=detections[nearest]
            name=str(row[3])[:35] if len(row)>3 else ''
            matched.append({'x':round(sx/width*100,3),'y':round(sy/height*100,3),
                            'mag':float(row[2]),'name':name,'residual_px':round(math.sqrt(closest),2)})
            if len(matched)>=max_markers:break
        # A single accidental coincidence must never be represented as a solved
        # overlay. The ASTAP WCS remains separately visible even without markers.
        if len(matched)<3:
            matched=[]
            note='Too few independent catalogue/photo matches for a trustworthy marker overlay. Sky coordinates were solved, but star circles are withheld.'
        else:
            note='Circles mark independent catalogue-to-photograph cross-checks, not ASTAP internal quad matches. Edge distortion is not calibrated.'
        return {'markers':matched,'north':celestial_north(wcs),'note':note}
    except Exception:
        # Overlay failure must never invalidate an otherwise legitimate solve.
        return {'markers':[],'north':celestial_north(wcs),'note':'Star marker cross-check unavailable. The valid ASTAP centre solution can still be reviewed.'}
