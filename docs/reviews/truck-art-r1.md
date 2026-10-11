# truck art pass r1 (issue #75, COLOR_SCRIPT row 10 v-truck)

Changes: sun #ffc98a 5.0 (keyed 20°/100° f1-120, 15°/90° f216), sky multiplied by horizon #ffd7a0 -> zenith #5f93c8 gradient, cool fill sun #8fb8e0 0.45 (az 280, no shadow), warm rim sun #ffd59a 1.6 (az 20, elev 18), baked material haze recoloured to morning #e8d2b0, sea shallows to teal, yard concrete warmer, plant PUF cooler blue-white, dock bay 5500 K, look.apply('truck').

Stills f1/22/58/108/194/216 (full res): all FAIL luma (mean 3-11). Cause: look.fog's world volume absorbs the whole sky and sun in EEVEE (same as sea r1). Fix: drop world fog; haze comes from the per-material distance haze.
