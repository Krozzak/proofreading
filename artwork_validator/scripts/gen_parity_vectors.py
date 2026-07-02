# scripts/gen_parity_vectors.py
"""
Generates cross-language parity vectors for the web port.

Runs the real Python validation engines (LithoValidator legacy + EnhancedValidator)
on synthetic briefs and dumps the expected outputs as JSON. The vitest suite in
artwork-validator-web/tests/core/parity.test.ts asserts that the TypeScript port
produces deep-equal results.

Usage:
    cd artwork_validator
    python scripts/gen_parity_vectors.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.validator import LithoValidator
from core.brand_configs.mny_config import MNYBrandConfig
from core.brand_configs.essie_config import ESSIEBrandConfig

OUTPUT = os.path.join(
    os.path.dirname(__file__), '..', '..',
    'artwork-validator-web', 'tests', 'fixtures', 'parity', 'vectors.json'
)


def make_row(**kwargs):
    """Builds an Excel record the way get_data_for_litho returns them."""
    row = {
        'LITHO': 'YCA12345',
        'DECRIPTION': 'MNY DISPLAY FALL',
        'UPC SEQUENCE': '',
        'UPC POSITION': 1,
        'UPC': '12345678901',
        'PRODUCT DESCRIPTION': 'MNY SS LIPSTICK',
        'SHADE NAME': 'FOREST BROWN',
        'SHADE NUMBER': 110,
        'PRODUCT FACING SL': 2,
        '4 DIGITS': 4501,
    }
    row.update(kwargs)
    return row


CASES = [
    {
        'name': 'standard_all_match',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'MNY SUPER STAY LIPSTICK 110 FOREST BROWN 120 CRIMSON RED shade info',
        'excel_data': [
            make_row(SHADE_ignore=None, **{'SHADE NAME': 'FOREST BROWN', 'SHADE NUMBER': 110}),
            make_row(**{'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120, 'UPC': '12345678902'}),
        ],
    },
    {
        'name': 'standard_partial_failures',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'MNY LIPSTICK 110 FOREST BROWN only',
        'excel_data': [
            make_row(),
            make_row(**{'SHADE NAME': 'MISSING SHADE', 'SHADE NUMBER': 999, 'UPC': '12345678902'}),
        ],
    },
    {
        'name': 'wtp_to_waterproof',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'GREAT LASH WATERPROOF MASCARA 401',
        'excel_data': [
            make_row(**{'SHADE NAME': 'GREAT LASH WTP', 'SHADE NUMBER': 401}),
        ],
    },
    {
        'name': 'waterproof_to_wtp_multi_occurrence',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'GREAT WTP LASH WTP MASCARA 401',
        'excel_data': [
            make_row(**{'SHADE NAME': 'GREAT WATERPROOF LASH WATERPROOF', 'SHADE NUMBER': 401}),
        ],
    },
    {
        'name': 'frame_and_space_saver',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'NOTHING RELEVANT HERE',
        'excel_data': [
            make_row(**{'PRODUCT FACING SL': 'FRAME', 'SHADE NAME': 'ABSENT', 'SHADE NUMBER': 111}),
            make_row(**{'UPC': 'SPACE_SAVER', 'SHADE NAME': 'ALSO ABSENT', 'SHADE NUMBER': 222}),
            make_row(**{'SHADE NAME': 'REAL PRODUCT', 'SHADE NUMBER': 333}),
        ],
    },
    {
        'name': 'mixed_facings',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'MNY 110 FOREST BROWN 120 CRIMSON RED',
        'excel_data': [
            make_row(**{'PRODUCT FACING SL': 2}),
            make_row(**{'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120, 'PRODUCT FACING SL': 3}),
            make_row(**{'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120, 'PRODUCT FACING SL': 'FRAME'}),
        ],
    },
    {
        'name': 'digits_check_enabled',
        'brand': 'MNY',
        'check_digits': True,
        'pdf_text': 'MNY 110 FOREST BROWN 4501 AND 120 CRIMSON RED WITHOUT DIGITS',
        'excel_data': [
            make_row(**{'4 DIGITS': 4501}),
            make_row(**{'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120, '4 DIGITS': 9999}),
            make_row(**{'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120, '4 DIGITS': ''}),
        ],
    },
    {
        'name': 'digits_check_disabled_by_brand',
        'brand': 'ESSIE',
        'check_digits': True,
        'pdf_text': 'ESSIE 2-IN-1 BASE & TOP COAT GEL COUTURE',
        'excel_data': [
            {
                'LITHO': 'CARE_S26_1_3',
                'DECRIPTION': 'ESSIE CARE DISPLAY',
                'UPC SEQUENCE': '',
                'UPC POSITION': 1,
                'UPC': '12345678901',
                'PRODUCT DESCRIPTION': 'ESSIE CARE',
                'SHADE NAME': 'GEL COUTURE',
                'SHADE NUMBER': '2-IN-1 BASE & TOP COAT',
                'PRODUCT FACING SL': 1,
            },
        ],
    },
    {
        'name': 'cubby_with_upc_sequence',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'MNY CUBBY DISPLAY 10F2T',
        'excel_data': [
            make_row(**{
                'DECRIPTION': 'MNY CUBBY 10F2T FALL',
                'UPC SEQUENCE': 'UPC.1, UPC.2, UPC.3',
                'UPC': 'UPC.2', 'SHADE NAME': 'SHADE B', 'SHADE NUMBER': 2,
            }),
            make_row(**{
                'DECRIPTION': 'MNY CUBBY 10F2T FALL',
                'UPC SEQUENCE': 'UPC.1, UPC.2, UPC.3',
                'UPC': 'UPC.1', 'SHADE NAME': 'SHADE A', 'SHADE NUMBER': 1,
            }),
            make_row(**{
                'DECRIPTION': 'MNY CUBBY 10F2T FALL',
                'UPC SEQUENCE': 'UPC.1, UPC.2, UPC.3',
                'UPC': 'FRAME', 'SHADE NAME': '', 'SHADE NUMBER': '',
            }),
            make_row(**{
                'DECRIPTION': 'MNY CUBBY 10F2T FALL',
                'UPC SEQUENCE': 'UPC.1, UPC.2, UPC.3',
                'UPC': 'UPC.3', 'SHADE NAME': 'SHADE C', 'SHADE NUMBER': 3,
            }),
        ],
    },
    {
        'name': 'cubby_tier_rollover',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'CUBBY',
        'excel_data': [
            make_row(**{'DECRIPTION': 'CUBBY 3F2T', 'UPC': 'UPC.1', 'SHADE NAME': 'A1', 'SHADE NUMBER': 1}),
            make_row(**{'DECRIPTION': 'CUBBY 3F2T', 'UPC': 'UPC.2', 'SHADE NAME': 'A2', 'SHADE NUMBER': 2}),
            make_row(**{'DECRIPTION': 'CUBBY 3F2T', 'UPC': 'UPC.3', 'SHADE NAME': 'A3', 'SHADE NUMBER': 3}),
            make_row(**{'DECRIPTION': 'CUBBY 3F2T', 'UPC': 'UPC.1', 'SHADE NAME': 'B1', 'SHADE NUMBER': 4}),
            make_row(**{'DECRIPTION': 'CUBBY 3F2T', 'UPC': 'UPC.2', 'SHADE NAME': 'B2', 'SHADE NUMBER': 5}),
            make_row(**{'DECRIPTION': 'CUBBY 3F2T', 'UPC': 'UPC.4', 'SHADE NAME': 'OVERFLOW', 'SHADE NUMBER': 6}),
        ],
    },
    {
        'name': 'cubby_default_dimensions',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'ANY TEXT',
        'excel_data': [
            make_row(**{'DECRIPTION': 'CUBBY DISPLAY', 'UPC': '11111111111', 'SHADE NAME': 'X', 'SHADE NUMBER': 7}),
        ],
    },
    {
        'name': 'no_upc_sequence_column_order_kept',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'CUBBY TEXT',
        'excel_data': [
            {k: v for k, v in make_row(**{'DECRIPTION': 'MNY 10F2T', 'UPC': 'B', 'SHADE NAME': 'B', 'SHADE NUMBER': 2}).items() if k != 'UPC SEQUENCE'},
            {k: v for k, v in make_row(**{'DECRIPTION': 'MNY 10F2T', 'UPC': 'A', 'SHADE NAME': 'A', 'SHADE NUMBER': 1}).items() if k != 'UPC SEQUENCE'},
        ],
    },
]

ENHANCED_CASES = [
    {
        'name': 'enhanced_standard',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'MNY SUPER 110 FOREST BROWN THEN 120 CRIMSON RED trailing words',
        'excel_data': [
            make_row(),
            make_row(**{'SHADE NAME': 'CRIMSON RED', 'SHADE NUMBER': 120}),
        ],
    },
    {
        'name': 'enhanced_duplicate_bug_rows_ge_2',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': '110 FOREST BROWN 110 FOREST BROWN 110 FOREST BROWN',
        'excel_data': [
            make_row(),
            make_row(),
            make_row(),
        ],
    },
    {
        'name': 'enhanced_orphans_and_failures',
        'brand': 'MNY',
        'check_digits': True,
        'pdf_text': 'RANDOM 4501 WORDS 110 FOREST BROWN EXTRA TOKENS HERE',
        'excel_data': [
            make_row(),
            make_row(**{'SHADE NAME': 'NOT PRESENT', 'SHADE NUMBER': 987, '4 DIGITS': 1234}),
        ],
    },
    {
        'name': 'enhanced_accented_shade_name',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'MNY 110 ROSÉ NUDE COLLECTION',
        'excel_data': [
            make_row(**{'SHADE NAME': 'ROSÉ NUDE'}),
        ],
    },
    {
        'name': 'enhanced_wtp_normalization',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'GREAT LASH WATERPROOF 401',
        'excel_data': [
            make_row(**{'SHADE NAME': 'LASH WTP', 'SHADE NUMBER': 401}),
        ],
    },
    {
        'name': 'enhanced_frame_space_saver',
        'brand': 'MNY',
        'check_digits': False,
        'pdf_text': 'ONLY 333 REAL PRODUCT HERE',
        'excel_data': [
            make_row(**{'PRODUCT FACING SL': 'FRAME', 'SHADE NAME': 'ABSENT', 'SHADE NUMBER': 111}),
            make_row(**{'PRODUCT DESCRIPTION': 'SPACE_SAVER', 'SHADE NAME': 'ALSO ABSENT', 'SHADE NUMBER': 222}),
            make_row(**{'SHADE NAME': 'REAL PRODUCT', 'SHADE NUMBER': 333}),
        ],
    },
]


def clean_rows(rows):
    """Removes helper keys that are not real Excel columns."""
    return [{k: v for k, v in row.items() if not k.startswith('SHADE_ignore')} for row in rows]


def build_validator(brand, check_digits):
    config = MNYBrandConfig() if brand == 'MNY' else ESSIEBrandConfig()
    validator = LithoValidator(brand_config=config)
    validator.check_digits = check_digits
    return validator


def main():
    vectors = {'legacy': [], 'enhanced': []}

    for case in CASES:
        validator = build_validator(case['brand'], case['check_digits'])
        excel_data = clean_rows(case['excel_data'])
        results = validator.validate(case['pdf_text'], excel_data)
        vectors['legacy'].append({
            'name': case['name'],
            'brand': case['brand'],
            'check_digits': case['check_digits'],
            'pdf_text': case['pdf_text'],
            'excel_data': excel_data,
            'expected': results,
        })

    for case in ENHANCED_CASES:
        validator = build_validator(case['brand'], case['check_digits'])
        validator.enhanced_validator.check_digits = case['check_digits']
        excel_data = clean_rows(case['excel_data'])
        full = validator.enhanced_validator.validate_enhanced(case['pdf_text'], excel_data)
        # Drop the normalized-row echo keys that leak the input back
        vectors['enhanced'].append({
            'name': case['name'],
            'brand': case['brand'],
            'check_digits': case['check_digits'],
            'pdf_text': case['pdf_text'],
            'excel_data': excel_data,
            'expected': {
                'results': full['results'],
                'stats': full['stats'],
                'errors': full['errors'],
                'orphan_tokens': full.get('orphan_tokens', []),
                'summary': full.get('summary'),
            },
        })

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(vectors, f, indent=2, ensure_ascii=False)
    print(f"OK: {len(vectors['legacy'])} legacy + {len(vectors['enhanced'])} enhanced vectors -> {OUTPUT}")


if __name__ == '__main__':
    main()
