# ARCH Developer Notes · Behaviour Rules

Plain-English edition · 1 November 2026. For the developer who builds ARCH.

## About this document

1. These notes hold the rules that no screen image can show.
2. They cover four things. When a screen appears. What the app remembers. What it stores and deletes. What is free.
3. They replace `ARCH_Developer_Notes_Daniyal.md` and the Brow Modes notes where those files disagree.
4. Where these notes are silent, the old files still apply.
5. If a PNG disagrees with these notes, follow these notes.
6. This edition changes wording and layout only. It also corrects three lines in section 7. See the Change Log.

### How to read the rules

| Label | Meaning | What to do |
| --- | --- | --- |
| No label | Decided. | Build it. |
| PROPOSED | Suggested. Not approved. | Do not build it as if decided. |
| Open | Not decided, or not confirmed. | Listed in section 9. Do not guess. Ask. |

Each section has two parts. "Build" says what to build. "Reasons" says why. You can build from "Build" alone. A section with no "Reasons" part needs none.

### Status of the drawn screens

1. Batches B, C, D and E are approved and drawn.
2. The team has not installed them yet.
3. They go out together in one upload, with the regenerated exports.
4. Screen 02 now reads `within 24 months of your last use`. This applies to the image, the text and the strings file.
5. The retention line is the only change to screen 02.
6. The line runs close to the edge of its box. The native text wrap of the platform sets the final line break.

### Terms

Each term has one meaning. The notes use no other word for it.

| Term | Meaning |
| --- | --- |
| User | The person who uses the app. |
| Guest | A user with no account. |
| Free account | A user with an account and no membership. |
| Member | A user with a paid membership. |
| Scan | The face scan. It makes the brow profile. |
| Brow profile | The measurements that ARCH holds for one user. |
| Mode | Refine mine or Reshape mine. |
| Refine mine | The mode that fills and grooms the user's own brow. |
| Reshape mine | The mode that places the style's shape on the user's brow. |
| Tracing | The guided drawing session. REFINE and SCULPT are its two sessions. |
| Style | One brow shape, for example Arch. |
| Intensity | Understated, Defined or Deliberate. |
| Tone | One of six skin tones: Fair, Light, Medium, Tan, Deep, Rich. |
| Look | A saved result. It has a name, a style, an intensity and a colour. |
| Recipe | The style, intensity, colour and mode of a look. |
| Library image | A stored WebP image of a style. It is not live AR. |
| Live AR | An image drawn on the user's own face, from the scan. |
| Gate | The screen that asks for an account (13) or a membership (64). |
| Consent record | The stored proof of the user's consent. |

Screen numbers are in the list at the end of this document.

---

## 1. Conditional routes

### 1.1 When screen 23 appears

#### Build

Screen 23 is the camera permission and face scan consent screen.

| State | Route |
| --- | --- |
| No consent record (first scan) | 22 → 23 → 25 |
| Consent recorded, not withdrawn (every later scan) | 22 → 25 |
| Consent withdrawn by Delete my face scan | 22 → 23 → 25 |

Rules:

1. Show screen 23 once per account, at the first scan.
2. Show it again only after the user uses Delete my face scan.
3. The build must tell the three states apart. Confirm that it can (section 9, question 1).
4. Keep screen 23. The team may remove it later.
5. Put screen 23 behind one condition. Build it so that the team can remove it.
6. Keep screen 02. Record its consent separately from the consent on screen 23.
7. Omit the optional camera line on screen 22. Keep screen 22 clean.
8. Keep the iOS camera purpose string `NSCameraUsageDescription`. Apple requires it.
9. Do not release that string until the owner supplies the wording (section 9, question 19).

#### Reasons

- Screen 23 is the Google Play disclosure. It must appear immediately before the permission prompt.
- Screen 23 meets that rule only when it appears.
- On a new device, the system prompt can appear with no screen 23 before it. The same happens after a reset of camera permission in system settings.
- The three states above do not cover that case. It is not decided (section 9, question 2).
- Screen 22 needs no camera line. The purpose string does not depend on screen 22.

### 1.2 Try-on route

#### Build

Main route:

22 → 23 (first scan only) → 25 → 27 → 28 → 29 → 30 → 31 → 32, 33 or 34 → 36 → 37 → 38

Screen 31 sends the user to 32, 33 or 34. The intensity the user selects on 31 decides which.

Rules for screens 22 to 35b:

1. Screen 30 has one gold button: `HOW FAR TO TAKE IT`. It goes to 31.
2. Remove `SAVE THIS LOOK` and `TRY ANOTHER` from screen 30.
3. Screen 30 keeps four things. They are the face, the mode toggle, the gold button and the back arrow.
4. Screen 31 has a Compare control. It goes to 35a.
5. Route: 35a → 35b → 36.
6. The back arrow on 35b goes to 35a. It keeps the user's selections.
7. `Go back to all styles` on 35b is a text link. It goes to 29.
8. Screen 22 has a `Browse styles instead` link. It goes to 29.
9. Screen 28 has one button. It goes to 29.

Recommendations:

1. Screen 27 shows two style chips: one recommended style and one alternate.
2. Take both from Table 2 of the Measurement Reference. Table 2 gives one pair for each face shape.
3. Do not show a third recommended chip. Feathered was the third chip. It is not in Table 2. The one exception is a style the user chose on screen 29 that is not one of the two (section 9, question 12): it is added as a selected third chip.
4. On screen 29, mark the two recommended tiles with a small gold dot.
5. Add the legend `Recommended for you` to screen 29.

Screen 29 by state:

| Item | User has a scan | User has no scan |
| --- | --- | --- |
| Style selected by default | The first recommendation on 27 | None |
| Recommended markers | Yes | None |
| Caption under the preview | `ARCH · DARK BROWN` (style and colour only) | None |
| Large preview | Live AR, in the user's mode | Library image of the selected style |
| Mode toggle | None on 29 | None on 29 |
| `PREVIEW THIS LOOK` | No rule here | Disabled until the user taps a style |

Screen 29 with no scan:

1. This is one state. It has no mode and no toggle.
2. Before a tap, the preview panel stays. It shows one line: `Choose a style to see it.`
3. Set that line in muted type. Centre it in the space of the preview.
4. After a tap, the panel shows the library image of the style. It shows one preview and no toggle.
5. Remove the caption `NO STYLE SELECTED`.
6. Keep the space of that caption. After a tap, `ARCH · DARK BROWN` appears there.
7. The design shows both states: `S29_Style_Selector_NoScan` and `S29_Style_Selector_NoScan_Selected`.
8. In the second file, ARCH is an example. It is not a recommendation.

Preview with no scan:

1. The user taps a style on screen 29.
2. The user taps `PREVIEW THIS LOOK`.
3. The app starts the scan: 22 → 23 (first scan only) → 25 → 27.
4. The app goes to 30 with that style applied.
5. If the user is a guest, screen 13 appears first.
6. After the guest creates an account, she follows one route: screen 05, then screens 14 to 18, then screen 29 with her chosen style already selected. She has no scan and no skin tone until then, so she cannot reach a try-on without 14 to 18. Screen 14 has no `I’ll add this later` link, because skin tone is the input the image library depends on. Screen 16 keeps its `I’ll add this later` link, because style direction can wait. `PREVIEW THIS LOOK` is ready. Decided 1 November 2026.
7. On this route, screen 27 does not offer `EXPLORE YOUR STYLES`.
8. The app keeps her chosen style through the sign-up and screens 14 to 18 (section 2, Mode, item 4). It keeps nothing else. The developer decides how.

Gold button on screen 27:

| State on screen 27 | Gold button | Goes to |
| --- | --- | --- |
| No chip selected | `EXPLORE YOUR STYLES` | 28 |
| A recommended chip selected | `PREVIEW` plus the style name, for example `PREVIEW ARCH` | 30, with that style applied, in the user's remembered mode |
| A style chosen on 29 that is not one of the two recommended | The style joins the row as a selected third chip, after the two recommendations, which stay unselected. `PREVIEW` plus its name, for example `PREVIEW BOLD` | 30, with that style applied, in the user's remembered mode |

1. The wording `PREVIEW ARCH` is approved.
2. Never name a style on the button unless the user selects that chip.
3. Mark the selected chip with a gold border.

Mode and images:

1. The mode toggle appears only after a scan exists.
2. Before a scan, show one preview. It is a library image.
3. After a scan (22, 23 on the first scan only, 25, 27), the mode applies.
4. After a scan, the toggle appears on the screens that carry it.

| Item | Type | Depends on mode? |
| --- | --- | --- |
| Small style tiles on 29 | Library image | No. One image serves both modes. |
| Large preview on 29, user has a scan | Live AR | Yes |
| Large preview on 29, user has no scan | Library image | No |
| AFTER image on 44 | Live AR | Yes |
| Screens 30 and later | Live AR | Yes |

1. Make every Refine mine image from the user's scan.
2. Never take a Refine mine image from the library.
3. The design mocks show an illustration of each mode. They are not library assets.

#### Reasons

- Two recommendations, not three: nothing in Table 2 supports a third.
- Screen 29 selects the first recommendation by default. The user then sees a value that the app gave the user.
- With no scan, no style can be a recommendation. A default choice would show a value that no scan gave (section 3, rule 2).
- An empty preview box looks broken. A collapsed panel makes the layout jump when the user taps. So the panel stays and shows one line.
- The caption `NO STYLE SELECTED` repeated the panel line. Its space stays so that the layout does not move.
- The preview with no scan is not an error. It is a longer route through the scan.
- The button must not name an unmarked style. The button would then claim a choice the user did not make.
- Refine mine fills the user's own brow. With no scan, nothing exists to fill.
- No library photograph can stand for Refine mine.
- Reshape mine places a known shape. That is why a library image can show it.
- The small tiles show the style, not the user. One library image serves both modes.

### 1.3 Recommendation route (after the merge)

#### Build

| State | Route |
| --- | --- |
| First time, no scan held | 39 → 22 → 23 (first scan only) → 25 → 27 |
| Already scanned | 39 → 27 |
| User used Delete my face scan | Same as first time |

Rules:

1. Screens 40 and 41 no longer exist.
2. The once-only rule for screen 23 is the same on this route.
3. Do not ask a user with a scan to scan again.
4. In the already-scanned state, screen 39 shows `SEE MY RECOMMENDATIONS`.
5. In that state, the body of screen 39 says the user's scan will be used. The owner approved the wording. Batch C shows it.
6. Scan age limit: not decided (section 9, question 13).

Routes from screen 27 to screen 30:

| Control | On screen | Goes to |
| --- | --- | --- |
| `Why these suit you` link | 27 | 42 |
| `WHY IT SUITS YOUR FACE` | 42 | 43 |
| `Try another` | 42 | 29 |
| `SEE THE DIFFERENCE` | 43 | 44 |
| `Try a different recommendation` | 43 | 27 (was 41) |
| `THIS IS THE ONE` | 44 | 30, recommended style applied, in the user's remembered mode |
| `Try another style` | 44 | 29 |

Rules for screens 42, 43 and 44:

1. The eyebrow on screen 42 reads `ABOUT THIS SHAPE`.
2. Remove `Save for later` from screen 42.
3. Remove `TRY THIS ON` from screen 42. Its one gold button is `WHY IT SUITS YOUR FACE`.
4. Until the user chooses otherwise, the remembered mode is Refine mine.
5. On screen 44, BEFORE and AFTER show the same woman. They use the same photograph and framing.
6. BEFORE shows the natural brow.
7. AFTER shows the result for the mode. Reshape mine places the style. Refine mine fills the brow.
8. In production, both images come from the user's scan and live AR.
9. In the mocks, both panels are composites on one plate.
10. Remove the line `Your before and after is saved automatically to My Looks.` from screen 44.
11. Move the button and the link up on screen 44 to close the gap.
12. Failures on this route (face not found, poor light) use screens 26, 84 and 85. Screen 40 has no failure screens.
13. The copy on screens 42 and 43 must explain why a shape suits a face.
14. That copy must be specific. This holds for all seven face shapes.
15. The headline on screen 43 describes an oval face. It matches screen 27.
16. Copy for all seven shapes is in `ARCH_Face_Shape_Copy.md`. It awaits approval (section 9, question 14).
17. Screen 43 shows all seven shapes. Each has its own proportion outline.
18. The drawn outline lies over a sample oval face. In the build, fit it to the user's face landmarks.
19. Question 24 in section 9 is open. It asks how the scan sorts faces into seven shapes.

Dependency:

1. The AR partner must confirm in writing that one scan gives both reads. The reads are the brow profile and the recommendation data (section 9, question 3).
2. Until then, keep screens 40 and 41 in the build.
3. If the app needs two reads, screens 25 and 40 stay separate.

#### Reasons

- The user already holds the data. A second scan would ask for data that ARCH already has.
- Screen 42 had `Save for later`. The user has not tried the style yet. A save here would duplicate the save on screen 37.
- The user reaches screen 30 through screens 43 and 44. So screen 42 needs no `TRY THIS ON`.
- The saving line on screen 44 claimed a save. The user did not ask for it.
- The mocks on screen 44 show one eye. Faces elsewhere show two.
- The team tried a two-eye composite. It cannot reach photoreal standard without a browless two-eye base of that woman. That base does not exist. So the existing pair stays.

### 1.4 What screen 36 shows from other entries

#### Build

Screen 36 opens from the main flow and from five other places:

| Entry | Screen |
| --- | --- |
| My Looks | 50 |
| Library | 89 to 94 |
| Welcome | 21 |
| Leave-session prompt | 75d |

1. What screen 36 shows for a style the user has not tried is not decided.
2. Whether `SAVE THIS LOOK` appears on a look that is already saved is not decided.
3. See section 9, question 9.
4. Until then, apply section 3, rule 2. Screen 36 shows only values that a user or a scan set.

### 1.5 Leaving a tracing session (screen 75d)

#### Build

1. `LEAVE SESSION` goes to screen 36.
2. Plan: show one line. It says the session ended and the app saved nothing.
3. Do not write that line until the developer confirms it (section 9, question 6).
4. The line is true only if leaving discards nothing already saved.
5. Until then, go to screen 36 with no line.

### 1.6 The gate: three tiers, one gate, two entrances

#### Build

| Tier | User | Free to do | Not free |
| --- | --- | --- | --- |
| 1 | Guest | Browse styles. Screen 29 and the screens around it stay open. The user sees a sample face. | Scan |
| 2 | Free account | Scan, recommendations, all eight styles, try-on, intensity, comparison. Everything through screen 36. | Save a look. Trace. |
| 3 | Member | Save a look. Trace. Hand-drawn guides (45, 49a, 49b). | — |

Entrances:

| Entrance | The gate appears when the user | After purchase |
| --- | --- | --- |
| Save | Taps `SAVE THIS LOOK` on 36, or the save control on 37 | `ENTER ARCH` on 67 returns the user to 37. The look stays. |
| Trace | Taps `BEGIN` on 36a | The app returns to 36a. `BEGIN` is ready. |

The trace entrance in steps:

1. The user taps `TRACE THIS LOOK` on screen 36.
2. Screen 36a appears. It says the user will draw the look by hand, with a guide. It lists what the user needs.
3. The user taps `BEGIN`.
4. The gate appears.

Rules:

1. Tracing must never reach screen 73 without passing the gate.
2. The gate does not appear on screens 27, 29, 30 or 36a.
3. After the gate, return the user to the action. The user does not repeat any work.
4. A guest who creates an account follows one route: screen 05, then screens 14 to 18, then screen 29 with her chosen style already selected (section 1.2, step 6). She does not go to home, and she does not return to the screen where the gate appeared. Decided 1 November 2026.
5. Screen 13 requires an account. It shows no pricing. Screen 13a (below) shows no pricing either.
6. A free sign-up must not look like a paywall. Screen 13a shows no price, says what an account keeps, and offers `Keep browsing`, so it is not one.
7. A free account scans and keeps the brow profile. Screen 13 says so.
8. Screen 64 lists three benefits. They are step-by-step tracing for every style, saved looks, and new styles from the team.
9. Remove the guides line from screen 64.
10. The subtitle on screen 64 reads `The part you do yourself. Membership buys the doing.`
11. Screen 64 does not list try-on, recommendations or the brow profile. They are free.
12. The 14-day free trial is the same on every platform (section 6).

Screen 12a:

1. Screen 12a says `A preview. The full experience begins with an account.`
2. This is consistent with these notes. Do not change it.

Guest tab bar (screens 12 and 12a). Decided 1 November 2026:

1. A guest sees all four tabs: `HOME`, `TRY-ON`, `LOOKS` and `PROFILE`.
2. `LOOKS` and `PROFILE` do not open the member screens (50 and 53). They open the account gate.
3. The account gate is a new screen, 13a. Its body line says `Your saved looks and your brow profile are kept in your account.`
4. Screen 13a has `CREATE AN ACCOUNT`, which goes to 05, and `Keep browsing`, which returns to the guest screen she came from (12 or 12a). It shows no pricing.
5. After she creates an account, she follows the route in rule 4 above.
6. `HOME` opens 12 and `TRY-ON` opens 12a for a guest.

#### Reasons

- A guest sees a sample face. The user's own face needs a scan. A scan needs an account.
- Hand-drawn guides teach the user to draw the user's own brows. That is the paid product.
- The user reaches the gate to keep a look or start tracing.
- Screen 36a explains tracing before the gate asks for payment.
- The team removed the guides line. Step-by-step tracing already covers it.
- Three honest benefits are better than four with one filler.

### 1.7 Screen 49d (removed)

#### Build

1. Screen 49d is removed from the set. Decided 1 November 2026.
2. Do not build it. No screen leads to it.
3. Saving a hand-drawn guide stays explicit. On screen 49 the user taps `SAVE MY GUIDE`. Screen 49a follows. Screen 49b confirms the save.
4. Keep `SAVE MY GUIDE`, 49a and 49b exactly as drawn.
5. If a file named `S49d_Guide_Complete` (PNG or JSON) is in the repository, delete it.

#### Reasons

- Screen 49b already confirms the save. Screen 49d said the same thing in different words.

### 1.8 My Looks tabs

All rules in this section are approved.

#### Build

1. The tabs are `ALL`, `TRACED` and `PREVIEWED`. They replace `ALL`, `STYLE`, `GUIDES` and `SAVED`.
2. Guides are not a category. Every look has the tag `TRACED` or `PREVIEWED`.
3. `TRACED` holds looks the user traced. This includes hand-drawn guides.
4. `PREVIEWED` holds saved looks that the user has not traced.
5. On the `ALL` tab, show the tag on every look. `TRACED` is gold. `PREVIEWED` is muted grey.
6. Screen 49b reads `This look is in My Looks.`
7. The button on 49b is `VIEW IT IN MY LOOKS`. The wording comes from screen 77. It opens the `TRACED` tab.
8. Keep the tab row and the navigation bar the same for every account type.

Empty states:

| Tab | Text |
| --- | --- |
| `ALL` | `Nothing saved yet.` (existing wording from screen 51) |
| `TRACED` | `Nothing traced yet.` |
| `PREVIEWED` | `Nothing previewed yet.` |

1. Each empty state has one gold button: `CREATE A NEW LOOK`.
2. Show no tick. A tick means done. The user has done nothing.
3. Open: whether the "+" on the populated button carries over.

Routing for `CREATE A NEW LOOK`:

| Condition | Goes to |
| --- | --- |
| The user holds a scan | 29 |
| The user holds no scan | 22 |

1. This applies on screen 50 and on the three empty states.
2. It is the same rule as `PREVIEW THIS LOOK`.

Free account:

1. My Looks shows for a free account. It shows an empty state.
2. The text is `Nothing saved yet. Keeping your looks is part of membership.` Screen 51, Empty, Free, shows it.
3. The same text appears under `TRACED` and `PREVIEWED`.
4. Add the text link `See what membership includes`. The owner approved it on 30 October 2026. It goes to 64.
5. Keep the gold button `CREATE A NEW LOOK`. The routing is the same.

Use of the word guide:

1. The word guide is correct as an ordinary word during tracing.
2. Screen 71 keeps its use.
3. Do not audit the other screens for this word.

#### Reasons

- The new tabs remove a clash. Screen 77 says "tracing guide". Screen 49b said "Saved Guides".
- A navigation bar that changes shape between account types is worse than an empty tab.
- A tick means done. In an empty state, the user has done nothing.

---
## 2. State and persistence

### Build

Mode:

1. The starting mode is Refine mine. It stays until the user chooses otherwise.
2. Remember the user's last mode for each account. Do not remember it for each device.
3. The mode follows the user to a new device.
4. A guest cannot scan. A guest never reaches screen 30. The app remembers the style a guest chooses, and only that, until she signs up or the session ends. It remembers no mode for a guest (section 1.2).
5. Screens 29 and 31 inherit the mode. They have no control of their own.
6. The mode toggle is on screens 30, 32, 33, 34, 35b and 36.
7. Store the mode with each look. Screens 21 and 50 show it, for example `Saved 12 October 2026 · Reshape mine`.

The mode on leaving screen 36 decides the tracing session:

| Mode | Tracing session | First frame |
| --- | --- | --- |
| Reshape mine | SCULPT | 75-01 |
| Refine mine | REFINE | 76-01 |

Screen 74 has no switch. The user cannot change mode after tracing begins.

Screen 36a:

1. Show screen 36a every time. Do not show it on first use only.
2. It names the session.
3. It says what the user needs.
4. It has one gold button: `BEGIN`.
5. It states no duration until the app measures a duration.
6. It never uses the word mirror.
7. It does not repeat the checks on screen 73: light, steady phone, product to hand.

Screen 30a (mode explanation):

| Item | Rule |
| --- | --- |
| Trigger | The user arrives on screen 30. Wait two seconds, so the user can look first. |
| Frequency | Once for each account. Not once for each device. |
| Flag | An account-level flag replaces the per-install flag `modeIntroSeen`. |
| Dismiss control | `GOT IT`, a text link. It is not a gold button. |
| Position | Below the photograph. |
| Toggle | The toggle stays active while 30a is up. |
| Drawn states | Two: the Refine state and the Reshape state. |

Skin tone:

1. The user sets skin tone on screen 14.
2. The user can change skin tone from Profile.
3. No Profile screen for this exists (section 9, question 15).

#### Reasons

- Tracing follows the mode, so the user's choice on screen 36 decides the session.
- The phone is the mirror. So screen 36a never says mirror.
- Screen 73 already holds the checks. Screen 36a does not repeat them.
- The earlier trigger for 30a was the first tap on the toggle, after 1,000 ms. The new trigger replaces it.
- Four older files still describe the old trigger. They are the Component Specification (entry 51), the old notes, the change logs, the prototype. Treat them as history.

---

## 3. The two spec rules

Source: `ARCH_Enhance_Replace_Modes/04-documents/ARCH_Spec_Rules.md`. This document gives both rules in full. Check every screen against both.

### Rule 1 · Write "whose brow it is" twice

#### Build

1. Write twice every sentence that says whose brow it is, or what it was before.
2. Write one version for Refine mine and one for Reshape mine.
3. Show the version for the user's current mode.
4. Sentences about intensity, colour or feeling may stay the same in both versions.

How to test:

1. Read each line on a screen that follows the mode choice.
2. Write two versions when a line claims one of three things. The brow is the user's own. The brow was already there. The app only made it clearer.

Known breaches:

| Where | Breach | Decision |
| --- | --- | --- |
| 32 | `The brow your face was wearing all along, simply made clearer.` shows in Reshape mine. | Write a Reshape line for 32. The Refine line is already separate. Batch 2 shows the new line. It is PROPOSED until the owner approves it. |
| 36 and 38 | Two style lines fail in Reshape mine: `The Shape That Was Always There` (Arch) and `As If You Woke Up With It` (Feathered). | Remove the poetic line, or keep it only on 36 in different type. Not decided (section 9, question 16). Batch 2 draws it removed. |

This is a note, not a breach. Screens 01, 03 and 60 carry brand lines before the user selects a mode. Example: `The shape that was always yours.`

#### Reasons

- In Refine mine, the brow is the user's own, filled and groomed.
- In Reshape mine, the brow is the style's shape placed on the face.
- A sentence that is true in one mode is false in the other.

### Rule 2 · No screen shows a value that nobody set

#### Build

1. A screen shows a style, intensity, colour, mode, name or state only in these cases:
   - The user chose it.
   - The app computed it from the scan.
   - The app stored it from an earlier action of the user.
2. A screen with no value shows nothing. Or it says plainly that no value is set.
3. If a screen has two paths to it, set every value on both. Or hide the value.

Known breaches:

| Where | Breach | Decision |
| --- | --- | --- |
| 29 | The caption reads `STRUCTURED · DEFINED · DARK BROWN` before the user selects an intensity. Structured is the default, while 27 recommends Arch. | Select whatever 27 recommended. Never hard-code a style. Before intensity, the caption is `ARCH · DARK BROWN`. Approved and drawn. |
| 36 from the library | Not defined for a style the user has not tried. | Not decided (section 9, question 9). |
| 36, 37, 38 | Screen 36 reads Structured. Screen 37 fills in Arch. The tagline is not the name the user gives. | Build the name from the user's choices. Read it from one stored value (section 4). |
| 44 | It says the app saves the before and after to My Looks. The user did not ask for that. | Remove the line. Drawn in Batch C. |

Placeholder values in the screens are not breaches. They are sample names, dates and a card ending 4242. Replace them with real values in the product.

---

## 4. Data and naming

### Build

Look name:

1. The look name is one stored value.
2. Build it from what the user chose: style, intensity and colour. Example: `Arch · Defined · Dark Brown`.
3. Screen 37 fills the name in by default. The user can edit it to anything.
4. Screens 36, 38, 50 and 21 read the same stored value.
5. Screen 36 shows what the user chose. A Structured and Arch mismatch is a defect.

Screen 77 (tracing complete):

1. Screen 77 lets the user name the trace. It uses the same default name.
2. It says what the app kept, and that the user traced it.
3. Its tone differs from screen 38. It acknowledges. It does not congratulate.
4. The build must write both branches:

| Case | What screen 77 does |
| --- | --- |
| The user taps `TRACE` on 36 without saving first. | Create a new look. Use the same default name. The user can rename it. |
| The user saved on 37 first. | Attach the trace to that look. Do not create a second look. |

Other rules:

1. Screen 29 selects by default whatever screen 27 recommended.
2. A square face may get Rounded as the recommendation. Do not hard-code Arch or Structured.
3. Keep the 24 editorial titles in the data model (89 to 94).
4. Whether to show the editorial titles depends on section 9, question 16.
5. On screens 89 to 94, each card shows three things. They are a thumbnail, the style name and the intensity name.
6. Open: what a saved look stores. The options are a photograph composite, a recipe, or both.
7. The Delete my face scan rules assume both can exist (section 9, question 5).

---
## 5. Privacy

### 5.1 Retention

#### Build

1. Keep facial and biometric data for 24 months from the last interaction.
2. Use one rule in every market. Do not vary it by market.
3. Screen 02 reads `within 24 months of your last use`. Build the line from the strings file.
4. Keep the 24 months as a configuration value. Do not hard-code it in logic.
5. This rule covers facial and biometric data only.
6. It is not a retention rule for payment, tax or other business records. Those follow the retention that the law requires.
7. Saved photographs: the retention rule is not final.
8. Build so that the app can keep and delete biometric measurements and saved photographs separately. Section 5.4 already treats them this way.
9. Do not release a retention rule for saved photographs until the owner confirms it.
10. The Privacy Policy lives at `cbygroyals.com/privacy`. The team maintains it outside the app build. The app links to it.

Open (section 9, question 17):

1. What counts as last interaction: app open, scan or try-on.
2. What the deletion removes.

#### Reasons

- The 24-month period may change. A configuration value lets it change without a code change.

### 5.2 Consent record

#### Build

1. Store the biometric consent with a timestamp and the policy version.
2. Record screens 02 and 23 separately, while screen 23 stays.
3. On screen 02, the four boxes start unchecked.
4. On screen 02, `CONTINUE` stays disabled until the user ticks all four boxes.
5. The age box is a self-declaration. Its wording is not final.
6. Re-consent when the Privacy Policy version changes is not decided as a product rule.

#### Reasons

- Store the policy version with each consent record. Then the team can add re-consent later.

### 5.3 Privacy Policy row

#### Build

1. Add a `PRIVACY POLICY` row to screen 53, under `LEGAL`.
2. The row opens `cbygroyals.com/privacy`.
3. Terms of Use and Privacy Policy are two separate rows.

#### Reasons

- The user must find the policy easily inside the app after onboarding.

### 5.4 Delete my face scan (on screen 55)

#### Build

The owner decided this. The wording is approved.

Steps:

1. Screen 55b is step 1. It lists what the app removes: the user's measurements and brow profile.
2. Screen 55b also says what stops working: try-on cannot run until the user scans again.
3. Screen 55c is step 2. It is a separate screen with two choices of equal weight.
4. The question on 55c is: `Your saved looks include photographs of your face. Remove those too?`
5. Delete nothing until the user answers step 2.
6. If the user backs out at either step, nothing happens.
7. Steps 1 and 2 are one action.
8. If the user removes the photographs, keep the look.
9. The look then has no photograph. It keeps its record: style, intensity and colour. The user can re-apply it.
10. After deletion, mark the consent as withdrawn.
11. The next scan shows screen 23 again.
12. Screen 55f is what screen 55 shows when there is no scan to delete.

Wording not yet applied:

1. Screens 55b and 55c say only that the app removes photographs.
2. They should say that the app keeps the look.
3. This change is PROPOSED. The design does not show it yet.

#### Reasons

- A checkbox that the user may miss is wrong for this choice. So step 2 is a separate screen.
- Deleting the whole look would penalise the user for a privacy choice.

### 5.5 Account deletion

#### Build

1. Give a 14-day recovery window.
2. If the user signs in within 14 days, stop the deletion.
3. Engineering must not purge any data before the 14 days end.
4. Send the confirmation email before purging the account record.
5. If sending the email fails, do not show the email-sent line.
6. Deleting the account must not trigger an in-app purchase.
7. Screen 78 uses the StoreKit call `showManageSubscriptions(in:)`. Do not use a URL.

#### Reasons

- Apple billing continues after the user deletes the account. It stops only when the user cancels in Apple settings.

### 5.6 What not to claim

#### Build

1. Make no absolute claim about data or security in any copy.
2. Never write `Your data. Yours alone.`
3. Screen 02 has the sentence `We do not sell them, share them, or use them to identify you.` It is not final (section 9, question 18).
4. Three screens wait for the AR engine answers. They are 61 (privacy wording), 75e (hand occlusion) and 87 (Try-On row).
5. Confirm Saved Guides caching before screen 87 goes out.

#### Reasons

- The sentence on screen 02 depends on where the app stores the brow profile.
- It also depends on whether a third party processes face data.

---

## 6. Commerce

### Build

Prices:

| Plan | Price |
| --- | --- |
| Monthly | $19.99 |
| Yearly | $179.99 |

1. Take prices from the price configuration. Do not hard-code them in copy.
2. The yearly plan saves $59.89 against twelve monthly payments.

Trial:

1. The free trial lasts 14 days on every platform.
2. The product computes the trial dates. Both dates are dynamic.
3. `FREE UNTIL` is the last free day.
4. `FIRST CHARGE` is the next day.
5. The two dates are one day apart.
6. Example: a trial starting 30 October shows `FREE UNTIL` 12 November and `FIRST CHARGE` 13 November.

Plan name:

1. The plan name is `ARCH Membership · Annual`. It is dynamic.
2. It appears on screens 54, 63, 66, 67, 71 and 72.

Purchase screens:

1. The gate is at screen 37 and at the trace entrance. It is not at screen 27 (section 1.6).
2. Screens 66 and 69 are for web only. iOS and Android use the native purchase sheet.
3. Screen 65 (phone number) follows payment on every path: 66 → 65 → 67.
4. `Not now` on screen 65 is a text link.
5. Screen 82 (notification priming) comes after screen 67.
6. Screen 68 reads 16 days. Confirm the grace length against the billing configuration.
7. `SWITCH TO MONTHLY` on screen 70 uses `showManageSubscriptions(in:)`.
8. Card 1 on screen 70 takes its figure from the price configuration.

Refund wording on screen 71. One key with three values, chosen by billing path:

| Billing path | Key | Wording | Status |
| --- | --- | --- | --- |
| App Store (iOS) | `screen_71_copy_0544` | `Refunds for App Store purchases are handled by Apple, under Apple’s policies.` | Approved (1 November 2026) |
| Google Play (Android) | `screen_71_copy_0544_android` | `Refunds for Google Play purchases are handled by Google, under Google Play’s policies.` | Approved (1 November 2026) |
| Web | `screen_71_copy_0544_web` | Empty | Empty until further notice |

1. The screen image is drawn once, with the App Store value.
2. When the value is empty (web), do not draw the line or its bullet. The card height follows its content. Confirm with a build screenshot.
3. The wording may change by region.
4. Keep all three in the strings file. Do not hard-code any of them.

Emails, by who sends them:

| Email | App Store subscriber | Web subscriber |
| --- | --- | --- |
| Payment confirmed | Apple sends it. ARCH does not. | ARCH sends it. |
| Renewed | Apple sends it. ARCH does not. | ARCH sends it. |
| Payment failed | ARCH sends it. It is about access. It has no amounts and no last four digits. | ARCH sends it. |
| Trial started | ARCH sends it. | ARCH sends it. |
| Trial ending | ARCH sends it, 2 days before. | ARCH sends it, 2 days before. |
| Membership cancelled | ARCH sends it. | ARCH sends it. |
| Annual renewal reminder | ARCH sends it. | ARCH sends it. |

Reminder timings:

| Reminder | When |
| --- | --- |
| Annual renewal | 30 days before renewal |
| Monthly plan | On the anniversary |
| Trial ending | 2 days before the trial ends |

1. Send the trial reminder email whether or not the user allows notifications.

Marketing images:

1. Do not use illustrative frames or composites on AI-generated faces. This covers App Store screenshots and marketing.
2. Use real captures. Submission needs them.

### Reasons

- Apple owns the payment. ARCH owns the experience. So ARCH does not repeat Apple's payment emails.

---
## 7. Assets

### Build

Source: `ARCH_Brow_Library_Spec_v3.md` and `ARCH_Brow_Library_Manifest_v2.csv` in `05-assets/brow-styles/`. The manifest has 252 rows. Read `05-assets/brow-styles/README_brow_library_v1.md` first.

Library size:

| Finish | Styles | Tones | Intensities | Images |
| --- | --- | --- | --- | --- |
| Full | 8 | 6 | 3 | 144 |
| Ombre | 6 | 6 | 3 | 108 |
| Total | | | | 252 |

1. Ombre excludes Straight and Micro.
2. Build that as a per-style flag, `supports_ombre`. The finish control reads it.

Image files:

| Use | Size | Format |
| --- | --- | --- |
| Full-screen preview | 1254 × 1254 | WebP |
| Grid thumbnail | 512 × 512 | WebP |

1. Grids use the 512 file.
2. Only the full-screen preview loads the 1254 file.

Delivery:

1. Host the images on a CDN. Cache them on the device.
2. Do not bundle the images in the app binary.
3. One exception: the eight Medium Defined thumbnails (about 360 KB) go inside the app. Then the grid is never empty at the first launch.
4. These eight files come from the Medium library in `05-assets/brow-styles/v1/`.
5. Load one tone at a time.
6. Start the fetch when the user selects a tone on screen 14. Do not wait for the grid.
7. Keep the previous tone cached. Users often change tone.
8. The user must be able to change tone from Profile.
9. Served paths carry a version: `v1/<finish>/<tone>/ARCH_<Tone>_<Style>_<Intensity>_{1254|512}.webp`.
10. Publish a revised image under the next prefix.

Lookup:

1. Build the lookup against the manifest. Do not build it against the images in the repository.
2. The only library is under `05-assets/brow-styles/v1/`.
3. The 19 October set was in `05-assets/brow-styles/full/` and `ombre/`. The repository no longer holds it.
4. If the build points at the old paths, change it to read the manifest.

AR overlays:

| Item | Rule |
| --- | --- |
| Source | The AR partner. A separate set. |
| Format | PNG with a straight alpha channel |
| Size | 1119 × 392 |
| Colour | 8-bit RGBA, untagged sRGB |
| File prefix | `AR_Overlay_` |
| Folder | A separate top-level folder |

1. Never convert the AR overlays to WebP.
2. PNG masters never go in the app. They are not in the repository.

Brow colour:

| Tone | Colour |
| --- | --- |
| Deep | A warm soft black-brown, about #1F130C |
| Deep: Bold, Straight and Micro (Full), and Bold (Ombre) | One step deeper. Understated #140A06. Deliberate #0D0704. |
| Rich | #120A06 |
| Rich: Bold, Straight and Micro | #0D0704 |

---

## 8. Support and identity

### Build

1. The support address is `office@cbygroyals.com`.
2. `hello@cbygroyals.com` becomes an alias.
3. Use `office@` everywhere: strings, emails and screens.
4. Screen 59 shows the address as pixels. It is already regenerated.
5. Screen 59 carries no response-time promise. Do not add one.
6. Set `CFBundleDisplayName` to `ARCH`.
7. Navigation has four tabs: `HOME`, `TRY-ON`, `LOOKS`, `PROFILE`.
8. `C by G Royals` appears only in the App Store subtitle and on screen 60.
9. Make every control at least 44 × 44 pt. Add a hit area where the visible control is smaller.
10. Text uses the gold text floor token (70%).
11. Error text is `#C97A7A`.
12. The token files are authoritative.
13. Keep the existing login, email verification, backend and TestFlight pipeline.

---

## 9. Still undefined

Nobody has decided these items, or the developer or AR partner has not confirmed them. Nothing above guesses at them. Do not build any of them as a rule until you have the answer.

### For the developer or the AR partner

1. Can the build tell the three consent states apart: no record, consented, withdrawn? Where is the consent record stored?
2. What happens on a new device? What happens after a camera permission reset? What happens when the policy version changes? Does screen 23 show again? Nobody has decided this.
3. Does one scan give both the brow profile and the recommendation data? The merge of screens 25 and 40 needs written confirmation from the AR partner.
4. Closed on 1 November 2026: screen 49d is removed (section 1.7). Saving a hand-drawn guide stays explicit. Nothing to answer.
5. What does a saved look store: a photograph composite, a recipe, or both? Is the brow profile stored on the device, on a server, or both? The answer decides whether `We do not share them` on screen 02 stays.
6. Does leaving a tracing session on screen 75d discard anything already saved?
7. How does the 24-month deletion run? What does it delete?
8. The library spec names a Flutter package (`cached_network_image`). These notes name StoreKit and SwiftUI. Which platform builds the app?

### Not decided: build as written above, and add no rules

9. What does screen 36 show for each entry route? The routes are My Looks, the library, the welcome and screen 75d. Does `SAVE THIS LOOK` appear on a look the user already saved?
10. Closed. A free account sees My Looks. It has an empty state and a text link to screen 64 (section 1.8). The link wording `See what membership includes` is approved. Nothing to answer.
11. Closed. Screen 64 lists three benefits. The team removed the guides line. Nothing to answer.
12. Decided on 1 November 2026 (Option A). A style chosen on screen 29 may not be one of the two recommendations. Bold is an example. Screen 27 then adds it as a selected third chip, after the two recommendations, and the gold button reads `PREVIEW` plus its name, for example `PREVIEW BOLD`. `EXPLORE YOUR STYLES` is unchanged. The developer decides how the choice survives the scan and the sign-up.
13. How old may a scan be before the recommendation route stops reusing it? Which events make a scan stale? Candidates: a new device, a profile change, Delete my face scan.
14. The copy for all seven face shapes (`ARCH_Face_Shape_Copy.md`) is a draft. It is not approved. Do not release it as final. Screen 43 now draws a proportion outline for each shape. Check the face descriptions against how the scan classifies each shape (question 24).
15. How does the user change skin tone from Profile? No design exists for it.
16. Screens 36 and 38 have a poetic line. Remove it, or keep it only on screen 36 in different type? Are the 24 editorial titles shown anywhere?
17. What counts as last interaction for the 24 months? What does the deletion remove? Options: measurements, brow profile, photographs in saved looks, or the account. Does the app send a notice before it deletes a dormant account?
18. The final sharing sentence on screen 02 is not final. Whether screen 02 must name saved photographs and tracing guides is also not final. Both wait for the AR engine answers.
19. The iOS camera purpose string is not approved. Do not release a string until the owner supplies the wording.
20. Refund wording may vary by region. Keep it in the strings file. Do not hard-code it. Do not change screen 71, the Terms or the purchase flow without a written instruction.
21. Withdrawn.
22. The withdrawal footer on screen 02 still says that deleting the account withdraws consent. Delete my face scan is a second way. Nobody has changed this.
23. Withdrawn.

### Added 30 October 2026

24. Ask the developer and the AR partner: how does the scan sort faces into seven shapes? The shapes are oval, round, square, heart, diamond, oblong and triangle. Do the standard definitions in `ARCH_Face_Shape_Copy.md` match that logic? Screen 43 draws each outline from the standard definitions, not from the scan.
25. Withdrawn.

### Added 1 November 2026

26. Decided 1 November 2026: the account gate for a guest who taps `LOOKS` or `PROFILE` is the new screen 13a. Build it. It shows no price.
27. Decided 1 November 2026: `HOME` opens 12 and `TRY-ON` opens 12a for a guest.
28. Decided 1 November 2026: screen 14 has no `I’ll add this later` link. Screen 16 keeps its link. A guest cannot reach a try-on without a skin tone.

### Waiting on others

1. Screens 61, 75e and 87 wait for the AR engine answers.

---

## Screen numbers used in this document

The number is the name in these notes. This list gives the screen title from the Screen Index.

| Screen | Title |
| --- | --- |
| 01 | Splash |
| 02 | Before We Begin · Biometric Notice |
| 03 | Brand Manifesto |
| 12a | Guest Try-On Preview |
| 13 | Scan Gate |
| 13a | Account Gate (Looks and Profile) |
| 14 | Skin Tone + Goal Selection |
| 20 | Home (Returning User) |
| 21 | Personalised Returning Welcome |
| 22 | Face Scan Intro |
| 23 | Camera Permission + Face Scan Consent |
| 25 | Scanning Active |
| 26 | Face Not In Frame |
| 27 | Scan Complete |
| 28 | Post-Scan Discovery |
| 29 | Style Selector |
| 30 | Style Applied |
| 30a | Style Applied · Mode Introduction (first use) |
| 31 | Intensity Selector |
| 32 | Intensity · Understated |
| 33 | Intensity · Defined |
| 34 | Intensity · Deliberate |
| 35a | Two Looks · Selection |
| 35b | Two Looks · Comparison |
| 36 | This Is Your Look |
| 36a | Before You Trace |
| 37 | Save Look |
| 38 | Saved Confirmation |
| 39 | Recommendation Intro |
| 40 | Reading Face |
| 41 | Your Result |
| 42 | Why This Shape (View 1) |
| 43 | Why This Shape (View 2) |
| 44 | The Difference |
| 45 | Tracing Guide Intro |
| 49a | Save Guide |
| 49b | Guide Saved |
| 50 | My Looks (Populated) |
| 51 | My Looks (Empty State) |
| 53 | Profile Home |
| 54 | My Account (Edit) |
| 55 | Brow Profile |
| 55b | Delete my face scan · Step 1 |
| 55c | Delete my face scan · Step 2 · photographs |
| 55f | Profile · Brow Profile · no scan |
| 59 | Contact Us |
| 60 | About ARCH |
| 61 | How ARCH Works |
| 63 | Membership Standing |
| 64 | Membership Gate (Unlock) |
| 65 | Phone Number (Trial Start) |
| 66 | Payment Details |
| 67 | Free Trial Begun |
| 68 | Payment Failed |
| 69 | Update Payment |
| 70 | Cancellation Retention |
| 71 | Cancel Membership |
| 72 | Membership Cancelled |
| 73 | Tracing · Setup Check |
| 74 | Tracing · Position & Adjust |
| 75d | Tracing · Exit Confirmation |
| 75e | Tracing · Hand Occlusion |
| 77 | Tracing · Completion |
| 78 | Delete My Account |
| 82 | Notification Priming |
| 84 | Scan Lighting Error |
| 85 | Scan Slow |
| 87 | Between Connections |
| 89 to 94 | Looks · The Library (six screens) |
