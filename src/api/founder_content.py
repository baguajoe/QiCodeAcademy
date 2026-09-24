"""Founder copy, seeded once so staff can edit it later in the admin.

This text is VERBATIM from the organization. Do not add, change, or embellish
credentials, lineage names, titles, or dates. The frontend keeps an identical
fallback in src/front/js/founderContent.js (checked by tests/test_founder.py).

Format of founder_full_bio: paragraphs separated by blank lines; a line starting
with "## " is a section heading. founder_credentials: one credential per line.
"""

FOUNDER_NAME = "Joseph Gallop"
FOUNDER_ROLE = "Founder & Principal Instructor"

FOUNDER_SHORT_BIO = (
    "Joseph Gallop has spent more than twenty years studying and teaching the internal martial arts: "
    "Tai Chi, Baguazhang, and Xing Yi. A Boston native, he has taught at Grove Hall Community Center "
    "since 2016, in Boston City Parks since 2014, and at Dorchester House, where he leads Tai Chi for "
    "older adults. He has also taught at MIT, UMass Boston, and the Roxbury YMCA. As a senior student "
    "of Master Vincent Chu, he assists in teaching classes in Boston and, since 2022, at Master Chu's "
    "annual international Tai Chi workshop in Prague.\n\n"
    "Joseph is also a 200-hour certified yoga instructor, holds a massage therapy diploma and an Asian "
    "bodywork certification, and earned a Full-Stack Web Developer certification from 4Geeks Academy "
    "in 2024. He founded Qi Code Academy to bring these worlds together: helping older adults stay "
    "active and connected through traditional movement, and teaching young people in Boston's "
    "neighborhoods to build with technology.\n\n"
    "His work has been featured in The Boston Globe and on WCVB Channel 5's Chronicles."
)

FOUNDER_FULL_BIO = (
    "## Lineage and training\n\n"
    "Joseph is a senior student of Master Vincent Chu of Gin Soon Tai Chi. Vincent Chu is the son of "
    "Grandmaster Gin Soon Chu, a disciple of Grandmaster Yang Sau Chung, the eldest son of Yang Cheng "
    "Fu. Joseph assists Master Chu in teaching classes in Boston and, since 2022, at his annual "
    "international Tai Chi workshop in Prague. He has also studied extensively with Arthur Goodridge, "
    "a student of T.T. Liang.\n\n"
    "Joseph's Baguazhang is in the Fu Style lineage, through Sun Ba Gang, a student of Fu Zhen Song, "
    "and Master Tak Wong. He also studied Yin Style Baguazhang of the Cao family, taught by Chen Xiao "
    "Ping.\n\n"
    "## Bodywork and wellness\n\n"
    "Joseph completed 650 hours of study at the New England School of Therapeutics under Richmond "
    "Dickson, earning his massage therapy diploma in 2021. He holds an Asian Bodywork Therapy "
    "certification from Master Tak Wong and a 200-hour yoga teacher certification from 33 Degree "
    "Yoga.\n\n"
    "## Technology, media, and creative work\n\n"
    "Joseph earned a Bachelor of Science from Bowling Green State University, with a minor in Visual "
    "Communications, and a Full-Stack Web Developer certification from 4Geeks Academy. He is the "
    "founder of Eye Forge Studios, the author of the comic book Iron Dragon, and has worked in music "
    "and media production for more than 25 years, with experience in Logic Pro, Final Cut Pro, "
    "Photoshop, and Maya 3D. He has also taught children's Kung Fu, focusing on discipline, respect, "
    "and physical development."
)

FOUNDER_CREDENTIALS = "\n".join([
    "Certified Tai Chi Instructor — training under Master Vincent Chu and Master Tak Wong",
    "200-Hour Yoga Instructor Certification — 33 Degree Yoga, 2020",
    "Massage Therapy Diploma — New England School of Therapeutics, 2021",
    "Asian Bodywork Therapy Certification — Master Tak Wong, 2023",
    "Full-Stack Web Developer Certification — 4Geeks Academy, 2024",
    "BS, Bowling Green State University, 1996",
])
