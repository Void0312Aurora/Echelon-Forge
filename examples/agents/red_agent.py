import math
import numpy as np

class RedScriptedAgent:
    """
    A simple scripted agent for the Red Target.
    Behavior:
    1. Cruise East normally.
    2. If Blue is within threat range (< 10km), perform evasive maneuvers (Turn 90 degrees).
    3. If very close (< 2km), jink (hard turn).
    """
    def __init__(self, kernel, unit_id):
        self.kernel = kernel
        self.unit_id = unit_id
        self.evading = False
        self.cruise_heading = 90.0 # East
        self.evade_heading_offset = 0.0
        self.last_action_time = 0.0

    def step(self, blue_pos, current_time):
        # 1. Get own state
        my_pos = self.kernel.get_unit_position(self.unit_id)
        
        # 2. Calculate threat geometry
        dx = blue_pos[0] - my_pos[0]
        dy = blue_pos[1] - my_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        target_speed = 200.0 # Cruise
        target_heading = self.cruise_heading
        
        # 3. Logic
        if dist < 2000.0:
            # High Threat: Jink!
            # Turn perpendicular to the threat vector
            threat_angle = math.atan2(dy, dx) # Math angle
            threat_angle_deg = math.degrees(threat_angle)
            
            # Beam the threat (fly 90 deg offset to the missile/bandit line)
            # This forces the bandit to pull max G
            target_heading = (90.0 - threat_angle_deg) + 90.0 
            target_speed = 300.0 # Max power
            
        elif dist < 10000.0:
            # Medium Threat: Evasive turn
            if not self.evading:
                self.evade_heading_offset = 45.0
                self.evading = True
            
            target_heading = self.cruise_heading + self.evade_heading_offset
            target_speed = 250.0
            
        else:
            self.evading = False
            
        # Normalize
        target_heading = target_heading % 360.0
        
        # Apply Command
        self.kernel.set_command(self.unit_id, target_heading, target_speed, my_pos[2])
        
        return {"evading": self.evading, "dist": dist}
