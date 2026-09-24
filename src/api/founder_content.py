"""Founder copy, seeded so staff can edit it later in the admin.

This text is VERBATIM from the organization (final version, September 2026). Do not
add, change, or embellish credentials, lineage names, titles, or dates. The frontend
keeps an identical fallback in src/front/js/founderContent.js (checked by
tests/test_founder.py).

Format of founder_full_bio: paragraphs separated by blank lines; a line starting
with "## " is a section heading. founder_credentials: one credential per line.
"""

FOUNDER_NAME = "Joseph Gallop"
FOUNDER_ROLE = "Founder & Principal Instructor"

FOUNDER_SHORT_BIO = "Joseph Gallop brings 26 years of training and 18 years of professional teaching in the internal martial arts: Tai Chi, Baguazhang, and Xing Yi. A Boston native, he currently teaches at Grove Hall Senior Center, Codman Square Library, and in Boston City Parks, where he has taught since 2014. He has also taught at Dorchester House, MIT, UMass Boston, and the Roxbury YMCA. As a senior student of Master Vincent Chu, he assists in teaching classes in Boston and, since 2022, at Master Chu's annual international Tai Chi workshop in Prague.\n\nJoseph is also a 200-hour certified yoga instructor, holds a massage therapy diploma and an Asian bodywork certification, and earned a Full-Stack Web Developer certification from 4Geeks Academy in 2024. He founded Qi Code Academy to bring these worlds together: helping older adults stay active and connected through traditional movement, and teaching young people in Boston's neighborhoods to build with technology.\n\nHis work has been featured in The Boston Globe and on WCVB Channel 5's Chronicles."

FOUNDER_FULL_BIO = "## Lineage and training\n\nJoseph is a senior student of Master Vincent Chu of Gin Soon Tai Chi. Vincent Chu is the son of Grandmaster Gin Soon Chu, a disciple of Grandmaster Yang Sau Chung, the eldest son of Yang Cheng Fu. Joseph assists Master Chu in teaching classes in Boston and, since 2022, at his annual international Tai Chi workshop in Prague. He has also studied extensively with Arthur Goodridge, a student of T.T. Liang.\n\nJoseph's Baguazhang is in the Fu Style lineage of Fu Zhen Song, through Sun Baogang and Master Tak Wong. He also studied Cao-style Yin Baguazhang under Chen Xiao Ping, and has taught a Baguazhang workshop in Prague.\n\n## Bodywork and wellness\n\nJoseph completed 650 hours of study at the New England School of Therapeutics under Richmond Dickson, earning his massage therapy diploma in 2021. He holds a myofascial therapy certification, an Asian Bodywork Therapy certification from Master Tak Wong, and a 200-hour yoga teacher certification from 33 Degree Yoga.\n\n## Technology, media, and creative work\n\nJoseph earned a Bachelor of Science from Bowling Green State University, with a minor in Visual Communications, and a Full-Stack Web Developer certification from 4Geeks Academy. He is the founder of Eye Forge Studios, the author of the comic book Iron Dragon, and has worked in music and media production for more than 25 years, with experience in Logic Pro, Final Cut Pro, Photoshop, and Maya 3D. He has also taught children's Kung Fu, focusing on discipline, respect, and physical development."

FOUNDER_CREDENTIALS = "\n".join([
    "Certified Tai Chi Instructor — training under Master Vincent Chu and Master Tak Wong",
    "200-Hour Yoga Instructor Certification — 33 Degree Yoga, 2020",
    "Massage Therapy Diploma — New England School of Therapeutics, 2021",
    "Myofascial Therapy Certification",
    "Asian Bodywork Therapy Certification — Master Tak Wong, 2023",
    "Full-Stack Web Developer Certification — 4Geeks Academy, 2024",
    "BS, Bowling Green State University, 1996"
])

# SHA-256 fingerprints of earlier seeded versions (the old wording is intentionally
# not kept in the codebase). `flask seed` replaces a value whose fingerprint matches
# with the current text, but never overwrites anything staff have edited.
LEGACY_FINGERPRINTS = {
    "short_bio": {"b66c5e708f4e688feef3c354155c2cfc9963655422b9f240cb0cfde799154efb"},
    "full_bio": {"c9d2739d2dd066b15d1b2814d090d3a0b91ed100efc7c4f6d149e8dee9fe1bc7"},
    "credentials": {"fd7a52f3c5cb4356cbdd7a6b9577e34fe772a3cc54a8a34482f387f03a26b182"},
}


def fingerprint(text):
    import hashlib
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
