"""Copy for screens 42 and 43 (M6).

Arch (42) and Oval (43) are quoted from the Visual Screen Map. Everything
else is drafted to match the client's Table 2 (Measurement JSON v1.3.1) and
is marked provisional: question 14 says face shape copy for all seven shapes
is still a draft on the client's side.
"""

# Screen 42 "ABOUT THIS SHAPE": two style lines, then one face line.
STYLE_WHY = {
    "arch": {"lines": ["It lifts your face along the natural line of your brow bone.",
                       "The graduated arch creates elegance without effort."], "provisional": False},
    "structured": {"lines": ["A clean, architectural line gives the upper face clear shape.",
                             "Its defined peak brings quiet precision to the eye."], "provisional": True},
    "feathered": {"lines": ["Visible, separated hairs keep the brow soft and natural.",
                            "Its gentle lift frames the eye without hardening it."], "provisional": True},
    "bold": {"lines": ["A fuller body gives the brow presence.",
                       "It anchors the upper face with confident weight."], "provisional": True},
    "straight": {"lines": ["A flat, level line sits calmly across the brow bone.",
                           "It keeps a longer face balanced and open."], "provisional": True},
    "micro": {"lines": ["Finer hairs give a delicate, precise finish.",
                        "It refines the brow without adding weight."], "provisional": True},
    "sharp": {"lines": ["A defined angle lifts the eye with intent.",
                        "Its clear peak adds structure where the face is soft."], "provisional": True},
    "rounded": {"lines": ["A soft curve eases strong angles.",
                          "It brings a gentle, open look to the eye."], "provisional": True},
}

# Third line of 42, by how the style relates to her face shape.
FIT_LINE = {
    "suits": "{face} faces carry this shape beautifully — it works with your proportions, not against them.",
    "neutral": "This shape can work on {face_lower} faces with careful placement.",
    "avoid": "{face} faces are usually better served by a softer line than this one.",
}

# Screen 43: what her face is, and why the shape is placed where it is.
FACE_WHY = {
    "oval": {"title": "Your face is balanced, a little longer than wide, its jaw gently rounded.",
             "body": "An arch placed fractionally above the brow bone's peak draws the eye upward — "
                     "creating lift without effort.", "provisional": False},
    "round": {"title": "Your face is nearly as wide as it is long, with soft, full curves.",
              "body": "A sharper peak set a little further out adds length and lift to soft lines.",
              "provisional": True},
    "square": {"title": "Your face is strong and balanced, with a broad, defined jaw.",
               "body": "A softer curve, peaked a little earlier, eases the angles of the jaw.", "provisional": True},
    "heart": {"title": "Your face is widest at the forehead and narrows to a delicate chin.",
              "body": "A structured line with an earlier peak keeps the upper face calm.", "provisional": True},
    "diamond": {"title": "Your cheekbones are your widest point, with a narrower forehead and chin.",
                "body": "A rounded line, peaked a touch earlier, softens the cheekbones and frames the eye.",
                "provisional": True},
    "oblong": {"title": "Your face is longer than it is wide, with straight, even sides.",
               "body": "A level line across the brow bone shortens the face and brings it into balance.",
               "provisional": True},
    "triangle": {"title": "Your jaw is your widest point, with a narrower forehead.",
                 "body": "An arch set slightly further out adds width above and answers the jaw.",
                 "provisional": True},
}
CLOSING_43 = "Precise. Effortless."

# MediaPipe Face Mesh face-oval landmarks, clockwise from the forehead.
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
