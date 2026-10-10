# prod art round 5 (stills art5): FAIL
Tried pulling each disc forward until its whole extent cleared the sweep (min hit distance over centre/bottom/side rays x0.85). The hard line went away, but the big ice glow ended up in front of the tuna and washed it milky (f108).
Fix (r6): back to centre-hit x0.9 placement but never nearer than (camera distance + 0.6 x product length), and each glow's emission fades to 0 toward the floor (world z from floor to floor + 0.45 S, smootherstep), so the sweep never cuts a visible edge.
