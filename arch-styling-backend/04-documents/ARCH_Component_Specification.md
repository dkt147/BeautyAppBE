# ARCH Component Specification

Source: the 132 rendered screen states (127 screen numbers) at 393 × 852 points. Measurements are exact values read from the render operations, in points (1 point = 1 CSS pixel = 3 device pixels). The PNGs are reference output; the HTML files in `screens/` carry the same geometry as tokens.

## 30 October 2026 delta

Read this first. The tables below, and the counts in them, were measured from the 15 October render operations of 132 states (127 screen numbers). They have not been re-measured. The render sources for the 30 October corrected screens are not part of this package, so the 163 states (134 screen numbers) could not be re-run through the same process. Nothing below is an updated count. This section lists what the corrected screens add or change, with sizes read from each screen's JSON file in points. Anything not in the JSON is marked as read from the PNG.

| Entry | What changed on the corrected screens | Where | Source of the numbers |
| --- | --- | --- | --- |
| Collection tabs | Label set is now ALL, TRACED, PREVIEWED (was ALL, STYLE, GUIDES, SAVED). Box 343 × 24 pt at x 25, y 228. The active tab shows gold text with a rule under it (PNG). Library screens 89 to 94 still carry the old label set. | 50 (three states), 51 (four states) | JSON, PNG |
| Chip (recommendation) | Two chips, recommended and one alternate, each 165.5 × 46 pt, 12 pt apart, at x 25 and x 202.5, y 618. Selected state is a gold border (PNG). No chip is selected in S27_Scan_Complete_NoStyleSelected. | 27 | JSON, PNG |
| Card (saved look) | 343 × 104 pt, radius 18, thumbnail 90 × 76 pt at x 39 inside the card. A tag, TRACED in gold or PREVIEWED in the muted grey, sits at the top right of the card on the ALL tab. | 50 | JSON, tag read from PNG |
| Overlay (face-proportion guide), new | Outline of the face shape drawn over the photograph frame, 151 × 148 pt at x 121, y 188, frame radius 16, same stroke on all seven screens. In the build it is fitted to her face landmarks; the drawn outline is a standard proportion over a sample face. Not in the 50 entries above. | 43 (seven shapes) | JSON |
| Empty state block, new | Headline Cormorant Garamond 300 Italic 28 pt, warm white; one or two lines of Montserrat Regular 11.5 pt body; primary button 343 × 54 pt at y 650. On the free account, the quiet link See what membership includes (Montserrat Regular 11 pt, gold) sits below the body. Not in the 50 entries above. | 51 | JSON |
| Button (two equal-weight choices) | Two ghost buttons, 343 × 52 pt at y 630 and y 698, same size and style, no default, with a Go back link below. Nothing is pre-selected. | 55c | JSON |
| Mode toggle (Refine mine, Reshape mine) | Drawn on 30, 32, 35b and 36 in this package, and on 33 and 34, which were not redrawn. The Toggle row below counts the earlier form-toggle use only and has not been updated for the mode toggle. | 30, 32, 33, 34, 35b, 36 | Not re-measured |

Colours, type and radii are the existing tokens. No new colour or type style is introduced on any corrected screen.

## One-page summary

Total: **50** entries, made up of **38 UI components** and **12 text styles**. Each row lists the number of screen numbers that use the entry, most frequent first.

| # | Type | Category | Component | Screens | Instances | Variants |
|---|---|---|---|---|---|---|
| 1 | Text style | Text | Display heading | 98 | 154 | 1 |
| 2 | Component | Decoration | Corner flourish | 97 | 102 | 1 |
| 3 | Component | System | Status bar | 97 | 103 | 1 |
| 4 | Component | Decoration | Hairline rule | 96 | 158 | 1 |
| 5 | Component | Image | Raster layer | 96 | 406 | 1 |
| 6 | Component | Brand | Monogram | 93 | 98 | 1 |
| 7 | Text style | Text | Accent text | 90 | 290 | 1 |
| 8 | Component | Button | Primary (solid) | 73 | 78 | 2 |
| 9 | Text style | Text | Button label (on gold) | 71 | 85 | 1 |
| 10 | Text style | Text | Body text | 69 | 264 | 1 |
| 11 | Text style | Text | Section label | 63 | 76 | 1 |
| 12 | Component | Navigation | Back button | 60 | 62 | 1 |
| 13 | Text style | Text | Secondary text | 58 | 148 | 1 |
| 14 | Component | Button | Secondary (outlined) | 43 | 68 | 5 |
| 15 | Component | Image | Photograph frame | 42 | 83 | 1 |
| 16 | Text style | Text | Button label (outlined) | 41 | 60 | 1 |
| 17 | Component | Text | Text link | 41 | 47 | 1 |
| 18 | Text style | Text | Display subheading | 40 | 114 | 1 |
| 19 | Component | Card | Card | 37 | 88 | 3 |
| 20 | Text style | Text | Navigation label | 30 | 98 | 1 |
| 21 | Component | Button | Exit mark | 29 | 29 | 1 |
| 22 | Component | Image | Live-camera reference | 29 | 29 | 1 |
| 23 | Component | Overlay | Brow guide | 28 | 28 | 1 |
| 24 | Component | Indicator | Progress marks | 23 | 23 | 1 |
| 25 | Component | Overlay | Transient edge controls | 21 | 21 | 1 |
| 26 | Text style | Text | Card subtitle (all caps) | 20 | 92 | 1 |
| 27 | Component | Icon | Arrow | 14 | 53 | 1 |
| 28 | Component | Indicator | Selection badge | 14 | 22 | 1 |
| 29 | Component | Navigation | Bottom navigation | 13 | 52 | 1 |
| 30 | Component | Input | Text input | 12 | 36 | 1 |
| 31 | Component | Navigation | Collection tabs | 7 | 7 | 1 |
| 32 | Component | List | List row | 6 | 29 | 3 |
| 33 | Component | Decoration | OR divider | 6 | 6 | 1 |
| 34 | Text style | Text | Other text | 6 | 15 | 1 |
| 35 | Component | Form | Checkbox | 5 | 16 | 1 |
| 36 | Component | Button | Icon button (circular) | 5 | 19 | 3 |
| 37 | Component | Chip | Chip | 4 | 11 | 1 |
| 38 | Component | Form | Colour swatch | 4 | 19 | 1 |
| 39 | Component | Form | Radio | 4 | 14 | 1 |
| 40 | Component | List | Checklist item | 3 | 11 | 1 |
| 41 | Component | Overlay | Modal sheet | 3 | 4 | 1 |
| 42 | Component | Indicator | Stroke-weight sample | 3 | 6 | 1 |
| 43 | Component | Decoration | Accent bar | 2 | 2 | 1 |
| 44 | Component | Indicator | Badge | 2 | 2 | 1 |
| 45 | Component | Icon | Status circle | 2 | 2 | 1 |
| 46 | Component | Input | Code digit box | 1 | 6 | 1 |
| 47 | Component | Indicator | Dot | 1 | 1 | 1 |
| 48 | Text style | Text | Language name (own script) | 1 | 2 | 1 |
| 49 | Component | Tile | Style tile | 1 | 8 | 1 |
| 50 | Component | Form | Toggle | 1 | 3 | 1 |

Bottom navigation counts four tab instances per screen (one active, three inactive). Counting rules: instances are render operations, so a component repeated on one screen counts once per repeat. Text styles are counted as merged text runs. Components marked with the source "measurement JSON" have no render operation of their own (they sit on mirror and camera screens) and are measured from the per-screen measurement files.

## Reading this document

- Tokens are listed as CSS custom property names from `arch-tokens.css`. Geometry that is specific to one screen lives in `arch-geometry.json` and is not repeated here.
- Touch target: the measured visual size is shown. Visible size and hit area are specified separately. Where the smaller side is under 44 points, the hit area is 44 × 44 points minimum, centred on the visible element (token `--arch-touch-min`), and the visual does not change. The screens do not draw hit regions.
- VoiceOver label patterns are proposed wording for the build. They are not drawn on any screen.
- Contrast rows that cite gold 65% describe the delivered PNGs, which were drawn before the contrast correction. The corrected functional text floor is gold 70% (`--arch-gold-text-floor`, 4.69:1 on obsidian). The error text token is `--arch-error-text` (#C97A7A, 6.17:1).
- Contrast ratios are computed from the token values over the obsidian ground (gold opacities are composited first). Text is tested against 4.5:1 and non-text borders against 3:1.
- States that are specified without being drawn (pressed, disabled input, featured card) are listed under "States specified for the build" with their source. States that nothing specifies are listed under "States not drawn".

## Text / Display heading

Variants: 12 distinct styles (154). Used on 98 screens: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 12a, 13 +84 more.

| Property | Values |
|---|---|
| Typeface | Cormorant Garamond 300 italic; Cormorant Garamond 500; Cormorant Garamond 500 italic |
| Sizes (pt) | 27, 29, 30, 31, 32, 33.7, 34, 36, 42, 72.7 |
| Tracking (pt) | 0, 12.4 |
| Colours | --arch-gold, --arch-render-fcfaf6, --arch-warm-white |
| Text runs | 154 across 98 screens |
| Contrast | gold on obsidian 8.66:1; render-fcfaf6 on obsidian 18.99:1; warm-white on obsidian 18.39:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Decoration / Corner flourish

Variants: Four corners (102). Used on 97 screens: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 12a, 13 +83 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-flourish-size, --arch-gold | 113.33 | 113.33 | n/a | n/a | none | not a control | 97: 01, 02, 03, 04, 05, 06, 07, 08 +89 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative. Hidden from VoiceOver.
- Contrast: no text or border pair on this component.

## System / Status bar

Variants: Raster layer (103). Used on 97 screens: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 12a, 13 +83 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 53.33 | 393 | n/a | n/a | none | not a control | 97: 01, 02, 03, 04, 05, 06, 07, 08 +89 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): System layer. Not part of the app accessibility tree.
- Contrast: no text or border pair on this component.

## Decoration / Hairline rule

Variants: Fading hairline (158). Used on 96 screens: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 12a, 13 +82 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-border-1, --arch-gold-65 | 1 | 87–350 | n/a | n/a | 1 pt | not a control | 96: 01, 02, 03, 04, 05, 06, 07, 08 +88 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative. Hidden from VoiceOver.
- Contrast: no text or border pair on this component.

## Image / Raster layer

Variants: Photograph or illustration (406). Used on 96 screens: 01, 03, 04, 05, 06, 07, 08, 10, 12, 12a, 13, 17, 18, 19 +82 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 13–852 | 15.33–852 | n/a | n/a | none | not a control | 96: 01, 03, 04, 05, 06, 07, 08, 10 +88 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative unless it is the subject of the screen; then "<description>, image".
- Contrast: no text or border pair on this component.

## Brand / Monogram

Variants: Header (98). Used on 93 screens: 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 12a, 13, 14 +79 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 28.88 | 39 | n/a | n/a | none | not a control | 93: 02, 03, 04, 05, 06, 07, 08, 09 +85 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): "ARCH" (header image, not a control unless it routes).
- Contrast: no text or border pair on this component.

## Text / Accent text

Variants: 43 distinct styles (290). Used on 90 screens: 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15 +76 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 300; Montserrat 400; Montserrat 500 |
| Sizes (pt) | 7.3, 7.7, 8.7, 9, 9.3, 10, 10.3, 10.7, 11, 11.3, 12, 12.7, 13 |
| Tracking (pt) | 0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1, 1.3, 1.4, 1.5, 1.6 |
| Colours | --arch-gold, --arch-gold-50, --arch-gold-55, --arch-gold-60, --arch-gold-65, --arch-gold-70, --arch-gold-75, --arch-gold-80, --arch-gold-85, --arch-gold-90 |
| Text runs | 290 across 90 screens |
| Contrast | gold on obsidian 8.66:1; gold-50 on obsidian 2.89:1 (below 4.5:1); gold-55 on obsidian 3.28:1 (below 4.5:1); gold-60 on obsidian 3.7:1 (below 4.5:1); gold-65 on obsidian 4.16:1 (below 4.5:1); gold-70 on obsidian 4.67:1; gold-75 on obsidian 5.22:1; gold-80 on obsidian 5.82:1; gold-85 on obsidian 6.46:1; gold-90 on obsidian 7.14:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Button / Primary (solid)

Variants: Solid pill (76); Solid pill with arrow (2). Used on 73 screens: 02, 03, 05, 06, 07, 08, 09, 10, 11, 12a, 13, 14, 15, 16 +59 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default (gold fill) | --arch-gold, --arch-obsidian, --arch-radius-full | 44–58 | 149–343 | n/a | 22–29 pt | none | visual 44 × 149 · meets 44 pt; hit area equals the visible size | 71: 02, 03, 05, 06, 07, 08, 09, 10 +63 more |
| disabled (gold 30% fill) | --arch-gold-30, --arch-radius-27, --arch-radius-full, --arch-render-8e8c88 | 54 | 343 | 68.11–122.68 | 27 pt | none | visual 54 × 343 · meets 44 pt; hit area equals the visible size | 3: 23, 35a, 54 |

Accessibility

- Minimum touch target: smallest visual side 44 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<label>, button". Disabled adds ", dimmed". Arrow variant: arrow is decorative and hidden from VoiceOver.
- Contrast: text obsidian on gold 8.66:1; text render-8e8c88 on gold-30 3.38:1 (below 4.5:1)

## Text / Button label (on gold)

Variants: 2 distinct styles (85). Used on 71 screens: 02, 03, 05, 06, 07, 08, 09, 10, 11, 12a, 13, 14, 15, 16 +57 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 500 |
| Sizes (pt) | 12, 13 |
| Tracking (pt) | 0 |
| Colours | --arch-obsidian |
| Text runs | 85 across 71 screens |
| Contrast | obsidian on gold 8.66:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Text / Body text

Variants: 17 distinct styles (264). Used on 69 screens: 02, 06, 07, 11, 14, 17, 18, 23, 24, 26, 27, 29, 32, 33 +55 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 300; Montserrat 400 |
| Sizes (pt) | 7.7, 10.3, 10.7, 11, 11.3, 11.7, 12, 13, 20 |
| Tracking (pt) | 0, 0.5, 1.4 |
| Colours | --arch-render-dcd6cc, --arch-render-ece6dc, --arch-warm-white |
| Text runs | 264 across 69 screens |
| Contrast | render-dcd6cc on obsidian 13.7:1; render-ece6dc on obsidian 15.95:1; warm-white on obsidian 18.39:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Text / Section label

Variants: 3 distinct styles (76). Used on 63 screens: 02, 04, 12, 12a, 14, 15, 16, 18, 20, 21, 22, 23, 25, 27 +49 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 400 |
| Sizes (pt) | 10.7, 11 |
| Tracking (pt) | 2, 2.2 |
| Colours | --arch-gold-65 |
| Text runs | 76 across 63 screens |
| Contrast | gold-65 on obsidian 4.16:1 (below 4.5:1) |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Navigation / Back button

Variants: Circular outline (62). Used on 60 screens: 05, 06, 07, 08, 09, 10, 11, 13, 14, 15, 16, 17, 18, 22 +46 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-border-1, --arch-gold-75, --arch-radius-full | 30 | 30 | n/a | 15 pt | 1 pt | visual 30 × 30 · hit area 44 × 44 pt, centred on the visible element | 60: 05, 06, 07, 08, 09, 10, 11, 13 +52 more |

Accessibility

- Minimum touch target: smallest visual side 30 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "Back, button".
- Contrast: no text or border pair on this component.

## Text / Secondary text

Variants: 15 distinct styles (148). Used on 58 screens: 02, 04, 05, 06, 07, 08, 09, 10, 11, 12, 12a, 13, 14, 15 +44 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 300; Montserrat 400 |
| Sizes (pt) | 7.3, 9, 9.3, 10, 10.3, 10.7, 11, 11.3, 12 |
| Tracking (pt) | 0, 0.4, 0.6, 0.9, 2 |
| Colours | --arch-muted |
| Text runs | 148 across 58 screens |
| Contrast | muted on obsidian 5.58:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Button / Secondary (outlined)

Variants: Outlined pill (32); Inline pill (4); Provider sign-in (12); Other (4); Edge action (16). Used on 43 screens: 02, 05, 06, 07, 08, 12a, 21, 23, 30, 36, 46, 47, 48, 49 +29 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| dimmed (gold 70%) | --arch-border-1, --arch-gold-70, --arch-obsidian, --arch-radius-21, --arch-radius-full | 42 | 165 | 10.69 | 21 pt | 1 pt | visual 42 × 165 · hit area 44 × 44 pt, centred on the visible element | 3: 46, 47, 48 |
| default (gold border) | --arch-border-1, --arch-gold, --arch-obsidian, --arch-radius-18, --arch-radius-19, --arch-radius-21, --arch-radius-22, --arch-radius-23, --arch-radius-24, --arch-radius-25, --arch-radius-27, --arch-radius-full | 36–54 | 85–343 | 8.72–143.98 | 18–27 pt | 1 pt | visual 36 × 85 · hit area 44 × 44 pt, centred on the visible element | 31: 12a, 21, 36, 46, 47, 48, 49, 49c +23 more |
| dimmed (gold 90%) | --arch-border-1, --arch-gold-90, --arch-obsidian, --arch-radius-27, --arch-radius-full | 54 | 343 | 91.17 | 27 pt | 1 pt | visual 54 × 343 · meets 44 pt; hit area equals the visible size | 1: 50 |
| dimmed (gold 80%) | --arch-border-1, --arch-gold, --arch-gold-80, --arch-obsidian, --arch-radius-12, --arch-radius-14, --arch-radius-27, --arch-radius-full | 24–54 | 58–343 | 9.7–137.14 | 12–27 pt | 1 pt | visual 24 × 58 · hit area 44 × 44 pt, centred on the visible element | 5: 23, 30, 54, 66, 70 |
| filled (warm white) | --arch-obsidian, --arch-radius-22, --arch-radius-23, --arch-radius-24, --arch-radius-full, --arch-warm-white | 44–48 | 343 | 119.06–121.38 | 22–24 pt | none | visual 44 × 343 · meets 44 pt; hit area equals the visible size | 6: 05, 06, 07, 08, 66, 69 |
| default | --arch-border-2-33, --arch-gold, --arch-obsidian, --arch-radius-22, --arch-radius-26, --arch-radius-27, --arch-radius-full, --arch-rouge, --arch-warm-white | 44–54 | 189–343 | 57.68–93.54 | 22–27 pt | 2.33 pt | visual 44 × 189 · meets 44 pt; hit area equals the visible size | 9: 75-07, 75-08, 75a, 75d, 75f, 76-07, 76-08, 78 +1 more |
| disabled (gold 30% fill) | --arch-gold-30, --arch-radius-27, --arch-radius-full, --arch-render-8e8c88 | 54 | 343 | 135.52–149.91 | 27 pt | none | visual 54 × 343 · meets 44 pt; hit area equals the visible size | 2: 02, 73 |

Accessibility

- Minimum touch target: smallest visual side 24 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<label>, button". Provider sign-in: "Continue with <provider>, button".
- Contrast: border gold on obsidian 8.66:1; border gold-70 on obsidian 4.67:1; border gold-80 on obsidian 5.82:1; border gold-90 on obsidian 7.14:1; border obsidian on obsidian 1.0:1 (below 3.0:1); text gold on obsidian 8.66:1; text gold-70 on obsidian 4.67:1; text gold-80 on obsidian 5.82:1; text gold-90 on obsidian 7.14:1; text obsidian on warm-white 18.39:1; text render-8e8c88 on gold-30 3.38:1 (below 4.5:1); text warm-white on rouge 10.8:1

## Image / Photograph frame

Variants: Thumbnail or reference (83). Used on 42 screens: 22, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35a, 35b, 36, 37 +28 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| outlined (gold 50%) | --arch-border-1, --arch-gold-50, --arch-obsidian, --arch-radius-10, --arch-radius-12, --arch-radius-14, --arch-radius-16, --arch-radius-18, --arch-radius-22, --arch-radius-9 | 52–349 | 71.75–343 | 68.33 | 9–22 pt | 1 pt | not a control | 42: 22, 25, 26, 27, 29, 30, 31, 32 +34 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Photograph: "<style or look name>, photograph" or decorative where the label sits beside it.
- Contrast: border gold-50 on obsidian 2.89:1 (below 3.0:1); text obsidian on obsidian 1.0:1 (below 4.5:1)

## Text / Button label (outlined)

Variants: 12 distinct styles (60). Used on 41 screens: 01, 02, 10, 12a, 21, 23, 30, 35a, 36, 46, 47, 48, 49, 49c +27 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 500 |
| Sizes (pt) | 12, 12.3, 12.7, 13, 15.3, 26, 28, 30 |
| Tracking (pt) | 0, 1, 4.2 |
| Colours | --arch-gold, --arch-gold-70, --arch-gold-80, --arch-gold-90, --arch-render-8e8c88, --arch-warm-white |
| Text runs | 60 across 41 screens |
| Contrast | gold on obsidian 8.66:1; gold-70 on obsidian 4.67:1; gold-80 on obsidian 5.82:1; gold-90 on obsidian 7.14:1; render-8e8c88 on obsidian 5.9:1; warm-white on obsidian 18.39:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Text / Text link

Variants: Inline or standalone link (47). Used on 41 screens: 02, 04, 05, 06, 07, 08, 09, 10, 11, 13, 14, 16, 17, 18 +27 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 16–30 | 88–273 | n/a | n/a | none | visual 16 × 88 · hit area 44 × 44 pt, centred on the visible element | 41: 02, 04, 05, 06, 07, 08, 09, 10 +33 more |

Accessibility

- Minimum touch target: smallest visual side 16 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<link text>, link".
- Contrast: no text or border pair on this component.

## Text / Display subheading

Variants: 20 distinct styles (114). Used on 40 screens: 04, 12, 13, 16, 19, 20, 21, 27, 32, 33, 34, 35b, 36, 38 +26 more.

| Property | Values |
|---|---|
| Typeface | Cormorant Garamond 300 italic; Cormorant Garamond 500 italic |
| Sizes (pt) | 16, 17, 17.7, 18, 19, 20, 22, 23, 24, 25, 25.7, 26 |
| Tracking (pt) | 0 |
| Colours | --arch-gold, --arch-gold-55, --arch-render-ece6dc, --arch-render-fdfcf8, --arch-warm-white |
| Text runs | 114 across 40 screens |
| Contrast | gold on obsidian 8.66:1; gold-55 on obsidian 3.28:1 (below 4.5:1); render-ece6dc on obsidian 15.95:1; render-fdfcf8 on obsidian 19.29:1; warm-white on obsidian 18.39:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Card / Card

Variants: Standard container (65); Selected container (20); Outlined container (3). Used on 37 screens: 02, 04, 12, 13, 16, 20, 21, 23, 24, 27, 31, 35a, 35b, 41 +23 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| standard (border 2A2A2A) | --arch-border, --arch-border-1, --arch-card, --arch-gold, --arch-gold-55, --arch-gold-60, --arch-gold-65, --arch-gold-70, --arch-gold-85, --arch-muted, --arch-obsidian, --arch-radius-14, --arch-radius-16, --arch-radius-18, --arch-radius-22, --arch-warm-white | 72–306 | 166–343 | 16–120 | 14–22 pt | 1 pt | visual 72 × 166 · meets 44 pt; hit area equals the visible size | 30: 04, 12, 13, 16, 20, 21, 23, 24 +22 more |
| selected (gold border) | --arch-border-1, --arch-card, --arch-gold, --arch-gold-65, --arch-gold-70, --arch-gold-80, --arch-muted, --arch-obsidian, --arch-radius-14, --arch-radius-16, --arch-radius-18, --arch-radius-20, --arch-render-ece6dc, --arch-warm-white | 55–306 | 166–343 | 16–120 | 14–20 pt | 1 pt | visual 55 × 166 · meets 44 pt; hit area equals the visible size | 18: 04, 12, 16, 20, 21, 31, 35a, 35b +10 more |
| outlined (gold 45%) | --arch-border-1, --arch-gold-45, --arch-gold-80, --arch-muted, --arch-obsidian, --arch-radius-14 | 82 | 343 | 16 | 14 pt | 1 pt | visual 82 × 343 · meets 44 pt; hit area equals the visible size | 1: 61 |
| outlined (gold 65%) | --arch-border-1, --arch-card, --arch-gold-65, --arch-obsidian, --arch-radius-14, --arch-warm-white | 126 | 343 | 17 | 14 pt | 1 pt | visual 126 × 343 · meets 44 pt; hit area equals the visible size | 1: 02 |

Accessibility

- Minimum touch target: smallest visual side 55 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<title>, <subtitle>, button". Selected adds ", selected".
- Contrast: border gold on obsidian 8.66:1; border gold-45 on obsidian 2.55:1 (below 3.0:1); border gold-65 on obsidian 4.16:1; text gold on card 7.97:1; text gold-55 on card 3.26:1 (below 4.5:1); text gold-60 on card 3.64:1 (below 4.5:1); text gold-65 on card 4.06:1 (below 4.5:1); text gold-70 on card 4.51:1; text gold-80 on card 5.52:1; text gold-80 on obsidian 5.82:1; text gold-85 on card 6.07:1; text muted on card 5.14:1; text muted on obsidian 5.58:1; text obsidian on card 1.09:1 (below 4.5:1); text render-ece6dc on card 14.67:1; text warm-white on card 16.92:1

## Text / Navigation label

Variants: 9 distinct styles (98). Used on 30 screens: 05, 06, 07, 08, 09, 12, 12a, 20, 21, 37, 46, 47, 48, 49a +16 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 400; Montserrat 500 |
| Sizes (pt) | 7.3, 7.7, 8, 8.7 |
| Tracking (pt) | 0.8, 0.9, 1.4 |
| Colours | --arch-gold, --arch-gold-65, --arch-muted, --arch-obsidian, --arch-render-c44040 |
| Text runs | 98 across 30 screens |
| Contrast | gold on obsidian 8.66:1; gold-65 on obsidian 4.16:1 (below 4.5:1); muted on obsidian 5.58:1; render-c44040 on obsidian 3.92:1 (below 4.5:1) |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Button / Exit mark

Variants: Mirror-screen exit (29). Used on 29 screens: 74, 74a, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06, 75-07, 75-08, 75-09, 75-10, 75a, 75b +15 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 44 | 44 | n/a | n/a | none | visual 44 × 44 · meets 44 pt; hit area equals the visible size | 29: 74, 74a, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06 +21 more |

Accessibility

- Minimum touch target: smallest visual side 44 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "Exit, button".
- Contrast: no text or border pair on this component.

## Image / Live-camera reference

Variants: Mirrored reference raster (29). Used on 29 screens: 74, 74a, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06, 75-07, 75-08, 75-09, 75-10, 75a, 75b +15 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 393–852 | 393–852 | n/a | n/a | none | not a control | 29: 74, 74a, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06 +21 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Reference raster for the live camera. In build, the camera preview is announced "Camera preview".
- Contrast: no text or border pair on this component.

## Overlay / Brow guide

Variants: AR guide drawn over the camera (28). Used on 28 screens: 74, 74a, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06, 75-07, 75-08, 75-09, 75-10, 75a, 75b +14 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 393–852 | 393–852 | n/a | n/a | none | not a control | 28: 74, 74a, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06 +20 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative overlay; spoken guidance comes from the edge guidance text.
- Contrast: no text or border pair on this component.

## Indicator / Progress marks

Variants: Segmented bar or session marks (23). Used on 23 screens: 14, 16, 18, 75-01, 75-02, 75-03, 75-04, 75-05, 75-06, 75-07, 75-08, 75-09, 75-10, 76-01 +9 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 2–10 | 54–343 | n/a | n/a | none | not a control | 23: 14, 16, 18, 75-01, 75-02, 75-03, 75-04, 75-05 +15 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): "Step <n> of <total>" (or "<n> of <total> complete").
- Contrast: no text or border pair on this component.

## Overlay / Transient edge controls

Variants: Mirror and camera screens (21). Used on 21 screens: 75-01, 75-02, 75-03, 75-04, 75-05, 75-06, 75-07, 75-08, 75-09, 75-10, 75g, 76-01, 76-02, 76-03 +7 more.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 49 | 393–852 | n/a | n/a | none | visual 49 × 393 · meets 44 pt; hit area equals the visible size | 21: 75-01, 75-02, 75-03, 75-04, 75-05, 75-06, 75-07, 75-08 +13 more |

Accessibility

- Minimum touch target: smallest visual side 49 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<action>, button"; controls fade after the interval set on the screen.
- Contrast: no text or border pair on this component.

## Text / Card subtitle (all caps)

Variants: 14 distinct styles (92). Used on 20 screens: 18, 21, 27, 44, 50, 53, 54, 61, 63, 64, 67, 72, 78, 82 +6 more.

| Property | Values |
|---|---|
| Typeface | Montserrat 400; Montserrat 500 |
| Sizes (pt) | 9, 9.3 |
| Tracking (pt) | 1.1, 1.2, 1.3, 1.4, 1.6 |
| Colours | --arch-gold, --arch-gold-65, --arch-gold-70, --arch-gold-80, --arch-muted, --arch-warm-white |
| Text runs | 92 across 20 screens |
| Contrast | gold on obsidian 8.66:1; gold-65 on obsidian 4.16:1 (below 4.5:1); gold-70 on obsidian 4.67:1; gold-80 on obsidian 5.82:1; muted on obsidian 5.58:1; warm-white on obsidian 18.39:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Icon / Arrow

Variants: Forward arrow (53). Used on 14 screens: 20, 50, 52, 53, 55a, 58, 65, 78, 89, 90, 91, 92, 93, 94.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-border-1, --arch-gold | 8 | 12 | n/a | n/a | 1 pt | not a control | 14: 20, 50, 52, 53, 55a, 58, 65, 78 +6 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative. Hidden from VoiceOver.
- Contrast: no text or border pair on this component.

## Indicator / Selection badge

Variants: Check in circle (22). Used on 14 screens: 14, 15, 29, 38, 41, 49, 49b, 51, 67, 72, 73, 73a, 77, 80.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| selected | --arch-card, --arch-gold, --arch-radius-full | 12–42 | 12–42 | n/a | 6–21 pt | none | not a control | 14: 14, 15, 29, 38, 41, 49, 49b, 51 +6 more |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative. State is conveyed by the parent control ("selected").
- Contrast: no text or border pair on this component.

## Navigation / Bottom navigation

Variants: Four tabs (52). Used on 13 screens: 12, 12a, 20, 21, 50, 51, 53, 89, 90, 91, 92, 93, 94.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| inactive | --arch-muted, --arch-obsidian, --arch-type-navigation-size | 82 | 72 | n/a | n/a | none | visual 82 × 72 · meets 44 pt; hit area equals the visible size | 13: 12, 12a, 20, 21, 50, 51, 53, 89 +5 more |
| active | --arch-gold, --arch-obsidian, --arch-type-navigation-size | 82 | 72 | n/a | n/a | none | visual 82 × 72 · meets 44 pt; hit area equals the visible size | 13: 12, 12a, 20, 21, 50, 51, 53, 89 +5 more |

Accessibility

- Minimum touch target: smallest visual side 72 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<Tab>, tab, <n> of 4" with ", selected" on the active tab.
- Contrast: text gold on obsidian 8.66:1; text muted on obsidian 5.58:1

## Input / Text input

Variants: Labelled field (36). Used on 12 screens: 05, 06, 07, 08, 09, 37, 49a, 54, 59, 65, 66, 69.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| empty | --arch-border, --arch-border-1, --arch-card, --arch-muted, --arch-radius-14 | 46–52 | 167–343 | 16 | 14 pt | 1 pt | visual 46 × 167 · meets 44 pt; hit area equals the visible size | 6: 05, 07, 08, 54, 66, 69 |
| focused | --arch-border-1, --arch-card, --arch-gold, --arch-gold-65, --arch-obsidian, --arch-radius-14, --arch-warm-white | 50–67 | 343 | 16 | 14 pt | 1 pt | visual 50 × 343 · meets 44 pt; hit area equals the visible size | 10: 05, 08, 09, 37, 49a, 54, 59, 65 +2 more |
| filled | --arch-border, --arch-border-1, --arch-card, --arch-gold, --arch-gold-65, --arch-radius-14, --arch-warm-white | 52–114 | 343 | 16 | 14 pt | 1 pt | visual 52 × 343 · meets 44 pt; hit area equals the visible size | 5: 06, 07, 54, 59, 65 |
| error | --arch-border-1, --arch-obsidian, --arch-radius-14, --arch-render-280d0d, --arch-render-c44040, --arch-warm-white | 64 | 343 | 16 | 14 pt | 1 pt | visual 64 × 343 · meets 44 pt; hit area equals the visible size | 2: 06, 07 |

Accessibility

- Minimum touch target: smallest visual side 46 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<Field label>, text field" followed by "<value>" or "empty". Error state appends the error text.
- Contrast: border gold on obsidian 8.66:1; border render-c44040 on obsidian 3.92:1; text gold on card 7.97:1; text gold-65 on card 4.06:1 (below 4.5:1); text muted on card 5.14:1; text render-c44040 on render-280d0d 3.6:1 (below 4.5:1); text warm-white on card 16.92:1; text warm-white on render-280d0d 16.91:1

## Navigation / Collection tabs

Variants: ALL · STYLE · GUIDES · SAVED (7). Used on 7 screens: 50, 89, 90, 91, 92, 93, 94.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | none (raster or geometry only) | 24 | 343 | n/a | n/a | none | visual 24 × 343 · hit area 44 × 44 pt, centred on the visible element | 7: 50, 89, 90, 91, 92, 93, 94 |

Accessibility

- Minimum touch target: smallest visual side 24 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<Tab>, tab, <n> of 4, selected".
- Contrast: no text or border pair on this component.

## List / List row

Variants: Menu row (14); Setup check row (12); Preference row (3). Used on 6 screens: 53, 56, 73, 73a, 78, 87.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-radius-14, --arch-render-0d0d0d, --arch-render-6c6a68 | 55 | 343 | 16 | 14 pt | none | visual 55 × 343 · meets 44 pt; hit area equals the visible size | 1: 87 |
| selected (gold border) | --arch-border-1, --arch-gold, --arch-obsidian, --arch-radius-10 | 38 | 343 | 16 | 10 pt | 1 pt | visual 38 × 343 · hit area 44 × 44 pt, centred on the visible element | 1: 78 |
| standard (border 2A2A2A) | --arch-border, --arch-border-1, --arch-card, --arch-gold, --arch-muted, --arch-radius-10, --arch-radius-12, --arch-radius-14, --arch-warm-white | 28–48 | 343 | 17–44 | 10–14 pt | 1 pt | visual 28 × 343 · hit area 44 × 44 pt, centred on the visible element | 4: 53, 56, 73, 73a |

Accessibility

- Minimum touch target: smallest visual side 28 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<row title>, button" (chevron or arrow is decorative).
- Contrast: border gold on obsidian 8.66:1; text gold on card 7.97:1; text gold on obsidian 8.66:1; text muted on card 5.14:1; text render-6c6a68 on render-0d0d0d 3.61:1 (below 4.5:1); text warm-white on card 16.92:1

## Decoration / OR divider

Variants: Rule · OR · rule (6). Used on 6 screens: 05, 06, 07, 08, 66, 69.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-border-1, --arch-gold-27 | 1 | n/a | n/a | n/a | 1 pt | not a control | 6: 05, 06, 07, 08, 66, 69 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): "or" (static text).
- Contrast: no text or border pair on this component.

## Text / Other text

Variants: 8 distinct styles (15). Used on 6 screens: 06, 07, 19, 75-04, 76-04, 87.

| Property | Values |
|---|---|
| Typeface | Montserrat 400; Montserrat 600 |
| Sizes (pt) | 7.7, 9.7, 10, 11.3, 12, 16 |
| Tracking (pt) | -0.1, 0, 0.7, 2.7 |
| Colours | --arch-error-text, --arch-render-6c6a68, --arch-render-76653a, --arch-render-7e6b48, --arch-render-c44040, --arch-render-fafafa |
| Text runs | 15 across 6 screens |
| Contrast | error-text on obsidian 6.17:1; render-6c6a68 on obsidian 3.68:1 (below 4.5:1); render-76653a on obsidian 3.48:1 (below 4.5:1); render-7e6b48 on obsidian 3.85:1 (below 4.5:1); render-c44040 on obsidian 3.92:1 (below 4.5:1); render-fafafa on obsidian 18.97:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Form / Checkbox

Variants: Square (16). Used on 5 screens: 02, 23, 35a, 73, 73a.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| unchecked | --arch-border-1, --arch-gold, --arch-radius-9 | 18–20 | 18–20 | n/a | 4 pt | 1 pt | visual 18 × 18 · hit area 44 × 44 pt, centred on the visible element | 5: 02, 23, 35a, 73, 73a |
| checked | --arch-border-1, --arch-gold, --arch-radius-9 | 18–20 | 18–20 | n/a | 4 pt | 1 pt | visual 18 × 18 · hit area 44 × 44 pt, centred on the visible element | 4: 02, 23, 35a, 73 |

Accessibility

- Minimum touch target: smallest visual side 18 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<label>, checkbox, checked" or "unchecked".
- Contrast: no text or border pair on this component.

## Button / Icon button (circular)

Variants: Tool (15); Guide icon (3); Play (1). Used on 5 screens: 45, 46, 47, 48, 61.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default (border 2A2A2A) | --arch-border, --arch-border-1, --arch-card, --arch-radius-21, --arch-radius-full | 42 | 42 | n/a | 21 pt | 1 pt | visual 42 × 42 · hit area 44 × 44 pt, centred on the visible element | 3: 46, 47, 48 |
| selected (gold border) | --arch-border-1, --arch-card, --arch-gold, --arch-obsidian, --arch-radius-21, --arch-radius-22, --arch-radius-full | 42–43 | 42–43 | n/a | 21–21.5 pt | 1 pt | visual 42 × 42 · hit area 44 × 44 pt, centred on the visible element | 4: 46, 47, 48, 61 |
| outlined (gold 60%) | --arch-border-1, --arch-gold, --arch-gold-60, --arch-obsidian, --arch-radius-17, --arch-radius-full | 34 | 34 | 13.88–15.02 | 17 pt | 1 pt | visual 34 × 34 · hit area 44 × 44 pt, centred on the visible element | 1: 45 |

Accessibility

- Minimum touch target: smallest visual side 34 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<action>, button" (for example "Zoom in, button").
- Contrast: border gold on obsidian 8.66:1; border gold-60 on obsidian 3.7:1; text gold on obsidian 8.66:1

## Chip / Chip

Variants: Pill (11). Used on 4 screens: 14, 27, 28, 37.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| selected (gold border) | --arch-border-1, --arch-card, --arch-gold, --arch-obsidian, --arch-radius-14, --arch-radius-16, --arch-radius-22, --arch-radius-full | 44–46 | 107.67–229 | 26.31–58.88 | 14–22 pt | 1 pt | visual 44 × 107.67 · meets 44 pt; hit area equals the visible size | 4: 14, 27, 28, 37 |
| standard (border 2A2A2A) | --arch-border, --arch-border-1, --arch-card, --arch-radius-16, --arch-radius-22, --arch-radius-full, --arch-render-dcd6cc, --arch-warm-white | 44–46 | 107.67–166 | 25.11–48.54 | 16–22 pt | 1 pt | visual 44 × 107.67 · meets 44 pt; hit area equals the visible size | 3: 14, 27, 37 |

Accessibility

- Minimum touch target: smallest visual side 44 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<label>, button, selected" or "not selected".
- Contrast: border gold on obsidian 8.66:1; text gold on card 7.97:1; text render-dcd6cc on card 12.61:1; text warm-white on card 16.92:1

## Form / Colour swatch

Variants: Circle (19). Used on 4 screens: 14, 15, 18, 29.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-border-1, --arch-radius-full | 10–100 | 10–100 | n/a | 5–50 pt | 1 pt | visual 10 × 10 · hit area 44 × 44 pt, centred on the visible element | 4: 14, 15, 18, 29 |
| selected (gold ring) | --arch-border-1, --arch-gold, --arch-radius-full | 32–42 | 32–42 | n/a | 16–21 pt | 1 pt | visual 32 × 32 · hit area 44 × 44 pt, centred on the visible element | 3: 14, 15, 29 |

Accessibility

- Minimum touch target: smallest visual side 10 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<Colour name>, <n> of 8, button" with ", selected" on the ringed swatch.
- Contrast: no text or border pair on this component.

Swatch row (screen 29): measured pitch, centre to centre, is **42.875 pt** (eight swatches of 32 pt, centres 46.4375 to 346.5625, gap 10.875 pt, row box 25 to 368). That is under 44 pt, so adjacent 44 × 44 hit areas would overlap by 1.125 pt. The row is therefore a horizontally scrollable row: each swatch sits in a 44 × 44 slot, so eight swatches need 352 pt against a 343 pt content width. The screen 29 PNG and prototype show the drawn pitch; the build scrolls.

## Form / Radio

Variants: Circle (14). Used on 4 screens: 16, 31, 35b, 57.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| on | --arch-gold, --arch-radius-full | 22 | 22 | n/a | 11 pt | 1.2 pt | visual 22 × 22 · hit area 44 × 44 pt, centred on the visible element | 4: 16, 31, 35b, 57 |
| off | --arch-radio-border, --arch-radius-full | 22 | 22 | n/a | 11 pt | 1.2 pt | visual 22 × 22 · hit area 44 × 44 pt, centred on the visible element | 4: 16, 31, 35b, 57 |

Accessibility

- Minimum touch target: smallest visual side 22 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<label>, radio button, <n> of <total>, selected" or "not selected".
- Contrast: no text or border pair on this component.

## List / Checklist item

Variants: Tick + label (11). Used on 3 screens: 63, 64, 82.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| checked | --arch-gold | 11.4–11.8 | n/a | n/a | n/a | none | not a control | 3: 63, 64, 82 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): "<label>, included".
- Contrast: no text or border pair on this component.

## Overlay / Modal sheet

Variants: Bottom sheet (4). Used on 3 screens: 48, 79, 81.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| standard (border 2A2A2A) | --arch-border, --arch-border-1, --arch-card, --arch-gold, --arch-muted, --arch-obsidian, --arch-radius-24, --arch-warm-white | 360–370 | 343 | 27.22–67.73 | 24 pt | 1 pt | not a control | 2: 79, 81 |
| outlined (gold 50%) | --arch-border-1, --arch-gold, --arch-gold-50, --arch-obsidian, --arch-radius-14, --arch-render-dcd6cc, --arch-warm-white | 338 | 343 | 68.33 | 14 pt | 1 pt | not a control | 1: 48 |
| outlined (gold 70%) | --arch-border-1, --arch-card, --arch-gold, --arch-gold-70, --arch-obsidian, --arch-radius-22, --arch-render-dcd6cc, --arch-warm-white | 360 | 343 | 10.69 | 22 pt | 1 pt | not a control | 1: 48 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Container announces as alert dialog: "<title>". Focus moves to the first action; background content is hidden from VoiceOver.
- Contrast: border gold-50 on obsidian 2.89:1 (below 3.0:1); border gold-70 on obsidian 4.67:1; text gold on card 7.97:1; text gold on obsidian 8.66:1; text gold-70 on card 4.51:1; text muted on card 5.14:1; text obsidian on card 1.09:1 (below 4.5:1); text obsidian on obsidian 1.0:1 (below 4.5:1); text render-dcd6cc on card 12.61:1; text render-dcd6cc on obsidian 13.7:1; text warm-white on card 16.92:1; text warm-white on obsidian 18.39:1

## Indicator / Stroke-weight sample

Variants: Bar (6). Used on 3 screens: 46, 47, 48.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-obsidian, --arch-radius-8, --arch-radius-full, --arch-render-ece6dc | 16 | 34.26–39.52 | 6.4–6.82 | 8 pt | none | not a control | 3: 46, 47, 48 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative, paired with the adjacent control label.
- Contrast: text obsidian on render-ece6dc 15.95:1

## Decoration / Accent bar

Variants: Modal head (2). Used on 2 screens: 79, 81.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| default | --arch-gold-65, --arch-radius-2, --arch-radius-full | 3 | 44 | n/a | 1.5 pt | none | not a control | 2: 79, 81 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative.
- Contrast: no text or border pair on this component.

## Indicator / Badge

Variants: Label pill (2). Used on 2 screens: 53, 64.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| filled (gold) | --arch-gold, --arch-obsidian, --arch-radius-10, --arch-radius-full | 20 | 68 | 5.86 | 10 pt | none | not a control | 1: 64 |
| selected (gold border) | --arch-border-1, --arch-card, --arch-gold, --arch-obsidian, --arch-radius-11, --arch-radius-full | 22 | 343 | 145.95 | 11 pt | 1 pt | not a control | 1: 53 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): "<label>" (static text).
- Contrast: border gold on obsidian 8.66:1; text gold on card 7.97:1; text obsidian on gold 8.66:1

## Icon / Status circle

Variants: Outlined circle (2). Used on 2 screens: 48, 68.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| outlined (gold 80%) | --arch-border-1, --arch-gold, --arch-gold-80, --arch-obsidian, --arch-radius-29, --arch-radius-30, --arch-radius-full | 58–60 | 58–60 | 24.75–26.48 | 29–30 pt | 1 pt | not a control | 2: 48, 68 |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative.
- Contrast: border gold-80 on obsidian 5.82:1; text gold on obsidian 8.66:1

## Input / Code digit box

Variants: One digit (6). Used on 1 screens: 11.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| focused (gold border) | --arch-border-1, --arch-card, --arch-gold, --arch-obsidian, --arch-radius-12, --arch-warm-white | 56 | 46 | 17.32–17.34 | 12 pt | 1 pt | visual 56 × 46 · meets 44 pt; hit area equals the visible size | 1: 11 |
| resting | --arch-border, --arch-border-1, --arch-card, --arch-radius-12 | 56 | 46 | n/a | 12 pt | 1 pt | visual 56 × 46 · meets 44 pt; hit area equals the visible size | 1: 11 |

Accessibility

- Minimum touch target: smallest visual side 46 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "Digit <n> of <total>, text field".
- Contrast: border gold on obsidian 8.66:1; text warm-white on card 16.92:1

## Indicator / Dot

Variants: Small circle (1). Used on 1 screens: 73a.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| selected (gold border) | --arch-border-1, --arch-gold, --arch-obsidian, --arch-radius-7, --arch-radius-full | 14 | 14 | n/a | 7 pt | 1 pt | not a control | 1: 73a |

Accessibility

- Minimum touch target: not a control.
- VoiceOver label pattern (proposed): Decorative.
- Contrast: border gold on obsidian 8.66:1

## Text / Language name (own script)

Variants: 1 distinct styles (2). Used on 1 screens: 57.

| Property | Values |
|---|---|
| Typeface | Noto Serif CJK JP 400 |
| Sizes (pt) | 18 |
| Tracking (pt) | 0 |
| Colours | --arch-render-ece6dc |
| Text runs | 2 across 1 screens |
| Contrast | render-ece6dc on obsidian 15.95:1 |
| VoiceOver | Static text: read as written; headings carry the heading trait (display headings and section labels). |
| Measurement | Cap-aligned baseline positions per screen are in `arch-geometry.json`. Line height tokens: `--arch-line-height-ui`. |

## Tile / Style tile

Variants: Photograph + label (8). Used on 1 screens: 29.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| standard (border 2A2A2A) | --arch-border, --arch-border-1, --arch-card, --arch-radius-13, --arch-warm-white | 89 | 79.75 | 13.95–27.85 | 13 pt | 1 pt | visual 89 × 79.75 · meets 44 pt; hit area equals the visible size | 1: 29 |
| selected (gold border) | --arch-border-1, --arch-card, --arch-gold, --arch-obsidian, --arch-radius-13 | 89 | 79.75 | 11.03 | 13 pt | 1 pt | visual 89 × 79.75 · meets 44 pt; hit area equals the visible size | 1: 29 |

Accessibility

- Minimum touch target: smallest visual side 79.75 pt; meets 44 pt.
- VoiceOver label pattern (proposed): "<Style name>, <n> of 8, button" with ", selected" on the active tile.
- Contrast: border gold on obsidian 8.66:1; text gold on card 7.97:1; text warm-white on card 16.92:1

## Form / Toggle

Variants: Switch (3). Used on 1 screens: 56.

| State | Tokens consumed | Height | Width | Padding (inline) | Radius | Border | Touch target | Screens |
|---|---|---|---|---|---|---|---|---|
| on | --arch-gold-90, --arch-obsidian, --arch-radius-full | 22 | 40 | n/a | 11 pt | none | visual 22 × 40 · hit area 44 × 44 pt, centred on the visible element | 1: 56 |
| off | --arch-border, --arch-muted, --arch-radius-full | 22 | 40 | n/a | 11 pt | none | visual 22 × 40 · hit area 44 × 44 pt, centred on the visible element | 1: 56 |

Accessibility

- Minimum touch target: smallest visual side 22 pt; hit area 44 × 44 pt minimum, centred on the visible element. Visible size and hit area are specified separately.
- VoiceOver label pattern (proposed): "<label>, switch, on" or "off".
- Contrast: no text or border pair on this component.

## States specified for the build

| Component | State | Specification | Source | Status |
|---|---|---|---|---|
| Input / Text input | focused | Border gold (arch-gold) 1 pt, fill card, label gold, value warm white, radius 14, height 52. Drawn on screens 05, 08, 09, 37, 49a, 54, 59, 65 and two more; screens 05, 54 and 59 are the reference frames. | Extracted from the screens | Extracted |
| Card / Card | featured | Fill #0F0C05 (token arch-card-featured), which is the form ground in the June 2026 website design system. Border and radius are not stated in that source. Proposed here: radius 14 and a 1 pt gold 45% border, so that the card reads against the obsidian ground. No screen draws a featured card. | Fill from the design system; border proposed | Fill extracted, border PROPOSED |
| Overlay / Modal sheet | bottom sheet | Floating bottom-anchored sheet: 343 wide, 25 inset left and right, bottom edge 74 above the screen bottom, radius 24, fill card, 1 pt border #2A2A2A, grabber 44 × 3 (radius 1.5, gold 65%) 16 below the top edge, inner padding 18, stacked full-width actions. Drawn on screens 79 and 81. An earlier version of this specification labelled these two screens centred dialogs; that was wrong. | Extracted from screens 79 and 81 | Extracted |
| Button / Primary (solid) | pressed | Fill drops from gold to gold 85% (arch-gold-pressed-primary). Transition 200 ms ease-out (arch-comp-pressed-duration-ms, arch-comp-pressed-easing). Label stays obsidian. | Brief of 16 October 2026 | Specified |
| Button / Secondary (outlined) | pressed | Fill goes from none to gold 12% (arch-gold-pressed-secondary). Border and label unchanged. Transition 200 ms ease-out. | Brief of 16 October 2026 | Specified |
| Input / Text input | disabled | Border gold 12% (arch-gold-disabled-input-border), text #888888 (arch-muted), no caret, not focusable. Fill and radius as the resting field. | Brief of 16 October 2026 | Specified |

## Hit areas

Visible size and hit area are specified separately. Every control below has a visible size under 44 pt on at least one side; its hit area is 44 × 44 pt minimum, centred on the visible element.

| Component | Smallest visible size | Hit area |
|---|---|---|
| Back button | 30 × 30 pt | 44 × 44 pt, centred |
| Secondary (outlined) | 58 × 24 pt | 44 × 44 pt, centred |
| Text link | 160 × 16 pt | 44 × 44 pt, centred |
| Collection tabs | 343 × 24 pt | 44 × 44 pt, centred |
| List row | 343 × 28 pt | 44 × 44 pt, centred |
| Checkbox | 18 × 18 pt | 44 × 44 pt, centred |
| Icon button (circular) | 34 × 34 pt | 44 × 44 pt, centred |
| Colour swatch | 10 × 10 pt | 44 × 44 pt, centred |
| Radio | 22 × 22 pt | 44 × 44 pt, centred |
| Toggle | 40 × 22 pt | 44 × 44 pt, centred |

## Typography

The token file carries the rendered values and is authoritative; the written specification is superseded. Each tier token holds the weight, size, tracking and line height drawn on the approved screens.

| Tier token | Used for | Weight | Size (pt) | Tracking (pt) | Line height (pt) |
|---|---|---|---|---|---|
| tier-1 | Button label | 500 | 13 | 0 | 15.847 |
| tier-2 | Section label | 400 | 10.667 | 2 | 13.003 |
| tier-3 | Card subtitle (all caps) | 400 | 9 | 1.3 | 10.971 |
| navigation | Bottom navigation label | 400; active 500 | 8 | 0.9 | 9.752 |
| display | Display headline | 300 italic | 32 | 0 | 38.752 |

The style tile label on screen 29 is drawn at 7.667 pt with 0.45 pt tracking and has its own tokens (type-tile-label-size, type-tile-label-tracking). Tier 3 case is uppercase; the screens draw all caps, not small caps. Line height is 1.219 times the size for UI text and 1.211 times for display text.

## States not drawn

| Component | State | Note |
|---|---|---|
| Button / Primary (solid) | focused (keyboard) | No keyboard focus frame exists in the screen set. The package CSS draws a gold focus ring for prototype use only; the native build uses the system focus treatment. |

## Inventory coverage

Every element that appears more than twice in the measurement files (91 element names) is mapped to a component above, or listed as an exception below.

Mapped: 84 element names. Exceptions: 7.

| Element (kind · name) | Count | Exception reason |
|---|---|---|
| zone_guidance · Contextual fading edge text | 20 on 20 screens | Mirror-screen text that fades after a set interval. The measurement files carry no box for it, so it has no measurable component. Timing is in the developer notes. |
| routing · Entry and exit | 10 on 10 screens | Routing annotation for the handoff; not a UI element. |
| review · Pending confirmations | 10 on 10 screens | Pending-confirmation annotation for review; not a UI element. |
| note · Build | 7 on 7 screens | Developer annotation on the screen (Build note); not a UI element. |
| build · Library | 6 on 6 screens | Developer annotation. |
| state · Completion state | 3 on 1 screens | Describes a screen state, not an element. |
| checks · Automatic setup validation | 3 on 2 screens | Group of three setup checks; each check is a List row / Checklist item. |

## Observed radii and borders

Radii in use: 9, 10, 12, 13, 14, 16, 18, 20, 22, 24 points and the full pill. They do not follow a base-unit scale and are kept as observed. Border weights: 1 point (336 uses), 0.67 point (6), 2.33 points (7) and none (29).

