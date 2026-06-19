-- export_points.lua
-- Export a grid of points (x = North, z = East) -> (lat, lon) into dcs.log.
--
-- USAGE
--   1. Open the Mission Editor on the target map -> minimal mission (any
--      date / weather / aircraft).
--   2. Add a trigger:  TYPE = ONCE,  (no condition),
--      ACTION = DO SCRIPT  and paste this whole file.
--   3. Run the mission for ~5 seconds, then quit.
--   4. Grab the log:  Saved Games\DCS\Logs\dcs.log
--   5. Calibrate:  poetry run dcs-coords calibrate --log dcs.log --map <Name> --write
--
-- No de-sanitisation of MissionScripting.lua is required: we write via
-- env.info() into dcs.log (always allowed). The useful lines start with
-- "DCSXFORM;".
--
-- The first line emits the codified theatre name (env.mission.theatre, e.g.
-- "Caucasus", "PersianGulf", "SinaiMap"); the calibrator auto-detects the map
-- from it, so `dcs-coords calibrate --map` becomes optional.
--
-- dcs.log accumulates across runs, so you can export several maps in a row in
-- the same session: the calibrator only uses the LAST theatre block (the last
-- THEATRE line and the points after it).

local MIN  = -400000   -- min bound (m) on x (North) and z (East)
local MAX  =  400000   -- max bound (m)
local STEP =   50000   -- step (m)  ->  ((MAX-MIN)/STEP + 1)^2 points (here 17x17 = 289)

local count = 0
env.info("DCSXFORM;THEATRE;" .. tostring(env.mission.theatre))
env.info("DCSXFORM;BEGIN")
for x = MIN, MAX, STEP do        -- x = North (DCS x)
    for z = MIN, MAX, STEP do    -- z = East  (DCS z)
        local lat, lon = coord.LOtoLL({ x = x, y = 0, z = z })
        env.info(string.format("DCSXFORM;%.3f;%.3f;%.9f;%.9f", x, z, lat, lon))
        count = count + 1
    end
end
env.info(string.format("DCSXFORM;END;%d", count))
