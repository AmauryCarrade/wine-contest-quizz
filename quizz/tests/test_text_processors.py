from django.test import TestCase

from ..text_processors import normalize, gentle_levenshtein_distance


class TextProcessorsTestCase(TestCase):
    def test_normalization(self):
        self.assertEqual(
            normalize("François Asselineau"),
            "francois asselineau",
            "Accents and other diatrics are removed",
        )

        self.assertEqual(
            normalize(" A String   with     lots of spaceeee      "),
            "a string with lots of spaceeee",
            "Multiples spaces are removed from everywhere",
        )

        self.assertEqual(
            normalize("Line\nBreaks"),
            "line breaks",
            "Lines breaks are replaced with spaces",
        )
        self.assertEqual(
            normalize("Line\n\n\nBreaks"),
            "line breaks",
            "Multiple lines breaks are replaced with a single space",
        )

        self.assertEqual(
            normalize(
                "Agressif : « moi, monsieur, si j'avais un tel nez,\nIl faudrait sur le champ que je me l'amputasse ! »"
            ),
            "agressif moi monsieur si javais un tel nez il faudrait sur le champ que je me lamputasse",
            "Punctuation is removed and multiple occurrences are replaced by a single space",
        )

        self.assertEqual(
            normalize("On pouvait dire... oh ! Dieu ! ... bien des choses en somme..."),
            "on pouvait dire oh dieu bien des choses en somme",
            "Puctuation and spaces are all replaced by a single space per group",
        )

    def test_gentle_levenshtein_distance(self):
        self.assertEqual(
            gentle_levenshtein_distance(
                "Ah ! Non ! C'est un peu court, jeune homme !",
                "Ah! Non! C'est un peu court, jeune homme",
            ),
            0,
            "The gentle Levenshtein distance ignores spaces and missing punctuation",
        )

        self.assertEqual(
            gentle_levenshtein_distance(
                "Que paternellement vous vous préoccupâtes",
                "Que paternellement vous vous préoccupate",
            ),
            1,
            "The gentle Levenshtein distance ignores accents but not ascii characters",
        )

        self.assertEqual(
            gentle_levenshtein_distance(
                "Appelle hippocampelephantocamélos", "Appelle hippocampelephantocamàlos"
            ),
            1,
            "The gentle Levenshtein distances considers a distance of 1 if an accent "
            "is replaced by another non-similar accent",
        )

        self.assertEqual(
            gentle_levenshtein_distance(
                "Cavalier : « quoi, l'ami, ce croc est à la mode ? Pour pendre "
                "son chapeau c'est vraiment très commode ! »",
                "Cavalier : \"quoi, l'ami, ce croc est à la mode ? Pour pendre "
                "son chapeau c'est vraiment très commode ! \"",
            ),
            0,
            "The gentle Levenshtein distance allows mixed punctuation",
        )
