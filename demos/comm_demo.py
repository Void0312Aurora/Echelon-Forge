import sys
import os
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '../build'))

import ef_py
from ef_py import Side, SimulationKernel, CommMsgType

def main():
    kernel = SimulationKernel()
    kernel.reset(42)
    
    # Spawn A and B
    obs_a = kernel.spawn_unit(Side.Blue, "Aircraft", 0, 0, 5000, 0, 0, 0)
    obs_b = kernel.spawn_unit(Side.Blue, "Aircraft", 10000, 0, 5000, 0, 0, 0)
    
    print(f"Spawned A={obs_a}, B={obs_b}")
    
    # A Sends Message to B
    # Type: ReportContact, Arg: 999
    kernel.send_message_command(obs_a, obs_b, int(CommMsgType.ReportContact), 999)
    print("Command Sent from A to B")
    
    kernel.step()
    
    msgs = kernel.get_unit_messages(obs_b)
    print(f"B Inbox Size: {len(msgs)}")
    
    if len(msgs) > 0:
        msg = msgs[0]
        print(f"Msg: Sender={msg.sender_id}, Type={msg.type}, Ref={msg.entity_ref}")
        if msg.sender_id == obs_a and msg.entity_ref == 999:
            print("PASS: Message Received")
        else:
            print("FAIL: Content Mismatch")
    else:
        print("FAIL: No Message")

    # Step again, should clear?
    kernel.step()
    msgs2 = kernel.get_unit_messages(obs_b)
    print(f"B Inbox Size (Step 2): {len(msgs2)}")
    if len(msgs2) == 0:
        print("PASS: Inbox Cleared")
    else:
        print("FAIL: Inbox Persistent")

if __name__ == "__main__":
    main()
