# mapv/style.py - define graphical styles for attributes

import wx

light_blue = (214, 237, 251)
darker_blue = (0, 128, 255)
dark_green = (47, 79, 47)
dark_orange = (204, 50, 50)

map_style = dict(
    boundaries=dict(
        nodes={
            '020': None,
        },
        areas={
            '090': {
                '0100': dict(
                    description='Civil township, district, precinct, or barrio',
                    brush_color=(15, 128, 217, 20),
                ),
                '0101': dict(
                    description='Incorporated city, village, town, borough, or hamlet',
                    brush_color=(35, 178, 187, 20),
                ),
                '0103': dict(
                    description='National park, monument, lakeshore, seashore, parkway, battlefield, or recreation area',
                    brush_color=(55, 78, 157, 20),
                ),
                '0104': dict(
                    description='National forest or grassland',
                    brush_color=(75, 178, 127, 20),
                ),
                '0105': dict(
                    description='National wildlife refuge, game preserve, or fish hatchery',
                    brush_color=(95, 78, 97, 20),
                ),
                '0106': dict(
                    description='National scenic waterway, riverway, wild and scenic river, or wilderness area',
                    brush_color=(115, 178, 67, 20),
                ),
                '0107': dict(
                    description='Indian reservation',
                    brush_color=(135, 78, 37, 20),
                ),
                '0108': dict(
                    description='Military reservation',
                    brush_color=(155, 178, 7, 20),
                ),
                '0111': dict(
                    description='Miscellaneous Federal reservation',
                    brush_color=(175, 78, 247, 20),
                ),
                '0129': dict(
                    description='Miscellaneous State reservation',
                    brush_color=(195, 178, 200, 20),
                ),
                '0130': dict(
                    description='State park, recreation area arboretum, or lake',
                    brush_color=(215, 78, 190, 20),
                ),
                '0150': dict(
                    description='Large park (city, county, or private)',
                    brush_color=(140, 100, 170, 20),
                ),
            },
            '091': {
                '0025': dict(
                    description='Massachusetts',
                    pen_color=dark_green,
                    brush_color=(95, 78, 97),
                ),
                '0044': dict(
                    description='Rhode Island',
                    pen_color='red',
                    brush_color=(215, 78, 190),
                ),
            },
        },
    ),
    hydrography=dict(
        areas={
            '050': {
                '0100': dict(description='Void area'),
                '0101': dict(
                    description='Reservoir',
                    pen_color='gray',
                    brush_color=(64, 128, 128),
                ),
                '0111': dict(
                    description='Marsh, wetland, swamp, bog',
                    pen_color='gray',
                    brush_color=dark_green,
                ),
                '0116': dict(
                    description='Bays, estuaries, gulfs, oceans, seas',
                    brush_color=light_blue,
                ),
            },
        },
        lines={
            '050': {
                # '0202': dict(
                #     description='Closure line',
                #     pen_color='red',
                # ),
                '0204': dict(
                    description='Apparent limit',
                    pen_color=dark_orange,
                ),
            },
        },
        multiple={
            '050': {
                '0412': dict(
                    description='Stream',
                    pen_color=darker_blue,
                    brush_color=light_blue,
                ),
                # '0414': dict(
                #     description='Ditch or canal',
                #     pen_color='red',
                #     brush_color='red',
                # ),
                '0415': dict(
                    description='Aqueduct',
                    pen_color=dark_orange,
                    brush_color=dark_orange,
                ),
                '0421': dict(
                    description='Lake or pond',
                    brush_color=light_blue,
                ),
                '0604': dict(
                    description='Tunnel',
                    pen_color=dark_orange,
                    brush_color=dark_orange,
                ),
            },
        },
    ),
    hypsography=dict(
    
    ),
    railroads=dict(
        
    ),
    transmission=dict(
        
    ),
    roads=dict(
        
    ),
    public_land=dict(
        
    ),
)

def get_style(category, type_, major, minor, id=None):
    maj = major.strip()
    if len(maj) < 3:
        maj = f'{maj:>03}'
    
    min = minor.strip()
    if len(min) < 4:
        min = f'{min:>04}'

    # type_ is 'nodes', 'areas', or 'lines'. We must check in that type but
    # also in multiples
    # print(f'get_style: {category}, {type_} (id={id}), {maj}, {min}')

    try:
        # FIXME make pen and brush from d
        d = map_style[category]
        d = d[type_]
        d = d[maj]
        d = d[min]
        # print(f'd={d}')
        pen_color = None
        if 'pen_color' in d:
            pen_color = d['pen_color']
        brush_color = None
        if 'brush_color' in d:
            brush_color = d['brush_color']
        return pen_color, brush_color

    except KeyError:
        try:
            # FIXME make pen and brush from d
            d = map_style[category]
            d = d['multiple']
            d = d[maj]
            d = d[min]
            pen_color = None
            if 'pen_color' in d:
                pen_color = d['pen_color']
            brush_color = None
            if 'brush_color' in d:
                brush_color = d['brush_color']
            return pen_color, brush_color
        except KeyError:
            return None, None
        