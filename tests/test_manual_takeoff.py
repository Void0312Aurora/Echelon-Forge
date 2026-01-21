#!/usr/bin/env python3
"""
Manual Takeoff Test Script
Tests if the physics engine allows the aircraft to naturally take off.
Applies: Full throttle, gradual elevator pull at rotation speed.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gym_envs.universal_env import UniversalEnv
import numpy as np

def main():
    env = UniversalEnv("scenarios/takeoff.json")
    obs, _ = env.reset()
    
    print("="*60)
    print("MANUAL TAKEOFF TEST")
    print("="*60)
    
    # Action layout: [pitch, roll, rudder, throttle, gear, flaps, speedbrake, ...]
    # We'll use a simple controller:
    # - Full throttle
    # - Neutral stick until speed > 80 m/s, then pull back (pitch up)
    # - Retract gear after altitude > 20m
    
    for step in range(2000):
        inst = obs["instruments"]
        speed = inst[0]  # IAS
        alt = inst[2]    # alt_baro
        aoa = inst[5]
        pitch = inst[7]
        gear = inst[18]
        
        # Build action (17 dims)
        action = np.zeros(17, dtype=np.float32)
        
        # Throttle = full
        action[3] = 1.0
        
        # Pitch control logic (Proportional Controller for Pitch Angle)
        target_pitch = 15.0
        
        if speed < 100.0:
            action[0] = 0.0 # Wait for Vr
        else:
            # Simple P-controller
            pitch_err = target_pitch - pitch
            # kP = 0.05
            # If pitch is 0, err=15, action=0.75 (clamped to 1.0)
            # If pitch is 15, err=0, action=0
            # If pitch is 20, err=-5, action=-0.25
            action[0] = np.clip(pitch_err * 0.05, -1.0, 1.0) 
            
            # Dampen pitch rate if needed? 
            # (Let's stick to P-control for angle first)
        
        # Gear control
        if alt > 30.0:
            action[4] = 0.0  # Retract gear
        else:
            action[4] = 1.0  # Gear down
        
        obs, reward, terminated, truncated, info = env.step(action)
        
        # Get raw truth to see actual velocity
        truth = env.sim.get_agent_observation(env.agent_id)
        
        # Print status every 50 steps
        if step % 50 == 0:
            print(f"[Step {step:4d}] Speed: {speed:6.1f} m/s | Alt: {alt:6.1f} m | AoA: {aoa:5.1f}° | Pitch: {pitch:5.1f}° | Gear: {gear:.1f} | Reward: {reward:7.2f}")
            print(f"         -> Truth: vx={truth.vx:.2f}, vy={truth.vy:.2f}, vz={truth.vz:.2f}, z={truth.z:.2f}, health={truth.health}")
        
        # Check for success
        if alt > 300.0 and speed > 150.0:
            print("\n" + "="*60)
            print("SUCCESS! Aircraft has taken off and reached safe altitude.")
            print(f"Final: Alt={alt:.1f}m, Speed={speed:.1f}m/s")
            print("="*60)
            return True
            
        if terminated:
            print("\n" + "="*60)
            print(f"FAILED! Episode terminated at step {step}.")
            print(f"Final: Alt={alt:.1f}m, Speed={speed:.1f}m/s")
            print("="*60)
            return False
    
    print("\n" + "="*60)
    print(f"TIMEOUT! Did not reach target in 2000 steps.")
    print(f"Final: Alt={alt:.1f}m, Speed={speed:.1f}m/s")
    print("="*60)
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
