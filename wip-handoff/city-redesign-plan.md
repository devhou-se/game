# City audit and redesign plan (#210)

Outcome of the audit Bailey asked for: every city measured, rendered and looked at by an auditor, then checked by a sceptic. This is a plan, with an order of work and no dates. Nothing has been built or changed.

Evidence: `measure.md` (all tables), the per-city notes (`tokyo.md`, `osaka.md`, `sapporo.md`, `asahikawa.md`, `sendai.md`, `fukuoka.md`, `hokuriku.md`) and the renders, all in this folder. Kanazawa, Shirakawa-go and Toyama were read from the l4 lane, which is not on master yet.

## Headline findings

- **Damian is right about reuse.** Sendai and the Kanazawa region share 0.54 of all sprites; Sendai and Kanazawa as rooms share 0.63, the highest pair in the game. Kanazawa is Sendai's kit on Sendai's frame.
- **Sapporo and Asahikawa have 2 sprites of their own each** (5% and 7%). They look different from the south only because of snow. On buildings alone Sapporo and Osaka overlap 0.50.
- **Osaka has 3 real sprites of its own** (arch, wheel, tower), and the tower is a line-art placeholder.
- **The same three townhouses are in every city** (48 placed). The machiya row is in 4 of 7, the stock shrine in 4, the yellow high-rise in 4. Every generated town's station is a townhouse.
- **Only Tokyo and the Kanazawa region have districts in data.** Sapporo, Asahikawa, Sendai, Osaka and Fukuoka are single rooms whose areas exist only as generator comments. No district has a label or description the pipeline can place by.
- **Nothing is too far to walk.** No room takes more than 17 s corner to corner; all of Tokyo is 31 s. The scale problem is density and dead ground, not distance: Tokyo has 787 cells per dated post-state against Sendai's 336, and half its walkable ground is road and pavement.
- **Tokyo has the most art of its own (47%)** but only one of its four districts reads as a place.
- **Deleting Machi, Inaka and Yukimura loses no unique art.** They have none.

## Per city

Sizes are cells (width x height). "States" are dated post-states: one author at one spot on one date.

### Tokyo

- **Today:** four stitched districts plus Machi. 9,440 cells, about 6,800 walkable, 12 states once the Kanazawa posts leave, standing on four spots. Rooms are named Tokyo, Market, Palace, Park; two of those names are wrong for what is drawn.
- **Verdict:** has districts, but one of four passes. The moated palace block is unmistakable. Market is "a big red temple" in a car park of six 7-Elevens. Palace is two line-art placeholders. Park is an empty slab. Size is fine to walk (31 s) but far too empty. Three of the six posts about Tokyo stand in the wrong place for want of labels.
- **Changes:**
  1. Labels only, no map edits: display names (keys unchanged), a description per district, room-scoped LANDMARKS rows (Senso-ji hall, pagoda, gate, moat and pond, Izakaya). Re-place Bailey's Senso-ji post to the Asakusa hall, Julia's Don Quijote post to the Don Takote, Dylan's izakaya post to the Izakaya door, and Damian's Hakata-to-Okayama post out of Tokyo to Hakata Station.
  2. Delete Machi.
  3. Asakusa touch-up: stall rows replace the two blank roofs, a Kaminarimon lantern on the existing gate, six konbini cut to one, townhouses and high-rise out.
  4. Station block: real pixel art for Tokyo Station and Tokyo Tower (#70), tower moved off the road.
  5. Park rebuilt: Ueno on the west half, Shibuya on the east half.
- **Going forward:**
  - **Imperial Palace** (room Tokyo): moat, stone walls, palace gardens, the old gate. Left as built.
  - **Asakusa** (room Market): Senso-ji temple, the lantern gate, the stall street, crowds.
  - **Marunouchi / Tokyo Station** (room Palace): the red-brick station front, the shinkansen, Tokyo Tower on the skyline.
  - **Ueno** (Park, west): the park, a pond with swan boats, autumn trees.
  - **Shibuya** (Park, east): the scramble crossing, a two-sided high-rise street, Don Takote, izakaya and karaoke. Closes #94.
- **Size of job:** labels small; Asakusa and station art medium; Park is a big rebuild by hand, because the Tokyo maps are ported files with no generator.
- **Decided against the auditor:** no whole-city generator, no cell-count target, no room-key renames, no Tokyo-only road palette, no Meiji Jingu, zoo gate or Shibuya Sky tower. Reason: Tokyo already has the most art of its own and 12 states; its fault is misplacement and one empty block, and the walk time is already under the auditor's own target once Machi goes.

### Osaka

- **Today:** one room, 50x46, 4 states from two people over three nights. Arch, ferris wheel and Don Takote north of a canal; a dead five-row avenue; Tsutenkaku on a brick square with two blocks of flats.
- **Verdict:** no districts in data; the two halves are the same kit on two near-identical greys. Passes the city test only when the arch or wheel is on screen. Slightly too big for what happened there; about 40% of the walkable ground is dead.
- **Changes:** rebuild the generator around the kept landmarks (arch, wheel, store, boats, bridge). Shrink to about 50x40. Cut the avenue, the empty paving, all sakura, and high-rises outside the station front. Redraw Tsutenkaku in pixel art. About 9 to 11 new pieces, all look-alike names as with Don Takote.
- **Going forward:**
  - **Osaka Station front** (a threshold, not a district): a wide station front and the two office towers.
  - **Dotonbori:** neon canal with a boardwalk, giant food signs, takoyaki, ramen queues, bars, the discount store and its wheel.
  - **Shinsekai:** Tsutenkaku, retro arcades and game shops, kushikatsu, gacha machines, lantern street.
- **Size of job:** big. The only full rebuild in the plan.
- **Decided against the auditor:** no Umeda district, no konbini, no Osaka Castle reservation, no growth. Reason: four states; a third district nobody stands in is the padding we argued against. Nara and Himeji are separate owner decisions, not part of this job.

### Sapporo

- **Today:** one room, 56x43, no posts yet, five placement labels of which two are its own. Three Osaka high-rises, seven generic houses, a konbini, the Clock Tower, the TV Tower, three near-identical Odori blocks. 35% of walkable cells are asphalt.
- **Verdict:** two visual zones (the tower row and everything else). Fails the district test; passes the city test only in the north-east third. Walking size is fine; the proportions are a road map with buildings in the gaps. It hosts up to 49 author-days for devhouse 3.
- **Changes:** partial rebuild inside roughly the current footprint (56 wide, about 48 to 50 tall). Keep the street grid, both towers where they are (the Clock Tower's position is correct), Odori's shape and the interiors. Narrow two side streets. Cut all generic houses, the frozen pond (Asahikawa keeps it) and the Osaka high-rises. About 8 new pieces. About 9 to 10 placement labels; base NPCs spread across districts.
- **Going forward:**
  - **Sapporo Station front:** station plaza, arrivals, the meeting point; a station front with the star clock and two Sapporo office blocks.
  - **Clock Tower block:** the Clock Tower among office blocks, on its own paving.
  - **Odori Park:** long snowy boulevard park, snow sculptures, food stalls, TV Tower at the east end.
  - **Tanukikoji:** covered shopping arcade, souvenirs, Don Takote, the konbini.
  - **Susukino:** the neon crossing with the Nikka-style sign, ramen alley, bars and karaoke, tram rails.
- **Size of job:** big, and it has a deadline: the devhouse 3 lead-in opens 30 days before 18 Feb 2027.
- **Decided against the auditor:** not 64x64 and seven districts. Reason: zero posts; the three conditions can be met in about 15% more cells, not 70%. Akarenga, the Beer Garden, Nijo Market and the outskirts wait for a post that names them.

### Asahikawa

- **Today:** one room, 42x32, the smallest live city, no posts yet. A cottage as station, three machiya with ramen banners, a frozen river with a timber bridge, the stock shrine, three cottages. Own art: the bridge and the banner.
- **Verdict:** no distinguishable districts; a snow village. It is the Yukimura recipe. Size is right for four days (nothing more than 11 s from the station); about a third of the reachable ground is empty. Up to 28 author-days arrive with devhouse 3.
- **Changes:** partial rebuild, same footprint, river kept as the spine. Replace the station cottage, the machiya trio, the timber bridge and the shrine set. Fix the refused ramen-alley standing cell by moving three shrubs. Six new sprites and one ground tile. No posts to migrate.
- **Going forward:**
  - **Station front and Heiwa-dori:** the station, a paved pedestrian shopping street, ice sculptures, the konbini.
  - **Ramen alley:** shoyu ramen counters, red banners, steam.
  - **Asahibashi and the riverbank:** the green arch bridge, the frozen river, the riverside houses.
  - **Asahiyama Zoo gate** (a landmark, not yet a district): the zoo gate and a penguin walk in the snow.
- **Size of job:** medium. Same deadline as Sapporo, since the trip moves here on 25 Feb 2027.
- **Decided against the auditor:** no growth to 50x38, no wider river, no mountain skyline, no brewery, no zoo enclosure. Reason: the auditor's own finding is that a third of the map is empty.

### Sendai

- **Today:** one room, 70x48, 10 states over four days. Castle terrace, Zuihoden, a generic centre on a road cross, a Nikka kiln, an invented samurai quarter across the bottom 40%, and Matsushima bay down the east edge.
- **Verdict:** three areas pass (castle, Zuihoden, the bay's water side). The centre and the whole south third could be any generated town. Too big: the surplus is the samurai quarter, which no post mentions and nobody stands in.
- **Changes:** partial rebuild in one room that shrinks to about 70x34. Cut the samurai quarter (10 generic buildings, and 10 interiors that would otherwise be owed). Rebuild the centre as a zelkova avenue with a ramen shop and izakaya beside the pub. Give the distillery its own yard. Fix the bay's land side. About 8 new pieces including a station front. Re-place post 520 at the distillery and regenerate its dialogue.
- **Going forward:**
  - **Sendai Station front:** arrivals; a station front of its own.
  - **Aoba Castle ruins:** hilltop ruins, the Masamune statue, great-hall foundations.
  - **Zuihoden:** the black-and-gold mausoleum up cedar steps.
  - **Downtown:** zelkova avenue, the HUB pub, ramen, izakaya, 7-Eleven.
  - **Nikka distillery:** brick kiln, casks, autumn maples; Yamadera's stair and hall as a sealed landmark on the hill behind.
  - **Matsushima bay:** cruise pier on a timber boardwalk, pine islets, Godaido hall, sushi.
- **Size of job:** medium. The cut is cheap; the avenue and the bay's land side are the work.
- **Decided against the auditor:** not three stitched rooms. Reason: it called 3,360 cells too big, then proposed 4,072. Matsushima and the distillery are already walkable edges of the room, which meets the owner's rule. No sprite renames (churn across the lane in flight).
- **Decided against the sceptic:** Sendai gets its own station front now, not later. Reason: see cross-city rule 4; the townhouse-as-station is the first thing seen in six cities.

### Fukuoka

- **Today:** one room, 62x62, the largest in the game, 8 states over five days. Yatai river street, tower and beach, Canal City, Kushida and its float, Dazaifu, plus a generic station front, east plaza, high-rise row and an Ohori lawn.
- **Verdict:** six real places; Nakasu and Dazaifu pass outright, Momochi passes on its tower, Kushida on its hall and float. The north-east and south-west quarters fail. 8 of 15 buildings are shared kit. Padded: about 43% of walkable ground has no post and nothing unique.
- **Changes:** partial rebuild on the existing skeleton, trimmed to about 56x58. Remove the three high-rises, the generic east block, the machiya and the small pagoda. Give each district its own ground. Hedge Dazaifu so the way in is through the torii. About 8 new pieces. No rotation, no station move.
- **Going forward:**
  - **Hakata Station:** a station front of its own, Christmas market and illuminations, ramen shops, arrivals.
  - **Nakasu:** yatai stalls on the river at night, neon boards, bars and pubs.
  - **Canal City:** the mall, a strip of canal, the fountain, on warm paving.
  - **Old Hakata:** Kushida shrine and the Yamakasa float, Tochoji's hall.
  - **Momochi:** Fukuoka Tower, a real beach, the sea; the Ohori pond folds in here or goes.
  - **Dazaifu:** Tenmangu, the approach lane, the arched bridge, plum trees, the roof-grove hall. A walkable edge, not a train stop.
- **Size of job:** medium to large.
- **Decided against the auditor:** no rotated plan and no 56x52 re-lay. Reason: Damian asked for different tiles, not a different shape, and the generator is weeks old. The auditor also had two facts wrong (the south beach is reachable; the south lane is the Dazaifu approach). Canal City stays sealed.

### Kanazawa, Shirakawa-go, Toyama (one stitched region, one station)

- **Today (in the lane, not on master):** Kanazawa 60x52 with 8 states, Shirakawa-go 36x32 with 2, Toyama 44x34 with 3. Only 24 to 36% of cells are walkable.
- **Verdict:** Shirakawa-go passes outright; nothing else looks like it. Toyama passes as a town, but its old street is the shared machiya row. Kanazawa fails against Sendai and wastes its area (a downtown block with 1 walkable cell in 232; an avenue that is 40% of everything walkable). Distances are fine.
- **Changes:**
  - Kanazawa: partial rebuild in place, about 60x40. Own wall and gate replace Sendai's. Drum-gate station front. Downtown rebuilt as a short walkable lane. The hill behind the teahouses opened as the temple walk; the south-east Teramachi block deleted. Castle lawn and turret, a bigger Kenrokuen. Buildings go from 16 to about 12. About 11 new pieces.
  - Shirakawa-go: touch-up. Far bank trimmed and given the open-air farmhouse and ice-cream stand; the unused south farmhouse becomes the ryokan with an onsen pool; wider viewpoint.
  - Toyama: touch-up. Two Iwase merchant fronts replace the machiya; the old house made reachable; south wood halved.
- **Going forward:**
  - Kanazawa: **Station front** (drum gate, arrivals, bus to Shirakawa-go); **Higashi Chaya and the temple hill** (teahouses, gold leaf, the hill walk, the phonograph museum); **Katamachi** (whisky bar, all-you-can-drink dinner, konbini); **Castle** (Ishikawa gate, grounds under reconstruction); **Kenrokuen** (pond, Kotoji lantern, roped pines); **Nagamachi** (earthen walls, canal, samurai house).
  - Shirakawa-go: **Far bank and bridge** (bus, bears, the wobbly bridge, open-air museum); **Village** (gassho farmhouses, paddies); **Ryokan and onsen**; **Viewpoint** (over the roofs to the snow peaks).
  - Toyama: **Iwase port** (port tower, sea, old street, black ramen); **Tram street** (tram, Glass Art Museum, the old house).
- **Size of job:** Kanazawa big; the other two small.
- **Decided against the auditor:** no re-positioning of every Kanazawa district, no new tree set, no puddles or marathon barrier, the temple walk goes behind Chaya (where the posts put it), and fewer buildings, not more.
- **Decided against the sceptic:** the region lands as built first, and the Kanazawa re-skin follows. Reason: landing it re-homes 14 states out of the made-up towns and unblocks their deletion; holding it for 11 new art pieces holds that too. Cost: for a while the game ships the most-alike pair measured (0.63).
- **Separate pipeline item:** post 587 (Damian, Toyama) is not in the game and post 610 is dated a day early.

### San Franbourne (#218)

Being built separately as the home city reached by air. Not audited; it has to pass the same test below from the start.

### Machi, Inaka, Yukimura

Being deleted. They have no art of their own. Machi is empty once the Kanazawa region lands; Inaka's 6 Dylan states (2 to 8 Nov 2025) and Yukimura's 1 Julia state (2 Nov 2025) move to the real place each post is about first; Yukimura's base NPC James goes (not a current member).

## Cross-city rules that come out of the evidence

### 1. "Visually distinct" as a test

A district passes when all of these hold:

1. **Own ground.** Its main ground or paving differs from every district it touches.
2. **Own art.** It has at least one building or large scenery sprite used in no other city.
3. **No borrowed identity.** It contains no generic townhouse, machiya, stock shrine or high-rise that also stands in another city, unless that city is named as its owner in rule 4.
4. **A label and a spot.** It has a name, a one-line description and at least one named standing spot.
5. **The crop test.** Rendered with the HUD off, a person who knows the game names the city and the district from that district alone.

A city passes when every district passes and, by `measure.py`:

- building-sprite overlap with any other city is 0.25 or less (worst today: Sapporo and Osaka 0.50);
- all-sprite overlap with any other city is 0.40 or less (worst today: Sendai and Hokuriku 0.54);
- at least a third of its building and scenery sprites are its own (today: Sapporo 11%, Asahikawa 10%, Osaka 10%, Fukuoka 26%, Sendai 28%, Hokuriku 39%, Tokyo 52%).

The thresholds are proposed from where the passing districts sit today. Small job: put the measure into the checks so a new town cannot land below them.

### 2. How scale is set

Scale follows the posts and the length of stay, not a size class.

- **Walking:** a room is 20 s or less corner to corner and a stitched city 35 s or less. Everything already meets this, so no city grows to feel bigger.
- **Density:** about 250 to 500 room cells per dated state. Sendai, Fukuoka, Osaka and Kanazawa land inside this after their trims. Tokyo stays above it on purpose as the hub; it is fixed by filling Park, not by shrinking.
- **Before posts exist** (Sapporo, Asahikawa): size by expected author-days, and aim for one named spot per five or so author-days (about 10 in Sapporo, 6 in Asahikawa).
- **No dead ground:** every district has a named spot; no block of 150 or more walkable cells with nothing unique and nobody ever standing in it; road and pavement are a third or less of walkable ground (Tokyo is 50%, Kanazawa 40%, Sapporo 35% today).
- **No invented districts.** A district needs a post or a planned stay behind it. Sendai's samurai quarter goes for the same reason Machi does.

### 3. What stays shared on purpose

- Roads, kerbs, crossings, traffic lights, rail track and rail fence.
- The station interior template (line colour and name boards differ).
- 7-Eleven and its interior, vending machines, Don Takote (a chain: Tokyo, Osaka, Sapporo).
- Street furniture: lamp posts, red lanterns, pavers, bus stop, garden fence.
- Grass, water, basic trees and shrubs, and their snow recolours.

Shared kit may fill a district but may not be what identifies it. A label is never hung on a shared sprite (Odori Park is on a lantern today).

### 4. Generic buildings that get an owner or a per-city variant

| Generic today | In | Going forward |
|---|---|---|
| Townhouse as the station | 6 generated cities | each city gets its own station front (Sapporo, Asahikawa, Sendai, Osaka, Hakata, Kanazawa's drum gate) |
| Townhouse, three colours | 7 of 7 cities, 48 placed | no longer filler; kept only where a house is the point (Asahikawa's riverside row, Toyama's old house with its own look) |
| Machiya row | 4 of 7 | replaced by a local shopfront in each city (ramen front, Iwase fronts, gold-leaf shop, Tochoji hall) |
| Stock shrine, torii, foxes | 4 of 7 | Tokyo only |
| High-rise prefabs | 4 of 7 | Tokyo (Shibuya) and Osaka station front only; Sapporo gets its own office blocks |
| Sendai wall and gate | Sendai, Kanazawa | Sendai keeps them at Zuihoden; Kanazawa gets its own |

New buildings are stamped with door cells so the interiors work (#208, #212 to #217) can open them later. Landmarks stay sealed. The plan lowers the count of generic sealed buildings, so it lowers interior debt overall.

### 5. Labels into the pipeline

Every district gets a label and a one-line description offered to the blog placement model alongside the named spots, so a post that names an area and no landmark can be placed. This is the first job, needs no map change, and fixes four misplaced Tokyo posts on its own. It needs a small change to `tools/blog_to_npc.py` to carry district descriptions.

## Order of work

No dates. The only fixed constraint is that Sapporo and Asahikawa are ready before the devhouse 3 lead-in opens.

| # | Work | Kind | Size | New art |
|---|---|---|---|---|
| 0 | Already in flight: land the Kanazawa region; move the last 7 states; delete Machi, Inaka, Yukimura; San Franbourne (#218) | - | - | - |
| 1 | District labels and descriptions for every city; Tokyo display names; re-place the misplaced posts; the distinctness measure as a check | labels only | small | none |
| 2 | Sapporo | partial rebuild | big | about 8 |
| 3 | Asahikawa | partial rebuild | medium | 6 and a ground tile |
| 4 | Kanazawa | partial rebuild | big | about 11 |
| 5 | Shirakawa-go, Toyama | touch-up | small | about 6 |
| 6 | Sendai | partial rebuild (shrinks) | medium | about 8 |
| 7 | Osaka | rebuild | big | 9 to 11 |
| 8 | Fukuoka | partial rebuild | medium to large | about 8 |
| 9 | Tokyo: Asakusa, station and tower art (#70) | touch-up | medium | about 4 |
| 10 | Tokyo: Park into Ueno and Shibuya (#94) | rebuild of one block | big | about 3 |

Why this order: Sapporo and Asahikawa have the least art of their own and the next trip. Kanazawa and Sendai are the most-alike pair. Osaka is the third-emptiest of own art. Tokyo is last because it already has the most.

**Honest cost:** about 60 to 65 new pieces of pixel art across the game, four big jobs (Sapporo, Kanazawa, Osaka, Tokyo's Park), and every map change re-runs generators, landmark offsets, base-NPC cells, tests and docs. Step 1 is the only cheap one, and it is also the one that helps placement immediately.

## Decisions the owner may want to overrule

Listed in the `decisions_for_owner` field of the hand-back, most costly first.
