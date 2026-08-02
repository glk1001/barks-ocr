# Retrieval queries — the acceptance test for page capture

Written **before** any page-capture data exists, deliberately. The test of the capture layer is
whether it surfaces the right page, not whether its prose reads well, and a query set written
afterwards would unconsciously describe what the schema already happens to record.

Same discipline `docs/ocr-check-calibration.md` applies to the fit constants: pick the target
first, then tune against it.

Queries invented by the assistant test the assistant's idea of what matters, so the set was drafted
to be cut and replaced. GLK has since added 16 — mostly **actions and objects** (driving, swimming,
sneezing, a campfire, a cave, silhouettes), a category the draft missed almost entirely by
weighting itself toward iconic named moments. Keep cutting; a query that would not occur to you
will pass or fail and tell you nothing you wanted to know.

---

## How to read the table

**Layer** — which layer must answer the query. This is the discriminating column:

| | |
|---|---|
| `capture` | needs page capture (`characters`, `setting`, `beats`, `panels_of_note`). **The queries that justify the whole pass.** |
| `visible_text` | needs the new `visible_text` field — signs, posters, headlines, labels |
| `speech` | answerable from the OCR corpus alone; capture must not *regress* these |
| `both` | speech narrows it, capture disambiguates |

A query set weighted toward `speech` proves nothing about the vision pass. Aim for roughly
two-thirds `capture` + `visible_text`.

**Expected** — what a correct answer looks like. Page numbers are left `?` where they are not
recorded in `docs/vision-pass.md`; fill them in when the trial titles are chosen, rather than
guessing them now.

---

## Tier 1 — checkable today against the pilot

Vol. 1 pages 076-085, "The Victory Garden". Every expected answer below is drawn from
`docs/vision-pass.md`, so these can be run as soon as capture exists for that title — no new
reading required to know whether the answer is right.

| # | Query | Layer | Expected | Why it's in the set |
|---|---|---|---|---|
| 1 | the poster advertising invisible seeds | `visible_text` | 085 | The pilot's headline find: background lettering, the hook the ending hangs on, and unrecoverable from any existing field |
| 2 | the nephews wearing football helmets | `capture` | 078, 080, 083 | Three separate pages — tests recall, not just precision |
| 3 | a scene set at night | `capture` (`setting`) | 079 | The `setting` field's simplest job |
| 4 | the nephews in pyjamas | `capture` | 085 | Distinguishes a costume from a `cap_colour` — the art carries identity another way here |
| 5 | crows in the garden | `capture` (`characters`) | many pages | 17 groups carry `other:crows`; tests that a non-roster collective is retrievable at all |
| 6 | a football game in progress | `capture` | 078, 080, 083 | Same pages as #2 by a different route — does the query need the *prop* or the *activity*? |
| 7 | a crowd scene | `capture` (`characters`) | ? | `other:crowd` exists in the pilot; tests coarse collectives |
| 8 | the shopkeeper | `capture` (`characters`) | ? | A named-role one-off; the `other:` long tail |
| 9 | Donald planting or digging in the garden | `capture` | ? | The story's premise — should be trivially findable, and an alarm if it is not |
| 10 | pages where nobody speaks | `capture` + absence of speech | ? | Tests the *negative* case: silent panels are invisible to speech search by construction |

## Tier 2 — corpus-wide targets

The real goal. Only a handful are testable on a ~60-page trial, which is itself useful: **choose
the four trial titles so they light up 10-12 of these**, rather than choosing titles first and
discovering the queries don't reach them.

Confidence varies. Where a query names a story, the assistant is reasonably confident the story
contains that element but **has not verified the page** — treat the Expected column as a starting
hypothesis, not ground truth.

| #  | Query                          | Layer | Expected               | Why it's in the set                                                                                               |
|----|--------------------------------|---|------------------------|-------------------------------------------------------------------------------------------------------------------|
| 11 | Scrooge diving into his money bin | `capture` | recurs across many titles | The single most iconic Barks image, and pure art — dialogue rarely narrates it. If capture misses this, it fails. |
| 12 | the square eggs                | `both` | Lost in the Andes      | Named in dialogue *and* visible; tests that the two layers agree                                                  |
| 13 | cubical chickens               | `capture` | Lost in the Andes      | The same story's visual gag that dialogue may never name                                                          |
| 14 | ping-pong balls raising a sunken ship | `capture` | The Sunken Yacht       | A purely visual solution to the plot                                                                              |
| 15 | Bombie the Zombie              | `capture` (`characters`) | Voodoo Hoodoo          | A DB-tagged one-off — tests Decision 3's closed set end to end                                                    |
| 16 | Gyro's Little Helper           | `capture` (`characters`) | Gyro Gearloose stories | A DB-tagged recurring secondary character                                                                         |
| 17 | the Beagle Boys in their masks | `capture` (`characters`) | many titles            | Tests a *group* character across stories                                                                          |
| 18 | Bolivar the dog                | `capture` (`characters`) | several titles         | DB-tagged, easy to confuse with any dog in frame                                                                  |
| 19 | Grandma Duck's farm            | `capture` (`setting`) | several titles         | A recurring named setting — the promotion candidate case                                                          |
| 20 | the Junior Woodchucks in uniform | `capture` | many titles            | Uniform as a visual identifier, like the caps                                                                     |
| 21 | a newspaper headline           | `visible_text` | many titles            | The commonest non-speech lettering; a yield check for the new field                                               |
| 22 | a wanted poster or reward notice | `visible_text` | ?                      | Plot-bearing lettering                                                                                            |
| 23 | a shop window or storefront sign | `visible_text` | many titles            | The category the pilot's find belongs to                                                                          |
| 24 | lettering on Scrooge's office door | `visible_text` | Uncle Scrooge titles   | Small, specific, easy to miss                                                                                     |
| 25 | a character silhouetted against the moon or sky | `capture` | ?                      | Pure composition — no dialogue, no props, no named character                                                      |
| 26 | an establishing shot with no characters in frame | `capture` | ?                      | The hardest negative case, and invisible to every other layer                                                     |
| 27 | Donald in a rage               | `capture` (`beats`) | many titles            | A recurring *emotional* beat; tests whether `beats` carries anything retrievable                                  |
| 28 | Donald and Gladstone in the same panel | `capture` (`characters`) | several titles         | Co-occurrence, not presence — a different query shape                                                             |
| 29 | a chase or pursuit across several panels | `capture` (`beats`) | ?                      | Spans panels, so page-level capture should beat panel-level here                                                  |
| 30 | the story's splash page        | `capture` (`panels_of_note`) | every title            | Should be trivially answerable; if `panels_of_note` cannot find a splash, it is not earning its place             |
| 31 | the nephews driving a car      | `capture`  | ?                      | Should pick characters and car                                                                                    |
| 32 | a character swimming           | `capture`  | ?                      | Tests character actions                                                                                           |
| 33 | a character that is sick       | `capture`  | Billions to Sneeze At  | Tests character health                                                                                            |
| 34 | a character that is sad        | `capture`  | Billions to Sneeze At  | Tests character emotions                                                                                          |
| 35 | a character that is smiling    | `capture`  | Billions to Sneeze At  | Tests character emotions                                                                                          |
| 36 | a character that is using a machine | `capture`  | Billions to Sneeze At  | Tests character action                                                                                            |
| 37 | a character that is crying     | `capture`  | Billions to Sneeze At  | Tests character emotions                                                                                          |
| 38 | a character that is sneezing   | `capture`  | Billions to Sneeze At  | Tests character action                                                                                            |
| 39 | a character kissing            | `capture`  | Billions to Sneeze At  | Tests character action                                                                                            |
| 40 | identify a character that is a doctor | `capture`  | Billions to Sneeze At  | Tests character recognition                                                                                       |
| 41 | identify a cave                | `capture`  | Billions to Sneeze At  | Tests object recognition                                                                                          |
| 42 | a character that has a halo    | `capture`  | Billions to Sneeze At  | Tests object recognition                                                                                          |
| 43 | a panel containing silhouettes | `capture`(`panels_of_note`) | Billions to Sneeze At  | Tests silhouette recognition                                                                                      |
| 44 | a panel containing a campfire  | `capture`(`panels_of_note`) | Billions to Sneeze At  | Tests object recognition                                                                                          |
| 45 | a character pointing           | `capture`  | Billions to Sneeze At  | Tests character action                                                                                            |
| 46 | a sound effect                 | `visible_text`  | Billions to Sneeze At  | Very common non-speech lettering                                                                                  |

---

## Controls — the speech layer must not regress

The 46 above are deliberately capture-heavy — 39 `capture`, 6 `visible_text`, 1 `both`, 0 `speech`
— because a set weighted toward speech would prove nothing about the vision pass. But that leaves
no check that adding capture has not *broken* what already works, and no calibration for what a hit
looks like on data known to support it.

These three are not part of the 46. They should pass before and after, unchanged.

| # | Query | Layer | Expected | Why |
|---|---|---|---|---|
| C1 | an exact line of remembered dialogue | `speech` | wherever it is | The Whoosh index's core job; must be unaffected |
| C2 | every line a named speaker says in one story | `speech` | the speaker pass output | Verifies attribution survives the schema change |
| C3 | a distinctive word appearing in only one story | `speech` | one title | Precision check — a single-hit query that must stay single-hit |

## Scoring

Run each query against the capture data and record:

- **hit** — the right page is in the top few results
- **miss** — the right page is absent
- **false positive** — a confident wrong answer, which is worse than a miss and worth counting
  separately

Record the tally in `docs/vision-pass.md` beside the 1.5% correction-rate baseline. A `capture`
query that only a `speech` match could have answered is **not** a hit for the vision pass — note
which layer actually produced each result.

### Split every miss two ways

**This is the part that makes the trial answer anything.** Open the page's capture record and ask
whether the thing was written down at all:

| | meaning | the fix it argues for |
|---|---|---|
| **not recorded** | capture never mentions it — the page says nothing about a car, or about swimming | the *schema* is too thin: raise `MAX_BEATS`, or add a field |
| **not retrieved** | capture does mention it, but the query did not surface the page | the schema is fine; *retrieval* needs work |

These want opposite fixes, and a bare miss count cannot tell them apart. Scoring them separately
costs a glance at one JSON file per miss.

**Fix them in this order.** `MAX_BEATS = 3` is a policy number — chosen as a guard against capture
drifting into a page-by-page retelling, not tuned against any evidence. Four or five sentences per
page is still not an abridgment, so **raising the cap is the cheaper first move**, and an explicit
`objects` or `actions` field only earns its place if that fails. Settling that order now keeps it
from being reverse-engineered out of the results.

### Emotion is on trial, not assumed

Queries 33–39 include emotional and bodily states. `crying`, `smiling`, `sneezing` and `kissing`
are visible; **`sad` (#34) is the deliberate test case.** Barks draws feeling legibly enough that
readers agree on it instinctively, so the objection is not that a model cannot see it.

The objection is **discrimination**: a tag that is readable on most pages returns most pages, and
answers nothing. So score #34 by *what fraction of the trial's pages it returns*, not only by
whether the right one is among them. If it hits 2 pages in 10 and they are the right two, it has
earned its place. If it hits 6 in 10, it is dead on retrieval grounds however accurate each call
was.

Note also that emotion would be the **only capture field with no error detection** — no closed set,
no census, no review queue, no validator. Everything else has something that catches a wrong value.

**No target is set here on purpose.** The first run establishes the baseline; the number to beat
comes after, once it is known what is achievable rather than what sounds good.
