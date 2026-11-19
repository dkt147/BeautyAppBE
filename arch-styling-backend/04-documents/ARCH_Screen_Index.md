# ARCH Screen Index · 30 October 2026 update

Updated 30 October 2026 after the final corrections and Batch E (Batches A to E, staged for one push). Everything below this section is the 15 October index, with the rows for the corrected screens replaced. The rows for screens not redrawn are as at 15 October.

## What changed

Counts, from the files in the push package against the master screens folder:

| Step | PNGs |
| --- | --- |
| Master folder before this update | 132 |
| Retired names moved to _archive (S27_Scan_Complete, S51_My_Looks_Empty, S53_Profile_Home, S55_Brow_Profile). S39_Recommendation_Intro is not archived: it is the first-time state and stays beside the already-scanned state | −4 |
| New file names added (state variants, Refine variants, seven-shape 43, My Looks tabs and empty states, 36a, 55b to 55f, 30a Refine card, 29 no scan after a tap) | +36 |
| Same-name files overwritten with corrected art (not a count change) | 21 |
| **Final** | **164** |

Screen numbers: 127 before, plus 7 new rows in this index (30a, 36a, 55b, 55c, 55d, 55e, 55f) = 134. The Screen Text Export carries the same 134 rows.

Archive and routes:
- 27 is now two chip states (S27_Scan_Complete_NoStyleSelected, S27_Scan_Complete_ChosenStyle) and shows two recommendations.
- 39 gained the already-scanned state; 53 gained the Privacy Policy row; 55 gained Delete my face scan (55b to 55f).
- 43 now has seven shapes (Oval is S43_Why_This_Shape_2).
- 50 has three tabs, ALL, TRACED and PREVIEWED; 51 has four states: all, traced, previewed, free account.
- 40 and 41 stay in the build until the AR partner confirms in writing; the merged route does not use them.
- 30a: both cards are redrawn. The Reshape card was redrawn on 1 November 2026 on the current screen 30.
- Screens 89 to 94, 49 and 87 still show Guides in their copy. They were not redrawn and are not changed here; the audit was withdrawn by decision on 30 October 2026.
- 02 reads within 24 months of your last use. Pricing screens 13, 64, 66 and 67 carry $19.99 and $179.99.

---

# ARCH Screen Index · Final Correction Round

Issued 15 October 2026. Status is measured against the previous master delivery: new, corrected or unchanged. Unchanged means the PNG is pixel-identical to the master.

## Count reconciliation

Delivered PNGs: **132**. Distinct screen numbers: **127**. The previous master delivery held 127 PNGs across 125 screen numbers (its index also listed retired screen 86, which has no PNG).

PNG arithmetic, step by step:

| Step | PNGs |
| --- | --- |
| Master delivery | 127 |
| Remove old 02 (Privacy Policy) | −1 |
| Remove old 35 pair (selection and comparison) | −2 |
| Remove 77, 77a and 77b | −3 |
| Subtotal | 121 |
| Add new 02 (default and Ready) | +2 |
| Add 35a and 35b | +2 |
| Add 77 as one number with three state PNGs | +3 |
| Add 49c Tracing Unavailable | +1 |
| Add 13a Account Gate (Looks and Profile) | +1 |
| Add 73 Ready state | +1 |
| Add 55a Brow Profile editable state | +1 |
| **Final** | **132** |

Reading against the brief (127 − 2 + 2 = 127): the brief's arithmetic treats 77 as a single PNG. This set shows 77 as one screen number with three state PNGs (State 1, State 2, State 2 after SAVE LOOK), which is +2 against that reading. The other +3 are additions not named in the brief: the 02 Ready state, the 73 Ready state and 55a. 35 to 35a/35b is a numbering change; the old 35 already held two PNGs. Screen 23 is two PNGs (default and Ready) under one number.

Screen-number arithmetic: 125 master numbers, +1 for 35 splitting into 35a and 35b, −2 for 77a and 77b, +1 for 49c, +1 for 55a, +1 for 13a = 127.


Status by screen number: new 7 · corrected 66 · unchanged 54 (total 127).

## Renumbering and route updates

| Old | New | Routes updated |
| --- | --- | --- |
| 35 (selection / comparison) | 35a Selection · 35b Result | 31 → 35a; 35a → 35b; 35b → 36; 35b Go back → 29 |
| 77, 77a, 77b | 77 (two states) | Routes to 77a or 77b now point to 77; 77 State 1 SAVE LOOK → 77 State 2; VIEW IT IN MY LOOKS → 50; LOOKS GOOD → 20 |
| (none) | 49c Tracing Unavailable | 73 and 73a and 75c → 49c; 49c OPEN THE GUIDE → 45; TRY TRACING AGAIN → 73 |
| (none) | 13a Account Gate (Looks and Profile) | 12 and 12a tabs LOOKS and PROFILE → 13a; 13a CREATE AN ACCOUNT → 05, then 14 to 18, then 29; 13a Keep browsing and Back → 12 or 12a |
| (none) | 55a Brow Profile editable | 55 UPDATE → 55a; 55a SAVE CHANGES / CANCEL → 55 |
| 02 Privacy Policy | 02 Before We Begin | 01 → 02 → 03 unchanged; the old 02 is replaced |

## Screens

| No. | Name | Status | PNG file(s) | Routes out |
| --- | --- | --- | --- | --- |
| 01 | Splash | unchanged | S01_Splash.png | Auto-advance after splash → 02 |
| 02 | Before We Begin · Biometric Notice | corrected (30 October 2026) | S02_Before_We_Begin.png, S02_Before_We_Begin_Ready.png | CONTINUE (enabled only when all four boxes are ticked) → 03; Privacy Policy link → cbygroyals.com/privacy (web); Terms of Use link → 62 |
| 03 | Brand Manifesto | unchanged | S03_Brand_Manifesto.png | ENTER → 04 |
| 04 | New or Returning | corrected | S04_New_or_Returning.png | I’m new here → 05; Welcome back → 08; Continue as guest → 12 |
| 05 | Create Account | unchanged | S05_Create_Account.png | CREATE ACCOUNT (success) → 14; Validation error → 06; Email already registered → 07; SIGN IN → 08; Continue with Apple / Google → 14 |
| 06 | Create Account · Error State | corrected | S06_Create_Account_Error.png | CREATE ACCOUNT (after correction) → 05; SIGN IN → 08 |
| 07 | Account Already Exists | corrected | S07_Account_Already_Exists.png | Sign in instead → 08; Edit email → 05 |
| 08 | Sign In | unchanged | S08_Sign_In.png | SIGN IN → 11 (two-factor) or 20 / 21 (home); Forgot password? → 09; Create account → 05 |
| 09 | Forgot Password | unchanged | S09_Forgot_Password.png | SEND RESET LINK → 10 |
| 10 | Reset Link Sent | unchanged | S10_Reset_Link_Sent.png | Back to sign in → 08 |
| 11 | Two-Factor Auth | unchanged | S11_Two_Factor_Auth.png | VERIFY → 14 (new account) or 20 / 21 (returning) |
| 12 | Guest Home | unchanged | S12_Guest_Home.png | Brow styles → 12a; How ARCH works → 61; Try-On / scan → 13; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 12a | Guest Try-On Preview | unchanged | S12a_Guest_TryOn_Preview.png | CREATE AN ACCOUNT → 05; BACK TO BROWSING → 12; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 13 | Scan Gate | corrected (30 October 2026) | S13_Scan_Gate.png | CREATE AN ACCOUNT → 05; Keep browsing → 12 |
| 14 | Skin Tone + Goal Selection | corrected | S14_Skin_Tone_and_Goal.png | Next → 15 |
| 15 | Skin Tone Confirmation | unchanged | S15_Skin_Tone_Confirmation.png | CONFIRM THIS TONE → 16; Back → 14 |
| 16 | Style Direction Selection | corrected | S16_Style_Direction.png | BEGIN → 17; I’ll add this later → 18 |
| 17 | Style Direction Confirmation | corrected | S17_Style_Direction_Confirmation.png | THIS IS MY DIRECTION → 18; Choose a different direction → 16 |
| 18 | Onboarding Complete | corrected | S18_Onboarding_Complete.png | ENTER ARCH → 19; Edit your selections → 14 |
| 19 | Home (New User) | unchanged | S19_Home_New_User_Approved_Unchanged.png | Try a brow style → 22; Draw your tracing guide → 45; Get a recommendation → 39; Read my brows → 22 [to confirm] |
| 20 | Home (Returning User) | unchanged | S20_Home_Returning.png | Try a brow style → 22; Draw your tracing guide → 45 [to confirm]; Get a recommendation → 39 [to confirm]; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 21 | Personalised Returning Welcome | corrected | S21_Personalised_Returning_Welcome.png | RE-APPLY → 36 [to confirm]; NEW SCAN → 22; MY LOOKS → 50; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 22 | Face Scan Intro | corrected | S22_Face_Scan_Intro.png | BEGIN SCAN → 23; Browse styles directly → 29 |
| 23 | Camera Permission + Face Scan Consent (consent ticked) | unchanged | S23_Camera_Permission_Consent.png, S23_Camera_Permission_Consent_Ready.png | ALLOW CAMERA → 25 (granted) or 24 (denied); NOT NOW → 22; READ PRIVACY POLICY → cbygroyals.com/privacy (web) |
| 24 | Camera Access Settings (If Denied) | unchanged | S24_Camera_Access_Settings.png | TERMINAL (leaves the app to iOS Settings). OPEN SETTINGS → iOS Settings (leaves the app); Back → 22 |
| 25 | Scanning Active | unchanged | S25_Scanning_Active.png | CANCEL → 22; Scan complete → 27; No face detected → 26; Low light → 84; Scan timeout → 85 |
| 26 | Face Not In Frame | unchanged | S26_Face_Not_In_Frame.png | TRY AGAIN → 25 |
| 27 | Scan Complete | corrected (30 October 2026) | S27_Scan_Complete_ChosenStyle.png, S27_Scan_Complete_NoStyleSelected.png, S27_Scan_Complete_StyleCarriedIn.png | EXPLORE YOUR STYLES → 28 (no chip selected); PREVIEW plus the style name → 30 (a chip selected, including a style chosen on 29 that is added as a selected third chip); Why these suit you → 42; See all styles → 29 |
| 28 | Post-Scan Discovery | corrected | S28_Post_Scan_Discovery.png | SEE WHAT SUITS YOUR FEATURES → 29; Browse all styles instead → 29 |
| 29 | Style Selector | corrected (30 October 2026) | S29_Style_Selector.png (Refine mine), S29_Style_Selector_Reshape.png (Reshape mine), S29_Style_Selector_NoScan.png, S29_Style_Selector_NoScan_Selected.png | PREVIEW THIS LOOK → 30 (with a scan); with no scan → 22, then 23 (first scan only), 25, 27, landing on 30 with her choice applied; a guest meets 13 first; Back → 28. With no scan there is no mode toggle: S29_Style_Selector_NoScan is the state before a tap (the panel reads Choose a style to see it.; no caption; button disabled) and S29_Style_Selector_NoScan_Selected is the state after a tap (the panel shows the library image; no Recommended markers) |
| 30 | Style Applied | corrected (30 October 2026) | S30_Style_Applied.png (Refine mine), S30_Style_Applied_Reshape.png (Reshape mine) | HOW FAR TO TAKE IT → 31; Mode toggle (REFINE MINE / RESHAPE MINE) → same screen, no route; 30a appears on arrival at this screen, after two seconds, once for each account |
| 30a | Style Applied · Mode Introduction (first use) | new (30 October 2026); both cards redrawn (Reshape card 1 November 2026) | S30a_Mode_First_Use.png (Refine mine), S30a_Mode_First_Use_Reshape.png (Reshape mine; redrawn 1 November 2026) | GOT IT → 30 (same screen); Toggle tapped while the explanation is up → same screen (swap made, explanation dismissed) |
| 31 | Intensity Selector | corrected (30 October 2026) | S31_Intensity_Selector.png (Refine mine), S31_Intensity_Selector_Reshape.png (Reshape mine) | SEE THIS LOOK → 32 / 33 / 34 (by selected intensity); Compare two intensities → 35a [to confirm] |
| 32 | Intensity · Understated | corrected (30 October 2026) | S32_Intensity_Understated.png (Refine mine), S32_Intensity_Understated_Reshape.png (Reshape mine) | THIS IS THE ONE → 36; Try Defined instead → 33; Mode toggle (REFINE MINE / RESHAPE MINE) → same screen, no route |
| 33 | Intensity · Defined | corrected; second state added 1 November 2026 | S33_Intensity_Defined.png (REFINE MINE selected), S33_Intensity_Defined_Reshape.png (RESHAPE MINE selected) | THIS IS THE ONE → 36; Mode toggle (REFINE MINE / RESHAPE MINE) → same screen, no route |
| 34 | Intensity · Deliberate | corrected; second state added 1 November 2026 | S34_Intensity_Deliberate.png (REFINE MINE selected), S34_Intensity_Deliberate_Reshape.png (RESHAPE MINE selected) | THIS IS THE ONE → 36; Back to Defined → 33; Mode toggle (REFINE MINE / RESHAPE MINE) → same screen, no route |
| 35a | Two Looks · Selection | new | S35a_Two_Looks_Selection.png (Refine mine), S35a_Two_Looks_Selection_Reshape.png (Reshape mine) | SELECT ONE MORE TO COMPARE → (enabled at two selections) → 35b; Back → 31 |
| 35b | Two Looks · Comparison | corrected (30 October 2026) | S35b_Two_Looks_Comparison.png (Refine mine), S35b_Two_Looks_Comparison_Reshape.png (Reshape mine) | I CHOOSE [INTENSITY] → 36; Go back to all styles → 29; Mode toggle (REFINE MINE / RESHAPE MINE) → same screen, no route |
| 36 | This Is Your Look | corrected (30 October 2026) | S36_This_Is_Your_Look.png (Refine mine), S36_This_Is_Your_Look_Reshape.png (Reshape mine) | SAVE THIS LOOK → 37; TRACE THIS LOOK → 73; Return to home → 20; Mode toggle (REFINE MINE / RESHAPE MINE) → same screen, no route |
| 36a | Before You Trace | new (30 October 2026) | S36a_Before_You_Trace.png (Refine mine), S36a_Before_You_Trace_Reshape.png (Reshape mine) | BEGIN → 73; Back arrow → 36 |
| 37 | Save Look | corrected (30 October 2026) | S37_Save_Look.png (Refine mine), S37_Save_Look_Reshape.png (Reshape mine) | SAVE THIS LOOK → 38 |
| 38 | Saved Confirmation | corrected (30 October 2026) | S38_Saved_Confirmation.png (Refine mine), S38_Saved_Confirmation_Reshape.png (Reshape mine) | VIEW MY LOOKS → 50; Return to home → 20 |
| 39 | Recommendation Intro | corrected (30 October 2026) | S39_Recommendation_Intro.png, S39_Recommendation_Intro_AlreadyScanned.png | ANALYSE MY FACE → 22 (first time; 23 on the first scan, then 25 → 27); SEE MY RECOMMENDATIONS → 27 (already scanned); Browse all styles instead → 29. 40 and 41 stay in the build until the AR partner confirms in writing |
| 40 | Reading Face | unchanged | S40_Reading_Face.png | Reading complete (automatic) → 41; CANCEL → 39 |
| 41 | Your Result | corrected | S41_Your_Result.png | TRY TOP RECOMMENDATION → 42 [to confirm]; See all styles → 29 |
| 42 | Why This Shape (View 1) | corrected (30 October 2026) | S42_Why_This_Shape_1.png | WHY IT SUITS YOUR FACE → 43; Try another → 29 |
| 43 | Why This Shape (View 2) | corrected (30 October 2026) | S43_Why_This_Shape_2.png, S43_Why_This_Shape_2_Diamond.png, S43_Why_This_Shape_2_Heart.png, S43_Why_This_Shape_2_Oblong.png, S43_Why_This_Shape_2_Round.png, S43_Why_This_Shape_2_Square.png, S43_Why_This_Shape_2_Triangle.png | SEE THE DIFFERENCE → 44; Try a different recommendation → 27 |
| 44 | The Difference | corrected (30 October 2026) | S44_The_Difference.png (Refine mine), S44_The_Difference_Reshape.png (Reshape mine) | THIS IS THE ONE → 30; Try another style → 29 |
| 45 | Tracing Guide Intro | unchanged | S45_Tracing_Guide_Intro.png | BEGIN DRAWING → 46 |
| 46 | Draw Mode | unchanged | S46_Draw_Mode.png | MOVE TO RIGHT → 46 (other brow); ERASE → 47; RESET → 48; DONE → 49 |
| 47 | Erase | unchanged | S47_Erase.png | DRAW → 46; RESET → 48; DONE → 49 |
| 48 | Reset | unchanged | S48_Reset.png | YES, START AGAIN → 46; KEEP GOING → 46 |
| 49 | Guide Complete | unchanged | S49_Guide_Complete.png | SAVE MY GUIDE → 49a; SHARE WITH MY ARTIST → 52 (share sheet) [to confirm] |
| 49a | Save Guide | unchanged | S49a_Save_Guide.png | SAVE THIS GUIDE → 49b |
| 49b | Guide Saved | corrected (30 October 2026) | S49b_Guide_Saved.png | VIEW IT IN MY LOOKS → 50 (TRACED tab); Return to home → 20 |
| 49c | Tracing Unavailable | new | S49c_Tracing_Unavailable.png | OPEN THE GUIDE → 45; TRY TRACING AGAIN → 73 |
| 50 | My Looks (Populated) | corrected (30 October 2026) | S50_My_Looks_Populated.png, S50_My_Looks_Populated_Previewed.png, S50_My_Looks_Populated_Traced.png | Look card → 36 (look opened) [to confirm]; SHARE → 52; CREATE A NEW LOOK → 29 (scan held) or 22 (no scan); Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 51 | My Looks (Empty State) | corrected (30 October 2026) | S51_My_Looks_Empty_All.png, S51_My_Looks_Empty_Free.png, S51_My_Looks_Empty_Previewed.png, S51_My_Looks_Empty_Traced.png | CREATE A NEW LOOK → 29 (scan held) or 22 (no scan); Free account: See what membership includes → 64 (wording approved 30 October 2026); Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 52 | Share This Look | unchanged | S52_Share_This_Look.png | TERMINAL (leaf screen; back only). Back to look → 50 |
| 53 | Profile Home | corrected (30 October 2026) | S53_Profile_Home_Privacy_Policy.png | MEMBER badge → 63; About ARCH → 60; Brow Profile → 55; Preferences → 56; Language & Region → 57; Help & Support → 58; Contact → 59; How ARCH works → 61; Terms of Use → 62; My Account → 54; ARCH Membership → 63; Sign Out → 81; Delete My Account → 78; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 54 | My Account (Edit) | unchanged | S54_My_Account_Edit.png | SAVE CHANGES → 53 |
| 55 | Brow Profile | corrected (30 October 2026) | S55_Brow_Profile_Delete_Row.png | UPDATE → 55a; SCAN AGAIN → 22; DELETE MY FACE SCAN → 55b |
| 55a | Brow Profile · Editable | new | S55a_Brow_Profile_Editable.png | SAVE CHANGES → 55 [to confirm]; CANCEL → 55 [to confirm] |
| 55b | Delete my face scan · Step 1 | new (30 October 2026); wording updated 1 November 2026 | S55b_Delete_Face_Scan_Step_1.png | CONTINUE → 55c; KEEP MY FACE SCAN → 55 (nothing deleted) |
| 55c | Delete my face scan · Step 2 · photographs | new (30 October 2026) | S55c_Delete_Face_Scan_Step_2.png | REMOVE PHOTOGRAPHS TOO → 55d; KEEP MY PHOTOGRAPHS → 55e; Go back → 55b (nothing deleted yet) |
| 55d | Delete my face scan · Done · photographs removed | new (30 October 2026); wording updated 1 November 2026 | S55d_Face_Scan_Deleted_Photographs_Removed.png | SCAN AGAIN → 23 (consent shows again after deletion; to confirm); BACK TO PROFILE → 55 (shows 55f, no scan) |
| 55e | Delete my face scan · Done · photographs kept | new (30 October 2026); wording updated 1 November 2026 | S55e_Face_Scan_Deleted_Photographs_Kept.png | SCAN AGAIN → 23 (consent shows again after deletion; to confirm); BACK TO PROFILE → 55 (shows 55f, no scan) |
| 55f | Profile · Brow Profile · no scan | new (30 October 2026) | S55f_Brow_Profile_No_Scan.png | BEGIN SCAN → 23 (consent shows again after deletion; to confirm) |
| 56 | Preferences | corrected | S56_Preferences.png | Language → 57; SAVE CHANGES → 53 |
| 57 | Language & Region | unchanged | S57_Language_Region.png | SAVE PREFERENCE → 53 |
| 58 | Help & Support | unchanged | S58_Help_Support.png | TERMINAL (leaf screen; routes to other screens only through its rows). How ARCH works → 61; Your privacy and data → 61 [to confirm]; Managing your membership → 63; Delete your account → 78; Contact us → 59 |
| 59 | Contact Us | unchanged | S59_Contact_Us.png | SEND MESSAGE → 53 (confirmation then back) [to confirm] |
| 60 | About ARCH | corrected | S60_About_ARCH.png | TERMINAL (leaf screen; back only). Back → 53 |
| 61 | How ARCH Works | corrected | S61_How_ARCH_Works.png | TERMINAL (leaf screen; back only). Back → 53 |
| 62 | Terms of Use | unchanged | S62_Terms_of_Use.png | TERMINAL (leaf screen; back only). Back → 53 or 02 (when opened from the consent screen) |
| 63 | Membership Standing | corrected | S63_Membership_Standing.png | MANAGE MEMBERSHIP → 70 |
| 64 | Membership Gate (Unlock) | corrected (30 October 2026) | S64_Membership_Gate.png | BEGIN YOUR MEMBERSHIP → 66 (web) or native purchase sheet (iOS / Android) |
| 65 | Phone Number (Trial Start) | corrected | S65_Phone_Number.png | CONTINUE → 67; BACK TO PLANS → 64; Not now → 67 |
| 66 | Payment Details | corrected (30 October 2026) | S66_Payment_Details.png | START MY FREE TRIAL → 65; Change → 64; Restore purchase → native restore (iOS / Android) |
| 67 | Free Trial Begun | corrected (30 October 2026) | S67_Free_Trial_Begun.png | ENTER ARCH → 20 |
| 68 | Payment Failed | corrected | S68_Payment_Failed.png | UPDATE PAYMENT → 69; Remind me later → originating screen |
| 69 | Update Payment | unchanged | S69_Update_Payment.png | SAVE AND CONTINUE → originating screen / 63 |
| 70 | Cancellation Retention | corrected | S70_Cancellation_Retention.png | SWITCH TO MONTHLY → showManageSubscriptions(in:) (iOS); CONTACT US → 59; I STILL WANT TO CANCEL → 71 |
| 71 | Cancel Membership | corrected (30 October 2026) | S71_Cancel_Membership.png | CONFIRM CANCELLATION → 72; Keep my membership → 63 |
| 72 | Membership Cancelled | corrected | S72_Membership_Cancelled.png | TERMINAL (end of the cancellation journey). RETURN TO PROFILE → 53 |
| 73 | Tracing · Setup Check | corrected | S73_Setup_Check.png, S73_Setup_Check_Ready.png | BEGIN (enabled only when Light, Phone, Face pass and Product is ticked) → 74; Light recovers → 73 (ready); Tracing cannot proceed → 49c |
| 73a | Tracing · Setup light too low | corrected | S73a_Setup_Light_Too_Low.png | CONTINUE ANYWAY → 74; Light recovers (automatic) → 73; Tracing cannot proceed → 49c |
| 74 | Tracing · Position & Adjust | corrected | S74_Position_Adjust.png (Refine mine), S74_Position_Adjust_Reshape.png (Reshape mine) | BEGIN TRACING → 75-01 (SCULPT) or 76-01 (REFINE); Exit mark → 75d |
| 74a | Tracing · Position & Adjust · Landscape | corrected | S74a_Position_Adjust_Landscape.png (Refine mine), S74a_Position_Adjust_Landscape_Reshape.png (Reshape mine) | BEGIN TRACING → 75-01 (SCULPT) or 76-01 (REFINE); Exit mark → 75d |
| 75a | Tracing · Interrupted | unchanged | S75a_Interrupted.png (Refine mine), S75a_Interrupted_Reshape.png (Reshape mine) | RESUME TRACING → same stage; 74 after readiness review; Exit mark → 75d |
| 75b | Tracing · Light Too Low | unchanged | S75b_Light_Too_Low.png (Refine mine), S75b_Light_Too_Low_Reshape.png (Reshape mine) | Light recovers (automatic) → 75f |
| 75c | Tracing · Tracking Lost | unchanged | S75c_Tracking_Lost.png | Face recovered (automatic) → 75f; Repeated failure → 49c |
| 75d | Tracing · Exit Confirmation | unchanged | S75d_Exit_Confirmation.png (Refine mine), S75d_Exit_Confirmation_Reshape.png (Reshape mine) | KEEP TRACING → same stage; LEAVE SESSION → 36 |
| 75e | Tracing · Hand Occlusion | unchanged | S75e_Hand_Occlusion.png (Refine mine), S75e_Hand_Occlusion_Reshape.png (Reshape mine) | Hand clears (automatic) → same stage |
| 75f | Tracing · Recovery ready | corrected | S75f_Recovery_Ready.png (Refine mine), S75f_Recovery_Ready_Reshape.png (Reshape mine) | RESUME TRACING → same stage |
| 75g | SCULPT · Landscape tracing | corrected | S75g_SCULPT_Landscape.png | Rotate to portrait (automatic) → same stage |
| 75-01 | SCULPT · Session begins | corrected | S75-01_SCULPT_Session_Begins.png | Next stage (user-driven or automatic) → 75-02; Exit mark → 75d |
| 75-02 | SCULPT · First strokes | corrected | S75-02_SCULPT_First_Strokes.png | Next stage (user-driven or automatic) → 75-03; Exit mark → 75d |
| 75-03 | SCULPT · Partway | corrected | S75-03_SCULPT_Partway.png | Next stage (user-driven or automatic) → 75-04; Exit mark → 75d |
| 75-04 | SCULPT · Stroke drift | corrected | S75-04_SCULPT_Drift.png | Next stage (user-driven or automatic) → 75-05; Exit mark → 75d |
| 75-05 | SCULPT · Correction resolved | corrected | S75-05_SCULPT_Correction_Resolved.png | Next stage (user-driven or automatic) → 75-06; Exit mark → 75d |
| 75-06 | SCULPT · Zone change | corrected | S75-06_SCULPT_Zone_Change.png | Next stage (user-driven or automatic) → 75-07; Exit mark → 75d |
| 75-07 | SCULPT · One brow complete | corrected | S75-07_SCULPT_One_Brow_Complete.png | NEXT BROW → 75-08; Exit mark → 75d |
| 75-08 | SCULPT · Second-brow transition | corrected | S75-08_SCULPT_Second_Brow_Transition.png | CONTINUE → 75-09; Exit mark → 75d |
| 75-09 | SCULPT · Paused · zoomed section | corrected | S75-09_SCULPT_Paused_Zoom.png | Next stage (user-driven or automatic) → 75-10; Exit mark → 75d |
| 75-10 | SCULPT · Both brows complete | corrected | S75-10_SCULPT_Both_Brows_Complete.png | FINISH → 77 |
| 76-01 | REFINE · Session begins | corrected | S76-01_REFINE_Session_Begins.png | Next stage (user-driven or automatic) → 76-02; Exit mark → 75d |
| 76-02 | REFINE · First strokes | corrected | S76-02_REFINE_First_Strokes.png | Next stage (user-driven or automatic) → 76-03; Exit mark → 75d |
| 76-03 | REFINE · Partway | corrected | S76-03_REFINE_Partway.png | Next stage (user-driven or automatic) → 76-04; Exit mark → 75d |
| 76-04 | REFINE · Stroke drift | corrected | S76-04_REFINE_Drift.png | Next stage (user-driven or automatic) → 76-05; Exit mark → 75d |
| 76-05 | REFINE · Correction resolved | corrected | S76-05_REFINE_Correction_Resolved.png | Next stage (user-driven or automatic) → 76-06; Exit mark → 75d |
| 76-06 | REFINE · Zone change | corrected | S76-06_REFINE_Zone_Change.png | Next stage (user-driven or automatic) → 76-07; Exit mark → 75d |
| 76-07 | REFINE · One brow complete | corrected | S76-07_REFINE_One_Brow_Complete.png | NEXT BROW → 76-08; Exit mark → 75d |
| 76-08 | REFINE · Second-brow transition | corrected | S76-08_REFINE_Second_Brow_Transition.png | CONTINUE → 76-09; Exit mark → 75d |
| 76-09 | REFINE · Paused · zoomed section | corrected | S76-09_REFINE_Paused_Zoom.png | Next stage (user-driven or automatic) → 76-10; Exit mark → 75d |
| 76-10 | REFINE · Both brows complete | corrected | S76-10_REFINE_Both_Brows_Complete.png | FINISH → 77 |
| 77 | Tracing · Completion | new | S77_Completion_State_1.png, S77_Completion_State_2.png, S77_Completion_State_2_After_SAVE_LOOK.png | State 1: SAVE LOOK → 77 State 2 (after SAVE LOOK); State 1: LOOKS GOOD → 20; State 2: VIEW IT IN MY LOOKS → 50; State 2: LOOKS GOOD → 20 |
| 78 | Delete My Account | changed 1 November 2026 (deletion wording) | S78_Delete_My_Account.png | MANAGE IN APPLE SETTINGS → showManageSubscriptions(in:); DELETE MY ACCOUNT → 79; KEEP MY ACCOUNT → 53 |
| 79 | Deletion Confirmation Modal | changed 1 November 2026 | S79_Deletion_Confirmation_Modal.png | YES, DELETE MY ACCOUNT → 80; KEEP MY ACCOUNT → 78 |
| 80 | Deletion Underway | changed 1 November 2026 (deletion wording) | S80_Account_Deleted.png | TERMINAL (ends the signed-in session; CONTINUE returns to 04). CONTINUE → 04 |
| 81 | Sign Out Modal | unchanged | S81_Sign_Out_Modal.png | SIGN OUT → 08 [to confirm]; CANCEL → 53 |
| 82 | Notification Priming | unchanged | S82_Notification_Priming.png | YES, KEEP ME INFORMED → 83; NOT RIGHT NOW → originating screen |
| 83 | Native OS Permission Dialog (Reference) | unchanged | S83_Native_Notification_Permission_Reference.png | TERMINAL (OS dialog, reference only). ALLOW / DON’T ALLOW → originating screen |
| 84 | Scan Lighting Error | unchanged | S84_Scan_Lighting_Error.png | TRY AGAIN → 25; BROWSE STYLES → 29 |
| 85 | Scan Slow | unchanged | S85_Scan_Slow.png | TRY AGAIN → 25; BROWSE STYLES → 29 |
| 87 | Between Connections | unchanged | S87_Between_Connections.png | OPEN MY LOOKS → 50 / 51; Retry → originating operation |
| 88 | Generic Error | corrected | S88_Generic_Error.png | TRY AGAIN → originating operation; Return to home → 20 |
| 89 | Looks · The Library (1 of 6) | corrected | S89_Curated_Looks_1_of_6.png | Look card → 36 (look opened) [to confirm]; Scroll to next / previous of 6 → 89 / 90; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 90 | Looks · The Library (2 of 6) | corrected | S90_Curated_Looks_2_of_6.png | Look card → 36 (look opened) [to confirm]; Scroll to next / previous of 6 → 89 / 91; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 91 | Looks · The Library (3 of 6) | corrected | S91_Curated_Looks_3_of_6.png | Look card → 36 (look opened) [to confirm]; Scroll to next / previous of 6 → 90 / 92; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 92 | Looks · The Library (4 of 6) | corrected | S92_Curated_Looks_4_of_6.png | Look card → 36 (look opened) [to confirm]; Scroll to next / previous of 6 → 91 / 93; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 93 | Looks · The Library (5 of 6) | corrected | S93_Curated_Looks_5_of_6.png | Look card → 36 (look opened) [to confirm]; Scroll to next / previous of 6 → 92 / 94; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |
| 94 | Looks · The Library (6 of 6) | corrected | S94_Curated_Looks_6_of_6.png | Look card → 36 (look opened) [to confirm]; Scroll to next / previous of 6 → 93 / 94; Tab bar HOME · TRY-ON · LOOKS · PROFILE → 20 · 22 · 50 · 53 |

Each PNG has a matching measurement file of the same name (.json) in screens/. 01, 03 and 19 carry canvas size and manually entered strings only.
