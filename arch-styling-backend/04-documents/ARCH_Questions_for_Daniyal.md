# ARCH Questions for Daniyal

1 November 2026. A short answer to each is plenty. Where you do not know yet, say so and say what you need.

1. Which framework is the app built on, Flutter or SwiftUI? The brow library spec names a Flutter package (cached_network_image), but the notes refer to StoreKit and SwiftUI.
2. What is the minimum iOS version, and the minimum Android version? The library images are WebP, which needs iOS 14 or later and Android 4.0 or later.
3. If a member leaves a tracing session from the leave-session prompt (75d), is anything already saved kept, or is anything discarded? One line will be written on the next screen saying the session ended and nothing was saved. It will not be written until you confirm it is true.
4. When the scan completes, is the brow profile stored on the device, on a server, or both? One line is enough.
5. Can the build tell three consent states apart: no consent record, consent recorded, and consent withdrawn after Delete my face scan? The face-scan consent screen (23) shows in the first and third and is skipped in the second. Where is the consent record stored?
6. What does a saved look store: a photograph of her face with the brow applied, or only the recipe (style, intensity, colour, mode), or both? If she removes the photographs, the look must stay as a record she can re-apply.
7. What does completing a hand-drawn guide at 49d produce: an instruction only, or a saved guide?
8. How would the 24-month retention be run: a scheduled job, and what would it delete (measurements, brow profile, photographs in saved looks, the account)? Last use is not defined yet, so no answer is needed beyond what is feasible.
9. If a member takes the recommendation route after already scanning, can the build reuse her existing scan, or must it rescan?
10. How does the scan classify a face into one of the seven shapes (oval, round, square, heart, diamond, oblong, triangle)? Answer what you know. If it is the AR engine's decision, say so and pass it to Mamooth.
