# Reading a cap with the scan tools

How the cap-ink tools actually behave, and the ways each one reports **no ink**
on a cap that is plainly there. Every failure below was paid for in speaker
corrections; the titles and hexes are kept so a claim can be re-checked.

The reading *rule* lives in `roster.txt` (generated from `vision_schema.py`):
an absence claim needs the census's own `N blob(s) total` header to say 0, and
that count has to be quoted in the note. **This file is the operational half —
why a zero happens and which tool answers which question.**

## Which tool answers what

| tool | answers | never answers |
|---|---|---|
| `capsum.py` | roughly which cap sits on which head | "there is no cap" |
| `capwide.py` | is there cap-sized ink anywhere in this panel | "there is no cap" |
| `capscan.py` | every roster-band blob, with hex, area and box | whether the blob is *on a head* |
| `heads.py` | where the heads are, and what ink sits on one | whether an unattached blob is a cap |
| `probe.py` | the true pixel histogram of one box, no floors | anything about other boxes |

`capsum` for *which head*, `capscan` for **every verdict**, `probe` when the
answer is "the scan says zero and I still do not believe it".

## The bands are a property of the tool, not of the art

From `scripts/vision/capscan.py` — read them there, do not assume:

```python
RED_LO, RED_HI = 340.0, 12.0  # wraps through 0
GREEN_LO, GREEN_HI = 140.0, 182.0
BLUE_LO, BLUE_HI = 183.0, 235.0
LEAFGRN_LO, LEAFGRN_HI = 95.0, 140.0
MIN_SAT, MIN_VAL = 0.40, 0.25
DEFAULT_MIN_AREA = 25
```

Four consequences, each measured:

**`leafgrn` is where a cap green lives.** In Vols. 5, 6, 7 and 13 the cap green
is H108–113 (`#4da33f`, `#4da33e`, `#4ea23f`), which lands in `leafgrn`; the band
*named* `green` holds grass, hedge and blanket at H147 and reports **0 for the
whole story**. Reading `green: 0` as "no green cap" is backwards. Three Vol. 5
titles and all of Vol. 13 behave this way.

**There is a one-degree crack between the bands.** `green` ends at 182 and `blue`
starts at 183. On *Lost in the Andes!* 031 p3 a cap at `#1fa3a8` **H182.2** fell
in it, another at `#81331c` **H13.7** sat 1.7 degrees outside `red`, and the
third was reported under `leafgrn` and read as scenery. All three bands printed
zero, the note said "NO red, NO green and NO blue ink at any size", and the
review named Dewey, Huey and Louie. A 1.7x crop showed three plainly coloured
caps.

**The default floor of 25px hides whole constructions.** *Spending Money* 202 p2
is a black skull cap with a coloured chip at the crown edge: Dewey `#07a5d5`
**60px**, Huey `#b21e20` **10px**, Louie `#4da544` **12px**. At the default only
Dewey clears; at a floor of **8** all three appear and the three names follow.
Every hex was correct at every floor — the floor decided whether the blob
existed. Pass the floor explicitly on every census and quote it in the note.

**The saturation floor of 0.40 hides shaded caps.** Where Barks draws a cap
mostly black with a shaded band, the ink falls under it: *Race to the South
Seas!* 068 p4's green is `#68a36f` H127 **S0.36**, and `capwide` at min-area 40
reported `green: 0`. Nearly every cap in *Managing the Echo System* is that
construction — `capwide` found almost nothing across ten pages and a probe found
clean red, green and blue on eleven heads. Indoors is worse: *Gladstone's* 095 g6
probes at `#536c4a` **S0.31**. **A cellar or an interior means probe, not scan.**

## Read the header, not the rows

`-- red: 2 blob(s) total, 1 in window` is the answer. The listed rows are what
survived the window.

On *Christmas on Bear Mountain* 011 p3 the note said "capscan returns ZERO red,
green, blue or leafgreen blobs of any size" — while the scan on screen read
`2 blob(s) total` and listed `area=129 #902b17`. The review named that boy Huey
off that cap. `#902b17` is H10 V0.56: the red under snow-shadow. If the header
says `N total, 0 in window`, drop the floor and run it again before claiming
anything.

## Run it wide

Both edges of a size window remove exactly what you are looking for. `head` on
an area-sorted list cuts the **small** end, where every cap is; a low `--max`
cuts the **large** end, where a cap drawn front-on or from above lives. On
*Picnic Tricks* 190 p3 a cap scanned at 60–3000px vanished — it is **16,867px**,
a cap seen from above at full size. A nephew's cap is 30px in one panel and
17,000px in the next *within the same story*.

Run 25–40000 and read all of it. Use the window to annotate candidates, never
to decide absence.

## Saturation, and which inks it applies to

Below about **S0.75** a cool band names nobody on its own, because blue and green
converge as they desaturate — the two cool inks are each other's only rival.
Above it, hue plus in-panel ranking is fine. Below it, rank the band against a
clean cool cap in the same panel; if the panel has none, decline the colour.

**The floor is for the cool bands only.** Red has no rival — nothing else warm is
a cap — so a dimmed red is still red at any saturation. Applying the floor to a
red on *Rival Beachcombers* 170 p4 (`#8c5b46` H18 **S0.50**) killed the anchor
that would have named all three boys in the row, and the review named all three.

Outdoors, saturation is also the only thing separating cap green from foliage:
on *Gladstone's* 089 p2 the greenery is H100–108 S0.54–0.57 against caps at
H108–113 S0.57–0.63 — a three-degree gap. Key any census on hue **and**
saturation, never on band name.

## A teal band's drift direction is a per-title fact

A thin cool band drifts toward teal, and **which** ink it drifted from cannot be
assumed. On *Links Hijinks* the drift ran blue → teal and three bands read as
green came back Dewey (`#5da290` H164, `#07a082` H168, `#059f64` H157); what
stood as green was `#2a9359` **H146.9**. So the split is near H150, not in the
160s.

Twice more in one Vol. 11 batch, in both directions, each time after a per-title
rule had been built from the *lit* badges and applied to the *shaded* ones.
Shading moves a blue down into the green's value **and** across into its hue at
once, so value is no help: *Gladstone's* shaded blue sits at V0.64, the green's
own value.

**Anchor on the green**, which is the stable ink (H108–130 across these titles);
anything cooler than about H140 is the blue however muddy. Never name a nephew
off a teal band alone — find a clean band of the same colour in the same panel to
measure the drift against, or crop the cap.

## The last check is always the same

A blob is not a cap until it sits on a head. `capscan` finds ink; `heads.py`
places it; and `heads.py` failing to attach a blob is a statement about its
reach, not about the cap — a 21px crown sliver above a small figure's white
skull falls outside the region it searches and is still the cap.

Where even a low floor returns nothing, crop the crown at 3–6x and look before
declining.
