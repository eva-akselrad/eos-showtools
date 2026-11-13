-- extend_timecode.lua - lengthen the project's timecode-generator (LTC / "Timecode Generator") item
-- so MTC keeps running for the whole song. Eos stops firing events when timecode stops.
-- Reads `seconds=` (target end time) and `log=` from reaper_job.txt. Saves the project.
-- Run via:  python reaper_load.py extend-timecode --seconds 240
local here = ({reaper.get_action_context()})[2]:match("^(.*)[/\\]")
local job = {}
for line in io.lines(here .. "\\reaper_job.txt") do
  local k, v = line:match("^(%w+)=(.*)$")
  if k then job[k] = v end
end
local need = tonumber(job.seconds or "240")
local log = io.open(job.log, "w")
for i = 0, reaper.CountMediaItems(0) - 1 do
  local it = reaper.GetMediaItem(0, i)
  local tk = reaper.GetActiveTake(it)
  local nm = tk and reaper.GetTakeName(tk) or ""
  local src = tk and reaper.GetMediaItemTake_Source(tk)
  local typ = src and reaper.GetMediaSourceType(src, "") or ""
  local pos = reaper.GetMediaItemInfo_Value(it, "D_POSITION")
  local len = reaper.GetMediaItemInfo_Value(it, "D_LENGTH")
  log:write(i, " ", nm, " type=", typ, " pos=", pos, " len=", len, "\n")
  if nm:find("Timecode") or typ:find("LTC") or typ:find("TIMECODE") then
    if pos + len < need then
      reaper.SetMediaItemInfo_Value(it, "D_LENGTH", need - pos)
      log:write("  extended to ", need - pos, "\n")
    end
  end
end
reaper.UpdateArrange()
reaper.Main_SaveProject(0, false)
log:close()
