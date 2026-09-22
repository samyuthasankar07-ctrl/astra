from utils.geometry import distance,iou

def infer(person,obj,hand_distance):
    # Require confident detections and real spatial proximity before assigning interaction.
    if getattr(person, 'confidence', 1.0) < 0.45 or getattr(obj, 'confidence', 1.0) < 0.45:
        return 'NONE', 0.0

    d=distance(person.center,obj.center); overlap=iou(person.bbox,obj.bbox)
    near = d < 60 or overlap > 0.05 or hand_distance < 50
    if not near:
        return 'NONE', 0.0

    if hand_distance < 50 and obj.velocity > 80 and obj.direction != 'NONE':
        return 'THROWING', 0.85
    if hand_distance < 50 and obj.velocity < 35:
        return 'HOLDING', 0.78
    if hand_distance < 70 and person.velocity > 25 and obj.velocity > 15:
        if obj.direction == person.direction:
            return 'CARRYING', 0.75
        return 'PUSHING' if obj.direction != 'NONE' else 'USING', 0.65
    if hand_distance < 70:
        return 'REACHING', 0.60
    return 'NEAR', 0.45
