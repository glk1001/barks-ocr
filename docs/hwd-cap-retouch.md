# High-wire Daredevils — cap colours that contradict the dialogue

The nephew cap convention (red Huey, blue Dewey, green Louie) is the anchor the
vision pass uses to name a boy. In *High-wire Daredevils* (Vol. 2, pages
177–186) parts of the colouring do not follow it, and the dialogue says so out
loud. Colourists were not consistent between stories, so the plan is to
**retouch the caps to match the dialogue** rather than reinterpret the
convention.

This note was first written from the vision pass alone, when the only evidence
was three lines of dialogue and a lot of caps that sampled muddy. The speaker
review is now complete — 132/132 groups, 41 nephews named individually — and it
turns a list of suspects into a diagnosis. **Read the diagnosis, not the
suspects**: the earlier version of this file listed thirteen panels as
"indeterminate" and twelve of them turned out to be fine.

## The diagnosis

Check every individually-named nephew against the convention and the mismatches
fall into two tight groups:

| pages | what is wrong |
|---|---|
| **177–179** | **red and green are swapped.** Louie prints red, Huey prints green. Blue is correctly Dewey throughout. |
| **184 panel 2** | one cap: the ticket seller is Dewey and prints **red**. Not part of any swap. |
| 180, 182, 183, 185, 186 | **nothing.** 26 named nephews, zero mismatches. |

All nine mismatches, from the finished review:

| page | group | panel | is | prints | should print |
|---|---|---|---|---|---|
| 177 | g7 | 5 | Louie | red | green |
| 177 | g9 | 7 | Louie | red | green |
| 177 | g11 | 7 | Huey | green | red |
| 178 | g1 | 2 | Louie | red | green |
| 178 | g4 | 5 | Louie | red | green |
| 178 | g6 | 6 | Louie | red | green |
| 178 | g8 | 7 | Huey | green | red |
| 179 | g7 | 5 | Huey | green | red |
| 184 | g3 | 2 | Dewey | red | blue |

### How the names were established

Two anchors, both from dialogue, neither reliant on a cap:

- **179 panel 1**, "TRY TO LAND IN THE NET, **LOUIE**!" — the falling
  wire-walker is Louie. He is one continuous boy from 177 panel 5 to 179 panel
  4, which carries the name back across six panels. Corroborated by 179 panel 5,
  "LET **LOUIE** GET BACK TO HIS BALANCING!", spoken by a boy who is therefore
  not Louie.
- **184 panel 2**, "HOW MANY TICKETS HAVE WE SOLD, **DEWEY**?" — the boy in the
  ticket booth is Dewey.

Everything else was settled by the review reading the art directly.

Note that **184 panel 3 is correct**: an identically red cap that Donald calls
Huey, two panels after the red cap that is Dewey. That is why this cannot be
fixed by remapping the palette globally — the fault is confined to 177–179 plus
one stray.

## What to retouch

### A. Pages 177–179: swap red and green on every nephew cap

Not only the caps listed above — the silent boys on those pages carry the same
swap, so it is safest to treat the whole three-page run as red↔green and leave
blue alone. Anchor boxes, in **full-page source coordinates** (the frame
`text_box` uses, which `panel-NN.png` shares). They are small boxes *inside* the
flat colour, for sampling and locating; retouch the whole sliver.

| page | panel | full-page box | prints | is | → |
|---|---|---|---|---|---|
| 177 | 5 | `[1556,1611]-[1636,1641]` | `#b02820` | Louie | green |
| 177 | 7 | `[1441,2321]-[1469,2333]` | `#a82820` | Louie | green |
| 177 | 7 | `[1826,2380]-[1849,2390]` | `#406868` | Huey | red |
| 178 | 2 | `[1459,373]-[1514,398]` | `#e01818` | Louie | green |
| 178 | 5 | `[609,1727]-[689,1762]` | `#e01818` | Louie | green |
| 178 | 6 | `[1324,1670]-[1399,1705]` | `#e01820` | Louie | green — **cap off his head**, in the air beside him |
| 179 | 1 | `[834,216]-[904,256]` | `#e01820` | Louie | green — **cap off his head**, top right |
| 179 | 2 | `[1312,274]-[1395,351]` | `#e01820` | Louie | green — **cap alone in mid-air**, top left; 2760 ink px, the cleanest sample in the story |

Also on those pages, from the same sampling pass: 178 panel 7 has the green
Huey cap at panel-local `(340,232)-(420,260)` and 179 panel 5 has his at
`(580,355)-(625,400)`. Blue caps on 177 p7, 178 p7, 179 p5 and 179 p7 are
Dewey and correct.

Nothing to do on 179 panels 3 and 4 — he is bare-headed in both and the cap is
not in frame.

### B. Page 184 panel 2: red → blue

| page | panel | full-page box | prints | is | → |
|---|---|---|---|---|---|
| 184 | 2 | `[1092,487]-[1162,522]` | `#e01818` | Dewey | blue |

### C. Do not touch

| page | panel | full-page box | why |
|---|---|---|---|
| 184 | 3 | `[1511,642]-[1586,672]` | the boy Donald calls Huey, printing red. Correct. |

And the whole of 180, 182, 183, 185 and 186: 26 named nephews, every cap
matching the convention. 183 panel 7 is the best reference in the title — the
three caps are knocked clean off the heads and float isolated, sampling
`#e01820` / `#00a0d0` / `#009840` at over 4000 ink px each.

Two pages have no cap colour to judge and are deliberate, not faults: **181**,
where the boys are in top hats for the vaudeville act, and **180 panel 5**,
where they are flat black silhouettes at sunrise. **182 panel 1** has three
solid black caps with no colour sliver at all — the only saturated colour on
any of those heads is the `#f0a820` of their beaks — so there is nothing to
swap there either.

## After the retouch

The annotations already carry the **right names**. What they carry is the cap as
it printed at pass time, so after the art changes, nine `cap_colour` values will
disagree with the art in the opposite direction. Flip them to match:

- 177 g7, g9 and 178 g1, g4, g6 — Louie, `red` → `green`
- 177 g11, 178 g8, 179 g7 — Huey, `green` → `red`
- 184 g3 — Dewey, `red` → `blue`

All nine are `speaker_reviewed`, so `vision_apply` will not touch them and a
re-read is not needed; it is a nine-value scripted edit against the prelim JSON
(4-space, `ensure_ascii`, no trailing newline — prove the round trip first),
then `vision-mirror --write` to carry it to paddleocr. The `LATER FINDING`
paragraphs appended to those groups' `vision_note` should be trimmed at the same
time, since they describe a disagreement that will no longer exist.

## What the first version of this note got wrong

Worth keeping, because it is the same measurement error twice:

The first draft listed thirteen caps as "wrong on their own terms" — three
panels where two brothers appeared to carry an identical value, seven
off-palette caps, and one panel with none. **Twelve of the thirteen were fine.**
Once the review named the boys, the caps agreed with the convention. What had
actually happened is that a wide sampling box on a 20-pixel sliver picks up the
black cap edge, the shading and whatever is behind the head, and two such boxes
converge on the same muddy average from two different inks. The one real
finding in that list, 177 panel 7's far boy, is part of the red↔green swap.

The rule that follows: before recording a cap as unreadable or as tied with
another, re-crop that cap alone at 8–12x and place the sample box *inside* the
flat area. A genuine tie is much rarer than a badly placed box.

## Why the pass could not settle this itself

`roster.txt` hardcodes red/blue/green → Huey/Dewey/Louie and offers no way to
say "this story is coloured differently". The pass therefore did what the roster
tells it to and named off the sampled cap, recording the clash in prose in each
group's `vision_note`.

That is the right failure mode — record a cap-versus-dialogue disagreement and
hand it on, never quietly pick a winner. But nothing downstream reads that
prose, and the editor shows `vision_note` only for the group in hand, so the
pass flagged the conflict on the panels where it *noticed* (179, 184) and left
the six panels it *implicated* (177, 178) reading as confident, unqualified
Huey. A reviewer working 177 in queue order met the wrong name with no warning.
If a second title turns up like this, the fix is a per-story palette override in
the prep step, so the pass can be told the mapping instead of inferring it.

Related: `docs/vision-pass.md`, `.claude/skills/vision-pass/SKILL.md`.
