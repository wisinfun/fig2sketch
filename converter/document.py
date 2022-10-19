import utils
from . import fonts
from .context import context


def convert(pages):
    return {
        '_class': 'document',
        'do_objectID': utils.gen_object_id((0, 0), b'document'),
        'assets': {
            '_class': 'assetCollection',
            'do_objectID': utils.gen_object_id((0, 0), b'assetCollection'),
            'imageCollection': {
                '_class': 'imageCollection',
                'images': {}
            },
            'colorAssets': [],
            'gradientAssets': [],
            'images': [],
            'colors': [],
            'gradients': [],
            'exportPresets': []
        },
        'colorSpace': 1,
        'currentPageIndex': 0,
        'foreignLayerStyles': [],
        'foreignSymbols': [],
        'foreignTextStyles': [],
        'foreignSwatches': [],
        'layerStyles': {
            '_class': 'sharedStyleContainer',
            'do_objectID': utils.gen_object_id((0, 0), b'sharedStyleContainer'),
            'objects': []
        },
        'layerSymbols': {
            '_class': 'symbolContainer',
            'do_objectID': utils.gen_object_id((0, 0), b'symbolContainer'),
            'objects': []
        },
        'layerTextStyles': {
            '_class': 'sharedTextStyleContainer',
            'do_objectID': utils.gen_object_id((0, 0), b'sharedTextStyleContainer'),
            'objects': []
        },
        'perDocumentLibraries': [],
        'sharedSwatches': {
            '_class': 'swatchContainer',
            'do_objectID': utils.gen_object_id((0, 0), b'swatchContainer'),
            'objects': [component for component in context.sketch_components() if
                        component['_class'] == 'swatch']
        },
        'fontReferences': convert_fonts(),
        'documentState': {
            '_class': 'documentState'
        },
        'pages': [
            {
                '_class': 'MSJSONFileReference',
                '_ref_class': 'MSImmutablePage',
                '_ref': f"pages/{page.do_objectID}"
            } for page in pages
        ]
    }


def convert_fonts():
    for ffamily in fonts.figma_fonts.keys():
        fonts.download_and_unzip_webfont(ffamily)
    fonts.organize_sketch_fonts()

    font_references = []
    for ffamily, ffamily_dict in fonts.figma_fonts.items():
        for fsfamily, (font_hash, psname) in ffamily_dict.items():
            font_references.append(
                {
                    '_class': 'fontReference',
                    'do_objectID': utils.gen_object_id((0, 0), bytes.fromhex(font_hash)),
                    'fontData': {
                        '_class': 'MSJSONFileReference',
                        '_ref_class': 'MSFontData',
                        '_ref': 'fonts/%s' % font_hash
                    },
                    'fontFamilyName': ffamily,
                    'fontFileName': '%s-%s.ttf' % (ffamily, fsfamily),
                    'options': 3,  # Embedded and used
                    'postscriptNames': [
                        psname
                    ]
                })

    print(fonts.figma_fonts)
    font_references.sort(key=lambda f: f['do_objectID'])

    return font_references
