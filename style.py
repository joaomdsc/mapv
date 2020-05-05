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
            '020': {
                '0100': dict(
                    description='Void area',
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
    return b

def get_style(category, type_, major, minor):
    maj = major.strip()
    if len(maj) < 3:
        maj = f'{maj:>03}'
    
    min = minor.strip()
    if len(min) < 4:
        min = f'{min:>04}'

    # type_ is 'nodes', 'areas', or 'lines'. We must check in that type but
    # also in multiples

    try:
        # FIXME make pen and brush from d
        d = map_style[category]
        d = d[type_]
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
        