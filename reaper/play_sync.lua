-- Wait 3 s (so the test harness can put Eos/Augment3d back in front - Reaper jumps forward when a
-- script is launched and an occluded Augment3d pauses rendering), then play from 0 and log
-- (time_precise, audible play position) pairs to play_sync.txt so song time can be mapped exactly.
local here = ({reaper.get_action_context()})[2]:match("^(.*)[/\\]")
local f = io.open(here .. "\\play_sync.txt", "w")
local t0 = reaper.time_precise()
local started = nil
reaper.SetEditCurPos(0, false, false)
local function loop()
  local now = reaper.time_precise()
  if not started and now - t0 >= 7.0 then
    reaper.SetEditCurPos(0, false, false); reaper.OnPlayButton(); started = now
  end
  if started and reaper.GetPlayState() & 1 == 1 then
    f:write(string.format("%.6f %.6f\n", now, reaper.GetPlayPosition())); f:flush()
  end
  if not started or now - started < 4 then reaper.defer(loop) else f:close() end
end
loop()


