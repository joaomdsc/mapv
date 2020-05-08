# mapv/style.py - define graphical styles for attributes

import wx

light_blue = wx.Colour(214, 237, 251)
darker_blue = wx.Colour(0, 128, 255)

map_style = dict(
    boundaries=dict(
        nodes={
            '020': None,
        },
        areas={
            '090': {
                '0100': dict(
                    description='Civil township, district, precinct, or barrio',
                    brush=dict(color=wx.Colour(15, 128, 217, 20)),
                ),
                '0101': dict(
                    description='Incorporated city, village, town, borough, or hamlet',
                    brush=dict(color=wx.Colour(35, 178, 187, 20)),
                ),
                '0103': dict(
                    description='National park, monument, lakeshore, seashore, parkway, battlefield, or recreation area',
                    brush=dict(color=wx.Colour(55, 78, 157, 20)),
                ),
                '0104': dict(
                    description='National forest or grassland',
                    brush=dict(color=wx.Colour(75, 178, 127, 20)),
                ),
                '0105': dict(
                    description='National wildlife refuge, game preserve, or fish hatchery',
                    brush=dict(color=wx.Colour(95, 78, 97, 20)),
                ),
                '0106': dict(
                    description='National scenic waterway, riverway, wild and scenic river, or wilderness area',
                    brush=dict(color=wx.Colour(115, 178, 67, 20)),
                ),
                '0107': dict(
                    description='Indian reservation',
                    brush=dict(color=wx.Colour(135, 78, 37, 20)),
                ),
                '0108': dict(
                    description='Military reservation',
                    brush=dict(color=wx.Colour(155, 178, 7, 20)),
                ),
                '0111': dict(
                    description='Miscellaneous Federal reservation',
                    brush=dict(color=wx.Colour(175, 78, 247, 20)),
                ),
                '0129': dict(
                    description='Miscellaneous State reservation',
                    brush=dict(color=wx.Colour(195, 178, 200, 20)),
                ),
                '0130': dict(
                    description='State park, recreation area arboretum, or lake',
                    brush=dict(color=wx.Colour(215, 78, 190, 20)),
                ),
                '0150': dict(
                    description='Large park (city, county, or private)',
                    brush=dict(color=wx.Colour(140, 100, 170, 20)),
                ),
            },
            '091': {
                '0025': dict(
                    description='Massachusetts',
                    pen=dict(color='dark green'),
                    brush=dict(color=wx.Colour(95, 78, 97)),
                ),
                '0044': dict(
                    description='Rhode Island',
                    pen=dict(color='red'),
                    brush=dict(color=wx.Colour(215, 78, 190)),
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
                    pen=dict(
                        width=2,
                        color='gray',
                    ),
                    brush=dict(color=wx.Colour(64, 128, 128)),
                ),
                '0111': dict(
                    description='Marsh, wetland, swamp, bog',
                    pen=dict(
                        color='gray',
                    ),
                    brush=dict(color='dark green'),
                ),
                '0116': dict(
                    description='Bays, estuaries, gulfs, oceans, seas',
                    brush=dict(color=light_blue),
                ),
            },
        },
        lines={
            '050': {
                # '0202': dict(
                #     description='Closure line',
                #     pen=dict(color='red'),
                # ),
                '0204': dict(
                    description='Apparent limit',
                    pen=dict(color='dark orange'),
                ),
            },
        },
        multiple={
            '050': {
                '0412': dict(
                    description='Stream',
                    pen=dict(color=darker_blue),
                    brush=dict(color=light_blue),
                ),
                # '0414': dict(
                #     description='Ditch or canal',
                #     pen=dict(color='red'),
                #     brush=dict(color='red'),
                # ),
                '0415': dict(
                    description='Aqueduct',
                    pen=dict(color='dark orange'),
                    brush=dict(color='dark orange'),
                ),
                '0421': dict(
                    description='Lake or pond',
                    brush=dict(color=light_blue),
                ),
                '0604': dict(
                    description='Tunnel',
                    pen=dict(color='dark orange'),
                    brush=dict(color='dark orange'),
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

def make_pen(params):
    """Arg 'params' is a dict"""
    p = wx.Pen()
    if 'width' in params:
        p.SetWidth(params['width'])
    if 'color' in params:
        p.SetColour(params['color'])
    return p

def make_brush(params):
    """Arg 'params' is a dict"""
    b = wx.Brush()
    if 'width' in params:
        b.SetWidth(params['width'])
    if 'color' in params:
        b.SetColour(params['color'])
    # print(f'make_brush: b={b}, color={b.GetColour()}')
    return b

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
        pen = None
        if 'pen' in d:
            pen = make_pen(d['pen'])
        brush = None
        if 'brush' in d:
            brush = make_brush(d['brush'])
        return pen, brush

    except KeyError:
        try:
            # FIXME make pen and brush from d
            d = map_style[category]
            d = d['multiple']
            d = d[maj]
            d = d[min]
            pen = None
            if 'pen' in d:
                pen = make_pen(d['pen'])
            brush = None
            if 'brush' in d:
                brush = make_brush(d['brush'])
            return pen, brush
        except KeyError:
            return None, None
        