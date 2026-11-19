# ARCH · Frontend screen checklist (client review, 19 November 2026)

**For:** the mobile team (Masooma, Daniel), to check the app before the next TestFlight build goes to the client.
**Sources:** the client review call on 19 November 2026 (Chi), the Live Brow Experience Specification Draft 3.2 (6 November 2026), and `BACKEND_HANDOVER.md` section 7.
**How to use it:** work through each screen on a real iPhone and a real Android phone, with a fresh account that holds a scan. Tick a box only when the screen does what it says on both phones. Record a short video of each tracing check, because the client will test the same way.

The client's priority is clear: "What I'm basically selling is the trace. It's the style, and it's this trace." Sections 1 to 3 come first.

---

## 1. Tracing (73 to 77): the client's top priority

What the client saw: a solid brown patch. What she wants: a guide line she follows with a real brow pencil, with the app telling her when she goes off it and to keep going.

| # | Screen | Check | Spec |
|---|---|---|---|
| - [ ] 1.1 | 36a → 73 | After BEGIN, the app calls `GET /v1/tracing/sessions/{id}/strokes` and gets two brow outlines | Handover 7.1 |
| - [ ] 1.2 | 75-01 / 76-01 | The guide is a **thin gold line** (`#C9A84C`) along the brow outline. **No brown fill anywhere.** | Spec 8, stage 01 |
| - [ ] 1.3 | 75-01 | SCULPT (Reshape mine): the full selected shape is outlined. The active brow has the stronger line. | Spec 8 |
| - [ ] 1.4 | 76-01 | REFINE (Refine mine): only the add zones are outlined (fill areas, extension points). Her own brow has no overlay. | Spec 8 |
| - [ ] 1.5 | All stages | The line stays on her brow when she turns her head slowly, and does not shake when she holds still | Spec 3 rules 1, 2 |
| - [ ] 1.6 | 75-02 / 75-03 | Stretches she has drawn along the guide turn a heavier solid gold. No percentages. | Spec 8 stages 02, 03 |
| - [ ] 1.7 | 75-04 | A stroke off the guide shows a thin dashed rose line with an inward cue. Line: "Bring this stroke back to the guide." (Refine: "…back inside the guide.") | Spec 8 stage 04 |
| - [ ] 1.8 | 75-05 | Back on the guide: the rose line clears. "That's it. Back on the guide." (Refine: "…Back inside the guide.") | Spec 8 stage 05 |
| - [ ] 1.9 | 75-04 | A stroke that stays off the guide: "No harm done. Wipe it away and draw it again." | Spec 8 |
| - [ ] 1.10 | 75-07 to 75-10 | One brow done, then the other. Both settle to gold at the end. **No score** is ever shown. | Spec 8 stages 07 to 10 |
| - [ ] 1.11 | 75c | Face lost: the line is removed, never left floating. It returns when the face returns. | Spec 3 rule 6, 75c |
| - [ ] 1.12 | 75e | Hand over the brow: the guide dims and is never drawn on top of the hand | Spec 75e |
| - [ ] 1.13 | 75b | Low light is never shown as a drift mistake | Spec 3 rule 7, 75b |
| - [ ] 1.14 | 77 | SAVE LOOK keeps the look with its tracing guide. LEAVE WITHOUT SAVING asks first (77c). | Spec 77, 77c |

**Open question for the client, before building around it.** Items 1.6 to 1.9 need the app to see what she has actually drawn on her face (specification question 5). If the app can't do that yet, say so to the client. Don't ship a fake indicator.

**Also confirm with the client.** On the call she said nobody should ever trace their brows with a finger. The specification still keeps the finger-drawn guide (45 to 49c) as the fallback when live tracing can't run (49c). Ask whether 45 to 49c stays as that fallback, or is removed.

---

## 2. Full / Ombre on screen 29: missing in the reviewed build

| # | Screen | Check | Spec |
|---|---|---|---|
| - [ ] 2.1 | 29 | A FULL / OMBRE toggle sits on the preview, centred, its bottom edge 10 pt above the preview's bottom edge | Spec 7, entry 29 |
| - [ ] 2.2 | 29 | Visible 176 × 36 pt, two segments of 88 × 36 pt, touch area 88 × 44 pt each | Spec 7, entry 29 |
| - [ ] 2.3 | 29 | Fill `#080808` at 84%, 1 pt gold border `#C9A84C`, 11 pt Montserrat SemiBold, gold on dark (dark on gold when selected), soft shadow | Spec 7, entry 29 |
| - [ ] 2.4 | 29 | Ombre shows a **gradient**: soft and light at the head, defined at the tail, with visible hair strokes. **Not a flat block.** | Spec 2, Handover 7.2 |
| - [ ] 2.5 | 29 | Tapping Straight or Micro removes the toggle. The preview and caption show Full. | Spec 7, entry 29 |
| - [ ] 2.6 | 29 | Back on a style with Ombre, the toggle returns with her last finish (remembered for her account, also on a new device) | Spec 7, entry 29 |
| - [ ] 2.7 | 29 | Caption: `ARCH · DARK BROWN · OMBRE` in Ombre, with no suffix in Full | Spec 7, entry 29 |
| - [ ] 2.8 | 29 | Switching finish changes the preview straight away, and the camera never freezes, flashes or goes blank | Spec 3 rule 5 |
| - [ ] 2.9 | 30 to 36 | The finish chosen on 29 carries through, in both modes. There is no toggle on these screens. | Spec 2 |
| - [ ] 2.10 | 37 | The saved name adds ` · Ombre`: `Arch · Defined · Dark Brown · Ombre` | Spec 7, entry 37 |
| - [ ] 2.11 | 36, 50 | A saved Ombre look comes back as Ombre | Spec 7, entry 36 |
| - [ ] 2.12 | 29 (no scan) | A guest or a user with no scan sees no toggle | Spec 7, entry 29 |

---

## 3. Brow fit and realism (Bold "past the ear")

What the client saw: Bold reached toward the ear and "doesn't sit inside the face". The server now shortens Bold to 1.80 eye widths and keeps every style's tail inside the face outline.

| # | Screen | Check | Spec |
|---|---|---|---|
| - [ ] 3.1 | 29, 30, 32 to 34, 36 | **Bold** ends inside the face on both sides, with the head straight and turned slightly | Client review |
| - [ ] 3.2 | Same | All eight styles end inside the face: Arch, Structured, Feathered, Bold, Straight, Micro, Sharp, Rounded | Client review |
| - [ ] 3.3 | Same | Test at least three different faces (different face shapes and skin tones) | Client review |
| - [ ] 3.4 | 89 to 94, 29 (no scan) | Library images: Bold doesn't run past the ear. These may be pre-made images the server change doesn't touch, so check them by eye and replace any that do. | Client review |
| - [ ] 3.5 | All live overlays | It looks like hair on skin, not a sticker. Soft edges, matching the light on her face. | Spec 3 rule 3 |
| - [ ] 3.6 | All live overlays | Each brow follows its own side of the face; the two don't look pasted from one picture | Spec 3 rule 4 |
| - [ ] 3.7 | Old saved looks | Looks saved before this change keep their old images until rendered again. Re-render test accounts before the client test. | Handover 7.3 |

---

## 4. Other screens the client asked about

| # | Screen | Check | Spec |
|---|---|---|---|
| - [ ] 4.1 | 42 | "Why this shape" view 1: the recommended style as heading, three lines specific to her face shape (7 versions), WHY IT SUITS YOUR FACE → 43, Try another → 29 | Spec 8, entry 42 |
| - [ ] 4.2 | 43 | View 2: the face outline for her shape, fitted to her own landmarks. Three-line headline, three-line body and tagline (7 versions). SEE THE DIFFERENCE → 44. The client will send a cleaner image for this screen. | Spec 8, entry 43 |
| - [ ] 4.3 | 44 | The Difference: BEFORE (her natural brow) and AFTER (the recommended style in her mode), the same photo and framing. "After: Arch". No line about saving. | Spec 8, entry 44 |
| - [ ] 4.4 | 27 | Two recommendation chips only. A style she chose on 29 that isn't recommended joins as a third chip, and the label reads YOUR STYLE, AND TWO MORE. See all styles → 29. | Spec 5, entry 27 |
| - [ ] 4.5 | 28 / 29 | "Browse all styles instead" is there for someone who doesn't want the recommendation | Spec 5, entries 28, 29 |
| - [ ] 4.6 | 74 | START POINT, LENGTH and THICKNESS change the selected brow's guide only. Touch areas are at least 44 × 44 pt. | Spec 8, entry 74 |
| - [ ] 4.7 | 22a | A returning member with a scan goes straight to 29, with no new capture | Spec 5, entry 22a |

---

## 5. Before sending the build to the client

- [ ] Sections 1 to 3 pass on iPhone and Android.
- [ ] A screen recording of a full tracing session (36a → 73 → 74 → 75 or 76 → 77) in each mode is posted in the group chat.
- [ ] A short clip of 29 showing Full, Ombre, Straight (toggle removed) and back to Arch (Ombre restored).
- [ ] Bold on three faces, as stills from 36.
- [ ] Daniel sends the TestFlight build to the client. The client sends videos or screenshots of anything wrong to the group chat, and meets Masooma to test together.
