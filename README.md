# lootTracker

- download the [lootTracker executable](/dist/raidTracker.exe) 
- start the exe
- add players by choosing class, enter name, select if main character or twink (twink only works with main added ofc)
- for the first raid everyone starts at quotient 1. if a member participate on a raid and got nothing, he has quotient 0 in second raid and thus is able to roll on a drop
- quotient is calculated by (sum(setpieces gain)+zaudru questitem)/(sum(joined raids)), thus, the more raids a player do, the lower the quotient. Storvagun Qitem, Mirdanant and Beryl shards are just for tracking, not influence the quotient. Just if you wanna distribute these drops fairly, you can keep track.
- If player access the raid with an alt, you can assign raid participation or gained loot to the alt/twink, but it counts towards just one main quotient.
- all stats are safed to raid_data.json. This file need to be in the same folder as the executable. 
- If you remove a players main/alt and will later add him back to the list, he will remain in database and can be added via "chose database" freezing his stats

# shard tracker 
- download [beryl shard tracker executeable](/dist/shardTrack.exe)
- for any kins/groups who wanna distribute beryl shards fairly from carn dum drops. Just add group and members, if anyone got one shards, group will be green, delete it and add new group. 
- one player can ofc be part of several groups
- just kept it easy 
- data is also stored in a .json file called shard_count.json. keep this file always within the same file than the executable when starting the programm. all active stats are safed here. 
- in this case there will be no data base. once a group is deleted, you need to re-add the group.