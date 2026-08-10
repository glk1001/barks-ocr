# High-wire Daredevils — cap colours that contradict the dialogue

The nephew cap convention (red Huey, blue Dewey, green Louie) is the anchor the
whole vision pass uses to name a boy. In *High-wire Daredevils* (Vol. 2, pages
177–186) the colouring does not follow it, and the dialogue says so out loud.
Colourists were not consistent between stories, so the plan is to **retouch the
caps to match the dialogue** rather than to reinterpret the convention.

This is the retouch list. Coordinates are **full-page source coordinates** —
the same frame as `text_box` in the prelim group files, and the frame the
`panel-NN.png` crops share. They are small boxes *inside* the flat colour, not
the outline of the cap: use them to sample and to locate, then retouch the whole
sliver.

## What the story actually establishes

Three lines of dialogue name a boy directly. They are the only identity
evidence in the title, and two of the three fight the cap:

| page | panel | who | line | cap prints | convention says |
|---|---|---|---|---|---|
| 179 | 1 | the falling wire-walker | "TRY TO LAND IN THE NET, **LOUIE**!" | red | green |
| 184 | 2 | the ticket seller | "HOW MANY TICKETS HAVE WE SOLD, **DEWEY**?" | red | blue |
| 184 | 3 | the boy at the turnbuckle | "IS THE WIRE TIGHT, **HUEY**?" | red | red ✔ |

A fourth line corroborates the first: 179 panel 5, "LET **LOUIE** GET BACK TO
HIS BALANCING!", is spoken by a **green**-capped boy — so whoever green is in
that panel, he is not Louie, and Louie is the one out on the wire.

Note the third row. 184 panel 3 is the convention working correctly, so this is
**not** a clean story-wide permutation of the palette — red is not simply
"Louie's colour here". Three different names land on a red cap in the same
title. Whatever the cause, it has to be fixed panel by panel from the dialogue,
not by remapping the palette.

## A. Identity conflicts — retouch these

### A1. The wire-walker is Louie: red → green `#009840`

One continuous boy from 177 panel 5 to 179 panel 4 — he practises on the wire,
Donald loads his balancing pole with ball bearings, and he falls. 179 panel 1
names him Louie. His cap is red in every panel he appears in:

| page | panel | full-page box | prints | where |
|---|---|---|---|---|
| 177 | 5 | `[1556,1611]-[1636,1641]` | `#b02820` | on the wire, mid-panel |
| 177 | 7 | `[1441,2321]-[1469,2333]` | `#a82820` | on the wire, left of centre |
| 178 | 2 | `[1459,373]-[1514,398]` | `#e01818` | on the wire |
| 178 | 5 | `[609,1727]-[689,1762]` | `#e01818` | on the wire |
| 178 | 6 | `[1324,1670]-[1399,1705]` | `#e01820` | **cap off his head**, in the air beside him |
| 179 | 1 | `[834,216]-[904,256]` | `#e01820` | **cap off his head**, top right of the panel |
| 179 | 2 | `[1312,274]-[1395,351]` | `#e01820` | **cap alone in mid-air**, top left — the largest clean sample in the story at 2760 ink px |

Nothing to do on 179 panels 3 and 4: he is bare-headed in both and the cap is
not in frame.

Knock-on once this is done: in the panels where he appears with his brothers,
green is then taken, so the other two must be red and blue. Worth checking
177 panel 7 (see B1) and 178 panel 7 (currently green + blue, so the green one
would need to become red) at the same sitting.

### A2. The ticket seller is Dewey: red → blue `#00a0d0`

| page | panel | full-page box | prints | where |
|---|---|---|---|---|
| 184 | 2 | `[1092,487]-[1162,522]` | `#e01818` | leaning out of the booth with the megaphone |

### A3. Do not touch

| page | panel | full-page box | prints | why |
|---|---|---|---|---|
| 184 | 3 | `[1511,642]-[1586,672]` | `#e01818` | the boy Donald calls Huey. Correct as printed. |

## B. Panels that are wrong on their own terms

No dialogue names anyone in these, so the *right* colour is a judgement call —
but each is impossible as it stands, either because two brothers in one panel
carry the same colour or because the cap is not a palette colour at all.

### B1. Two boys the same colour — at least one of the two is wrong

| page | panel | full-page box | prints | which boy |
|---|---|---|---|---|
| 183 | 1 | `[315,644]-[326,662]` | `#408858` | middle boy |
| 183 | 1 | `[369,617]-[380,634]` | `#408858` | boy behind him — identical value |
| 185 | 3 | `[992,1140]-[1022,1155]` | `#587060` | middle boy |
| 185 | 3 | `[1097,1150]-[1117,1180]` | `#587060` | rear boy — identical value |
| 186 | 4 | `[1538,1141]-[1578,1166]` | `#389080` | middle boy |
| 186 | 4 | `[1628,1161]-[1668,1186]` | `#389080` | rear boy — identical value |

### B2. Off-palette caps

Not red, blue or green, and not close enough to snap to one:

| page | panel | full-page box | prints | which boy |
|---|---|---|---|---|
| 177 | 7 | `[1826,2380]-[1849,2390]` | `#406868` | far boy on the table — slate, G=B |
| 180 | 4 | `[1693,1139]-[1748,1169]` | `#089898` | middle boy — teal, G=B |
| 182 | 8 | `[1072,2606]-[1084,2626]` | `#985020` | left boy — rust brown |
| 182 | 8 | `[1169,2576]-[1186,2585]` | `#689880` | middle boy — muted green |
| 185 | 2 | `[1935,479]-[1965,491]` | `#708888` | middle boy — grey-teal |
| 185 | 2 | `[1990,477]-[2015,489]` | `#505850` | right boy — grey |
| 186 | 5 | `[448,1914]-[493,1939]` | `#389088` | middle boy — teal |

### B3. No cap colour at all

182 panel 1, all three boys on the fence: solid black caps with no colour
sliver anywhere. The only saturated colour on any of the three heads is the
`#f0a820` of their beaks.

## C. Deliberate, leave alone

- **181, the whole page** — the boys are in top hats for the vaudeville act.
- **180 panel 5** — the three are drawn as flat black silhouettes at sunrise.
- **183 panel 7, 180 panel 3, 185 panel 8, 186 panel 8** — one clean red, one
  clean blue, one clean green. Internally consistent, so nothing to fix even
  though nothing anchors which boy is which. 183 panel 7 is the best reference
  in the title: the caps are knocked clean off the heads and float isolated,
  sampling `#e01820` / `#00a0d0` / `#009840` at over 4000 ink px each.

## After the retouch

1. Re-sample the boxes above to confirm the new values.
2. Re-run the speaker queue for the title — the annotations record the cap as
   it printed at pass time, so 12 groups carry a `cap_colour` that will no
   longer match the art:
   - 177 g7, g9 and 178 g1, g4, g6 are the wire-walker, annotated `Huey` /
     `cap_colour: red`. After A1 they are **Louie / green**. Note that 177 and
     178 are already `speaker_reviewed`, so these five need changing by hand or
     unreviewing first — a re-apply will not touch a reviewed group.
   - 184 g3 is the ticket seller, annotated `Huey` / `red`. After A2 it is
     **Dewey / blue**.
   - 184 g5 stays `Huey` / `red`.
3. The 21 groups left collective in this title were left that way because of
   B1–B3. Most become nameable once those panels are fixed, so it is worth
   re-reading the title rather than only patching the groups above.

## Why the pass could not settle this itself

`roster.txt` hardcodes red/blue/green → Huey/Dewey/Louie and offers no way to
say "this story is coloured differently". The pass therefore did what the
roster tells it to and named off the sampled cap, recording the clash in each
group's `vision_note` — 179 g0, 179 g7, 184 g3 and 184 g5 all carry it.

That is the right failure mode: the pass should record a cap-versus-dialogue
disagreement and hand it on, never quietly pick a winner. But it does mean a
title like this one produces confidently wrong names, and the only signal is
prose in a note that nothing downstream reads. If a second title turns up like
this, the thing to add is a per-story palette override in the prep step, so the
pass can be told the mapping instead of inferring it.

Related: `docs/vision-pass.md`, `.claude/skills/vision-pass/SKILL.md`.
