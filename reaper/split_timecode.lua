-- split_timecode.lua - make MTC run past ~3:00.
-- The SMPTE/LTC generator item stops generating after its original source length (~180 s) even if
-- the item is lengthened. Fix: keep the first item 0..SPLIT, and add a copy at SPLIT with
-- STARTTIME = SPLIT (its timecode starts at that value) running to `seconds`.
-- Job keys: seconds (end), split (default 170), log.  Run via: python reaper_load.py split-timecode
local here = ({reaper.get_action_context()})[2]:match("^(.*)[/\\]")
local job = {}
for line in io.lines(here .. "\\reaper_job.txt") do
  local k, v = line:match("^(%w+)=(.*)$")
  if k then job[k] = v end
end
local need = tonumber(job.seconds or "300")
local split = tonumber(job.split or "170")
local log = io.open(job.log, "w")
local src_item, tr
for i = 0, reaper.CountMediaItems(0) - 1 do
  local it = reaper.GetMediaItem(0, i)
  local tk = reaper.GetActiveTake(it)
  local s = tk and reaper.GetMediaItemTake_Source(tk)
  if s and reaper.GetMediaSourceType(s, "") == "LTC" and reaper.GetMediaItemInfo_Value(it, "D_POSITION") < 1 then
    src_item = it; tr = reaper.GetMediaItem_Track(it)
  end
end
if not src_item then log:write("no LTC item at 0\n"); log:close(); return end
reaper.Undo_BeginBlock()
-- remove any previous continuation items (LTC items not at 0)
for i = reaper.CountTrackMediaItems(tr) - 1, 0, -1 do
  local it = reaper.GetTrackMediaItem(tr, i)
  local tk = reaper.GetActiveTake(it)
  local s = tk and reaper.GetMediaItemTake_Source(tk)
  if it ~= src_item and s and reaper.GetMediaSourceType(s, "") == "LTC" then reaper.DeleteTrackMediaItem(tr, it) end
end
local _, chunk = reaper.GetItemStateChunk(src_item, "", false)
reaper.SetMediaItemInfo_Value(src_item, "D_LENGTH", split)
local c2 = chunk:gsub("\nPOSITION [^\n]*", "\nPOSITION " .. split, 1)
c2 = c2:gsub("\nLENGTH [^\n]*", "\nLENGTH " .. (need - split), 1)
c2 = c2:gsub("STARTTIME [^\n]*", "STARTTIME " .. split, 1)
c2 = c2:gsub("\n%s*IGUID [^\n]*", "", 1):gsub("\n%s*GUID [^\n]*", "", 1)
local it2 = reaper.AddMediaItemToTrack(tr)
reaper.SetItemStateChunk(it2, c2, false)
log:write("item1 0..", split, "  item2 ", reaper.GetMediaItemInfo_Value(it2, "D_POSITION"), " len ",
          reaper.GetMediaItemInfo_Value(it2, "D_LENGTH"), "\n")
reaper.Undo_EndBlock("Split timecode generator", -1)
reaper.UpdateArrange()
reaper.Main_SaveProject(0, false)
log:close()
