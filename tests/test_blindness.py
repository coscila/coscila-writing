# SPDX-License-Identifier: Apache-2.0
"""Lab-facing writing files carry no tokens of the census study the lab reproduces (hashed, as in coscila-review)."""
from __future__ import annotations

import hashlib
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Verbatim copy of FORBIDDEN from coscila-review tests/test_instruments.py, including its rounded, fraction and
# further forms; keep the two copies in step.
FORBIDDEN = {
    4: {"0c90dd551bf12b5fecc7a9c5caa5a728d45b1c2a5f1760aca9331c12ce0df252",
        "c31e0fcedb154b3269a7fbf9b8e71a41d16af95fd4b16cb805df3dcdddf0e700"},
    5: {"0cbe66614a15a187a5aa341c71efafd84d550ff34dc178e773605f28f45cc84b",
        "1a5cf5c59619f15229f4f8c805d0667fd7c2e4001194717fb7ee62582f829045",
        "23c6a973a31b0bd5f99638209767556a02ac34bb793729382b6fd994d1e90b91",
        "486f4110f8bbcf7eda1c0878929785fddddfa708c01ab0a7ef55a79c8ca6d834",
        "787e3c87ea2a0aa33edd0cc62d12ffd6d5c5457f12bbeab3bc9cedeffc06c8e9",
        "844cb8bb059c33fa526cb7124d8c52c6ff309f5113241e4dd16e04f20c9b005d",
        "94957c17d26f4b6175d2162c79e1165bd4071fbba49ae5797c00b1b3131b31b7",
        "a46773d48e58ed47190eba1132d7d735ab2d06fd94859332b8ead7bc2e5163e9",
        "b8ad25220cb9a5bcb26f18dac02f87a1e947b58e5cba443d566601a4e9cd601e",
        "fc17580b56601023f5104f60e79b6e3390def8e30e35cc4fc0ab4ed1a5de3777"},
    6: {"2c1ea11a3e37bce82366e296bbb04a05204ae360b5046b7ebe103682bfbace78",
        "357bd9eef9d277dae8eabee6f41863f6a7489733bafdeb12c7770524a9e51b59",
        "36d383e4f228cc0bdbfcaaf4d78ef76bd7dc2767737a7af341e8c49277be30b7",
        "3e933e14fd7af6bce60513e218c94d1210e2e43eaecb68c911762ace10142a55",
        "47214e5b4a0d19d7eda978b74955ba4e914e0bb4020ecca9dc036241424917d5",
        "d7198881bf92a4872f10e9fa0ef00fb5c8860f56060f85642fcbe1d4ac05a6fd",
        "d88fb831cf45ec772adf0d3aa8537656fe3656b94c06965929d6cfe1d98c7e11"},
    7: {"6736ce4e60cd6dd9edd3bf565368a5cb70c18b0a5c53f4b032f6fc81badd7ff0",
        "9973b513d82595b8bd6b569b85ab24ea7d6793074697276db508ed424124e31a",
        "c0c83edd9625e9bb2d3cd03550dc250197624f743a1a5bd3dad969167bdc8347"},
    8: {"2991c4f2dbfc89e3e183e2afafd355e3901bce7b8c2752b280125ebd5648e769",
        "42474026dbf58ea83c4f5a17a2ce9f74e5690a9ab3b9195e8682d39ad3a17dd2",
        "4636f0a96191eb01b381ce832aa8c719e1a4a92d106067a4102b7534cd7bd48b",
        "7d24b99d06d2eaaacb3962cbd29ebce5c4ccd4c3be5a1ebae44c370ff1d60d5b",
        "7fcf1fa435db30d801a0cabcf6b52a5a01b13c63cd9cf2dd2c2ebe5ce99b20ef",
        "87e405c491a5436773e6386d96c2eabba587a224508a2eda3fcfe4333f3dfb27",
        "a18577d59248e450bed92c174eaa2b1fdeacd73d7b417a819085dd8543c7b3eb",
        "e89c2935a82eb5858fdb7b1ec108c72b5fc288730f5dfd123a53a591a625d4b9",
        "f08b56e242e5cab22bfce9b61d13b457a8f7bf49db4343ff2243a1f72aa76550"},
    9: {"5ae55e00a3e720f2689992cec849487cddbd3903ecabe29db9331004e2912045",
        "ac3fdda654a75afb24caa46cfc59612c03d3daaee4cbfdb94833df7eee51e24e"},
    12: {"2463f01a9b90a2ad08a97f6c854d48e18ced053a7f61906c01e12b4ab438990b"},
    42: {"d8e6d64915d843b393a00b1c75711cf9b95a45cb5ec3ca55f2194600e4daea33"},
    53: {"4a644f4c0b74832906e22a4322b92a083cc26e14fa38b131b03fc46b4c16684e"},
}
# Rounded, fraction and spacing variants of study figures, the forms a facts-lint example or a written range can take.
for _length, _digests in {
    4: {"3e239cbbd360793f0ebd640df0b475e267be0cf1d7d7c80a6250ba0fc6e1f566",
        "974c474e03d760995d1bac1d06fbcd28a8d62b16a5b53f212cbbe6134832939d",
        "a7071849fb72be7f6138ee4d048867bcd88f2250589bc6da81141fb8fce73d89",
        "aaae6b81b3239e64dbcd6dc0b5dfa117884d112b56ddaf59ab9ef9b8f94bb7d2",
        "f1e8aa5a065b37a6d729411d50b8531b35a836efa6ca8efb20d028d9df83d2aa"},
    5: {"f9cd6c42de299434f0cace60f6d4837206dddb9dddeee6a9e37869cf671859cf"},
    6: {"3bd54cc0263127e91067fca32cd9b3a1f0ec2f73e1c1647a88b93ad4033c2751",
        "928423789231f88fc7042d8140369886581e87d1d7c342385f687467fc5037fc"},
    7: {"52a3d7397e8776140a09443ec657d971371625d344c9208cfdee6e56661a144a"},
    9: {"52ae8db672be4012d76616a42c6b3093fa364d46c1b687c0e26895a566068f9f"},
    10: {"0040ce1bd1f1b649087327396c80c29d5b68f4a2d7861ecf52c0ed8ddcb97204",
         "039ed5ce153c651a4c083c0ce5a57b0831843bf7c13cc2ced001bee5d9dba80c"},
    11: {"b3d18e1164052ad49fcb59ee72190d6ca9594d6ccd2f04c2149633f4faf2fded"},
}.items():
    FORBIDDEN.setdefault(_length, set()).update(_digests)
# Further study figures and identifiers a final review found missing: population and readable counts with and without
# separators, corpus totals, the diagnostic bands in both dash spellings, token and runtime totals, the corrected
# report's title and file names, the snapshot's directory name, and the identifiers of further census sessions.
for _length, _digests in {
    4: {"0a95ca5e3efad73cd92ae12559d1189d05ff48b6344f0f83f760e59352f22689",
        "6c4c237fa6808f1c64a0a64254a296c0b006ede809a804447cd6dc06b46cb192",
        "aaae6b81b3239e64dbcd6dc0b5dfa117884d112b56ddaf59ab9ef9b8f94bb7d2"},
    5: {"139923821f09b19101c003fb15d7b873c0d37b528a80f61936eff528b1a0acbc",
        "20d4ea1b58b071504152736437b77fd13793af17b3a4ca0611f9793d0d36a838",
        "589b1174e8d1f3a929d4c9237c06614379e9d061503c19ede8c00529b320ec98",
        "69d325d196c62c699477760d45136fb4b56550cd8fc6ded59d5ed6f6e8bb1488",
        "ce7971f95aeac24e316891e78bfa924ceac221030e7f03ffdae5c0f9af06e4a5"},
    6: {"6dc2606829c647713389befda0fb36a684a41d042c738863a40bf4b060488ba7",
        "b3384b6dff9e1bef0865f9d58d8b78d43ae118f5fbe6ad874a3b032df584bfd8",
        "c603e8999513029e44d9e978c1fc67f6fe08f7dda2158d8a9d22ed7ebbaac7de"},
    7: {"28ad27422591424f71c86df882f94dfaf52a45930cf67e8486a27bd892fae388",
        "3007dd62825805d659236c8fbbbeddfbf6c0142ea348a48e41b93517856ffee3",
        "35a94fec15e6ecef565c0e271154a4490d7b3e6a2c524fa5105126af55be3d45",
        "52a3d7397e8776140a09443ec657d971371625d344c9208cfdee6e56661a144a",
        "b8c2168dd9b003c2831c38e953d3e93ca149a7c83ad6399af08f05b1637d6529",
        "f379cdca4ff319e198b2bb178c54cdeb6ce6aad81206092c55522c3f90c69fe2"},
    8: {"1003143bea389f7ef87fa8c910464010c8bc8c7d5864f116bb2a4878688f48c9",
        "322ade8662be4dd8776d5021ddb866ed3ffdd26d8d6c91b03ac5c2a0ad4bb668",
        "54b0dc5426c4e7100617f94b1421a71a42f8b986f395378e7b7f087e15b8fd44",
        "8d9174f77b32df3dd6bd11330a9f2f0e38582340619fb3ac472ba1bc3f4ceeca",
        "c08b71f7f21a6d9b060343d2426c243e742aea023f08074d0c46b54f6c89ca09",
        "dcc58a67a288e50ff9f31b805e7cf1a29e9ba2d188e8cce3a0ee944566d89d75"},
    9: {"0d5887fe37d9f3447ee1f57da00aee968a4e47adb40f1a129f679f10d45258a8"},
    10: {"b23d1ce0d23777d1e3d54a39edb274ec0e3ca91dcb8eda72a0e32344868f7da7",
        "d8c0e27bab7b0333437c043441f313ff792755325b8c5b37cfcb445142a5c3b7"},
    12: {"7e67e8069bd0cdf29a6f7608d7ebcc6a8cc181be232a119b7df0072c5cb6265d"},
    16: {"290b42a29e439a84354ca30fcfa035dca0d3eec9297f5ef35b77b89113b9a235",
        "9ceab4517efe93e787263de5fdcd5bbd5ea955ac47449f93453905505ad8138c"},
    20: {"b77790e3aec8b76e96fef34e34ca6667da8c87f786d5b01352c2e6b8cebdc7d0",
        "b965fe2d415f0f51958dcaeb121e5feb863b6258496ea78f078303213af0a9a0"},
    21: {"3837e95ba23a92e4ec96e2768e54ba4c6091f22c2fda291b219c511deafa5332",
        "715a0fcdccb251665c3abd899d877027259671e21c2bf9eb69cc9a9e11063ade"},
    23: {"31f89bc0c1520411347e937220e6c599ba8f5f67ebb56d9e6d4086d504015c81"},
    51: {"eae3d450ca367e62d119f56da83d611e6f5239d32ba2746dd08e8a72ecbcc531"},
}.items():
    FORBIDDEN.setdefault(int(_length), set()).update(_digests)
SPACES = str.maketrans({"\u00a0": " ", "\u2007": " ", "\u2009": " ", "\u200a": " ", "\u202f": " "})
SCANNED = ("skills", "docs", "src", "tests", "README.md")
EXCLUDED = ("tests/test_blindness.py",)


def hits(text: str) -> list[int]:
    text = text.translate(SPACES)
    found = []
    for start in range(len(text)):
        if start and (text[start - 1].isalnum() or text[start - 1] == "."):
            continue
        for length, digests in FORBIDDEN.items():
            window = text[start:start + length]
            if len(window) == length and hashlib.sha256(window.encode("utf-8")).hexdigest() in digests:
                found.append(start)
    return found


class BlindnessTests(unittest.TestCase):
    def test_lab_facing_writing_files_carry_no_study_tokens(self):
        names = subprocess.run(["git", "-C", str(ROOT), "ls-files", *SCANNED], capture_output=True, text=True,
                               check=True, timeout=30).stdout.splitlines()
        files = [ROOT / name for name in names if name not in EXCLUDED and (ROOT / name).is_file()]
        self.assertGreater(len(files), 100)
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertEqual([], hits(text))

    def test_writing_skills_name_no_earlier_headline_or_legacy_replay(self):
        """Phrases that point a reader to an earlier study's results; whitespace is folded before matching."""
        phrases = ("earlier headline", "legacy workflow", "historical outputs", "oncology census",
                   "five figure themes", "panel drawn only from flagged", "earlier census", "earlier study")
        for name in ("skills/facts-first-reporting/SKILL.md", "skills/llm-judge-study-reporting/SKILL.md",
                     "skills/llm-judge-study-reporting/references/reporting-standard.md", "docs/runtime.md"):
            text = " ".join((ROOT / name).read_text(encoding="utf-8").lower().split())
            with self.subTest(path=name):
                for phrase in phrases:
                    self.assertNotIn(phrase, text)

    def test_scanner_detects_tokens_at_word_starts_only(self):
        global FORBIDDEN
        saved = FORBIDDEN
        try:
            FORBIDDEN = {5: {hashlib.sha256(b"7.7 %").hexdigest()}}
            self.assertTrue(hits("a share of 7.7 % here"))
            self.assertTrue(hits("a share of 7.7\u202f% here"))
            self.assertFalse(hits("a share of 17.7 % here"))
        finally:
            FORBIDDEN = saved


if __name__ == "__main__":
    unittest.main()
